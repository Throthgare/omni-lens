#!/usr/bin/env python3
"""
Comprehensive Test Suite for OmniLens

Tests every possible use case, edge case, user pipeline, and option combination.
Run this script to validate the entire OmniLens functionality.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import time

class TestSuite:
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="codebase_test_"))
        self.script_path = Path("../commit_gather_script.py").resolve()
        self.python_cmd = "python3"
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, message, level="INFO"):
        """Log test messages."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_command(self, cmd, cwd=None, expect_success=True, timeout=60):
        """Run a command and return result."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or self.test_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0 if expect_success else result.returncode != 0
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def setup_script(self):
        """Copy the script to test directory."""
        source_dir = Path("omnilens")
        if source_dir.exists():
            shutil.copytree(source_dir, self.test_dir / "omnilens")
            self.script_path = self.test_dir / "omnilens" / "__main__.py"
        else:
            self.log("ERROR: omnilens package not found in current directory", "ERROR")

    def assert_test(self, condition, test_name, details=""):
        """Assert a test condition."""
        if condition:
            self.passed += 1
            self.log(f"✓ PASS: {test_name}")
        else:
            self.failed += 1
            self.log(f"✗ FAIL: {test_name} - {details}")
        self.results.append({
            'test': test_name,
            'passed': condition,
            'details': details
        })

    def setup_test_repo(self):
        """Create a test git repository with sample data."""
        repo_dir = self.test_dir / "test_repo"
        
        # Remove existing directory if it exists to ensure clean state
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        
        repo_dir.mkdir()

        # Initialize git repo
        self.run_command("git init", cwd=repo_dir)
        self.run_command("git config user.name 'Test User'", cwd=repo_dir)
        self.run_command("git config user.email 'test@example.com'", cwd=repo_dir)

        # Create sample files
        (repo_dir / "README.md").write_text("# Test Repository\n\nThis is a test repo for codebase analysis.")
        (repo_dir / "main.py").write_text("""
def hello_world():
    '''A simple function'''
    print("Hello, World!")
    return "hello"

class TestClass:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value

if __name__ == "__main__":
    hello_world()
""")

        (repo_dir / "utils.py").write_text("""
import os
from main import TestClass

def helper_function():
    '''Helper function'''
    return "helper"

class UtilityClass:
    @staticmethod
    def static_method():
        return True
""")

        (repo_dir / "test_main.py").write_text("""
import unittest
from main import hello_world, TestClass

class TestMain(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(hello_world(), "hello")

    def test_class(self):
        obj = TestClass()
        self.assertEqual(obj.get_value(), 42)

if __name__ == "__main__":
    unittest.main()
""")

        # Create subdirectory
        sub_dir = repo_dir / "src"
        sub_dir.mkdir()
        (sub_dir / "module.py").write_text("""
def module_function():
    '''Function in a module'''
    return "module"
""")

        # Add and commit files
        self.run_command("git add .", cwd=repo_dir)
        self.run_command("git commit -m 'feat: initial commit with basic functionality'", cwd=repo_dir)

        # Make more commits
        (repo_dir / "main.py").write_text("""
def hello_world():
    '''A simple function'''
    print("Hello, World!")
    return "hello"

def new_function():
    '''New function added'''
    return "new"

class TestClass:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = val

if __name__ == "__main__":
    hello_world()
""")
        self.run_command("git add main.py", cwd=repo_dir)
        self.run_command("git commit -m 'feat: add new_function and set_value method'", cwd=repo_dir)

        # Bug fix commit
        (repo_dir / "main.py").write_text("""
def hello_world():
    '''A simple function'''
    print("Hello, World!")
    return "hello"

def new_function():
    '''New function added'''
    return "new"

class TestClass:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = val

    def double_value(self):
        return self.value * 2

if __name__ == "__main__":
    hello_world()
""")
        self.run_command("git add main.py", cwd=repo_dir)
        self.run_command("git commit -m 'fix: add double_value method to TestClass'", cwd=repo_dir)

        # Documentation commit
        (repo_dir / "README.md").write_text("""
# Test Repository

This is a test repo for codebase analysis.

## Features

- Hello world function
- Test class with methods
- Utility functions
- Unit tests

## Usage

Run `python main.py` to execute the main script.
""")
        self.run_command("git add README.md", cwd=repo_dir)
        self.run_command("git commit -m 'docs: update README with usage instructions'", cwd=repo_dir)

        # Refactoring commit
        (repo_dir / "utils.py").write_text("""
import os
from main import TestClass

def helper_function():
    '''Helper function'''
    return "helper"

def another_helper():
    '''Another helper function'''
    return "another"

class UtilityClass:
    @staticmethod
    def static_method():
        return True

    @staticmethod
    def new_static_method():
        return False
""")
        self.run_command("git add utils.py", cwd=repo_dir)
        self.run_command("git commit -m 'refactor: add another_helper function and new_static_method'", cwd=repo_dir)

        return repo_dir

    def test_basic_functionality(self):
        """Test basic script execution."""
        self.log("Testing basic functionality...")

        # Test help
        result = self.run_command(f"{self.python_cmd} {self.script_path} --help")
        self.assert_test(result['success'], "Help command works", result.get('stderr', ''))

        # Test with non-existent path
        result = self.run_command(f"{self.python_cmd} {self.script_path} /non/existent/path")
        self.assert_test(not result['success'], "Handles non-existent path correctly")

        # Test with current directory (should work)
        result = self.run_command(f"{self.python_cmd} {self.script_path} . --no-git")
        self.assert_test(result['success'], "Works with current directory")

    def test_git_repository_analysis(self):
        """Test git repository analysis."""
        self.log("Testing git repository analysis...")

        repo_dir = self.setup_test_repo()

        # Basic analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir}")
        self.assert_test(result['success'], "Basic git repo analysis works")

        # Test with different formats
        for fmt in ['json', 'markdown', 'html', 'csv']:
            result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --format {fmt} --output test.{fmt}")
            self.assert_test(result['success'], f"Format {fmt} works")

        # Test with date filters
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --since '1 day ago'")
        self.assert_test(result['success'], "Date filtering works")

        # Test with author filter
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --author 'Test User'")
        self.assert_test(result['success'], "Author filtering works")

        # Test with all commits
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --all")
        self.assert_test(result['success'], "All commits option works")

    def test_advanced_options(self):
        """Test advanced analysis options."""
        self.log("Testing advanced options...")

        repo_dir = self.setup_test_repo()

        # Tech debt analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --tech-debt")
        self.assert_test(result['success'], "Tech debt analysis works")

        # Complexity analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --complexity")
        self.assert_test(result['success'], "Complexity analysis works")

        # Dependency graph
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --deps")
        self.assert_test(result['success'], "Dependency graph extraction works")

        # Combined analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --tech-debt --complexity --deps")
        self.assert_test(result['success'], "Combined advanced options work")

    def test_output_options(self):
        """Test various output options."""
        self.log("Testing output options...")

        repo_dir = self.setup_test_repo()

        # CSV exports - files are created relative to repo_dir
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --export-csv commits.csv --export-classes-csv classes.csv")
        self.assert_test(result['success'], "CSV exports work")

        # Verify CSV files were created (in repo_dir, not test_dir)
        commits_csv = repo_dir / "commits.csv"
        classes_csv = repo_dir / "classes.csv"
        self.assert_test(commits_csv.exists(), "Commits CSV file created")
        self.assert_test(classes_csv.exists(), "Classes CSV file created")

        # Test HTML shorthand
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --html --output report.html")
        self.assert_test(result['success'], "HTML shorthand works")

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        self.log("Testing edge cases...")

        # Empty directory
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        result = self.run_command(f"{self.python_cmd} {self.script_path} {empty_dir} --no-git")
        self.assert_test(result['success'], "Handles empty directory")

        # Directory with no code files
        no_code_dir = self.test_dir / "no_code"
        no_code_dir.mkdir()
        (no_code_dir / "text.txt").write_text("Just some text")
        (no_code_dir / "data.json").write_text('{"key": "value"}')
        result = self.run_command(f"{self.python_cmd} {self.script_path} {no_code_dir} --no-git")
        self.assert_test(result['success'], "Handles directory with no code files")

        # Git repo with no commits
        empty_repo = self.test_dir / "empty_repo"
        empty_repo.mkdir()
        self.run_command("git init", cwd=empty_repo)
        result = self.run_command(f"{self.python_cmd} {self.script_path} {empty_repo}")
        self.assert_test(result['success'], "Handles empty git repository")

        # Test with invalid format
        repo_dir = self.setup_test_repo()
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --format invalid")
        self.assert_test(not result['success'], "Rejects invalid format")

    def test_configuration_options(self):
        """Test configuration and filtering options."""
        self.log("Testing configuration options...")

        repo_dir = self.setup_test_repo()

        # Exclude directories
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --exclude-dirs src")
        self.assert_test(result['success'], "Directory exclusion works")

        # Exclude files
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --exclude-files test_main.py")
        self.assert_test(result['success'], "File exclusion works")

        # No LOC counting
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --no-loc")
        self.assert_test(result['success'], "No LOC option works")

        # No classes extraction
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --no-classes")
        self.assert_test(result['success'], "No classes option works")

        # Verbose output
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --verbose")
        self.assert_test(result['success'], "Verbose output works")

    def test_branch_comparison(self):
        """Test branch comparison functionality."""
        self.log("Testing branch comparison...")

        repo_dir = self.setup_test_repo()

        # Create a feature branch
        self.run_command("git checkout -b feature-branch", cwd=repo_dir)
        (repo_dir / "feature.py").write_text("def feature_function(): return 'feature'")
        self.run_command("git add feature.py", cwd=repo_dir)
        self.run_command("git commit -m 'feat: add feature function'", cwd=repo_dir)

        # Compare branches
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --diff main..feature-branch")
        self.assert_test(result['success'], "Branch comparison works")

    def test_relative_dates(self):
        """Test relative date parsing."""
        self.log("Testing relative date parsing...")

        repo_dir = self.setup_test_repo()

        # Test various relative date formats
        date_formats = [
            "1 day ago",
            "2 weeks ago",
            "1 month ago",
            "6 hours ago",
            "30 minutes ago"
        ]

        for date_fmt in date_formats:
            result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --since '{date_fmt}'")
            self.assert_test(result['success'], f"Relative date '{date_fmt}' works")

    def test_output_validation(self):
        """Test output file validation."""
        self.log("Testing output validation...")

        repo_dir = self.setup_test_repo()

        # Test different output formats create correct files
        formats = {
            'json': 'report.json',
            'markdown': 'report.md',
            'html': 'report.html',
            'csv': 'report.csv'
        }

        for fmt, filename in formats.items():
            output_path = self.test_dir / filename
            result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --format {fmt} --output {output_path}")
            self.assert_test(result['success'] and output_path.exists(), f"Creates {fmt} output file")

            # Validate file content
            if output_path.exists():
                content = output_path.read_text()
                if fmt == 'json':
                    try:
                        json.loads(content)
                        self.assert_test(True, f"Valid JSON output for {fmt}")
                    except json.JSONDecodeError:
                        self.assert_test(False, f"Invalid JSON output for {fmt}")
                elif fmt == 'csv':
                    # Check if it's valid CSV
                    try:
                        csv.reader(content.splitlines())
                        self.assert_test(True, f"Valid CSV output for {fmt}")
                    except:
                        self.assert_test(False, f"Invalid CSV output for {fmt}")

    def test_performance_options(self):
        """Test performance-related options."""
        self.log("Testing performance options...")

        repo_dir = self.setup_test_repo()

        # No cache
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --no-cache")
        self.assert_test(result['success'], "No cache option works")

        # Progress bar (should work even without tqdm)
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --progress")
        self.assert_test(result['success'], "Progress option works")

        # Different depth levels
        for level in ['1', '2', '3', 'all']:
            result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --deep-level {level}")
            self.assert_test(result['success'], f"Depth level {level} works")

    def test_user_pipeline(self):
        """Test complete user pipeline scenarios."""
        self.log("Testing user pipeline scenarios...")

        repo_dir = self.setup_test_repo()

        # Scenario 1: New user first analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir}")
        self.assert_test(result['success'], "Basic analysis pipeline works")

        # Scenario 2: Developer checking recent changes
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --since '1 week ago' --format markdown")
        self.assert_test(result['success'], "Recent changes analysis works")

        # Scenario 3: Tech lead reviewing code quality
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --tech-debt --complexity --html --output quality_report.html")
        self.assert_test(result['success'], "Code quality analysis works")

        # Scenario 4: Data analyst exporting for analysis
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --export-csv commits.csv --export-classes-csv classes.csv --format json")
        self.assert_test(result['success'], "Data export pipeline works")

        # Scenario 5: CI/CD integration
        result = self.run_command(f"{self.python_cmd} {self.script_path} {repo_dir} --no-git --format json --output ci_report.json")
        self.assert_test(result['success'], "CI/CD pipeline works")

    def run_all_tests(self):
        """Run all test suites."""
        self.log("Starting comprehensive test suite...")

        # Setup script in test directory
        self.setup_script()

        start_time = time.time()

        # Run all test methods
        test_methods = [
            self.test_basic_functionality,
            self.test_git_repository_analysis,
            self.test_advanced_options,
            self.test_output_options,
            self.test_edge_cases,
            self.test_configuration_options,
            self.test_branch_comparison,
            self.test_relative_dates,
            self.test_output_validation,
            self.test_performance_options,
            self.test_user_pipeline
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.failed += 1
                self.log(f"Exception in {test_method.__name__}: {e}", "ERROR")

        end_time = time.time()
        duration = end_time - start_time

        # Print summary
        self.log(f"\n{'='*50}")
        self.log("TEST SUITE SUMMARY")
        self.log(f"{'='*50}")
        self.log(f"Total Tests: {self.passed + self.failed}")
        self.log(f"Passed: {self.passed}")
        self.log(f"Failed: {self.failed}")
        self.log(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        self.log(f"Duration: {duration:.2f} seconds")
        self.log(f"{'='*50}")

        # Detailed results
        if self.failed > 0:
            self.log("\nFAILED TESTS:")
            for result in self.results:
                if not result['passed']:
                    self.log(f"  - {result['test']}: {result['details']}")

        return self.failed == 0

    def cleanup(self):
        """Clean up test directory."""
        try:
            shutil.rmtree(self.test_dir)
            self.log("Test directory cleaned up")
        except Exception as e:
            self.log(f"Failed to cleanup: {e}", "WARNING")

def main():
    """Main test runner."""
    print("OmniLens - Comprehensive Test Suite")
    print("=" * 60)

    # Check if script exists
    if not Path("omnilens").exists():
        print("ERROR: omnilens package not found in current directory")
        sys.exit(1)

    # Check python3 availability
    try:
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: python3 not available")
            sys.exit(1)
        print(f"Using: {result.stdout.strip()}")
    except:
        print("ERROR: python3 not available")
        sys.exit(1)

    # Run tests
    suite = TestSuite()
    try:
        success = suite.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        suite.cleanup()

if __name__ == "__main__":
    main()
