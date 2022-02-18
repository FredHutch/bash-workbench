import argparse
import os
import bash_workbench as wb

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

    parser.add_argument(
        "--filesystem",
        type=str,
        default="local",
        help="Type of filesystem used to store datasets (options: local)."
    )

    # Add subparsers for each of the commands within the CLI
    subparsers = parser.add_subparsers(
        title="subcommands",
        help="Workbench CLI Commands"
    )

    # Store the information for each subcommand as a list
    command_parsers = [
        dict(
            key="setup_root_folder",
            help="""
            Ensure that the root workbench folder has all necessary folders set up.
            The location of the root workbench folder can be customized by modifying the
            base arguments for the CLI, e.g.
            workbench-cli --base-folder <> --profile <> setup_root_parser
            """
        ),
        dict(
            key="index_dataset",
            help="""
            Index a dataset folder, adding annotations and linking
            to the larger tree of datasets and collections.
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    required=True,
                    help="Location of folder to index"
                )
            )
        ),
        dict(
            key="index_collection",
            help="""
            Index a collection folder, adding annotations and linking
            to the larger tree of datasets and collections.
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    required=True,
                    help="Location of folder to index"
                )
            )
        ),
        dict(
            key="show_datasets",
            help="""
            Print the list of all datasets linked to the home directory.
            """,
            kwargs=dict(
                format=dict(
                    type=str,
                    default="json",
                    help="Format to use for printing"
                )
            )
        ),
        dict(
            key="find_datasets",
            help="""
            Find the dataset(s) by searching names, descriptions, and tags.
            """,
            kwargs=dict(
                name=dict(
                    type=str,
                    default=None,
                    help="Only show datasets containing this term or phrase in their name"
                ),
                description=dict(
                    type=str,
                    default=None,
                    help="Only show datasets containing this term or phrase in their description"
                ),
                tag=dict(
                    type=str,
                    default=None,
                    help="Only show datasets with this tag (specify as 'KEY=VALUE')"
                ),
                format=dict(
                    type=str,
                    default="json",
                    help="Format to use for printing"
                )
            )
        ),
        dict(
            key="change_name",
            help="""
            Change the name of a dataset
            """,
            kwargs=dict(
                uuid=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its uuid"
                ),
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                name=dict(
                    type=str,
                    default=None,
                    help="New name to apply to the dataset"
                )
            )
        ),
        dict(
            key="change_description",
            help="""
            Change the description of a dataset
            """,
            kwargs=dict(
                uuid=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its uuid"
                ),
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                description=dict(
                    type=str,
                    default=None,
                    help="New description to apply to the dataset"
                )
            )
        ),
    ]

    # Iterate over each of the subcommands
    for command_info in command_parsers:

        # Make sure that the required fields are available
        for field in ["help"]:
            assert field in command_info, f"All subcommands must have '{field}' defined"

        # Add a parser for this command
        command_info["parser"] = subparsers.add_parser(
            command_info["key"],
            help=command_info["help"]
        )

        # Iterate over any kwargs, if any
        for key, params in command_info.get("kwargs", {}).items():

            # Add the params for that kwarg, which applies to only this command
            command_info["parser"].add_argument(
                f"--{key}",
                **params
            )

        # Add the default function
        command_info["parser"].set_defaults(
            func=command_info["key"]
        )

    return parser
