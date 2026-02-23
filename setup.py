#!/usr/bin/env python3
"""
OmniClaw Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="omniclaw",
    version="1.0.0",
    author="Me",
    author_email="support@omniclaw.ai",
    description="The Hybrid Hive AI Agent System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/omniclaw/omniclaw",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "mobile_app"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Android",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.7.0",
            "flake8>=6.0.0",
        ],
        "gpu": [
            "torch>=2.1.0",
            "faiss-gpu>=1.7.4",
        ],
        "trading": [
            "ccxt>=4.0.0",
            "alpaca-trade-api>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "omniclaw=omniclaw:main",
            "omniclaw-daemon=omniclaw.daemon:main",
        ],
    },
    include_package_data=True,
    package_data={
        "omniclaw": [
            "kernel_bridge/Makefile",
            "kernel_bridge/src/**/*",
            "mobile_app/**/*",
        ],
    },
    zip_safe=False,
)
