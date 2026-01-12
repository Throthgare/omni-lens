#!/usr/bin/env python3
"""
Setup script for OmniLens
"""

from setuptools import setup, find_packages
import os

# Read the README
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "OmniLens - Professional-Grade Code Analysis Tool"

setup(
    name="omnilens",
    version="1.0.0",
    author="Throthgare",
    author_email="throthgare@example.com",  # Update with actual email
    description="Professional-Grade Code Analysis Tool for Git Repositories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Throthgare/omni-lens",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "omnilens=omnilens.__main__:run_analysis",
        ],
    },
    install_requires=[
        # Add dependencies here
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)