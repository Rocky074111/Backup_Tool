import os
import hashlib
import json
import shutil
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

logger = logging.getLogger("backuptool.core")


class BackupDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            home_dir = os.path.expanduser("~")
            db_path = os.path.join(home_dir, ".backuptool")

        self.db_path = db_path
        self.content_path = os.path.join(db_path, "content")
        self.snapshots_path = os.path.join(db_path, "snapshots")
        self.metadata_path = os.path.join(db_path, "metadata.json")

        try:
            os.makedirs(self.content_path, exist_ok=True)
            os.makedirs(self.snapshots_path, exist_ok=True)
            logger.debug(f"Database directories created at {db_path}")
        except OSError as e:
            logger.error(f"Failed to create database directories: {e}")
            raise

        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.debug("Metadata loaded successfully")
                return metadata
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading metadata: {e}")
                logger.warning("Creating new metadata file")
                metadata = {"next_snapshot_id": 1, "snapshots": []}
                self._save_metadata(metadata)
                return metadata
        else:
            logger.debug("Creating new metadata file")
            metadata = {"next_snapshot_id": 1, "snapshots": []}
            self._save_metadata(metadata)
            return metadata

    def _save_metadata(self, metadata: Dict) -> None:
        try:
            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.debug("Metadata saved successfully")
        except IOError as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    def _calculate_hash(self, file_path: str) -> str:
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            file_hash = sha256.hexdigest()
            logger.debug(f"Calculated hash for {file_path}: {file_hash[:8]}...")
            return file_hash
        except IOError as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise

    def _store_file_content(self, file_path: str) -> str:
        try:
            file_hash = self._calculate_hash(file_path)
            content_file_path = os.path.join(self.content_path, file_hash)

            if not os.path.exists(content_file_path):
                logger.debug(f"Storing new file content: {file_hash[:8]}...")
                shutil.copy2(file_path, content_file_path)
            else:
                logger.debug(f"File content already exists: {file_hash[:8]}...")

            return file_hash
        except Exception as e:
            logger.error(f"Failed to store file content for {file_path}: {e}")
            raise

    def create_snapshot(self, target_dir: str) -> int:
        target_dir = os.path.abspath(target_dir)
        if not os.path.isdir(target_dir):
            logger.error(f"Target directory does not exist: {target_dir}")
            raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

        snapshot_id = self.metadata["next_snapshot_id"]
        timestamp = datetime.datetime.now().isoformat()

        logger.info(f"Creating snapshot {snapshot_id} of {target_dir}")

        snapshot = {
            "id": snapshot_id,
            "timestamp": timestamp,
            "target_dir": target_dir,
            "files": {},
        }

        file_count = 0
        total_size = 0
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    rel_path = os.path.relpath(file_path, target_dir)

                    file_hash = self._store_file_content(file_path)

                    snapshot["files"][rel_path] = file_hash

                    file_count += 1
                    total_size += os.path.getsize(file_path)
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue

        snapshot_path = os.path.join(self.snapshots_path, str(snapshot_id))
        try:
            with open(snapshot_path, "w") as f:
                json.dump(snapshot, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save snapshot {snapshot_id}: {e}")
            raise

        self.metadata["next_snapshot_id"] = snapshot_id + 1
        self.metadata["snapshots"].append(
            {
                "id": snapshot_id,
                "timestamp": timestamp,
                "target_dir": target_dir,
                "file_count": file_count,
                "total_size": total_size,
            }
        )
        self._save_metadata(self.metadata)

        logger.info(
            f"Snapshot {snapshot_id} created successfully with {file_count} files ({total_size} bytes)"
        )
        return snapshot_id

    def list_snapshots(self) -> List[Dict]:
        logger.debug("Listing all snapshots")
        return self.metadata["snapshots"]

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict]:
        snapshot_path = os.path.join(self.snapshots_path, str(snapshot_id))
        if not os.path.exists(snapshot_path):
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None

        try:
            with open(snapshot_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None

    def restore_snapshot(self, snapshot_id: int, output_dir: str) -> bool:
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            logger.error(f"Cannot restore: Snapshot {snapshot_id} not found")
            return False

        logger.info(f"Restoring snapshot {snapshot_id} to {output_dir}")

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            return False

        restored_count = 0
        for rel_path, file_hash in snapshot["files"].items():
            source_path = os.path.join(self.content_path, file_hash)
            if not os.path.exists(source_path):
                logger.warning(
                    f"Content for file {rel_path} (hash: {file_hash}) not found in database"
                )
                continue

            target_path = os.path.join(output_dir, rel_path)
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                shutil.copy2(source_path, target_path)
                restored_count += 1
            except OSError as e:
                logger.warning(f"Failed to restore file {rel_path}: {e}")
                continue

        logger.info(f"Restored {restored_count} files from snapshot {snapshot_id}")
        return True

    def prune_snapshot(self, snapshot_id: int) -> bool:
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            logger.error(f"Cannot prune: Snapshot {snapshot_id} not found")
            return False

        logger.info(f"Pruning snapshot {snapshot_id}")

        snapshot_path = os.path.join(self.snapshots_path, str(snapshot_id))
        try:
            os.remove(snapshot_path)
        except OSError as e:
            logger.error(f"Failed to remove snapshot file {snapshot_path}: {e}")
            return False

        self.metadata["snapshots"] = [
            s for s in self.metadata["snapshots"] if s["id"] != snapshot_id
        ]
        self._save_metadata(self.metadata)

        used_hashes = set()
        for s_id in [s["id"] for s in self.metadata["snapshots"]]:
            s = self.get_snapshot(s_id)
            if s:
                used_hashes.update(s["files"].values())

        removed_count = 0
        for content_file in os.listdir(self.content_path):
            if content_file not in used_hashes:
                try:
                    os.remove(os.path.join(self.content_path, content_file))
                    removed_count += 1
                except OSError as e:
                    logger.warning(
                        f"Failed to remove unused content file {content_file}: {e}"
                    )
                    continue

        logger.info(
            f"Pruned snapshot {snapshot_id} and removed {removed_count} unused content files"
        )
        return True


def create_snapshot(target_dir: str, db_path: str = None) -> int:
    logger.info(f"Creating snapshot of {target_dir}")
    db = BackupDatabase(db_path)
    return db.create_snapshot(target_dir)


def list_snapshots(db_path: str = None) -> List[Dict]:
    logger.info("Listing snapshots")
    db = BackupDatabase(db_path)
    return db.list_snapshots()


def restore_snapshot(snapshot_id: int, output_dir: str, db_path: str = None) -> bool:
    logger.info(f"Restoring snapshot {snapshot_id} to {output_dir}")
    db = BackupDatabase(db_path)
    return db.restore_snapshot(snapshot_id, output_dir)


def prune_snapshot(snapshot_id: int, db_path: str = None) -> bool:
    logger.info(f"Pruning snapshot {snapshot_id}")
    db = BackupDatabase(db_path)
    return db.prune_snapshot(snapshot_id)
