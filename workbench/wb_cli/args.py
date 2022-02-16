import argparse
import os
import wb_utils

def make_parser():
    """Return a base parser used to format command line arguments for the Workbench CLI."""

    parser = argparse.ArgumentParser(
        description="Command Line Interface for the BASH Workbench"
    )

    # Options which apply to all invocations of the CLI
    parser.add_argument(
        "--base-folder",
        type=str,
        default=os.path.join(os.path.expanduser("~"), "._workbench"),
        help="Base folder which contains all profile folders"
    )

    parser.add_argument(
        "--profile",
        type=str,
        default="default",
        help="Profile name corresponding to a folder within the base folder. All datasets, tools, and configurations are stored here."
    )

    # Add subparsers for each of the commands within the CLI
    subparsers = parser.add_subparsers(
        title="subcommands",
        help="Workbench CLI Commands"
    )

    # Store the information for each subcommand as a nested dictionary
    command_parsers = dict(
        setup_root_folder=dict(
            func=wb_utils.filesystem.local.setup_root_folder,
            help="""
            Ensure that the root workbench folder has all necessary folders set up.
            The location of the root workbench folder can be customized by modifying the
            base arguments for the CLI, e.g.
            workbench-cli --base-folder <> --profile <> setup_root_parser
            """
        )
    )

    # Iterate over each of the subcommands
    for func_name in command_parsers:

        # Make sure that the required fields are available
        for field in ["func", "help"]:
            assert field in command_parsers[func_name], f"All subcommands must have '{field}' defined"

        # Add a parser for this command
        command_parsers[func_name]["parser"] = subparsers.add_parser(
            func_name,
            help=command_parsers[func_name]["help"]
        )

        # Iterate over any kwargs, if any
        for key, params in command_parsers[func_name].get("kwargs", {}).items():

            # Add the params for that kwarg, which applies to only this command
            command_parsers[func_name]["parser"].add_argument(
                key,
                **params
            )

    return parser
