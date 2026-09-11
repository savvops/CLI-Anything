#!/usr/bin/env python3
from pathlib import Path
from setuptools import setup, find_namespace_packages

ROOT = Path(__file__).parent
README = ROOT / "README.md"
long_description = README.read_text(encoding="utf-8") if README.exists() else ""

setup(
    name="cli-anything-sao-browser",
    version="1.0.0",
    description="CLI-Anything harness for SAO AI Browser and Autonomous Job Application Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SavvOps & Nelson Tsavnande",
    license="MIT",
    packages=find_namespace_packages(include=("cli_anything.*",)),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "prompt-toolkit>=3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7",
            "pytest-cov>=4",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-sao-browser=cli_anything.sao_browser.browser_cli:main",
            "cli-anything-job-apply=cli_anything.sao_browser.job_apply_cli:main",
        ],
    },
    package_data={
        "cli_anything.sao_browser": ["skills/*.md"],
    },
    include_package_data=True,
    zip_safe=False,
)
