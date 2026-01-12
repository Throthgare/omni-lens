#!/usr/bin/env python3
"""
Test script for commit_gather_script.py
Tests various scenarios to ensure the script works correctly.
"""
import subprocess
import sys
import os
import json
import tempfile
import pytest
from pathlib import Path

@pytest.fixture
def script_path():
    """Path to run the omnilens package."""
    # Return the path to the package root for PYTHONPATH
    return str(Path(__file__).parent.parent)

@pytest.fixture
def repo_path():
    """Path to the test repository (in tests folder)."""
    test_repo = Path(__file__).parent / "test_repo"
    if not test_repo.exists():
        pytest.skip("Test repository not found. Please create it first.")
    return str(test_repo)

def test_help(script_path):
    """Test that help message displays correctly."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", "--help"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0
    assert "--author" in result.stdout
    assert "--verbose" in result.stdout

def test_non_git_directory(script_path):
    """Test that script exits gracefully in non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["python3", "-m", "omnilens", tmpdir],
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "PYTHONPATH": script_path}
        )
        assert result.returncode != 0
        assert "Not a git repository" in result.stderr

def test_invalid_path(script_path):
    """Test that script exits with error for non-existent path."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", "/nonexistent/path/to/repo"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode != 0
    assert "does not exist" in result.stderr

def test_git_repository(script_path, repo_path):
    """Test that script runs correctly in a git repository."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0
    assert "Found" in result.stdout
    assert "commits" in result.stdout

def test_verbose_mode(script_path, repo_path):
    """Test verbose mode shows debug information."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc", "--verbose"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0
    assert "[DEBUG]" in result.stderr

def test_json_output(script_path, repo_path):
    """Test that JSON output is valid."""
    output_file = os.path.join(repo_path, "test_output.json")
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc", "--output", output_file],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )

    assert result.returncode == 0
    assert os.path.exists(output_file)

    try:
        with open(output_file, 'r') as f:
            data = json.load(f)

        # Check required fields
        assert 'metadata' in data
        assert 'stats' in data
        assert 'history' in data
        assert 'category_breakdown' in data
        assert 'author_stats' in data

        # Clean up
        os.remove(output_file)
    except json.JSONDecodeError as e:
        if os.path.exists(output_file):
            os.remove(output_file)
        raise AssertionError(f"JSON parse error: {e}")

def test_since_filter(script_path, repo_path):
    """Test that --since filter works."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc", "--since", "2020-01-01"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0

def test_until_filter(script_path, repo_path):
    """Test that --until filter works."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc", "--until", "2030-12-31"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0

def test_author_filter(script_path, repo_path):
    """Test that --author filter works."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc", "--author", ".*"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0

def test_category_breakdown(script_path, repo_path):
    """Test that category breakdown is displayed."""
    result = subprocess.run(
        ["python3", "-m", "omnilens", repo_path, "--no-loc"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": script_path}
    )
    assert result.returncode == 0
    assert "Category Breakdown:" in result.stdout



