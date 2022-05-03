# Import the Workbench class to specify input type
from .workbench import Workbench
from .misc import convert_size
from .params_menu import ParamsMenu
import questionary
import json
import sys
import textwrap
from time import sleep, strftime, gmtime
import bash_workbench

class WorkbenchMenu:

    def __init__(self, WB:Workbench):
        """Launch an interactive menu for the BASH Workbench"""

        # Attach the workbench which has been provided
        self.wb = WB

        # Set up the root folder
        self.wb.setup_root_folder()

        # Define a spacer which will indent text
        self.spacer = "    "

        # Set the current working directory
        self.cwd = self.wb.filelib.getcwd()

        # Report the version of all software used
        self.print_versions()

        # Start at the main manu
        self.main_menu()

    def print_versions(self):
        """Print the versions of all packages used."""
        self.wb.log("Python version:")
        for l in sys.version.split("\n"):
            self.wb.log(l)
        self.wb.log(sys.version_info)
        self.wb.log(f"BASH Workbench: {bash_workbench.__version__}")

    def type_validator(self, t, v):
        """Return a boolean indicating whether `v` can be cast to `t(v)` without raising a ValueError."""
        try:
            t(v)
            return True
        except ValueError:
            return False

    def questionary(self, fname, msg, validate_type=None, output_f=None, **kwargs) -> str:
        """Wrap questionary functions to catch escapes and exit gracefully."""

        # Get the questionary function
        questionary_f = questionary.__dict__.get(fname)

        # Make sure that the function exists
        assert questionary_f is not None, f"No such questionary function: {fname}"

        if fname == "select":
            kwargs["use_shortcuts"] = True

        if validate_type is not None:
            kwargs["validate"] = lambda v: self.type_validator(validate_type, v)

        # The default value must be a string
        if kwargs.get("default") is not None:
            kwargs["default"] = str(kwargs["default"])

        # Add a spacer line before asking the question
        print("")

        # Get the response
        resp = questionary_f(msg, **kwargs).ask()

        # If the user escaped the question
        if resp is None:
            self.exit()

        # If an output transformation function was defined
        if output_f is not None:

            # Call the function
            resp = output_f(resp)

        # Otherwise
        return resp

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
        selection = self.questionary(
            "select",
            prompt,
            choices=[
                option[0]
                for option in options
            ]
        )

        # Call the function provided, including any additional keywords
        # provided by the user when calling this wrapper function
        dict(options).get(selection)(**kwargs)

    def check_indexed_cwd(self):
        """
        Check to see if the cwd if indexed
          If not, ask if the user wants to:
          index the folder,
          move to the root folder,
          or exit.
        """

        # If this is the home directory of the workbench
        if self.cwd == self.wb.base_path:

            # It does not need to be indexed
            return

        # Try to read an index for the cwd, if one exists
        ds = self.wb.dataset(self.cwd)

        # If an index does not exist
        if ds.index is None:

            # Ask the user if they want to index it
            self.select_func(
                textwrap.dedent(f"""
                The current working directory is not indexed
                ({self.cwd})
                Select an action:
                """),
                [
                    (
                        "Index the folder",
                        lambda: self.index_folder(self.cwd)
                    ),
                    ("Exit", self.exit)
                ]
            )

        # If the dataset is not in the collection
        if not self.wb.datasets.path_exists(self.cwd):

            # Add it to the collection
            self.wb.add_to_home_tree(ds, self.cwd)

            # Add it to the dataset collection
            self.wb.datasets.add(ds)

    def main_menu(self):
        """Show the main menu"""

        # Print a header
        self.print_header("BASH Workbench")

        # Check to see if the cwd if indexed
        #   If not, ask if the user wants to index the folder,
        #   move to the root folder, or quit
        self.check_indexed_cwd()

        # If this is not the home directory
        if self.cwd != self.wb.path("data"):

            # Get the dataset information
            ds = self.wb.dataset(self.cwd)

            # Show the name as a header
            self.print_header(f"Dataset: {ds.index.get('name', self.cwd)}")

            # Print:
            #   description, tags of cwd, etc.
            for key, val in ds.index.items():
                if key not in ["name", "status"]:
                    self.print_line(f"{key}: {val}", indent=1)

            # Print the directory
            self.print_line(f"path: {self.cwd}", indent=1)

            # If there is a 'status' defined
            if ds.index.get('status') is not None:

                # Print the status
                self.print_header(f"Dataset Status: {ds.index['status']}")

        else:

            self.print_header("Home")

        # Add a spacer line
        print("\n")

        # Build a list of options
        options = list()

        # If this is not the home directory
        if self.cwd != self.wb.path("data"):

            # Add option for running the dataset
            options.append(
                ("Run Tool", self.run_tool_menu)
            )

            # If there is a non-FAILED or COMPLETED status
            if ds.index.get("status", "FAILED") not in ["FAILED", "COMPLETED"]:

                # Add option for refreshing the status
                options.append(
                    ("Refresh Status", self.refresh)
                )

            # If there are any log files available
            if ds.has_logs():

                # Add option for viewing the logs
                options.append(
                    ("View Logs", self.tail_logs)
                )

            # Add option for editing the dataset
            # and navigating the proximate filesystem
            options.extend([
                ("Edit Folder Name/Description", self.edit_name_description),
                ("Change Directory", self.change_directory_menu),
                ("Make Subfolder", self.create_subfolder_menu),
                ("List Files", self.list_files)
            ])

        # Add options used for all folders
        options.extend([
            ("Explore Datasets", self.explore_datasets_menu),
            ("Browse Tools", self.browse_tool_menu),
            ("Browse Launchers", self.browse_launcher_menu),
            ("Manage Repositories", self.manage_repositories_menu),
            ("Return to Shell", self.exit)
        ])

        # Select a submenu
        # The user selection will run a function
        self.select_func("Would you like to:", options)

    def list_all_datasets(self):
        """List the complete set of datasets which have been indexed by the workbench."""

        # Print:
        #   Dataset tree beneath the cwd
        print(self.wb.datasets.format_dataset_tree())

        # Print the number of datasets and any filters which have been applied
        self.print_filters()

        # Go back to the "Explore Datasets" menu
        self.explore_datasets_menu()


    def explore_datasets_menu(self):
        """Inspect and navigate the available indexed datasets."""

        choices = [
            ("List All Datasets", self.list_all_datasets),
            ("Add/Remove Dataset Filters", self.add_remove_filters),
            ("Import Existing Dataset", self.import_folder)
        ]

        if len(self.wb.datasets.filtered_paths(sep=" : ")) > 0:
            choices.append(
                ("Change Directory", self.jump_directory_menu)
            )

        choices.append(
            ("Back to Main Menu", self.main_menu)
        )

        self.select_func(
            """Would you like to:""",
            choices
        )

    def print_line(self, text, indent=0, leader="- "):
        """Print a single line, with optional indentation and leader."""

        assert isinstance(indent, int)
        assert indent >= 0

        assert isinstance(leader, str)

        print("".join([self.spacer for i in range(indent)] + [leader, text]))

    def print_header(self, text, border_char="#"):
        """Print text with a border."""

        assert isinstance(border_char, str)
        assert len(border_char) == 1

        print("")
        print("".join(border_char for _ in range(len(text) + 4)))
        print(" ".join([border_char, text, border_char]))
        print("".join(border_char for _ in range(len(text) + 4)))
        print("")

    def edit_name_description(self):
        """Edit the name and/or description for a dataset."""

        # Read the dataset index
        ds = self.wb.dataset(self.cwd)

        # Prompt for the name and description
        for k in ["name", "description"]:
            ds.set_attribute(
                k,
                self.questionary(
                    "text",
                    f"Dataset {k.title()}",
                    default=ds.index[k]
                )
            )

        # Go back to the main menu
        self.main_menu()

    def jump_directory(self, path):
        """Change the working directory and return to the main menu."""

        # The `path` will either be relative or absolute

        # If the relative path is not valid
        if not self.wb.filelib.exists(path):

            # Then extrapolate to the absolute path
            path = self.wb.filelib.path_join(
                self.wb.base_path,
                "data",
                path
            )

        # Change the working directory
        self.print_line(f"Navigating to {path}")
        self.cwd = path

        # Catch any errors while changing directory
        try:
            
            # If the change was successful
            self.wb.filelib.chdir(path)

            # Go back to the main menu
            self.main_menu()
        
        # If there was an error
        except FileNotFoundError as e:

            # Print the error
            for line in str(e).split("\n"):
                self.print_line(line)

            # Give the user another chance
            self.jump_directory_menu()

    def list_files(self):
        """List the files in the current working directory."""

        # Make a list of files and folders
        files = list()
        folders = list()

        # Iterate over the items in this folder
        for fn in self.wb.filelib.listdir(self.cwd):

            # Construct the full path
            fp = self.wb.filelib.path_join(self.cwd, fn)

            # If the path is a folder
            if self.wb.filelib.isdir(fp):

                # Get the number of items in the folder
                n = len(self.wb.filelib.listdir(fp))

                # Report the number of items
                folders.append(
                    (fn + "/", f"(contains {n:,} items)")
                )

            # If the path is a file
            else:

                # Get the size of the file (in bytes)
                filesize = self.wb.filelib.getsize(fp)

                # Report the filesize, formatted nicely
                files.append(
                    (fn, convert_size(filesize))
                )

        if len(files) + len(folders) == 0:
            self.print_line(f"No files or folders found in {self.cwd}")

        else:

            self.print_line(f"Files/folders in {self.cwd}:")

            # Get the longest file name
            max_namelen = max([
                len(fn)
                for l in [folders, files]
                for fn, _ in l
            ])

            # First print folders, then files
            for l in [folders, files]:

                # For each path and description
                for fn, fn_str in l:

                    # Calculate the length of the spacer
                    spacer_len = 1 + max_namelen - len(fn)
                    
                    # Print the filepath, spacer, and description
                    self.print_line(f"{fn}{' ' * spacer_len}{fn_str}")

        # Back to the main menu after the user hits enter
        self.select_func(
            "Next",
            [
                ("Back to the main menu", self.main_menu)
            ]
        )

    def browse_tool_menu(self):
        """Show the user the set of tools which are available."""

        self._browse_asset_menu("tool")

    def browse_launcher_menu(self):
        """Show the user the set of launchers which are available."""

        self._browse_asset_menu("launcher")

    def _prompt_user_to_select_asset(self, asset_type):
        """Show the user the set of assets which are available."""

        # Make a list of repositories to choose from
        repository_choices = [
            f"{repo_name}\n      {asset_type.title()}s available: {len(repo.assets.get(asset_type, []))}"
            for repo_name, repo in self.wb.repositories.items()
            if len(repo.assets.get(asset_type, [])) > 0
        ]

        # Sort the list alphabetically
        repository_choices.sort()

        # Give the option to go back
        repository_choices.append("Back")

        # Ask the user to select a repository
        selected_repo = self.questionary(
            "select",
            f"Select a repository",
            choices=repository_choices
        )
        
        # Remove the description
        selected_repo = selected_repo.split("\n")[0]

        # If the user decided to go back
        if selected_repo == "Back":

            return (selected_repo, None)

        # Format a list of strings using the asset key, name, and description
        asset_choices = [
            f"{asset_name}\n      {asset.config['name']}\n      {asset.config['description']}\n"
            for asset_name, asset in self.wb.repositories[selected_repo].assets.get(asset_type, []).items()
        ]

        # Sort the list alphabetically
        asset_choices.sort()

        # Add the option to go back
        asset_choices.append("Back")

        # Get the selction
        selected_asset = self.questionary(
            "select",
            f"Select a {asset_type}",
            choices=asset_choices
        )

        # Return a tuple with the repository and the asset
        return (selected_repo, selected_asset.split("\n")[0])

    def _browse_asset_menu(self, asset_type):
        """Show the user the set of assets which are available."""

        # Present the user with a list of assets and get their response
        # If they want to select none, they can use the "Back" option provided
        repo_name, asset_name = self._prompt_user_to_select_asset(asset_type)

        # If the user decided to go back
        if repo_name == "Back" or asset_name == "Back":

            # Go back
            self.main_menu()

        # If the user selected a tool
        else:

            # Drop the user into the menu used to browse a single asset
            self._browse_single_asset(
                asset_type=asset_type,
                asset_name=asset_name,
                repo_name=repo_name
            )

    def _browse_single_asset(
        self,
        asset_type=None,
        asset_name=None,
        repo_name=None
    ):
        """
        Give the user the option to view file assets,
        or view / modify saved parameters.
        """

        # Make sure that the repo is valid
        assert repo_name in self.wb.repositories

        # Make sure that the asset type is valid
        assert asset_type in self.wb.repositories[repo_name].assets

        # Make sure that the asset name is valid
        assert asset_name in self.wb.repositories[repo_name].assets[asset_type]

        # Get the asset
        asset = self.wb.repositories[repo_name].assets[asset_type][asset_name]

        # Make a list of the files in the asset folder
        choices = [
            f"Show file: {fn}"
            for fn in asset.listdir()
        ]

        # Give the user the option to add a set of saved parameters
        choices.append("Add params")
        
        # Get the list of previously saved paramters for this tool
        saved_params_list = self.wb._list_asset_params(
            asset_type=asset_type,
            name=asset_name
        )

        # If there are any saved parameters available
        if len(saved_params_list) > 0:
            
            # Give the user the option to view them
            choices.extend([
                f"View params: {saved_params_name}"
                for saved_params_name in saved_params_list
            ])

            # Give the user the opportunity to delete any of them
            choices.append("Delete params")
        
        # Also give the user the option to go back to the previous menu
        choices.append("Back")

        # Select from the options
        selection = self.questionary(
            "select",
            "Display contents or modify saved params",
            choices=choices
        )

        # If the user selected the option to go back
        if selection == "Back":

            # Go back
            self._browse_asset_menu(asset_type)

        # If the user opted to view a set of saved params
        elif selection.startswith("View params: "):

            # Read the params
            saved_params = self.wb._read_asset_params(
                asset_type=asset_type,
                asset_name=asset_name,
                params_name=selection[len("View params: "):]
            )

            # Print to the screen
            print(json.dumps(saved_params, indent=4))
            sleep(0.2)

        # If the user has selected the option to remove a set of params
        elif selection == "Delete params":

            self.delete_asset_params_menu(
                asset_type=asset_type,
                asset_name=asset_name
            )

        # If the user has selected the option to add a new set of params
        elif selection == "Add params":

            self.add_asset_params_menu(
                asset_type=asset_type,
                asset_name=asset_name
            )

        # Otherwise, the user has selected to view a file
        else:

            assert selection.startswith("Show file: ")

            # Get the file name from the selection
            fn = selection[len("Show file: "):]

            # If it is a JSON file
            if fn.endswith(".json") or fn.endswith(".json.gz"):

                # Read the file
                dat = asset.read_json(fn)

                # Print with JSON indenting
                print(json.dumps(dat, indent=4))
                
            # If not JSON, then straight text
            else:

                # Read the file
                dat = asset.read_text(fn)

                # Print it
                print(dat)

        # Redisplay the menu
        self._browse_single_asset(
            asset_type=asset_type,
            asset_name=asset_name,
            repo_name=repo_name
        )

    def add_asset_params_menu(
        self,
        asset_type=None,
        asset_name=None
    ):
        """Save a set of asset parameters."""

        # Get the list of previously saved paramters for this tool
        saved_params_list = self.wb._list_asset_params(
            asset_type=asset_type,
            name=asset_name
        )

        # Get a new name to use for the params
        name = self.questionary(
            "text",
            "Name for parameters",
            validate=lambda v: v not in saved_params_list and " " not in v
        )

        # Set up this asset
        asset = self.wb.asset(asset_type=asset_type, asset_name=asset_name)

        # Modify the argument configuration slightly, setting
        # each argument as optional (for the purpose of saving params)
        config = {
            kw: {
                k: v if k != 'required' else False
                for k, v in val.items()
            }
            for kw, val in asset.config["args"].items()
        }

        # Create an interactive menu to manipulate this set of parameters
        params_menu = ParamsMenu(
            config=config,
            params=dict(),
            menu=self,
            confirm_text="Finished editing"
        )

        # Prompt the user to modify the parameters as needed
        params_menu.prompt()

        # If the user approved the parameters
        if params_menu.approved:

            # Save the parameters for the asset
            self.wb._write_asset_params_json(
                asset_type=asset_type,
                asset_name=asset_name,
                name=name,
                params=params_menu.params,
                overwrite=True,
            )

    def delete_asset_params_menu(
        self,
        asset_type=None,
        asset_name=None
    ):
        """Delete a set of saved asset parameters."""

        # Get the list of previously saved paramters for this tool
        saved_params_list = self.wb._list_asset_params(
            asset_type=asset_type,
            name=asset_name
        )

        # Pick one to delete
        param_to_delete = self.questionary(
            "select",
            "Select parameters to delete",
            choices=saved_params_list + ["Do not delete any"]
        )

        # If the user decided to delete one of the saved params
        if param_to_delete != "Do not delete any":

            # Confirm that the user wants to make the deletion
            if self.questionary(
                "confirm",
                f"Confirm - remove saved parameter '{param_to_delete}'?"
            ):

                # Delete the saved parameters
                self.wb._delete_asset_params(
                    asset_name=asset_name,
                    asset_type=asset_type,
                    params_name=param_to_delete
                )

                self.print_line(f"Deleted saved parameter '{param_to_delete}'")

    def change_directory_menu(self):
        """Navigate to one of the folders immediately above or below this one."""

        # Get the list of subfolders within this one
        folder_list = [
            fp
            for fp in self.wb.filelib.listdir(".")
            if self.wb.filelib.isdir(fp)
        ]

        # Sort alphabetically
        folder_list.sort()

        # Make options for going up one level or staying put
        parent_option = ".. (move up one level)"
        no_change_option = ". (no change)"

        # Give the user the choice of where to go
        selection = self.questionary(
            "select",
            "Select a folder to navigate to",
            choices=[
                parent_option,
                no_change_option,
            ] + folder_list
        )

        if selection != no_change_option:
            if selection == parent_option:
                dest_path = self.wb.filelib.dirname(self.cwd)
            else:
                dest_path = self.wb.filelib.path_join(self.cwd, selection)

            self.print_line(f"Navigating to {dest_path}")
            self.cwd = dest_path
            self.wb.filelib.chdir(dest_path)

        # Go back to the main menu
        self.main_menu()

    def create_subfolder_menu(self):
        """Create a subfolder inside the current folder."""

        # Get a name for the folder
        folder_name = None

        # The folder path will have spaces replaced with "_"
        folder_path = None

        # Make sure the folder does not collide
        while folder_name is None or self.wb.filelib.exists(folder_path):

            # Get the name
            folder_name = self.questionary(
                "text",
                "Short name (2-5 words):"
            )

            # If the user provided an empty string
            if len(folder_name) == 0:

                # Stop the process
                break

            # Construct the path
            folder_path = folder_name.replace(" ", "_")

            # If a folder like this exists
            if self.wb.filelib.exists(folder_path):

                # Tell the user
                self.print_line(f"Folder already exists ({folder_path})")

        # If the user provided a folder name
        if len(folder_name) > 0:

            # Get a description
            folder_desc = self.questionary(
                "text",
                "Description (can be added/edited later):"
            )

            # Ask the user to confirm their entry
            if self.questionary(
                "confirm",
                f"Confirm - create folder '{folder_name}'?"
            ):

                # Get the absolute path
                folder_path = self.wb.filelib.path_join(self.cwd, folder_path)

                # Create the folder
                self.print_line(f"Creating folder {folder_path}")
                self.wb.filelib.mkdir_p(folder_path)

                # Index it
                self.wb.index_folder(folder_path)

                # Get the Dataset object
                ds = self.wb.datasets.from_path(folder_path)

                # Set the name and description
                self.print_line(f"Adding name {folder_name}")
                ds.set_attribute("name", folder_name)
                self.print_line(f"Adding description {folder_desc}")
                ds.set_attribute("description", folder_desc)

                # Move to the folder
                self.jump_directory(
                    self.wb.filelib.path_join(
                        self.cwd,
                        folder_path
                    )
                )

        self.print_line("Going back to main menu")
        sleep(0.1)

        # Back to the main menu
        self.main_menu()

    def run_tool_menu(self):
        """Run a tool in the current directory."""

        # Make sure that the current directory is indexed
        self.check_indexed_cwd()

        # Set up the tool
        self.setup_tool_menu()

        # Populate the params for the tool
        self.dataset_tool_params_menu()

        # Set up the launcher
        self.setup_launcher_menu()

        # Populate the params for the launcher
        self.dataset_launcher_params_menu()

        # Prompt the user to run the tool now or
        # save it to run later
        response = self.questionary(
            "select",
            "Would you like to run the dataset now?",
            choices = [
                "Run now",
                "Save to run later"
            ]
        )

        # If they want to run the dataset now
        if response == "Run now":

            # Run the dataset
            self.wb.run_dataset(path=self.cwd)

            self.print_line("The dataset has started running!")
            for _ in range(5):
                self.print_line(".")
                sleep(0.1)

            # Tail the logs
            self.tail_logs()

        # Otherwise
        else:

            # Return to the main menu
            self.main_menu()

    def setup_tool_menu(self):
        """Set up a tool for a dataset."""

        self._setup_asset_menu("tool")

    def setup_launcher_menu(self):
        """Set up a launcher for a dataset."""

        self._setup_asset_menu("launcher")

    def _setup_asset_menu(self, asset_type):
        """Set up an asset (tool or launcher)."""

        # Make a Dataset object
        ds = self.wb.dataset(self.cwd)

        # Make sure that the asset type is valid
        ds.validate_asset_type_format(asset_type)

        # If the asset has already been set up
        if ds.__dict__.get(asset_type) is not None:

            # Get the configuration of the asset
            asset_config = ds.__dict__.get(asset_type)

            # The asset must have a 'name'
            msg = f"Asset '{asset_type}' is not configured correctly for {self.cwd}"
            assert asset_config.get("name") is not None, msg

            # Get the asset name
            asset_name = asset_config.get('name')

            # Ask the user if they want to replace this asset
            # or keep it
            self.select_func(
                f"Previously selected {asset_type}:\n  - {asset_name}\n   ",
                [
                    (
                        f"Run previously selected {asset_type}",
                        lambda: self.print_line(f"Running {asset_type} {asset_name}")
                    ),
                    (
                        f"Choose new {asset_type}",
                        lambda: self._choose_asset(asset_type)
                    ),
                    ("Return to main menu", self.main_menu)
                ]
            )

        # If no asset has been set up yet
        else:

            # Drop right into the menu choosing an asset
            self._choose_asset(asset_type)

    def _choose_asset(self, asset_type):
        """Select an asset and set it up for a dataset."""

        # Make a Dataset object
        ds = self.wb.dataset(self.cwd)

        # Make sure that the asset type is valid
        ds.validate_asset_type_format(asset_type)

        # Present the user with a list of assets and get their response
        # If they want to select none, they can use the "Back" option provided
        repo_name, asset_name = self._prompt_user_to_select_asset(asset_type)

        # If the user decided to go back
        if repo_name == "Back" or asset_name == "Back":

            # Go back
            self.main_menu()

        # Otherwise
        else:

            # If the asset has already been set up
            if ds.__dict__.get(asset_type) is not None:

                # Delete the previously set-up asset
                ds.delete_asset_folder(asset_type)

            self.print_line(f"Selected {asset_type} = {repo_name}/{asset_name}")

            # Set up that asset in the folder
            self.wb.repositories[
                repo_name
            ].assets[
                asset_type
            ][
                asset_name
            ].copy_to_dataset(
                ds,
                overwrite=True
            )

            # Set the name of the asset
            ds.set_attribute(asset_type, f"{repo_name}/{asset_name}")

    def dataset_tool_params_menu(self):
        """Populate the params for a tool in a dataset."""

        self._dataset_asset_params_menu("tool")
    
    def dataset_launcher_params_menu(self):
        """Populate the params for a launcher in a dataset."""

        self._dataset_asset_params_menu("launcher")

    def _dataset_asset_params_menu(self, asset_type):
        """Populate the params for an asset in a dataset."""

        # Make a Dataset object
        ds = self.wb.dataset(self.cwd)

        # Get the name of the tool/launcher which has been set up
        asset_name = ds.index.get(asset_type)

        # If an asset has not been set up
        while asset_name is None:

            # Choose one
            self.print_line(f"No {asset_name} has been set up yet")
            self._choose_asset(asset_type)

            # Get the name of the tool/launcher which has now been set up
            asset_name = ds.index.get(asset_type)
        
        # Set up this asset
        asset = self.wb.asset(asset_type=asset_type, asset_name=asset_name)

        # If there are no arguments which need to be set up
        if len(asset.config["args"]) == 0:

            # Then we will write an empty JSON in params.json
            self.wb._set_asset_params(
                self.cwd,
                asset_type,
                overwrite=True
            )

            self.print_line(f"No parameters required for {asset_type} {asset_name}")
            return

        # See if there are any saved parameters available
        saved_params = self.wb._list_asset_params(
            asset_type=asset_type,
            name=asset_name
        )

        # Read in the params which are currently set up for the dataset, if any
        params = ds.read_asset_params(asset_type)

        # Empty params should be set up as an empty dict
        if params is None:
            params = dict()

        # If there are any saved parameters
        if len(saved_params) > 0:

            # Ask the user if they would like to load any of these params
            decline_response = "No thank you"
            selection = self.questionary(
                "select",
                "Would you like to load a set of previously-saved parameters?",
                choices=[decline_response] + saved_params
            )

            # If the user selected one of the saved params
            if selection != decline_response:

                # Read in that set of params
                params = self.wb._read_asset_params(
                    asset_type=asset_type,
                    asset_name=asset_name,
                    params_name=selection
                )

        # Create an interactive menu to manipulate this set of parameters
        params_menu = ParamsMenu(
            config=asset.config["args"],
            params=params,
            menu=self
        )

        # Prompt the user to modify the parameters as needed
        params_menu.prompt()

        # If the user approved the parameters
        if params_menu.approved:

            # Save the parameters for the asset
            self.wb._set_asset_params(
                self.cwd,
                asset_type,
                overwrite=True,
                **params_menu.params
            )

        # Otherwise
        else:

            # Return to the main menu
            self.main_menu()

    def tail_logs(self):
        """Show the user the log file as it is updated"""

        # Get the dataset information
        ds = self.wb.dataset(self.cwd)

        # Set up the text used to prompt the user
        print_logs_prompt = "View more logs"
        exit_logs_prompt = "Return to main menu"

        # Print logs to start
        user_choice = print_logs_prompt

        # Establish a connection to the log file
        with ds.file_watcher("log.txt") as log_file:

            # Until the user decides to return to the main menu
            while user_choice != exit_logs_prompt:

                # Print all of the lines currently written to the log
                log_file.print_all()

                # Refresh the status from the index
                ds.read_index()

                # Get the list of custom actions which may
                # optionally be available
                actions = ds.get_actions()

                # Ask the user what they want to do, while also showing
                # the dataset status
                user_choice = self.questionary(
                    "select",
                    f"Options (status: {ds.index.get('status', 'PENDING')})",
                    choices=[
                        print_logs_prompt,
                        exit_logs_prompt
                    ] + actions
                )

                # Erase the prompt line
                self.erase_lines(3)
                # If the user selected an action
                if user_choice in actions:

                    # Run the action
                    ds.run_action(user_choice)

        # When all done, return to the main menu
        self.main_menu()

    def erase_lines(self, n_lines:int):
        """Erase a number of lines from the display"""

        assert isinstance(n_lines, int)
        assert n_lines > 0

        # Erase the current line
        sys.stdout.write('\033[2K\033[1G')

        # For each additional line
        if n_lines > 1:
            for _ in range(n_lines - 1):
                # Go up a line
                sys.stdout.write("\033[F")
                # Erase that line
                sys.stdout.write('\033[2K\033[1G')

    def jump_directory_menu(self, sep=" : "):
        """Select an indexed directory and navigate to it."""

        # Get a path which passes the current filter
        resp = self.questionary(
            "autocomplete",
            "Start typing the name of a dataset, or press tab to see a list of options",
            choices=self.wb.datasets.filtered_paths(sep=sep),
            complete_style="COLUMN"
        )

        # The path of the selected dataset is the final entry
        path = resp.rsplit(sep, 1)[-1]

        self.print_line(f"Moving to dataset {path}")

        # Move to that directory
        self.jump_directory(path)

    def import_folder(self):
        """Import a folder from the filesystem."""

        # Prompt for the folder to add
        folder_to_import = self.questionary(
            "path",
            "Select a folder to be added to your workbench",
            complete_style="READLINE_LIKE",
            only_directories=True
        )

        # If the user selected the home directory with a tilde
        if folder_to_import.startswith("~"):

            # Replace the tilde with the home directory
            folder_to_import = f"{self.wb.filelib.home()}{folder_to_import[1:]}"

        # Try to add the folder
        try:
            self.wb.index_folder(folder_to_import)
        except Exception as e:
            self.print_line(
                f"Folder could not be added: {str(e)}"
            )
            # Back to the main menu
            self.main_menu()
            return

        # Report success
        self.print_line(f"Imported folder {folder_to_import}")

        # Back to the Explore Datasets menu
        self.explore_datasets_menu()
    
    def manage_repositories_menu(self):
        """Manage the repositories available"""

        # Populate a list of options
        options = [
            ("Download New Repository", self.download_repo),
            ("Link Local Repository", self.link_repo),
            ("Back to Main Menu", self.main_menu)
        ]

        # Make a dict of functions
        func_map = dict()

        # Make a list of choices to present
        choices = list()

        # Populate the dictionary and the list
        for name, f in options:
            func_map[name] = f
            choices.append(name)

        # Add options to modify each of the downloaded and linked repositories

        # Get the list of repositories which have been downloaded
        local_repos = self.wb.list_repos()

        # Sort the list
        local_repos.sort()

        # Add an option for each of the downloaded repositories
        for repo in local_repos:
            choices.append(f"Manage repository: {repo}")

        # Ask the user
        choice = self.questionary(
            "select",
            "Manage Repositories",
            choices=choices
        )

        # If the user decided to manage a repository
        if choice.startswith("Manage repository: "):

            # Get the repository name
            repo = choice[len("Manage repository: "):]

            # Launch the menu for managing that repository
            self.manage_repo(repo)

        # If the user selected something else
        else:

            # Make sure that we know what function to run
            assert choice in func_map, f"Cannot map selection ({choices}) to options ({', '.join(list(func_map.keys()))})"

            # Open that menu
            func_map[choice]()

    def download_repo(self):
        """Download a GitHub repository."""

        # Get the name of the repository to download
        repo_name = self.questionary("text", "Repository name")

        # If the user entered an empty string, or one without a '/' in the middle
        if len(repo_name) < 3 or "/" not in repo_name or len(repo_name.split("/")) != 2:

            # Tell the user that the repository is not valid
            self.print_line(f"Repository name not valid: '{repo_name}'")

        # If the repository name is plausible
        else:

            # Make sure that the user has checked the spelling and trusts
            # the content of this repository
            prompt = textwrap.dedent(f"""
            Do you trust the code in this repository?
            
            Make sure that the spelling of the repository is correct: {repo_name}

            Press <ENTER> or Y to confirm download.""")

            # If the user is not sure
            if not self.questionary("confirm", prompt):

                # Go back to the repository menu
                self.manage_repositories_menu()

            # Try to download it
            try:
                self.wb.add_repo(repo_name)
            except Exception as e:
                self.print_line(f"ERROR: {str(e)}")

            # Update the list of Repositories which are available
            self.wb.repositories = self.wb.setup_repositories()

        # Back to the repository menu
        self.manage_repositories_menu()

    def link_repo(self):
        """Link a local a GitHub repository."""

        # Get the folder containing the repository to link
        repo_fp = self.questionary(
            "path",
            "Repository location",
            only_directories=True
        )

        # If the user selected the home folder
        if repo_fp.startswith("~"):

            # Replace it with the complete home folder
            repo_fp = repo_fp.replace("~", self.wb.filelib.home())

        # Make sure that the path is valid
        is_valid = True

        if len(repo_fp) == 0:
            self.print_line("No entry made")
            is_valid = False

        elif not self.wb.filelib.exists(repo_fp):
            self.print_line("Path is not valid")
            is_valid = False

        # If the path is valid, and the user is sure
        if is_valid and self.questionary(
            "confirm",
            f"Confirm - link local repository: {repo_fp}"
        ):

            # Try to link it
            try:
                self.wb.link_local_repo(
                    path=repo_fp,
                    name=repo_fp.rstrip("/").rsplit("/", 1)[-1]
                )
            except Exception as e:
                self.print_line(f"ERROR: {str(e)}")

            # Update the list of Repositories which are available
            self.wb.repositories = self.wb.setup_repositories()

        # Back to the repository menu
        self.manage_repositories_menu()

    def manage_repo(self, repo_name):
        """Manage a downloaded repository."""

        # Print the version of the local repository
        if self.wb.repositories[repo_name].repo is not None:
            self.print_repo_version(repo_name)

        # Ask the user what to do
        self.select_func(
            f"Local copy of downloaded repository: {repo_name}",
            [
                ("Update to latest version", lambda: self.update_local_repo(repo_name)),
                ("Switch branch", lambda: self.local_repo_switch_branch(repo_name)),
                ("Remove repository", lambda: self.remove_repo(repo_name)),
                ("Back", self.manage_repositories_menu)
            ]
        )

    def print_repo_version(self, repo_name:str) -> None:
        """Print the version of a repo."""
        hexsha = self.wb.repositories[repo_name].repo.head.object.hexsha
        self.print_line(f"Branch name: {self.wb.repositories[repo_name].repo.head.name}")
        committed_date = strftime("%a, %d %b %Y %H:%M", gmtime(self.wb.repositories[repo_name].repo.head.object.committed_date))
        self.print_line(f"Commit date: {committed_date}")
        self.print_line(f"Commit hash: {hexsha}")

    def update_local_repo(self, repo_name):
        """Update a local repository to the most recent version."""

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - update local copy of repository {repo_name}"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to update the repository
        try:
            self.wb.update_repo(name=repo_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

        # Update the list of Repositories which are available
        self.wb.repositories = self.wb.setup_repositories()

        # Print the updated repo version
        self.print_repo_version(repo_name)

        # Go back to the repository menu
        self.manage_repositories_menu()

    def remove_repo(self, repo_name):
        """Delete the local copy of a downloaded repository."""

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - remove repository {repo_name}"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to delete the repository
        try:
            self.wb.delete_repo(name=repo_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

        # Update the list of Repositories which are available
        self.wb.repositories = self.wb.setup_repositories()

        # Go back to the repository menu
        self.manage_repositories_menu()

    def local_repo_switch_branch(self, repo_name):
        """Switch the branch of a local repository."""

        # Get the name of the branch to switch to
        branch_name = self.questionary("text", "Name of branch")

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - switch repository {repo_name} to branch {branch_name}"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to update the repository
        try:
            self.wb.switch_branch(name=repo_name, branch=branch_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

        # Update the list of Repositories which are available
        self.wb.repositories = self.wb.setup_repositories()

        # Print the updated repo version
        self.print_repo_version(repo_name)

        # Go back to the repository menu
        self.manage_repositories_menu()

    def index_folder(self, path):
        """Add an index to a folder."""

        # Create an index
        ix = self.wb.index_folder(path)

        # Show the user the index information
        for key, val in ix.items():

            self.print_line(f"{key}: {val}")

    def exit(self):
        """Exit the interactive display."""

        self.print_line(
            "Closing the BASH Workbench -- restart at any time with: wb" + \
                "\n" + \
                    self.wb.filelib.navigate_text(self.cwd)
        )
        sys.exit(0)

    def print_filters(self):
        """Print the number of datasets and any filters which have been applied."""

        self.print_line(f"Total datasets: {len(self.wb.datasets.datasets):,}")

        # Print:
        #   Any filters which have been applied
        if len(self.wb.datasets.filters) > 0:

            self.print_header("Dataset Filters")

            for filter_item in self.wb.datasets.filters:
                self.print_line(": ".join(filter_item), indent=1)

            # Print:
            #   The number of datasets which pass these filters
            print(f"Filtered datasets: {self.wb.datasets.filtered_len():,}")

    def add_remove_filters(self):
        """Menu to add or remove filters to the set of displayed datasets."""

        # Print:
        #   Dataset tree beneath the cwd
        print(self.wb.datasets.format_dataset_tree())

        # Print the number of datasets and any filters which have been applied
        self.print_filters()

        # Make a list of options
        options = [("Add filter", self.add_filter)]

        # If there are any filters
        if len(self.wb.datasets.filters) > 0:
            options.append(("Remove filter", self.remove_filter))

        # Always let the user go back without taking an action
        options.append(("Back to main menu", self.main_menu))

        # Present the menu
        self.select_func(
            "Add or remove a filter on the displayed datasets",
            options
        )

    def remove_filter(self):
        """Remove one of the filters applied to the datasets."""

        # If there are filters to remove
        if len(self.wb.datasets.filters) > 0:

            # Pick a filter to remove
            resp = self.questionary(
                "select",
                "Select a filter to remove",
                choices=[
                    f"{field}: {value}"
                    for field, value in self.wb.datasets.filters
                ]
            )

            [field, value] = resp.split(": ", 1)

            self.print_line(f"Removing filter {resp}")
            self.wb.datasets.remove_filter(field=field, value=value)

        # Go back to the previous menu
        self.add_remove_filters()

    def add_filter(self):
        """Add a filter to the set of displayed dadtasets."""

        # Pick a field of the dataset to filter by
        field = self.questionary(
            "select",
            "Filter type",
            choices=[
                "name",
                "description",
                "tag",
            ]
        )

        value = None

        # Make sure that any entries for tags have the = delimiter
        while value is None or (field == "tag" and "=" not in value):

            # If the user selected a tag and they did not provide the format "key=value"
            if value is not None:
                self.print_line("To filter by tag, you must use the format: key=value")

            # Get the filter value
            value = self.questionary(
                "text",
                dict(
                    name="Only show datasets with names that contain the string (case sensitive):",
                    description="Only show datasets with descriptions that contain the string:",
                    tag="Only show datasets which have the tag (key=value):"
                )[field]
            )

        # Add the filter
        self.wb.datasets.add_filter(field=field, value=value)

        # Back to the previous menu
        self.add_remove_filters()

    def refresh(self):
        """Refresh the status of the current dataset."""

        # Re-read the index
        self.wb.dataset(self.cwd).read_index()

        # Go back to the main menu
        self.main_menu()
