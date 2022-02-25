#!/bin/bash

set -e

echo "Compressing ${TARGET} to create ${ARCHIVE}.tar.gz"

# -c : create
# -a : automatically gzip compress
# -v : report progress recursively
# -f : write to file
tar cavf ${ARCHIVE}.tar.gz ${TARGET}
