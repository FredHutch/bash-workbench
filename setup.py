#!/usr/bin/env python

import codecs
from distutils.core import setup
import os.path
from pathlib import Path

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

# Read the requirements from requirements.txt
with open("requirements.txt", "rt") as handle:
    requirements = [
        line.rstrip("\n")
        for line in handle
    ]

setup(
    name="bash_workbench",
    version=get_version("bash_workbench/__init__.py"),
    description="Dataset manager for more reproducible analysis with shell scripts",
    long_description_content_type='text/markdown',
    long_description=long_description,
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
    include_package_data=True
)