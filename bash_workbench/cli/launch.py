#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argcomplete
import bash_workbench as wb
import json
import yaml

def cli():
    
    # Get the base parser for the CLI
    parser = wb.cli.args.make_parser()

    # Enable autocomplete
    argcomplete.autocomplete(parser)

    # Parse the arguments
    args = parser.parse_args()

    # Get a logger which writes to standard out
    logger = wb.utils.logging.setup_logger(
        log_stdout=True,   # Print to standard out
        log_fp=None,       # Do not write to a file
    )

    # Set up a Workbench object
    WB = wb.utils.workbench.Workbench(
        base_folder=args.base_folder,
        profile=args.profile,
        filesystem=args.filesystem,
        logger=logger
    )

    # Run the specified command, passing through the arguments
    # which were not used to specify the configuration of the
    # Workbench object itself
    r = WB._run_function(
        args.func,
        **{
            k: v
            for k, v in args.__dict__.items()
            if k not in [
                "func",
                "filesystem",
                "base_folder",
                "profile",
                "print_format"
            ]
        }
    )

    # Print the returned value of the function, if there is any

    # If there is a value which was returned
    if r is not None:

        # Transform the data into a string based on the serialization
        # method specified by the user

        print_funcs = dict(
            json = lambda r: print(json.dumps(r, indent=4)),
            yaml = lambda r: print(yaml.dump(r))
        )

        # Invoke the function, falling back to print() for other types
        print_funcs.get(
            args.print_format,
            lambda r: print(r)
        )(r)
