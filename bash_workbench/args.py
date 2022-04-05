import argparse
import os
import json
from .filelib import FileLib


def read_asset_configs() -> dict:
    """Before setting up the parser, read any asset configurations from the current working directory."""

    # Get a filesystem library helper
    filelib = FileLib()
    
    asset_configs = dict()

    # Keep a list of all of the asset types
    asset_type_list = ["tool", "launcher"]

    # Check for configurations of both a tool and launcher    
    for asset_type in asset_type_list:

        # If the index folder eixsts
        if filelib.isdir("._wb"):

            # Get the folder used for the asset
            asset_folder = filelib.path_join("._wb", asset_type)

            # Get the file used for the configuration, if it exists
            asset_config = filelib.read_json_in_folder(asset_folder, "config.json")

            # If there is a configuration
            if asset_config is not None:

                # If there are arguments defined
                if asset_config.get("args") is not None:

                    # Save them
                    asset_configs[asset_type] = asset_config.get("args")

        # If arguments were defined
        if asset_configs.get(asset_type) is not None:

            # Read any previously-set parameters
            params_json = filelib.read_json_in_folder(asset_folder, "params.json")

            # If parameters were previously set
            if params_json is not None:

                # Iterate over each of those
                for kw, val in params_json.items():

                    # If there is an argument configured
                    if asset_configs[asset_type].get(kw) is not None:

                        # Set the default value
                        asset_configs[asset_type][kw]["default"] = val

                        # Make sure that it is no longer rquired
                        asset_configs[asset_type][kw]["required"] = False

    # Create a set of arguments which combines all asset types
    # Note that any arguments with the same key will be mapped to the first
    # asset type in the list.
    combined_configs = dict()

    # Iterate over the asset types
    for asset_type in asset_type_list:

        # For each of the arguments set by this asset
        for kw, arg in asset_configs.get(asset_type, dict()).items():

            # If the argument has not been set by a previous asset type
            if combined_configs.get(kw) is None:

                # Set the argument
                combined_configs[kw] = arg

    # Set a new value for the combined arguments
    asset_configs["combined"] = combined_configs

    return asset_configs


def make_parser():
    """Return a base parser used to format command line arguments for the Workbench CLI."""

    # Before setting up the parser, read any asset configurations from the current working directory
    asset_configs = read_asset_configs()

    parser = argparse.ArgumentParser(
        description="Command Line Interface for the BASH Workbench"
    )

    # Options which apply to all invocations of the CLI
    parser.add_argument(
        "--base-folder",
        type=str,
        default=os.getenv(
            "WB_BASE",
            default=os.path.join(os.path.expanduser("~"), "._workbench")
        ),
        help="Base folder which contains all profile folders"
    )

    parser.add_argument(
        "--profile",
        type=str,
        default=os.getenv(
            "WB_PROFILE",
            default="default"
        ),
        help="Profile name corresponding to a folder within the base folder. All datasets, tools, and configurations are stored here."
    )

    parser.add_argument(
        "--filesystem",
        type=str,
        default="local",
        help="Type of filesystem used to store datasets (options: local)."
    )

    parser.add_argument(
        "--print-format",
        type=str,
        default="json",
        help="Format used to print CLI output (default: json, options: json, yaml)."
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
            key="index_folder",
            help="""
            Index a dataset folder, adding annotations and linking
            to the larger tree of indexed dataset folders.
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    required=True,
                    help="Location of folder to index as a dataset"
                )
            )
        ),
        dict(
            key="list_datasets",
            help="""
            Print the list of all datasets linked to the home directory.
            """,
            kwargs=dict()
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
                    nargs="+",
                    help="Only show datasets containing this term or phrase in their name"
                ),
                description=dict(
                    type=str,
                    default=None,
                    nargs="+",
                    help="Only show datasets containing this term or phrase in their description"
                ),
                tag=dict(
                    type=str,
                    default=None,
                    nargs="+",
                    help="Only show datasets with this tag (specify one or more as 'KEY1=VALUE1 KEY2=VALUE2')"
                )
            )
        ),
        dict(
            key="change_name",
            help="""
            Change the name of a dataset
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                name=dict(
                    type=str,
                    default=None,
                    nargs="+",
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
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                description=dict(
                    type=str,
                    default=None,
                    nargs="+",
                    help="New description to apply to the dataset"
                )
            )
        ),
        dict(
            key="update_tag",
            help="""
            Change the value of a tag for a dataset
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                key=dict(
                    type=str,
                    default=None,
                    help="Name of the tag"
                ),
                value=dict(
                    type=str,
                    default=None,
                    help="Value of the tag"
                )
            )
        ),
        dict(
            key="delete_tag",
            help="""
            Remove a tag from a dataset if it is present
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    default=None,
                    help="Specify the dataset to modify by its absolute or relative path"
                ),
                key=dict(
                    type=str,
                    default=None,
                    help="Name of the tag"
                )
            )
        ),
        dict(
            key="update_base_toolkit",
            help="""
            Copy all tools and launchers from the repository into the home directory
            """,
            kwargs=dict(
                overwrite=dict(
                    action="store_true",
                    help="If specified, overwrite any local tools or launchers with the same name"
                )
            )
        ),
        dict(
            key="list_tools",
            help="""
            Print a list of all available tools
            """,
            kwargs=dict()
        ),
        dict(
            key="list_launchers",
            help="""
            Print a list of all available launchers
            """,
            kwargs=dict()
        ),
        dict(
            key="setup_dataset",
            help="""
            Populate a dataset directory with the configuration and script for a tool and launcher
            """,
            kwargs=dict(
                path=dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder to be populated"
                ),
                tool=dict(
                    type=str,
                    default=None,
                    help="Name of tool used to run the analysis"
                ),
                launcher=dict(
                    type=str,
                    default="base",
                    help="Name of launcher used to run the analysis"
                ),
                overwrite=dict(
                    action="store_true",
                    help="If specified, overwrite any local tools or launchers in the folder"
                )
            )
        ),
        dict(
            key="set_tool_params",
            help="""
            Set the parameters used to run the tool in a particular dataset
            """,
            kwargs={
                "path": dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder to be configured"
                ),
                **asset_configs.get("tool", {})
            }
        ),
        dict(
            key="set_launcher_params",
            help="""
            Set the parameters used to run the launcher in a particular dataset
            """,
            kwargs={
                "path": dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder to be configured"
                ),
                **asset_configs.get("launcher", {})
            }
        ),
        dict(
            key="save_tool_params",
            help="""
            Save the parameters used to run the tool in a particular dataset
            """,
            kwargs={
                "path": dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder containing parameters to be saved"
                ),
                "name": dict(
                    type=str,
                    required=True,
                    help="Name associated with saved parameters"
                ),
                "overwrite": dict(
                    action="store_true",
                    help="If specified, overwrite any existing parameters with the same name"
                )
            }
        ),
        dict(
            key="save_launcher_params",
            help="""
            Save the parameters used to run the launcher in a particular dataset
            """,
            kwargs={
                "path": dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder containing parameters to be saved"
                ),
                "name": dict(
                    type=str,
                    required=True,
                    help="Name associated with saved parameters"
                ),
                "overwrite": dict(
                    action="store_true",
                    help="If specified, overwrite any existing parameters with the same name"
                )
            }
        ),
        dict(
            key="read_tool_params",
            help="""
            Read the saved parameters used to run the tool
            """,
            kwargs={
                "tool_name": dict(
                    type=str,
                    required=True,
                    help="Name of the tool"
                ),
                "params_name": dict(
                    type=str,
                    required=True,
                    help="Name associated with saved parameters"
                )
            }
        ),
        dict(
            key="read_launcher_params",
            help="""
            Read the saved parameters used to run the launcher
            """,
            kwargs={
                "launcher_name": dict(
                    type=str,
                    required=True,
                    help="Name of the launcher"
                ),
                "params_name": dict(
                    type=str,
                    required=True,
                    help="Name associated with saved parameters"
                )
            }
        ),
        dict(
            key="list_tool_params",
            help="""
            List the parameters which have been saved for this particular tool
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name of the tool"
                )
            }
        ),
        dict(
            key="list_launcher_params",
            help="""
            List the parameters which have been saved for this particular launcher
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name of the launcher"
                )
            }
        ),
        dict(
            key="run_dataset",
            help="""
            Launch the launcher + tool which have been configured in a dataset
            """,
            kwargs={
                "path": dict(
                    type=str,
                    default=os.getcwd(),
                    help="Dataset folder to be run"
                ),
                "wait": dict(
                    action="store_true",
                    help="If specified, block until the dataset has finished running"
                ),
                # Add the combined set of arguments for both the tool and launcher
                **asset_configs.get("combined", {})
            }
        ),
        dict(
            key="add_repo",
            help="""
            Download a GitHub repository for local execution, if it does not already exist
            """,
            kwargs={
                "remote-name": dict(
                    type=str,
                    required=True,
                    help="Name of repository to add (e.g. FredHutch/bash-workbench-tools)"
                )
            }
        ),
        dict(
            key="list_repos",
            help="""
            Print a list of the GitHub repositories which are available locally
            """,
            kwargs={}
        ),
        dict(
            key="update_repo",
            help="""
            Update a repository to the latest version
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name of repository to update (e.g. FredHutch/bash-workbench-tools)"
                )
            }
        ),
        dict(
            key="delete_repo",
            help="""
            Delete the local copy of a repository, if it exists
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name of repository to update (e.g. FredHutch/bash-workbench-tools)"
                )
            }
        ),
        dict(
            key="link_local_repo",
            help="""
            Link a local repository (containing a ._wb/ directory of tools and/or launchers)
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name to use for linked repository"
                ),
                "path": dict(
                    type=str,
                    required=True,
                    help="Path to local repository which should be linked"
                )
            }
        ),
        dict(
            key="unlink_local_repo",
            help="""
            Remove a link to a local repository
            """,
            kwargs={
                "name": dict(
                    type=str,
                    required=True,
                    help="Name used for linked repository"
                )
            }
        )
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
        if command_info.get("kwargs") is not None:
            for key, params in command_info["kwargs"].items():

                # Add the params for that kwarg, which applies to only this command
                command_info["parser"].add_argument(
                    f"--{key}",
                    **{
                        k: v
                        for k, v in params.items()
                        if not k.startswith("wb_")
                    }
                )

        # Add the default function
        command_info["parser"].set_defaults(
            func=command_info["key"]
        )

    return parser
