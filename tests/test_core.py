import os
import shutil
import tempfile
import unittest
import hashlib
from pathlib import Path

from backuptool.core import BackupDatabase


class TestBackupDatabase(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        self.create_test_files()

        self.db = BackupDatabase(self.db_dir)

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

        with open(os.path.join(self.test_dir, "subdir2", "file4.txt"), "w") as f:
            f.write("This is file 1")

    def test_calculate_hash(self):
        file_path = os.path.join(self.test_dir, "file1.txt")

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            sha256.update(f.read())
        expected_hash = sha256.hexdigest()

        actual_hash = self.db._calculate_hash(file_path)

        self.assertEqual(expected_hash, actual_hash)

    def test_create_snapshot(self):
        snapshot_id = self.db.create_snapshot(self.test_dir)

        self.assertEqual(1, snapshot_id)
        self.assertTrue(os.path.exists(os.path.join(self.db.snapshots_path, "1")))

        self.assertEqual(2, self.db.metadata["next_snapshot_id"])
        self.assertEqual(1, len(self.db.metadata["snapshots"]))

        self.assertGreater(len(os.listdir(self.db.content_path)), 0)

    def test_list_snapshots(self):
        self.db.create_snapshot(self.test_dir)
        self.db.create_snapshot(self.test_dir)

        snapshots = self.db.list_snapshots()

        self.assertEqual(2, len(snapshots))
        self.assertEqual(1, snapshots[0]["id"])
        self.assertEqual(2, snapshots[1]["id"])

    def test_get_snapshot(self):
        snapshot_id = self.db.create_snapshot(self.test_dir)

        snapshot = self.db.get_snapshot(snapshot_id)

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot_id, snapshot["id"])
        self.assertEqual(4, len(snapshot["files"]))

    def test_restore_snapshot(self):
        snapshot_id = self.db.create_snapshot(self.test_dir)

        success = self.db.restore_snapshot(snapshot_id, self.output_dir)

        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file1.txt")))
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "subdir1", "file2.txt"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "subdir2", "file3.txt"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, "subdir2", "file4.txt"))
        )

        with open(os.path.join(self.output_dir, "file1.txt"), "r") as f:
            self.assertEqual("This is file 1", f.read())

    def test_prune_snapshot(self):
        self.db.create_snapshot(self.test_dir)
        self.db.create_snapshot(self.test_dir)

        content_files_before = len(os.listdir(self.db.content_path))

        success = self.db.prune_snapshot(1)

        self.assertTrue(success)
        self.assertFalse(os.path.exists(os.path.join(self.db.snapshots_path, "1")))
        self.assertEqual(1, len(self.db.metadata["snapshots"]))

        content_files_after = len(os.listdir(self.db.content_path))
        self.assertEqual(content_files_before, content_files_after)

        with open(os.path.join(self.test_dir, "new_file.txt"), "w") as f:
            f.write("This is a new file")

        self.db.create_snapshot(self.test_dir)

        content_files_new = len(os.listdir(self.db.content_path))
        self.assertEqual(content_files_after + 1, content_files_new)

        success = self.db.prune_snapshot(2)

        content_files_final = len(os.listdir(self.db.content_path))
        self.assertEqual(content_files_new - 1, content_files_final)

    def test_deduplication(self):
        self.db.create_snapshot(self.test_dir)

        content_files = len(os.listdir(self.db.content_path))

        self.assertEqual(3, content_files)

    def test_incremental_backup(self):
        self.db.create_snapshot(self.test_dir)

        content_files_before = len(os.listdir(self.db.content_path))

        self.db.create_snapshot(self.test_dir)

        content_files_after = len(os.listdir(self.db.content_path))

        self.assertEqual(content_files_before, content_files_after)

        with open(os.path.join(self.test_dir, "new_file.txt"), "w") as f:
            f.write("This is a new file")

        self.db.create_snapshot(self.test_dir)

        content_files_final = len(os.listdir(self.db.content_path))

        self.assertEqual(content_files_after + 1, content_files_final)


if __name__ == "__main__":
    unittest.main()
