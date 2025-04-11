import os
import random
import argparse


def create_test_data(base_dir, num_files=10, max_depth=3, max_file_size=1024):
    os.makedirs(base_dir, exist_ok=True)

    dirs = [base_dir]
    for _ in range(max_depth):
        new_dir = os.path.join(random.choice(dirs), f"dir_{len(dirs)}")
        os.makedirs(new_dir, exist_ok=True)
        dirs.append(new_dir)

    for i in range(num_files):
        dir_path = random.choice(dirs)

        is_text = random.choice([True, False])

        if is_text:
            file_path = os.path.join(dir_path, f"file_{i}.txt")
            with open(file_path, "w") as f:
                content = " ".join(
                    [
                        "".join(
                            random.choices(
                                "abcdefghijklmnopqrstuvwxyz", k=random.randint(3, 10)
                            )
                        )
                        for _ in range(random.randint(10, 100))
                    ]
                )
                f.write(content)
        else:
            file_path = os.path.join(dir_path, f"file_{i}.bin")
            with open(file_path, "wb") as f:
                content = os.urandom(random.randint(1, max_file_size))
                f.write(content)

    print(f"Created {num_files} files in {len(dirs)} directories under {base_dir}")


def main():
    parser = argparse.ArgumentParser(description="Create test data for the backup tool")
    parser.add_argument(
        "--base-dir",
        default="./test_data",
        help="Base directory to create test data in",
    )
    parser.add_argument(
        "--num-files", type=int, default=10, help="Number of files to create"
    )
    parser.add_argument(
        "--max-depth", type=int, default=3, help="Maximum directory depth"
    )
    parser.add_argument(
        "--max-file-size", type=int, default=1024, help="Maximum file size in bytes"
    )

    args = parser.parse_args()
    create_test_data(args.base_dir, args.num_files, args.max_depth, args.max_file_size)


if __name__ == "__main__":
    main()
