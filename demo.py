import os
import shutil
import tempfile
import subprocess
import time
import sys
from pathlib import Path


def run_command(command):
    print(f"\n> {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    source_dir = tempfile.mkdtemp()
    db_dir = tempfile.mkdtemp()
    restore_dir = tempfile.mkdtemp()

    try:
        print(f"Source directory: {source_dir}")
        print(f"Database directory: {db_dir}")
        print(f"Restore directory: {restore_dir}")

        print("\nCreating test files...")
        os.makedirs(os.path.join(source_dir, "docs"), exist_ok=True)
        os.makedirs(os.path.join(source_dir, "images"), exist_ok=True)

        with open(os.path.join(source_dir, "file1.txt"), "w") as f:
            f.write("This is file 1")

        with open(os.path.join(source_dir, "docs", "document.txt"), "w") as f:
            f.write("This is a document")

        with open(os.path.join(source_dir, "images", "image.bin"), "wb") as f:
            f.write(os.urandom(1024))

        print("\n1. Taking first snapshot...")
        run_command(
            [
                sys.executable,
                "backuptool.py",
                "snapshot",
                f"--target-directory={source_dir}",
                f"--db-path={db_dir}",
            ]
        )

        print("\n2. Listing snapshots...")
        run_command([sys.executable, "backuptool.py", "list", f"--db-path={db_dir}"])

        print("\n3. Modifying files...")
        with open(os.path.join(source_dir, "file1.txt"), "w") as f:
            f.write("This is file 1 - modified")

        with open(os.path.join(source_dir, "file2.txt"), "w") as f:
            f.write("This is a new file")

        print("\n4. Taking second snapshot...")
        run_command(
            [
                sys.executable,
                "backuptool.py",
                "snapshot",
                f"--target-directory={source_dir}",
                f"--db-path={db_dir}",
            ]
        )

        print("\n5. Listing snapshots again...")
        run_command([sys.executable, "backuptool.py", "list", f"--db-path={db_dir}"])

        print("\n6. Restoring the first snapshot...")
        run_command(
            [
                sys.executable,
                "backuptool.py",
                "restore",
                "--snapshot-number=1",
                f"--output-directory={restore_dir}",
                f"--db-path={db_dir}",
            ]
        )

        print("\n7. Listing restored files...")
        for root, dirs, files in os.walk(restore_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, restore_dir)
                print(f"  {rel_path}")

        print("\n8. Pruning the first snapshot...")
        run_command(
            [
                sys.executable,
                "backuptool.py",
                "prune",
                "--snapshot=1",
                f"--db-path={db_dir}",
            ]
        )

        print("\n9. Listing snapshots after pruning...")
        run_command([sys.executable, "backuptool.py", "list", f"--db-path={db_dir}"])

        print("\nDemo completed successfully!")

    finally:
        print("\nCleaning up temporary directories...")
        shutil.rmtree(source_dir, ignore_errors=True)
        shutil.rmtree(db_dir, ignore_errors=True)
        shutil.rmtree(restore_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
