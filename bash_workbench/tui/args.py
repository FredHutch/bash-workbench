import argparse
import os

def parse_args():
    """Parse command line arguments for the Workbench TUI."""

    parser = argparse.ArgumentParser(
        description="User Interface for the BASH Workbench"
    )

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

    return parser.parse_args()
