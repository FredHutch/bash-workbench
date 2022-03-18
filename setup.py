#!/usr/bin/env python

from distutils.core import setup
import bash_workbench

# Read the requirements from requirements.txt
with open("requirements.txt", "rt") as handle:
    requirements = [
        line.rstrip("\n")
        for line in handle
    ]

setup(
    name="bash_workbench",
    version=bash_workbench.__version__,
    description="Dataset manager for more reproducible analysis with shell scripts",
    author="Samuel Minot",
    author_email="sminot@fredhutch.org",
    url="https://github.com/FredHutch/bash-workbench",
    packages=["bash_workbench"],
    license="MIT",
    entry_points={
        'console_scripts': [
            'wb=bash_workbench.cli.launch:cli'
        ],
    },
    install_requires=requirements,
)