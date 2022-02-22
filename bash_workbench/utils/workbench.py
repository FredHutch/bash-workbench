import bash_workbench as wb
import datetime
import os

class Workbench:
    """Object used to organize BASH Workbench attributes and methods."""

    def __init__(
        self,
        # By default, the base folder is in the home directory
        base_folder=os.path.join(os.path.expanduser("~"), "._workbench"),
        # Default profile name
        profile="default",
        # Parameter used to specify the filesystem being used,
        filesystem="local",
        # Optionally specify a logger instance
        logger=None,
        # Optionally print messages to the screen
        verbose=False
    ):

        assert base_folder is not None, "Must provide base_folder"
        assert profile is not None, "Must provide profile"

        # The home folder for the workbench is <base_folder>/<profile>/
        self.home_folder = os.path.join(base_folder, profile)
        self.base_folder = base_folder
        self.profile = profile
        self.filesystem = filesystem
        self.logger = logger
        self.verbose = verbose
        self.timestamp = Timestamp()

    def log(self, msg):
        """Print a logging message using the logger if available, and the screen if `verbose`."""

        if self.logger is not None:
            self.logger.info(msg)

        if self.verbose:
            print(msg)

    def _run_function(self, func, **kwargs):
        """Execute a function with the specified name, using the appropriate filesystem."""
    
        # The function to run will be determined by the --filesystem
        # as well as the subcommand. The pattern used to map the CLI
        # command to the exact function in the library is:
        # wb.utils.filesystem.<filesystem>.<subcommand>

        # First get the module used for this filesystem
        filesystem_lib = wb.utils.filesystem.__dict__.get(self.filesystem)

        assert filesystem_lib is not None, f"Cannot find filesystem module {self.filesystem}"

        # Next, get the function defined in that module
        func = filesystem_lib.__dict__.get(func)

        assert func is not None, f"Cannot find function {self.func} for filesystem {self.filesystem}"

        self.log(kwargs)

        # Run the function which was selected by the user
        return func(
            # Every function takes a Workbench instance
            self,
            # Pass through all of the command line argument
            **kwargs
        )

    def setup_root_folder(self, **kwargs):
        """Ensure that the root folder contains the required assets, and create them if necessary."""

        return self._run_function("setup_root_folder", **kwargs)

    def index_collection(self, **kwargs):
        "Add a collection index to a folder in the filesystem."

        return self._run_function("index_collection", **kwargs)

    def index_dataset(self, **kwargs):
        "Add a dataset index to a folder in the filesystem."

        return self._run_function("index_dataset", **kwargs)

    def show_datasets(self, **kwargs):
        "Print a list of all datasets linked from the home folder."

        return self._run_function("show_datasets", **kwargs)

    def change_name(self, **kwargs):
        "Modify the name of a folder (dataset or collection)."

        return self._run_function("change_name", **kwargs)

    def change_description(self, **kwargs):
        "Modify the description of a folder (dataset or collection)."

        return self._run_function("change_description", **kwargs)

    def update_tag(self, **kwargs):
        "Modify the value of a tag applied to a folder."

        return self._run_function("update_tag", **kwargs)

    def delete_tag(self, **kwargs):
        "Delete the value of a tag applied to a folder, if it exists."

        return self._run_function("delete_tag", **kwargs)

    def find_datasets(self, **kwargs):
        "Find any datasets which match the provided queries."

        return self._run_function("find_datasets", **kwargs)

    def _top_level_folder(self, folder_name):
        """Return the path to a top-level folder in the home directory."""

        return os.path.join(self.home_folder, folder_name)

    def update_base_toolkit(self, **kwargs):
        """Copy the tools and launchers from the package into the home directory"""

        return self._run_function("update_base_toolkit", **kwargs)


class Timestamp():
    """Encode / decode a date and time to / from string format."""

    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %Z"):
        
        self.fmt = fmt

    def encode(self):
        """Return a string representation of the current date and time."""

        # Current date and time
        now = datetime.datetime.now(datetime.timezone.utc)

        # Return a string formatted using the pattern shown above
        return now.strftime(self.fmt)

    def decode(self, timestamp_str):
        """Return the date and time represented by a string."""

        return datetime.strptime(timestamp_str, self.fmt)