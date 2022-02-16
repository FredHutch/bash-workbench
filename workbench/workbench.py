#!/usr/bin/env python3

from wb_tui.app import WorkbenchApp
from wb_tui.args import parse_args
from wb_utils.workbench import Workbench


if __name__ == "__main__":

    # Parse the command line arguments
    args = parse_args()

    # Instantiate an object which contains all of the data and functions needed
    # to coordinate the Workbench
    wb = Workbench(
        base_folder=args.base_folder,
        profile=args.profile
    )

    TA = WorkbenchApp()
    TA.run()
