"""
Backup Tool - A command line file backup tool that can take snapshots of a directory.

This package provides functionality for:
- Taking snapshots of directories
- Listing available snapshots
- Restoring directories from snapshots
- Pruning old snapshots
"""

import logging
import os

__version__ = '0.1.0'

# Configure logging
LOG_LEVEL = os.environ.get("BACKUPTOOL_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("backuptool")
