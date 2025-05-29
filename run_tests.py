#!/usr/bin/env python3
"""
Test runner script for MedScanner application
"""
import sys
import subprocess
import argparse


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests based on specified type"""
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    # Add test type specific options
    if test_type == "unit":
        cmd.append("tests/test_models.py")
        cmd.append("tests/test_utils.py")
    elif test_type == "integration":
        cmd.append("tests/test_routes.py")
    elif test_type == "fast":
        cmd.extend(["-k", "not slow"])
    elif test_type == "models":
        cmd.append("tests/test_models.py")
    elif test_type == "routes":
        cmd.append("tests/test_routes.py")
    elif test_type == "utils":
        cmd.append("tests/test_utils.py")
    else:  # all
        cmd.append("tests/")
    
    # Add common options
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    print(f"Running tests: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run MedScanner tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "fast", "models", "routes", "utils"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage report"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(args.type, args.verbose, args.coverage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()