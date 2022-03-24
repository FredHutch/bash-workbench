#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argcomplete
import bash_workbench as wb
import json
import yaml
import os

def cli():
    
    # Get the base parser for the CLI
    parser = wb.cli.args.make_parser()

    # Enable autocomplete
    argcomplete.autocomplete(parser)

    # Parse the arguments
    args = parser.parse_args()

    # If the base folder does not exist
    if not os.path.exists(args.base_folder):

        # Create it
        os.makedev(args.base_folder)

    # Get a logger
    # If the user specified a function, output to the screen
    # Either way, append to a log file in the base folder
    logger = wb.utils.logging.setup_logger(
        log_stdout="func" in args.__dict__,
        log_fp=os.path.join(args.base_folder, ".wb_log"),
    )

    # Set up a Workbench object
    WB = wb.utils.workbench.Workbench(
        base_folder=args.base_folder,
        profile=args.profile,
        filesystem=args.filesystem,
        logger=logger
    )

    # If the user did not provide any command to run
    if "func" not in args.__dict__:

        # Start the interactive menu
        wb.utils.menu.WorkbenchMenu(WB)

    # If a command was provided
    else:

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
