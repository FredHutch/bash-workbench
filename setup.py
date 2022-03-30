#!/usr/bin/env python

from distutils.core import setup

# Define the version of the package
__version__ = "0.0.1"

# Read the requirements from requirements.txt
with open("requirements.txt", "rt") as handle:
    requirements = [
        line.rstrip("\n")
        for line in handle
    ]

setup(
    name="bash_workbench",
    version=__version__,
    description="Dataset manager for more reproducible analysis with shell scripts",
    author="Samuel Minot",
    author_email="sminot@fredhutch.org",
    url="https://github.com/FredHutch/bash-workbench",
    packages=["bash_workbench"],
    license="MIT",
    entry_points={
        'console_scripts': [
            'wb=bash_workbench.launch:cli'
        ],
    },
    install_requires=requirements,
)