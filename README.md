# Dataset Workbench

A dataset manager for bioinformaticians

The world is awash in data, but different communities tend to organize their
data in different ways. The Dataset Workbench is a dataset manager for people
who tend to organize their data as collections of files. The goal of this
utility is to make it easier to keep track of where your datasets are, remember
how they were made, and quickly create new ones based on easily-sharable code
templates.

## Motivated by Bioinformatics

The number of technologies available for organizing data are far too numerous
to mention, but none of them quite fit the needs of bioinformaticians.
While the world of bioinformatics is broad, one common theme is its datasets
are large and do not adhere to strict formats or structures.

The prime exemplar of the theme which motivates this project is genomic data.
When genome sequencers are used to process a DNA sample, they output a
randomly ordered collection of genome sequence fragments with associated
quality information.
While it may be technically possible to load those sequences into a database,
it is far more efficient to store them as a compressed text file in FASTQ
format and process them with one of the many algorithms which have been
built by researchers to consume this file type.
In many cases the initial processing step for genomic sequence data is to
align each sequence fragment against a reference genome and record the position
from which it likely originated.
While the resulting dataset contains more structured information than the
raw FASTQ, the most efficient way to store and query these enormous datasets
is use a binary representation of those alignments (BAM format), or one of
its compressed incarnations.

If only it were simple enough to create a dataset manager oriented around
compressed BAM files with their standardized format.
After generating those BAM files, bioinformaticians may do any number of
interesting things with that data: detecting nucleotide variants, measuring
gene expression levels, discovering changes in genome structure, or even
identifying molecular changes to individual nucleotides.
Each of those different analyses produce outputs with different inherent
structures which may be serialized in a number of formats: CSV, HDF, JSON,
and HTML being some of the most common.
To make things even more complex, there are many types of genomic analysis
which entirely forego the alignment to BAM format, such as taxonomic profiling,
amplicon sequencing, CRISPR screening, etc.

Rather than bemoan the lack of file format standardization, we can focus on
the practices and traditions which are generally shared across the discipline.
Each discrete batch of analysis tends to have inputs which include both files
and parameters.
The most flexible way to codify a batch of analysis is using a shell script
containing one or more commands.
Depending on the goal, the analysis may range in complexity all the way from
calling a single executable program all the way up to invoking a workflow
manager to preform a series of interconnected steps.
After the analysis is complete a collection of file objects will be created,
typically within a single folder.

As a working bioinformatician, I frequently find myself in the position of
creating folders, creating a shell script based on something that I've done
before, adding in the appropriate reference to the files and parameters
that are appropriate for this anlaysis, and running the analysis to
create a new dataset.
The Dataset Workbench is an attempt to make this type of work easier,
for myself and others who work in a similar way.

## Key Concepts

To describe the behavior of the Dataset Workbench, we will use the terminology
of a local filesystem (files, folders, etc.). However, the core concepts
are easily extensible to object storage systems hosted by cloud service
providers. The underlying code used by the Dataset Workbench includes adapters
for each type of storage, and can conceptually be extended to any file-based
data storage system.

### Dataset

A **dataset** is a folder containing any number of files or subfolders.
However, it cannot contain any nested **datasets**. **Datasets** can be
created by the Dataset Workbench as the output of a **tool**, or by
simply indexing the contents of an existing folder.

### Collection

A **collection** is a folder which contains any number of **datasets**
and **collections**. The Dataset Workbench will make it easier to keep
track of **collections** of **datasets** using a typical folder
hierarchy system.

### Tool

The Dataset Workbench keeps track of a collection of **tools**, each
of which consists of a shell script which can be run on a defined set
of file and/or parameter inputs.

### Configuration

The way in which a particular set of **tools** can be executed on a
type of computational system is defined as a **configuration**. The
**configuration** makes it easier for a user to re-use a job submission
script and associated parameters across a collection of **tools**.

## Implementation

The Dataset Workbench makes it easier to manage and manipulate an existing
filesystem, and does not require that any data is moved to a dedicated
location. By using the file prefix `._dw_`, the DW can annotate any
existing folder and store associated metadata in-place. It is important
to remember that this metadata is visible to anyone who has permission
to view the contents of this folder. In other words, if one DW user creates
or imports a dataset it will be visible to any other DW user who has
access to that folder. The process of sharing data between users is
thereby entirely managed by the file system access permissions, and not
by the DW.

### Dataset Annotation

Every **dataset** contains a file `._dw_dataset.json` which contains
any metadata annotating that **dataset** in JSON format. This file may
be populated by importing the **dataset** directly, or by the output
of the **tool** which is used to create it, if any. Any user may also
manually alter the contents of this file as needed.

### Collection Annotation

Every **collection** contains a file `._dw_collection.json` which contains
any metadata annotating that **collection** in JSON format. This will
typically be used to attach titles and descriptions to the **collection**
to support the overall organization of data.

### Home Folder

The environment of each user is managed by updating the contents of
the folder `$HOME/._dataset_workbench/`. By setting the root of the
environment in this folder, every user of a multi-tenant system can
use the DW to manage their own unique collection of datasets.

The home folder contains:

 - `datasets/`: Contains symlinks to the **collections** which are
 at the root of the dataset hierarchy;
 - `tools/`: Contains all of the **tools** available to the user
 from the local environment;
 - `configurations/`: Contains all of the **configurations** available
 to the user from the local environment;
 - `repositories/`: Contains any external code repositories which
 contain **tools** and **configurations** that have been imported
 by the user.

### Tools

Each tool must consist of (1) a JSON file defining the files and
parameters used as input (`tool.json`), and (2) an executable
script which runs an appropriate analysis based on those inputs
(`tool.sh`).
Each of those files are located with the `tools/` folder in a
subfolder named for the tool.

```
$HOME/._dataset_workbench/tools/toolname/tool.json
$HOME/._dataset_workbench/tools/toolname/tool.sh
```

### Configurations

Each configuration must consist of (1) a JSON file defining the
files and parameters used as input (`config.json`), and (2) an
executable script which invokes a tool script appropriately,
based on those inputs (`config.sh`).
Each of those files are located with the `config/` folder in a
subfolder named for the configuration.

```
$HOME/._dataset_workbench/config/configname/config.json
$HOME/._dataset_workbench/config/configname/config.sh
```

### Sharing Tools and Configurations

Any external code repository which contains a folder `._dataset_mananger/`
may be used to host **tools** and **configurations**. Those tools will
be referenced with a `source` field corresponding to the repository,
while all of the local resources will be referenced with a `source`
value of `home`.

For example, when a user runs the following tool:
```
{"tool": "aligner", "source": "ExternalOrg/UsefulRepo"}
```
The GitHub repository `ExternalOrg/UsefulRepo` will be cloned to
`$HOME/._dataset_workbench/repositories/` and the **tool** will be sourced
from the subfolder `._dataset_workbench/tools/aligner/`.

With this approach, it should be possible to distribute the tools
and configurations needed to run a particular analysis by anyone
using the Dataset Workbench.
