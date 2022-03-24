# Import the Workbench class to specify input type
from cgitb import text
from .workbench import Workbench
from .dataset import Dataset
from .asset import Asset
from .utils import convert_size
from .params_menu import ParamsMenu
import questionary
import sys
import textwrap
import bash_workbench

class WorkbenchMenu:

    def __init__(self, WB:Workbench):
        """Launch an interactive menu for the BASH Workbench"""

        # Attach the workbench which has been provided
        self.wb = WB

        # Define a spacer which will indent text
        self.spacer = "    "

        # Parse all of the datasets available from the home directory
        self.wb.update_datasets()

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

    def questionary(self, fname, msg, **kwargs):
        """Wrap questionary functions to catch escapes and exit gracefully."""

        # Get the questionary function
        questionary_f = questionary.__dict__.get(fname)

        # Make sure that the function exists
        assert questionary_f is not None, f"No such questionary function: {fname}"

        if fname == "select":
            kwargs["use_shortcuts"] = True

        # Add a spacer line before asking the question
        print("")

        # Get the response
        resp = questionary_f(msg, **kwargs).ask()

        # If the user escaped the question
        if resp is None:
            self.exit()

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
        if self.cwd == self.wb.home_folder:

            # It does not need to be indexed
            return

        # Try to read an index for the cwd, if one exists
        ds = Dataset(self.cwd)

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
                    ("Browse all datasets", self.browse_home),
                    ("Exit", self.exit)
                ]
            )

    def main_menu(self):
        """Show the main menu"""

        # Print a header
        self.print_header("BASH Workbench")

        # Check to see if the cwd if indexed
        #   If not, ask if the user wants to index the folder,
        #   move to the root folder, or quit
        self.check_indexed_cwd()

        # If this is not the home directory
        if self.cwd != self.wb._top_level_folder("data"):

            # Get the dataset information
            ds = Dataset(self.cwd)

            # Show the name as a header
            self.print_header(f"Dataset: {ds.index.get('name', self.cwd)}")

            # Print:
            #   description, tags of cwd, etc.
            for key, val in ds.index.items():
                if key != "name":
                    self.print_line(f"{key}: {val}", indent=1)

            # Print the directory
            self.print_line(f"path: {self.cwd}", indent=1)

        else:

            self.print_header("Home")

        # Add a spacer line
        print("\n")

        # Select a submenu
        # The user selection will run a function
        self.select_func(
            """Would you like to:""",
            [
                ("Run Tool", self.run_tool_menu),
                ("Edit Dataset", self.modify_dataset_menu),
                ("Explore Datasets", self.explore_datasets_menu),
                ("Browse Tools", self.browse_tool_menu),
                ("Manage Repositories", self.manage_repositories_menu),
                ("Return to Shell", self.exit)
            ]
        )

    def modify_dataset_menu(self):
        """Menu options for modifying the current working directory."""
        
        self.select_func(
            """Would you like to:""",
            [
                ("Create Subfolder", self.create_subfolder_menu),
                ("Edit Name/Description", self.edit_name_description),
                ("List Files", self.list_files),
                ("Back to Main Menu", self.main_menu)
            ]
        )

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

        self.select_func(
            """Would you like to:""",
            [
                ("List All Datasets", self.list_all_datasets),
                ("Add/Remove Dataset Filters", self.add_remove_filters),
                ("Import Existing Dataset", self.import_folder),
                ("Change Directory", self.change_directory_menu),
                ("Back to Main Menu", self.main_menu)
            ]
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
        ds = Dataset(self.cwd)

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

    def change_directory(self, path):
        """Change the working directory and return to the main menu."""

        # Change the working directory
        self.print_line(f"Navigating to {path}")
        self.cwd = path
        self.wb.filelib.chdir(path)

        # Go back to the main menu
        self.main_menu()

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
                    f"{fn}/ (contains {n:,} items)"
                )

            # If the path is a file
            else:

                # Get the size of the file (in bytes)
                filesize = self.wb.filelib.getsize(fp)

                # Report the filesize, formatted nicely
                files.append(
                    f"{fn} {convert_size(filesize)}"
                )

        if len(files) + len(folders) == 0:
            self.print_line(f"No files or folders found in {self.cwd}")

        else:

            self.print_line(f"Files/folders in {self.cwd}:")
            for folder_str in folders:
                self.print_line(folder_str)
            for file_str in files:
                self.print_line(file_str)

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

    def _browse_asset_menu(self, asset_type):
        """Show the user the set of assets which are available."""

        # Make a list of the assets of this type which are available
        asset_dict = {
            asset_name: Asset(WB=self.wb, asset_type=asset_type, asset_name=asset_name)
            for asset_name in self.wb._list_assets(asset_type)
        }

        # Format a list of strings using the key, name, and description
        choices = [
            f"{asset_name}: {asset.config['name']}\n{asset.config['description']}"
            for asset_name, asset in asset_dict.items()
        ]

        # Sort the list alphabetically

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

            # Construct the path
            folder_path = folder_name.replace(" ", "_")

            # If a folder like this exists
            if self.wb.filelib.exists(folder_path):

                # Tell the user
                self.print_line(f"Folder already exists ({folder_path})")

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

            # Create the folder
            self.print_line(f"Creating folder {folder_path}")
            self.wb.filelib.mkdir_p(folder_path)

            # Index it
            ds = Dataset(folder_path)
            ds.create_index()

            # Set the name and description
            self.print_line(f"Adding name {folder_name}")
            ds.set_attribute("name", folder_name)
            self.print_line(f"Adding description {folder_desc}")
            ds.set_attribute("description", folder_desc)

            # Update the indexed datasets
            self.print_line("Updating list of datasets")
            self.wb.update_datasets()

            # Move to the folder
            self.change_directory(
                self.wb.filelib.path_join(
                    self.cwd,
                    folder_path
                )
            )

        else:
            self.print_line("Going back to main menu")

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
        ds = Dataset(self.cwd)

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
                f"Previously selected {asset_type}: {asset_name}",
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
        ds = Dataset(self.cwd)

        # Make sure that the asset type is valid
        ds.validate_asset_type_format(asset_type)

        # Make a list of the assets of this type which are available
        asset_dict = {
            asset_name: Asset(WB=self.wb, asset_type=asset_type, asset_name=asset_name)
            for asset_name in self.wb._list_assets(asset_type)
        }

        # Format a list of strings using the key and name
        choices = [
            f"{asset_name}: {asset.config['name']}"
            for asset_name, asset in asset_dict.items()
        ]

        # Also give the user an opportunity to bail
        choices = choices + ["Back to main menu"]

        # At this point, the user must select an {asset_type} to run
        selected_asset = self.questionary(
            "select",
            f"Select {asset_type}",
            choices=choices
        )

        # If the user bailed
        if selected_asset == "Back to main menu":

            # Go back to the main menu
            self.main_menu()

        # Otherwise
        else:

            # If the asset has already been set up
            if ds.__dict__.get(asset_type) is not None:

                # Delete the previously set-up asset
                ds.delete_asset_folder(asset_type)

            self.print_line(f"Selected {asset_type} = {selected_asset}")

            # Remove the description
            selected_asset = selected_asset.split(": ", 1)[0]

            # Set up that asset in the folder
            asset_dict[selected_asset].copy_to_dataset(ds, overwrite=True)

            # Set the name of the asset
            ds.set_attribute(asset_type, selected_asset)

    def dataset_tool_params_menu(self):
        """Populate the params for a tool in a dataset."""

        self._dataset_asset_params_menu("tool")
    
    def dataset_launcher_params_menu(self):
        """Populate the params for a launcher in a dataset."""

        self._dataset_asset_params_menu("launcher")

    def _dataset_asset_params_menu(self, asset_type):
        """Populate the params for an asset in a dataset."""

        # Make a Dataset object
        ds = Dataset(self.cwd)

        # Get the name of the tool/launcher which has been set up
        asset_name = ds.index.get(asset_type)

        # If an asset has not been set up
        if asset_name is None:

            # Choose one
            self.print_line(f"No {asset_name} has been set up yet")
            self._choose_asset(asset_type)
        
        # If an asset has been set up

        # Get the configuration for this asset
        asset_config = Asset(
            WB=self.wb,
            asset_type=asset_type,
            asset_name=asset_name
        ).config

        # If there are no arguments which need to be set up
        if len(asset_config["args"]) == 0:

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
            config=asset_config["args"],
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

    def change_directory_menu(self, sep=" : "):
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
        self.change_directory(
            self.wb.filelib.path_join(
                self.wb.home_folder,
                "data",
                path
            )
        )

    def import_folder(self):
        """Import a folder from the filesystem."""

        # Prompt for the folder to add
        folder_to_import = self.questionary(
            "path",
            "Select a folder to be added to your workbench",
            complete_style="READLINE_LIKE",
            only_directories=True
        )

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

        # Back to the main menu
        self.main_menu()
    
    def manage_repositories_menu(self):
        """Manage the repositories available"""

        # Populate a list of options
        options = [
            ("Download New Repository", self.download_repo),
            ("Link Local Repository", self.link_repo),
            ("Back to Main Menu", self.main_menu)
        ]

        # Add options to modify each of the downloaded and linked repositories

        # Get the list of repositories which have been downloaded
        local_repos = self.wb.list_repos()

        # Add an option for each of the downloaded repositories
        for repo in local_repos:
            options.append(
                (
                    f"Manage downloaded repository {repo}",
                    lambda: self.manage_downloaded_repo(repo)
                )
            )

        # Get the list of repositories which have been linked
        linked_repos = self.wb.list_linked_repos()

        # Add an option for each of the linked repositories
        for repo in linked_repos:
            options.append(
                (
                    f"Manage linked repository {repo}",
                    lambda: self.manage_linked_repo(repo)
                )
            )

        # Ask the user what to do
        self.select_func(
            "Manage Repositories",
            options
        )

    def download_repo(self):
        """Download a GitHub repository."""

        # Get the name of the repository to download
        repo_name = self.questionary("text", "Repository name")

        # If the user is not sure
        if not self.questionary("confirm", f"Confirm - download repository {repo_name}"):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to download it
        try:
            self.wb.add_repo(repo_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

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

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - link local repository {repo_fp}"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to link it
        try:
            self.wb.link_local_repo(
                path=repo_fp,
                name=repo_fp.rstrip("/").rsplit("/", 1)[-1]
            )
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

        # Back to the repository menu
        self.manage_repositories_menu()

    def manage_downloaded_repo(self, repo_name):
        """Manage a downloaded repository."""

        # Ask the user what to do
        self.select_func(
            f"Local copy of downloaded repository: {repo_name}",
            choices=[
                ("Update to latest version", lambda: self.update_local_repo(repo_name)),
                ("Switch branch", self.local_repo_switch_branch(repo_name)),
                ("Delete local copy", self.delete_local_repo(repo_name)),
                ("Back", self.manage_repositories_menu)
            ]
        )

    def manage_linked_repo(self, repo_name):
        """Manage a linked repository."""

        # Get the path which is linked
        linked_path = self.wb.filelib.abs_path(
            self.wb._top_level_file(
                folder_name="linked_repositories",
                file_name=repo_name
            )
        )

        # Ask the user what to do
        self.select_func(
            f"Linked repository: {repo_name} -> {linked_path}",
            [
                ("Remove link", lambda: self.unlink_repo(repo_name)),
                ("Back", self.manage_repositories_menu)
            ]
        )

    def unlink_repo(self, repo_name):
        """Remove a link to a local repository."""

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - remove link to repository '{repo_name}'"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to unlink the repository
        try:
            self.wb.unlink_local_repo(name=repo_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

        # Go back to the repository menu
        self.manage_repositories_menu()

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

        # Go back to the repository menu
        self.manage_repositories_menu()

    def delete_local_repo(self, repo_name):
        """Delete the local copy of a downloaded repository."""

        # If the user is not sure
        if not self.questionary(
            "confirm",
            f"Confirm - delete local copy of repository {repo_name}"
        ):

            # Go back to the repository menu
            self.manage_repositories_menu()

        # Try to delete the repository
        try:
            self.wb.delete_repo(name=repo_name)
        except Exception as e:
            self.print_line(f"ERROR: {str(e)}")

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

        # Go back to the repository menu
        self.manage_repositories_menu()

    def index_folder(self, path):
        """Add an index to a folder."""

        # Create an index
        ix = self.wb.index_folder(path)

        # Show the user the index information
        for key, val in ix.items():

            self.print_line(f"{key}: {val}")

    def browse_home(self):
        """Navigate to the top-level home directory."""

        # Directory containing all datasets
        data_dir = self.wb._top_level_folder("data")

        self.print_line(f"Changing working directory to {data_dir}")

        # Change the working directory
        self.cwd = data_dir

        # Go back to the main menu
        self.main_menu()

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
