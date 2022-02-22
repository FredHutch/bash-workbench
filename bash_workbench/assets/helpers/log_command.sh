#!/bin/bash

set -e

# The script used to execute the tool will be named with the
# ._wb_ prefix to avoid collision with any other files

# Run the tool with the `run_tool.sh` script defined by the
# tool developer. While running this command, route any
# messages to standard out or standard error to canonical
# filepaths
./._wb_run_tool.sh 2> ._wb_error.txt 1> ._wb_output.txt
