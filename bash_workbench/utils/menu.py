# Import the Workbench class to specify input type
from .workbench import Workbench
import questionary

class WorkbenchMenu:

    def __init__(self, WB:Workbench):
        """Launch an interactive menu for the BASH Workbench"""

        # Attach the workbench which has been provided
        self.wb = WB

        # Start at the main manu
        self.main_menu()

    def select_func(self, prompt, options, **kwargs):
        """Prompt the user to select from a list of functions to execute."""

        # `options` must be a list of tuples
        msg = "`options` must be a list of tuples"
        assert isinstance(options, list), msg

        # Each tuple in the list must consist of two strings:
        # 1) The string used to describe the option, and
        # 2) The function which will be executed

        # Make sure that the options follow that format, before
        # launching the questionary prompt
        for option in options:
            msg = f"Option must have two elements ({option})"
            assert len(option) == 2, msg
            msg = f"Option must have a string in the first position ({option})"
            assert isinstance(option[0], str), msg
            msg = f"Option must have a callable function in the second position ({option})"
            assert callable(option[1]), msg

        # Get the selection from the user
        selection = questionary.select(
            prompt,
            choices=[
                option[0]
                for option in options
            ]
        ).ask()

        # Call the function provided, including any additional keywords
        # provided by the user when calling this wrapper function
        dict(options).get(selection)(**kwargs)

    def main_menu(self):
        """Show the main menu"""

        # Select a submenu
        # The user selection will run a function
        self.select_func(
            """Would you like to:""",
            [
                ("Tools - Inspect the analysis tools available", self.tool_menu),
                ("Datasets - Browse and create new datasets", self.dataset_menu),
                ("Repositories - Add tools from code repositories", self.repository_menu)
            ]
        )

    def tool_menu(self):
        self.wb.log("Tools MENU")
    
    def dataset_menu(self):
        self.wb.log("Datasets MENU")
    
    def repository_menu(self):
        self.wb.log("Repositories MENU")