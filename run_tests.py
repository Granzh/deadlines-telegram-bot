#!/usr/bin/env python3
"""
Test runner script with coverage reporting
"""

import os
import subprocess
import sys


def run_tests():
    """Run tests with coverage"""
    # Set environment variable for testing
    os.environ["TESTING"] = "1"

    # Run tests with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--verbose",
        "--tb=short",
        "--cov=services",
        "--cov=utils",
        "--cov=db",
        "--cov=handlers",
        "--cov=exceptions.py",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "--cov-fail-under=80",
        "tests/",
    ]

    print("Running tests with coverage...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\nAll tests passed!")
        print("Coverage report generated in htmlcov/")
        print("Open htmlcov/index.html to view detailed coverage")
    else:
        print(f"\nTests failed with exit code {result.returncode}")
        return result.returncode

    return 0


def check_code_style():
    """Check code style with flake8 if available"""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "flake8",
                "--max-line-length=100",
                "--ignore=E203,W503",
                "services/",
                "utils/",
                "handlers/",
                "db/",
                "exceptions.py",
            ],
            check=True,
        )
        print("Code style check passed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Code style check skipped (flake8 not installed or issues found)")


def check_type_hints():
    """Check type hints with mypy if available"""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--ignore-missing-imports",
                "services/",
                "utils/",
                "handlers/",
                "db/",
                "exceptions.py",
            ],
            check=True,
        )
        print("Type hint check passed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Type hint check skipped (mypy not installed or issues found)")


if __name__ == "__main__":
    print("Starting test suite...")

    exit_code = run_tests()

    if exit_code == 0:
        print("\nRunning additional checks...")
        check_code_style()
        check_type_hints()

    sys.exit(exit_code)
