#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argcomplete
from .args import make_parser
from .filelib import FileLib
from .logging import setup_logger
from .menu import WorkbenchMenu
from .workbench import Workbench
import json
import yaml
import os

def cli():
    
    # Get the base parser for the CLI
    parser = make_parser()

    # Enable autocomplete
    argcomplete.autocomplete(parser)

    # Parse the arguments
    args = parser.parse_args()

    # Get the library of functions used to interact with the filesystem
    filelib = FileLib(args.filesystem)

    # If the base_folder field was not provided
    if args.base_folder is None:

        # Set the location as ~/.workbench/
        args.base_folder = filelib.path_join(filelib.home(), "._workbench")

    # If the base folder does not exist
    if not os.path.exists(args.base_folder):

        # Create it
        os.makedirs(args.base_folder)
    
    assert args.profile is not None, "Must provide profile"

    # The home folder for the workbench is <base_folder>/<profile>/
    base_path = filelib.path_join(args.base_folder, args.profile)

    # If the folder does not exist
    if not filelib.exists(base_path):

        # Create it
        filelib.mkdir_p(base_path)

    # Resolve the absolute path to the home folder
    base_path = filelib.abs_path(base_path)

    # Get a logger
    # If the user specified a function, output to the screen
    # Either way, append to a log file in the base folder
    logger = setup_logger(
        log_stdout="func" in args.__dict__,
        log_fp=os.path.join(base_path, ".wb_log"),
    )

    # Set up a Workbench object
    WB = Workbench(
        base_path=base_path,
        filelib=filelib,
        logger=logger,
        verbose=False
    )

    # If the user did not provide any command to run
    if "func" not in args.__dict__:

        # Start the interactive menu
        WorkbenchMenu(WB)

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
