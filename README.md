# Backup Tool

A robust, professional-grade command-line file backup tool that can take snapshots of a directory, storing its contents in a database and supporting incremental backups.

## Features

- **Snapshot**: Take snapshots of directories with incremental storage
- **List**: View all available snapshots
- **Restore**: Restore a directory from any snapshot
- **Prune**: Remove old snapshots without losing data
- **Content-addressable storage**: Files are stored by their content hash, ensuring deduplication

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Installation Steps

#### Option 1: Install from source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/backuptool.git
   cd backuptool
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

#### Option 2: Install using Make (Unix-like systems)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/backuptool.git
   cd backuptool
   ```

2. Use the Makefile to install:
   ```bash
   make install
   ```

This will install the `backuptool` command in your environment.

## Usage

### Taking a Snapshot

To take a snapshot of a directory:

```bash
backuptool snapshot --target-directory=/path/to/directory
```

This will create a snapshot of the specified directory and store it in the database.

### Listing Snapshots

To list all snapshots:

```bash
backuptool list
```

This will display a table with all snapshots, including their ID and timestamp.

### Restoring a Snapshot

To restore a snapshot to a new directory:

```bash
backuptool restore --snapshot-number=1 --output-directory=/path/to/output
```

This will recreate the directory structure and contents exactly as they were at the time of the snapshot.

### Pruning Snapshots

To remove an old snapshot:

```bash
backuptool prune --snapshot=1
```

This will remove the specified snapshot and delete any unreferenced data.

### Specifying a Custom Database Location

By default, the backup tool stores its database in `~/.backuptool`. You can specify a custom location with the `--db-path` option for all commands:

```bash
backuptool snapshot --target-directory=/path/to/directory --db-path=/custom/db/path
```

## How It Works

### Storage Mechanism

The backup tool uses a content-addressable storage system to efficiently store file contents. Each file is identified by its SHA-256 hash, and duplicate files are stored only once.

Snapshots store metadata about the directory structure and file references, but not duplicate content. This allows for efficient incremental backups.

### Database Structure

The database is stored in `~/.backuptool` by default and has the following structure:

- `content/`: Directory containing file contents, named by their hash
- `snapshots/`: Directory containing snapshot metadata
- `metadata.json`: File containing global metadata about all snapshots

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/backuptool.git
   cd backuptool
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Running Tests

To run the tests:

```bash
python -m unittest discover tests
```

Or using the provided test runner with coverage reporting:

```bash
python run_tests.py --html
```

This will run all tests and generate an HTML coverage report in the `htmlcov` directory.

### Using the Makefile

The project includes a Makefile with several useful targets:

- `make install`: Install the package
- `make test`: Run the tests
- `make coverage`: Run the tests with coverage reporting
- `make lint`: Run the linter
- `make clean`: Clean up build artifacts
- `make docs`: Generate documentation

On Windows, use `make clean-win` instead of `make clean`.

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure you have read/write permissions for the target directory and the database directory.

2. **Database corruption**: If you encounter database corruption, you can try removing the database directory (`~/.backuptool` by default) and starting fresh.

3. **Large files**: The tool may be slower with very large files. Consider excluding large files that don't need to be backed up.

### Logging

The tool uses Python's logging system. You can set the log level using the `BACKUPTOOL_LOG_LEVEL` environment variable:

```bash
BACKUPTOOL_LOG_LEVEL=DEBUG backuptool snapshot --target-directory=/path/to/directory
```

Valid log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
