#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="linux-whisperer",
    version="0.1.0",
    author="Linux Whisperer Team",
    author_email="your.email@example.com",
    description="An open-source voice dictation and command tool for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/linux-whisperer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "linux-whisperer=src.main:main",
        ],
    },
)
