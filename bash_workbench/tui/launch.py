#!/usr/bin/env python3

import bash_workbench as wb

def tui():

    # Parse the command line arguments
    args = wb.tui.args.parse_args()

    # Instantiate an object which contains all of the data and functions needed
    # to coordinate the Workbench
    workbench = wb.utils.workbench.Workbench(
        base_folder=args.base_folder,
        profile=args.profile
    )

    TA = wb.tui.app.WorkbenchApp()
    TA.run()
