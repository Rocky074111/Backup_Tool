import os
import sys
import unittest
import subprocess
import argparse


def install_dependencies():
    print("Installing test dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])


def run_tests_with_coverage(verbose=False, html=False):
    try:
        import coverage
    except ImportError:
        install_dependencies()
        import coverage

    cov = coverage.Coverage(source=["backuptool"], omit=["*/__init__.py", "*/tests/*"])

    print("Starting test run with coverage...")
    cov.start()

    loader = unittest.TestLoader()
    tests = loader.discover("tests")
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(tests)

    cov.stop()
    cov.save()

    print("\nCoverage Report:")
    cov.report()

    if html:
        cov.html_report(directory="htmlcov")
        print(f"HTML coverage report generated in: {os.path.abspath('htmlcov')}")

    return 0 if result.wasSuccessful() else 1


def parse_args():
    parser = argparse.ArgumentParser(description="Run tests for the backup tool")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_tests_with_coverage(verbose=args.verbose, html=args.html))
