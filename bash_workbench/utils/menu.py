# Import the Workbench class to specify input type
from .workbench import Workbench

class WorkbenchMenu:

    def __init__(self, WB:Workbench):
        """Launch an interactive menu for the BASH Workbench"""

        # Attach the workbench which has been provided
        self.wb = WB

        # Start at the main manu
        self.main_menu()

    def main_menu(self):
        """Show the main menu"""

        self.wb.log("HERE")