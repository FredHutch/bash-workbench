import os
import wb_utils

class Workbench:
    """Object used to organize BASH Workbench attributes and methods."""

    def __init__(
        self,
        base_folder=os.path.join(os.path.expanduser("~"), "._workbench"),
        profile="default"
    ):
        # The base folder for the workbench is <base_folder>/<profile>/
        self.root = os.path.join(base_folder, profile)
    
        # Check and make sure that the root folder is populated appropriately
        self.setup_root_folder()

    def setup_root_folder(self):
        """Ensure that the root folder contains the required assets, and create them if necessary."""

        wb_utils.filesystem.local.setup_root_folder(self.root)