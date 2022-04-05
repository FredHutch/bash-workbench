#!/bin/bash

set -euo pipefail

# Set the location of the workbench index
export WB_BASE=$PWD/base_folder
export WB_PROFILE=test

# Run the BATS tests
bats cli.bats