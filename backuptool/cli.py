import sys
import argparse
import datetime
import logging
from tabulate import tabulate
from . import core

logger = logging.getLogger("backuptool.cli")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backup Tool - A command line file backup tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Take a snapshot of a directory",
        description="Take a snapshot of a directory and store it in the database",
    )
    snapshot_parser.add_argument(
        "--target-directory", required=True, help="Directory to snapshot"
    )
    snapshot_parser.add_argument(
        "--db-path", help="Path to the database directory (default: ~/.backuptool)"
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List all snapshots",
        description="List all snapshots in the database",
    )
    list_parser.add_argument(
        "--db-path", help="Path to the database directory (default: ~/.backuptool)"
    )
    list_parser.add_argument(
        "--format",
        choices=["simple", "grid", "fancy_grid", "github"],
        default="simple",
        help="Output format for the table",
    )

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore a snapshot",
        description="Restore a snapshot to a specified directory",
    )
    restore_parser.add_argument(
        "--snapshot-number",
        type=int,
        required=True,
        help="ID of the snapshot to restore",
    )
    restore_parser.add_argument(
        "--output-directory", required=True, help="Directory to restore the snapshot to"
    )
    restore_parser.add_argument(
        "--db-path", help="Path to the database directory (default: ~/.backuptool)"
    )

    prune_parser = subparsers.add_parser(
        "prune",
        help="Prune a snapshot",
        description="Remove a snapshot and any unreferenced data",
    )
    prune_parser.add_argument(
        "--snapshot", type=int, required=True, help="ID of the snapshot to prune"
    )
    prune_parser.add_argument(
        "--db-path", help="Path to the database directory (default: ~/.backuptool)"
    )

    for p in [snapshot_parser, list_parser, restore_parser, prune_parser]:
        p.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

    return parser.parse_args()


def format_timestamp(iso_timestamp):
    dt = datetime.datetime.fromisoformat(iso_timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def setup_logging(verbose):
    if verbose:
        logging.getLogger("backuptool").setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    else:
        logging.getLogger("backuptool").setLevel(logging.INFO)


def main():
    try:
        args = parse_args()

        setup_logging(getattr(args, "verbose", False))

        if args.command == "snapshot":
            try:
                snapshot_id = core.create_snapshot(args.target_directory, args.db_path)
                print(f"Created snapshot {snapshot_id}")
                return 0
            except FileNotFoundError as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")
                return 1
            except Exception as e:
                logger.error(f"Failed to create snapshot: {e}")
                print(f"Failed to create snapshot: {e}")
                return 1

        elif args.command == "list":
            try:
                snapshots = core.list_snapshots(args.db_path)
                if not snapshots:
                    print("No snapshots found")
                    return 0

                table_data = []
                for snapshot in snapshots:
                    row = [
                        snapshot["id"],
                        format_timestamp(snapshot["timestamp"]),
                    ]

                    if "file_count" in snapshot:
                        row.append(snapshot["file_count"])
                    else:
                        row.append("N/A")

                    if "total_size" in snapshot:
                        row.append(format_size(snapshot["total_size"]))
                    else:
                        row.append("N/A")

                    row.append(snapshot["target_dir"])
                    table_data.append(row)

                headers = ["ID", "TIMESTAMP", "FILES", "SIZE", "TARGET DIRECTORY"]
                print(tabulate(table_data, headers=headers, tablefmt=args.format))
                return 0
            except Exception as e:
                logger.error(f"Failed to list snapshots: {e}")
                print(f"Failed to list snapshots: {e}")
                return 1

        elif args.command == "restore":
            try:
                success = core.restore_snapshot(
                    args.snapshot_number, args.output_directory, args.db_path
                )
                if success:
                    print(
                        f"Restored snapshot {args.snapshot_number} to {args.output_directory}"
                    )
                    return 0
                else:
                    print(f"Failed to restore snapshot {args.snapshot_number}")
                    return 1
            except Exception as e:
                logger.error(f"Error during restore: {e}")
                print(f"Error during restore: {e}")
                return 1

        elif args.command == "prune":
            try:
                success = core.prune_snapshot(args.snapshot, args.db_path)
                if success:
                    print(f"Pruned snapshot {args.snapshot}")
                    return 0
                else:
                    print(f"Failed to prune snapshot {args.snapshot}")
                    return 1
            except Exception as e:
                logger.error(f"Error during prune: {e}")
                print(f"Error during prune: {e}")
                return 1

        else:
            print("No command specified. Use --help for usage information.")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
