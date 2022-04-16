# BASH Workbench

[![CI](https://github.com/FredHutch/bash-workbench/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/FredHutch/bash-workbench/actions/workflows/ci.yaml)

A dataset manager for bioinformaticians

The world is awash in data, but research communities tend to organize their data in different ways.
The BASH Workbench is a dataset manager for people who tend to organize their data as collections of files.
The goal of this utility is to make it easier to keep track of where your datasets are, remember how they were made, and quickly create new ones based on easily-sharable BASH templates.

## Guide

- [Getting Started](#getting-started)
- [Background](#background)
- [Key Concepts](#key-concepts)
- [Developer's Guide](#developers-guide)
- [Contributing](#contributing)

## Getting Started

The BASH Workbench may be installed using Python3 with the following command:

```#!/bin/bash
pip3 install bash-workbench
```

or, on a shared system:

```#!/bin/bash
pip3 install --user bash-workbench
```

Note: The BASH Workbench was developed using Python 3.9 but will likely work with earlier versions of Python3.

The BASH Workbench can be run in two different ways:
- As an interactive "choose-your-own-adventure" style series of menus, or
- using a command-line interface for each individual command.

To start exploring the interactive menus, simply run the command:

```#!/bin/bash
wb
```

The command-line interface for running individual components of the BASH
Workbench can be run using the same command with additional sub-commands.
For example, the following command will download the
[bash-workbench-tools](https://github.com/FredHutch/bash-workbench-tools)
repository and import all of its **tools** and **launchers**.

```#!/bin/bash
wb add_repo --remote-name FredHutch/bash-workbench-tools
```

For a complete list of sub-commands available, print the help text (`wb --help`)
or use the tab key to populate a list of options.

## Background

### Motivated by Bioinformatics

The number of technologies available for organizing data are far too numerous to mention, but none of them quite fit the needs of bioinformaticians.
While the world of bioinformatics is broad, its most common theme is that datasets are large and do not adhere to strict formats or structures.

The prime exemplar of the theme which motivates this project is genomic data.
When genome sequencers are used to process a DNA sample, they output a randomly ordered collection of genome sequence fragments with associated quality information.
While it may be technically possible to load those sequences into a database, it is far more efficient to store them as a compressed text file in FASTQ format and process them with one of the many algorithms which have been built by researchers to consume this file type.
In many cases the initial processing step for genomic sequence data is to align each sequence fragment against a reference genome and record the position from which it likely originated.
While the resulting dataset contains more structured information than the raw FASTQ, the most efficient way to store and query these enormous datasets is use a binary representation of those alignments (BAM format), or one of its compressed derivatives.

If only it were simple enough to create a dataset manager oriented around compressed BAM files with their standardized format.
After generating those BAM files, bioinformaticians may do any number of interesting things with that data: detecting nucleotide variants, measuring gene expression levels, discovering changes in genome structure, or even identifying epigenetic modifications to individual nucleotides.
Each of those different analyses produce outputs with different inherent structures which may be serialized in a number of formats: CSV, HDF, JSON, and HTML being some of the most common.
To make things even more complex, there are many types of genomic analysis which entirely forego the alignment to BAM format, such as taxonomic profiling, amplicon sequencing, CRISPR screening, etc.

Rather than bemoan the lack of file format standardization, we can focus on the practices and traditions which are generally shared across the discipline.
Each discrete batch of analysis tends to have inputs which include both files and parameters.
The most flexible way to codify a batch of analysis is using a shell script containing one or more commands.
Depending on the goal, the analysis may range in complexity all the way from calling a single executable program all the way up to invoking a workflow manager to preform a series of interconnected steps.
After the analysis is complete a collection of file objects will be created, typically within a single folder.

As a working bioinformatician, I frequently find myself in the position of creating folders, creating a shell script based on something that I've done before, adding in the appropriate reference to the files and parameters that are appropriate for this anlaysis, and running the analysis to create a new dataset.
The BASH Workbench is an attempt to make this type of work easier, for myself and others who work in a similar way.

## Key Concepts

To describe the behavior of the BASH Workbench, we will use the terminology of a local filesystem (files, folders, etc.).
However, the core concepts are easily extensible to object storage systems hosted by cloud service providers.
The underlying code used by the BASH Workbench includes adapters for each type of storage, and can conceptually be extended to any file-based data storage system.

### Dataset

A **dataset** is a folder containing any number of files or subfolders.
**Datasets** can be created by the BASH Workbench as the output of a **tool**, or by simply indexing the contents of an existing folder.

### Tool Repositories

The BASH Workbench keeps track of a collection of **repositories** which contain **tools**. Each **tool** consists of a shell script which can be run on a defined set of file and/or parameter inputs.

### Launchers

The way in which a particular set of **tools** can be executed on a type of computational system is defined as a **launcher**.
For example, a single **tool** may be run on a laptop, SLURM cluster, or in the cloud by using a different **launcher** for each.
The **launcher** makes it easier for a user to re-use a job submission script and associated parameters across a collection of **tools**.

### Parameters

When using a **tool** or **launcher**, a user may want to re-use the settings or **parameters** across multiple **datasets**.
Some examples of **parameters** that a user may wish to save and re-use with the BASH Workbench may be the location of a folder
used to save temporary files, or the username associated with a SLURM account.

## Developers Guide

The BASH Workbench makes it easier to manage and manipulate an existing filesystem, and does not require that any data is moved to a dedicated location.
By using a dedicated subfolder `._wb/` (for 'workbench'), the Workbench can annotate any existing folder and store associated metadata in-place.
It is important to remember that this metadata is visible to anyone who has permission to view the contents of this folder.
In other words, if one Workbench user creates or imports a dataset it will be visible to any other Workbench user who has access to that folder.
The process of sharing data between users is thereby entirely managed by the file system access permissions, and not by the Workbench.

Relying on the file system for user authorization and file management is a core principle of the BASH Workbench.
Rather than storing user-level permissions in a separate database, the Workbench simply mirrors the permissions which have been granted to each user by the underlying file system (or object storage). Administrators have been successfully maintaining multitenant computing clusters for years, and there's no need to reinvent that particular wheel.

### Dataset Annotation

Every **dataset** folder contains a file `._wb/index.json` which contains any metadata annotating that folder.
The index JSON is structured as a set of key-value pairs, for example:
```
{
"uuid": "cb16a629-4eda-4da0-9d10-65e3ad7388f9",
"created_at": "2022-02-14 23:00:14",
"tags": {},
"tool": "make_tar_gz",
"launcher": "base",
"name": "Example Dataset",
"description": "Longer description used to describe the contents of the example dataset."
}
```

This file is created whenever the Workbench indexes a folder, and may be modified directly by the workbench, by any **tool**, or by any user with permission.

Useful elements of the folder attributes JSON may include:
- `description`: Free text allowing the user to describe the contents of the **dataset** or **collection**;
- `name`: Name displayed for the folder in the Workbench which is initially populated as the folder name, but can be edited without changing any file locations;
- `tags`: Nested dictionary of key-value pairs which can be used to quickly search and filter datasets across collections.

### Home Folder

The environment of each user is managed by updating the contents of their `HOME_FOLDER`.
By default, the `HOME_FOLDER` for each user is located inside the home directory within
the folder `~/._workbench/default/`.

The location of the BASH Workbench `HOME_FOLDER` may be modified using two variables:
- The "base folder" (default: `~/.workbench`) may be modified with the command line flag `--base-folder` or the environment variable `$WB_BASE`; and
- The "profile" (default: `default`) which may be modified with the command line flag `--profile` or the environment variable `$WB_PROFILE`. 

In both cases the command line flag takes precedence over the environment variable.

This configuration is intended to allow a single user can create additional `profile` 
folders (e.g. `$HOME/._workbench/demo`) to maintain alternate environments in the 
Workbench containing different sets of **datasets**, **tools** and **launchers**.

The profile home folder contains:

 - `data/`: Contains symlinks to the **datasets** which may be located in different parts of a larger filesystem;
 - `params/`: Contains the saved settings used to run any **tools** or **launchers**.
 - `repositories/`: Contains any external code repositories which contain **tools** and **launchers** that have been imported by the user.

### Repositories

All of the **tools** and **launchers** used by the BASH Workbench are intended to
be saved and shared in code repositories.
Any code repository may be used for this purpose by adding content to the top-level
directories `._wb/tool/` and/or `._wb/launcher/`.
Repositories can be added to the BASH Workbench for a single user by using built-in
utilities provided for either:
- (a) cloning a repository directly to the `<HOME>/repositories/` folder, or
- (b) creating a symlink in `<HOME>/repositories/` to a repository which has previously
been cloned to another location in the filesystem.

### Tools

Each tool must consist of (1) a JSON file defining the files and parameters used as input (`config.json`), and (2) an executable script which runs an appropriate analysis based on those inputs (`run.sh`).
Each of those files are located within a **repository** folder under the `tool/` folder in a subfolder named for the tool.

```
<HOME_FOLDER>/repositories/<REPO_NAME>/._wb/tool/<TOOL_NAME>/config.json
<HOME_FOLDER>/repositories/<REPO_NAME>/._wb/tool/<TOOL_NAME>/run.sh
```

### Launchers

Each launcher must consist of (1) a JSON file defining the files and parameters used as input (`config.json`), and (2) an executable script which invokes the helper script `run_tool`, which invokes the tool's run script while capturing all logs and error messages.
Each of those files are located within a **repository** folder under the `launcher/` folder in a subfolder named for the launcher.

```
<HOME_FOLDER>/repositories/<REPO_NAME>/._wb/launcher/<LAUNCHER_NAME>/config.json
<HOME_FOLDER>/repositories/<REPO_NAME>/._wb/launcher/<LAUNCHER_NAME>/run.sh
```

### Referencing Tools and Launchers

When a **repository** has been cloned by the BASH Workbench, it will be referenced
by a combination of the organization and repository names (in case there are two
repositories with the same name from two different organizations). For example,
the repository [FredHutch/bash-workbench-tools](https://github.com/FredHutch/bash-workbench-tools)
will be cloned to `<HOME_FOLDER>/repositories/FredHutch_bash-workbench-tools`
and referenced by the user with the name `FredHutch_bash-workbench-tools`.

When a **repository** has been linked into the BASH Workbench from another location
in the filesystem, the user may select any name for it to be referenced by.

Each **tool** or **launcher** is referenced by a combination of its repository and name.

For example, when a user runs the **tool** `FredHutch_bash-workbench-tools/make_tar_gz`, it will reference the tool which is configured within `<HOME_FOLDER>/repositories/FredHutch_bash-workbench-tools/._wb/tool/make_tar_gz/`

With this approach, it should be possible to distribute the **tools** and **launchers** needed to run a particular analysis by anyone using the BASH Workbench.

## Testing

To run the test suite configured in `tests/cli.bats`, use the [act](https://github.com/nektos/act)
utility to run the GitHub Actions (configured in `.github/workflows/ci.yaml`).
After installing `act`, the testing suite can be invoked with `act push`.

## Contributing

The BASH Workbench is intended to be an open project which benefits a broad community
of users. Contributions are welcome from any developer in the form of PRs on
[this](https://github.com/FredHutch/bash-workbench) repository.
If you have an interest in contributing, please get in touch or start an
[issue](https://github.com/FredHutch/bash-workbench/issues) to discuss and make
sure that the contribution fits into the larger development landscape.

The major areas in which this project could helpfully be supported moving forward
include:

- Configuring additional repositories with **tools** and **launchers** which are most useful to users;
- Adding support for more convenient user interfaces, e.g. a textual user interface built on something like [npyscreen](https://npyscreen.readthedocs.io/) or [textual](https://github.com/Textualize/textual/);
- Adding support for other filesystems, e.g. cloud computing platforms, both in terms of stand-along **launchers** as well as built-in adapters for managing **datasets** located in object storage.
