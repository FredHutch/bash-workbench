#!/bin/bash

set -e

# The script used to execute the tool will be named with the
# ._wb_ prefix to avoid collision with any other files

# Run the `log_command.sh` wrapper, which will save the
# STDOUT and STDERR to ._wb_stdout.txt and ._wb_stderr.txt
./._wb_log_command.sh
