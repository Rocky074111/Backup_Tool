import os
import sys
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backuptool.core import BackupDatabase


class TestBackupToolIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        self.create_test_files()

        self.script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "backuptool.py")
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.db_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def create_test_files(self):
        os.makedirs(os.path.join(self.test_dir, "subdir1"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "subdir2"), exist_ok=True)

        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("This is file 1")

        with open(os.path.join(self.test_dir, "subdir1", "file2.txt"), "w") as f:
            f.write("This is file 2")

        with open(os.path.join(self.test_dir, "subdir2", "file3.txt"), "w") as f:
            f.write("This is file 3")

        with open(os.path.join(self.test_dir, "binary_file.bin"), "wb") as f:
            f.write(os.urandom(1024))

    def run_command(self, args):
        command = [sys.executable, self.script_path] + args
        result = subprocess.run(command, capture_output=True, text=True)
        return result

    def test_snapshot_and_list(self):
        result = self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("Created snapshot 1", result.stdout)

        result = self.run_command(["list", f"--db-path={self.db_dir}"])

        self.assertEqual(0, result.returncode)
        self.assertIn("SNAPSHOT", result.stdout)
        self.assertIn("1", result.stdout)

    def test_snapshot_and_restore(self):
        result = self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        self.assertEqual(0, result.returncode)

        result = self.run_command(
            [
                "restore",
                "--snapshot-number=1",
                f"--output-directory={self.output_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        self.assertEqual(0, result.returncode)
        self.assertIn(f"Restored snapshot 1 to {self.output_dir}", result.stdout)

        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file1.txt")))
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "subdir1", "file2.txt"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "subdir2", "file3.txt"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "binary_file.bin"))
        )

        with open(os.path.join(self.output_dir, "file1.txt"), "r") as f:
            self.assertEqual("This is file 1", f.read())

        with open(os.path.join(self.test_dir, "binary_file.bin"), "rb") as f1:
            with open(os.path.join(self.output_dir, "binary_file.bin"), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

    def test_incremental_backup(self):
        self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        db = BackupDatabase(self.db_dir)
        content_files_before = len(os.listdir(db.content_path))

        self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        content_files_after = len(os.listdir(db.content_path))

        self.assertEqual(content_files_before, content_files_after)

        with open(os.path.join(self.test_dir, "new_file.txt"), "w") as f:
            f.write("This is a new file")

        self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        content_files_final = len(os.listdir(db.content_path))

        self.assertEqual(content_files_after + 1, content_files_final)

    def test_prune(self):
        self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        with open(os.path.join(self.test_dir, "new_file.txt"), "w") as f:
            f.write("This is a new file")

        self.run_command(
            [
                "snapshot",
                f"--target-directory={self.test_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        result = self.run_command(["prune", "--snapshot=1", f"--db-path={self.db_dir}"])

        self.assertEqual(0, result.returncode)
        self.assertIn("Pruned snapshot 1", result.stdout)

        result = self.run_command(["list", f"--db-path={self.db_dir}"])

        self.assertIn("2", result.stdout)
        self.assertNotIn("1", result.stdout)

        result = self.run_command(
            [
                "restore",
                "--snapshot-number=2",
                f"--output-directory={self.output_dir}",
                f"--db-path={self.db_dir}",
            ]
        )

        self.assertEqual(0, result.returncode)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "new_file.txt")))

    def test_relative_and_absolute_paths(self):
        abs_path = os.path.abspath(self.test_dir)
        rel_path = os.path.relpath(self.test_dir)

        self.run_command(
            ["snapshot", f"--target-directory={abs_path}", f"--db-path={self.db_dir}"]
        )

        original_dir = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(self.test_dir)))

        try:
            self.run_command(
                [
                    "snapshot",
                    f"--target-directory={rel_path}",
                    f"--db-path={self.db_dir}",
                ]
            )
        finally:
            os.chdir(original_dir)

        result = self.run_command(["list", f"--db-path={self.db_dir}"])

        self.assertIn("1", result.stdout)
        self.assertIn("2", result.stdout)


if __name__ == "__main__":
    unittest.main()
