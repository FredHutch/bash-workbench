import bash_workbench as wb
from bash_workbench.utils.asset import Asset
from bash_workbench.utils.dataset import Dataset
from bash_workbench.utils.repository import Repository
from bash_workbench.utils.datasets import Datasets
from importlib_resources import files

class Workbench:
    """Object used to organize BASH Workbench attributes and methods."""

    def __init__(
        self,
        # By default, the base folder is in the home directory
        base_folder=None,
        # Default profile name
        profile="default",
        # Parameter used to specify the filesystem being used,
        filesystem="local",
        # Optionally specify a logger instance
        logger=None,
        # Optionally print messages to the screen
        verbose=False
    ):

        # Attach the module used for this filesystem
        self.filelib = wb.utils.filesystem.__dict__.get(filesystem)

        assert self.filelib is not None, f"Cannot find filesystem module {self.filesystem}"

        # If the base_folder field was not provided
        if base_folder is None:

            # Set the location as ~/.workbench/
            base_folder = self.filelib.path_join(self.filelib.home(), "._workbench")
        
        assert profile is not None, "Must provide profile"

        # Attach the init variables to the object
        self.profile = profile
        self.filesystem = filesystem
        self.logger = logger
        self.verbose = verbose
        self.timestamp = wb.utils.timestamp.Timestamp()

        # The home folder for the workbench is <base_folder>/<profile>/
        self.home_folder = self.filelib.path_join(base_folder, profile)

        # If the root folder does not exist
        if not self.filelib.exists(self.home_folder):

            # Create it
            self.filelib.makedirs(self.home_folder)
            self.log(f"Created {self.home_folder}")
        
        else:

            self.log(f"Exists {self.home_folder}")

        # Resolve the absolute path
        self.home_folder = self.filelib.abs_path(self.home_folder)

        # Get the folder which contains assets installed with this package
        self.assets_folder = files("bash_workbench").joinpath('assets')

    def log(self, msg):
        """Print a logging message using the logger if available, and the screen if `verbose`."""

        if self.logger is not None:
            self.logger.info(msg)

        if self.verbose:
            print(msg)

    def _run_function(self, func, **kwargs):
        """Execute a function with the specified name."""
    
        # Next, get the class function accessed by function name
        f = getattr(self, func)

        assert f is not None, f"Cannot find function {func} for object Workbench"

        # Run the function which was selected by the user
        return f(
            # Pass through all of the command line argument
            **kwargs
        )

    def setup_root_folder(self):
        """Ensure that the root folder contains the required assets, and create them if necessary."""

        self.log(f"Setting up root folder at {self.home_folder}")

        # For each of a series of subfolders
        for subfolder in [
            "data",
            "launcher",
            "tool",
            "helper",
            "repositories",
            "linked_repositories",
            "params"
        ]:

            # Construct the path for this subfolder inside the root folder
            fp = self._top_level_folder(subfolder)

            # If the path does not exist
            if not self.filelib.exists(fp):

                # Create it
                self.filelib.makedirs(fp)
                self.log(f"Created {fp}")

            else:
                self.log(f"Exists: {fp}")

        # Add an index to the root data folder
        self.index_folder(self._top_level_folder("data"))
        self.change_name(
            path=self._top_level_folder("data"),
            name="Datasets"
        )
        self.change_description(
            path=self._top_level_folder("data"),
            description="Collection of all datasets indexed in the workbench"
        )

        # Provide each of the tools and launchers defined in the repository,
        # if they do not already exist
        self.update_base_toolkit(overwrite=False)

    def index_folder(self, path:str=None):

        assert path is not None, "Must provide --path for folder to index"

        self.log(f"Preparing to index folder: {path}")

        # Create a Dataset object
        ds = Dataset(path, filesystem=self.filesystem)

        # Create the index
        ds.create_index()

        # Finally, link this dataset to the home folder if it is not already
        # nested below a collection which is similarly linked
        self.add_to_home_tree(path)

        return ds.index

    def add_to_home_tree(self, path):
        """If a folder is not already contained in the home tree, add it."""

        # Resolve symlinks and remove any terminal slashes
        path = self.filelib.abs_path(path)

        # If the path _is_ the home dataset directory
        if path == self.filelib.abs_path(self._top_level_folder("data")):

            # Do not take any further action
            # (prevent the creation of a circular link)
            return

        self.log(f"Making sure that folder is present in home tree: {path}")

        # Keep track of whether we've seen this path
        path_seen = False

        # Iterate over each of the datasets/collections in the home tree
        for ds in self.walk_home_tree():

            # If we come across this folder
            if ds.path == path:

                # Mark this path as seen
                path_seen = True

                # Break the loop
                break

        # If the path was found
        if path_seen:

            self.log(f"Path already contained in home tree ({path})")

        # If it was not found
        else:

            # Link the folder to the home directory
            self.link_to_home(path)

            self.log(f"Link for path added to home tree ({path})")

    def walk_home_tree(self):
        """Walk through all of the indexed folders which are linked anywhere within the home folder."""

        # Keep track of all of the folders which we've found before
        seen_folders = set()

        # Keep a list of folders that we need to walk through
        folders_to_check = list()

        # To start, add the home folder to the list of folders to check
        folders_to_check.append(self._top_level_folder("data"))

        # Iterate while there are folders remaining to check
        while len(folders_to_check) > 0:

            # Get a folder to check, removing it from the list
            folder_to_check = folders_to_check.pop()

            # Iterate over each path within it
            for subpath in self.filelib.listdir(folder_to_check):

                # Construct the full path
                subpath = self.filelib.abs_path(
                    self.filelib.path_join(folder_to_check, subpath)
                )

                # If the path is not a directory
                if not self.filelib.isdir(subpath):

                    # Skip it
                    continue

                # Attempt to make a Dataset object
                ds = Dataset(subpath)

                # If the folder is a dataset or collection
                if ds.index is not None:

                    # If we've already seen it, there is some circular link which
                    # must be resolved by the user
                    msg = f"Encountered circular link: user must resolve (re: {subpath})"
                    assert subpath not in seen_folders, msg

                    # Add the subpath to the set of seen folders
                    seen_folders.add(subpath)

                    # Emit this Dataset
                    yield ds

                    # Add the subpath to the list of paths to check next
                    folders_to_check.append(subpath)

    def link_to_home(self, path):
        """Add a symlinnk of a path to the home directory."""

        # If there is a link to this folder already in the home directory
        if path in self.links_from_home_directory():

            # No need to take any further action
            return

        # Get the folder name
        folder_name = path.rsplit("/", 1)[1]

        # Get the path to the symlink
        home_symlink = self._top_level_folder(f"data/{folder_name}")

        # To prevent collisions, add a suffix to make it unique (if not already)
        n = 0
        while self.filelib.exists(home_symlink):

            # Increment the counter to make a new suffix
            n += 1

            # Make a new the path to the symlink
            home_symlink = self._top_level_folder(f"data/{folder_name}_{n}")

        # Add a symlink
        self.filelib.symlink(path, home_symlink)

    def links_from_home_directory(self):
        """Return the list of folders which are linked from the home data directory."""

        # Assemble the path to the home data directory
        data_home = self._top_level_folder("data")

        # Make a list of the linked folders
        linked_folders = list()

        # Iterate over the files in this folder
        for fp in self.filelib.listdir(data_home):

            # Construct the full path to each file
            fp = self.filelib.path_join(data_home, fp)

            # If the file is a symlink
            if self.filelib.islink(fp):

                # Add the target to the list
                linked_folders.append(self.filelib.abs_path(fp))

        # Return the list of all folders which are linked
        return linked_folders

    def update_datasets(self):
        """Parse all of the datasets available from the home directory."""

        # Instantiate a collection of Datasets
        self.datasets = Datasets()

        # Iterate over all of the datasets and collections linked to the home folder
        for ds in self.walk_home_tree():

            # Add the dataset to the collection
            self.datasets.add(ds)

    def list_datasets(self):
        """Return a list of all datasets linked from the home folder."""

        # Parse all of the datasets available from the home directory
        self.update_datasets()

        # Return the simple dict of all datasets
        return self.datasets.datasets

    def find_datasets(
        self,
        name=None,
        description=None,
        tag=None
    ):
        """Find any datasets which match the provided queries."""

        # Parse all of the datasets available from the home directory
        self.update_datasets()

        # Filter the datasets based on the name, description, and/or tag filters provided
        self.filter_datasets(
            name=name,
            description=description,
            tag=tag
        )

        # Extract the dict of datasets which pass all of these filters, including
        # the parent folders all the way back to the root
        # Note that this will return a simple dict
        datasets = self.datasets.filtered()

        self.log(f"Number of datasets matching query: {len(datasets):,}")

        # Return the dict of datasets found
        return datasets

    def filter_datasets(self, name=None, description=None, tag=None):
        """Apply one or more filters to the datasets in the workbench."""

        # If a query name was provided
        if name is not None:

            # If the name is provided as a list, collapse it into a string
            if isinstance(name, list):
                name = " ".join(name)

            self.log(f"Querying datasets by name={name}")

            # Apply the filter
            self.datasets.add_filter(field="name", value=name)

        # If a query description was provided
        if description is not None:

            # If the description is provided as a list, collapse it into a string
            if isinstance(description, list):
                description = " ".join(description)

            self.log(f"Querying datasets by description={description}")

            # Apply the filter
            self.datasets.add_filter(field="description", value=description)

        # If a query tag was provided
        if tag is not None:

            # If the tag is not a list, make a list of 1
            if not isinstance(tag, list):
                tag = [tag]

            # Iterate over the multiple tags which may have been provided
            for tag_item in tag:

                self.log(f"Querying datasets by tag {tag_item}")

                # Apply the filter
                self.datasets.add_filter(field="tag", value=tag_item)

    def tree(
        self,
        name=None,
        description=None,
        tag=None,
    ):
        """
        Return the list of datasets formatted as a tree.
        If any of name, description, or tag is provided, filter to just those
        datasets which match the provided pattern, as well as their parents
        """

        # Parse all of the datasets available from the home directory
        self.update_datasets()

        # Filter the datasets based on the name, description, and/or tag filters provided
        self.filter_datasets(
            name=name,
            description=description,
            tag=tag
        )

        # Format the list of dataset in tree format
        return self.datasets.format_dataset_tree()

    def change_name(self, path=None, name=None):
        "Modify the name of a folder (dataset or collection)."

        # Change the name, collapsing a list with spaces if needed
        return self.change_dataset_attribute(
            path=path,
            attribute="name",
            value=" ".join(name) if isinstance(name, list) else name
        )

    def change_description(self, path=None, description=None):
        "Modify the description of a folder (dataset or collection)."

        # Change the description, collapsing a list with spaces if needed
        return self.change_dataset_attribute(
            path=path,
            attribute="description",
            value=" ".join(description) if isinstance(description, list) else description
        )

    def change_dataset_attribute(self, path=None, attribute=None, value=None):
        """Change any attribute of a dataset."""

        assert path is not None
        assert attribute is not None
        assert value is not None

        # Read the dataset
        ds = Dataset(path)

        # Set the attribute
        ds.set_attribute(attribute, value)

        # Return the updated configuration
        return ds.index

    def update_tag(
        self, 
        path=None,
        key=None,
        value=None
    ):
        "Modify the value of a tag applied to a folder."

        assert path is not None
        assert key is not None
        assert value is not None

        # Read the dataset
        ds = Dataset(path)

        # Set the tag
        ds.set_tag(key, value)

        # Return the updated configuration
        return ds.index

    def delete_tag(
        self, 
        path=None,
        key=None,
    ):
        "Delete the value of a tag applied to a folder, if it exists."

        assert path is not None
        assert key is not None

        # Read the dataset
        ds = Dataset(path)

        # Delete the tag
        ds.delete_tag(key)

        # Return the updated configuration
        return ds.index

    def _top_level_folder(self, folder_name):
        """Return the path to a top-level folder in the home directory."""

        return self.filelib.path_join(self.home_folder, folder_name)

    def _top_level_file(self, folder_name, file_name):
        """Return the path to a file in a top-level folder of the home directory."""

        return self.filelib.path_join(self._top_level_folder(folder_name), file_name)

    def _asset_folder(self, folder_name):
        """Return the path to a top-level folder in the asset directory of the package."""

        return self.filelib.path_join(self.assets_folder, folder_name)

    def _asset_file(self, folder_name, filename):
        """Return the path to a file in a top-level folder of the asset directory of the package."""

        return self.filelib.path_join(self._asset_folder(folder_name), filename)

    def _copy_repo_file_to_home(self, folder, filename, overwrite=False):
        """Copy a file from the repository assets to the home directory."""

        # The destination folder is in the home directory
        destination_folder = self._top_level_folder(folder)
        destination_path = self._top_level_file(folder, filename)

        # Create the destination folder if it does not exist
        self.filelib.mkdir_p(destination_folder)

        # If the file already exists
        if self.filelib.exists(destination_path):

            # If the overwrite flag was not set
            if not overwrite:

                # Do not take any action
                self.log(f"File already exists: {destination_path}")
                return

        # At this point, either the destination_path does not exist, or --overwrite was set

        # Construct the path to the file in the asset folder
        source_path = self._asset_file(folder, filename)

        # Copy the file
        self.log(f"Copying {source_path} to {destination_path}")
        self.filelib.copyfile(source_path, destination_path, follow_symlinks=True)

    def update_base_toolkit(self, overwrite=False):
        """Copy the tools and launchers from the package into the home directory"""

        # Copy all files in helpers/
        for filename in self.filelib.listdir(self._asset_folder("helpers")):

            # Copy the repository asset from the package to the home directory
            self._copy_repo_file_to_home("helpers", filename, overwrite=overwrite)

        # Copy the folders within the launcher/ and tool/ folders
        for asset_type in ["launcher", "tool"]:

            self.log(f"Copying all {asset_type} to home directory")

            # Iterate over each of the tools or launchers
            for asset_name in self.filelib.listdir(self._asset_folder(asset_type)):

                # Reconstruct the full path
                asset_path = self._asset_folder(f"{asset_type}/{asset_name}")

                # If the asset is not a folder
                if not self.filelib.isdir(asset_path):
                    # Skip it
                    continue

                # Iterate over each of the files in that folder
                for filename in self.filelib.listdir(asset_path):

                    # Copy the asset from the package to the home directory
                    self._copy_repo_file_to_home(
                        f"{asset_type}/{asset_name}",
                        filename,
                        overwrite=overwrite
                    )

    def _list_assets(self, asset_type):

        assert asset_type in ["tool", "launcher"]

        # Get the folder which contains all of the assets of this type
        asset_type_folder = self._top_level_folder(asset_type)

        # Make a list for all of the tools
        asset_list = []

        # Iterate over the folders in the tools/ or launchers/ directory
        for asset_name in self.filelib.listdir(asset_type_folder):

            # Validate that the asset has a properly formatted configuration
            asset = Asset(WB=self, asset_name=asset_name, asset_type=asset_type)

            # Add the name to the list
            asset_list.append(asset.config["key"])

        return asset_list
    
    def list_launchers(self):
        """List the launchers available for creating datasets."""

        return self._list_assets("launcher")
    
    def list_tools(self):
        """List the tools available for creating datasets."""

        return self._list_assets("tool")

    def _copy_helpers_to_dataset(self, dataset_path, overwrite=False):
        """Copy all of the helper scripts to a dataset inside the subfolder ._wb"""

        # Instantiate a Dataset object
        dataset = Dataset(dataset_path)

        # All of the files will be copied to the folder
        # {dataset.wb_folder}/helpers/
        dest_folder = self.filelib.path_join(dataset.wb_folder, "helpers")

        # Create the folder if it does not exist
        self.filelib.mkdir_p(dest_folder)

        # Iterate over all of the files in the "helpers" folder
        helpers_folder = self._top_level_folder("helpers")
        for fn in self.filelib.listdir(helpers_folder):

            # Reconstruct the source path
            source_fp = self.filelib.path_join(helpers_folder, fn)

            # Make the path for the destination
            dest_fp = self.filelib.path_join(dest_folder, fn)

            # If the file already exists
            if self.filelib.exists(dest_fp):

                # Raise an error if the overwrite flag was not set
                assert overwrite, f"File already exists: {dest_fp}"

            # Copy the file
            self.log(f"Copying {source_fp} to {dest_fp}")
            self.filelib.copyfile(source_fp, dest_fp)
            
    def setup_dataset(self, path=None, tool=None, launcher=None, overwrite=False):
        """Set up a dataset with a tool and a launcher."""

        self.log(f"Setting up a dataset for analysis at {path}")

        # Instantiate a Dataset object
        ds = Dataset(path, filesystem=self.filesystem)

        msg = f"path must indicate an already-indexed folder"
        assert ds.index is not None, msg

        # Instantiate the tool and launcher
        tool = Asset(WB=self, asset_type="tool", asset_name=tool)
        launcher = Asset(WB=self, asset_type="launcher", asset_name=launcher)

        # Copy the tool and asset to the dataset
        tool.copy_to_dataset(ds, overwrite=overwrite)
        launcher.copy_to_dataset(ds, overwrite=overwrite)

        # Record the time at which the scripts were set up
        self.log("Recording tool and launcher in dataset index")
        ds.set_attribute("setup_at", self.timestamp.encode())
        ds.set_attribute("tool", tool.name)
        ds.set_attribute("launcher", launcher.name)

    def set_tool_params(self, path=None, overwrite=False, **kwargs):
        """Set the parameters used to run the tool in a particular dataset."""

        self._set_asset_params(path, "tool", overwrite=overwrite, **kwargs)

    def set_launcher_params(self, path=None, overwrite=False, **kwargs):
        """Set the parameters used to run the launcher in a particular dataset."""

        self._set_asset_params(path, "launcher", overwrite=overwrite, **kwargs)

    def _set_asset_params(self, path, asset_type, overwrite=False, **kwargs):
        """Set the parameters used to run a tool or launcher in a particular dataset."""

        # Instantiate the dataset object
        ds = Dataset(path)

        # The folder must be set up as an indexed folder
        msg = f"Folder is not an indexed folder: {path}"
        assert ds.index is not None, msg

        # A tool/launcher must have been set up for this dataset
        msg = f"No {asset_type} has been set up for {path}"
        assert ds.index.get(asset_type) is not None, msg

        # Get the name of the asset
        asset_name = ds.index.get(asset_type)
        self.log(f"Setting up parameters for {asset_type} {asset_name}")

        # Get the configuration of this asset, read in from the file
        # ._wb_{asset_type}_config.json
        asset_config = ds.__dict__.get(asset_type)
        assert asset_config is not None, f"No configuration defined for {asset_type}"

        # Populate a dict with the params,
        # validated from the kwargs based on the rules in the config
        params = dict()

        # Populate a dict with the environment variables that will be set
        env = dict()

        # Iterate over the arguments in the configuration
        for param_name, param_def in asset_config["args"].items():

            # If the parameter is required
            if param_def.get("required", False):

                # It must be in the kwargs
                assert kwargs.get(param_name) is not None, f"Must provide {param_name}"

            # If the parameter was not provided
            if kwargs.get(param_name) is None:

                # Skip it
                continue

            # Get the value provided
            param_value = kwargs[param_name]

            # If a list was provided
            if isinstance(param_value, list):

                # Collapse a string, using `wb_sep` if provided, ' ' if not
                param_value = param_def.get("wb_sep", " ").join(list(map(str, param_value)))

            # Add it to the params
            params[param_name] = param_value

            # If an environment variable was set
            if param_def.get("wb_env") is not None:

                # Add the parameter name and value to the dict
                env[param_def.get("wb_env")] = param_value

        # Write out the params
        self.log(f"Writing out parameters for {asset_type}")
        ds.write_asset_params(asset_type, params, overwrite=overwrite)

        # Write out a file which can be used to source the environment variables
        self.log(f"Writing out environment variables for {asset_type}")
        ds.write_asset_env(asset_type, env, overwrite=overwrite)

    def save_tool_params(self, path=None, name=None, overwrite=False):
        """Save the parameters used to run the tool in a particular dataset."""

        self._save_asset_params(path, "tool", name, overwrite=overwrite)

    def save_launcher_params(self, path=None, name=None, overwrite=False):
        """Save the parameters used to run the launcher in a particular dataset."""

        self._save_asset_params(path, "launcher", name, overwrite=overwrite)

    def _save_asset_params(self, path, asset_type, name, overwrite=False):
        """Save the parameters used to run a tool or launcher in a particular dataset."""

        # Instantiate the dataset object
        ds = Dataset(path)

        # The folder must be set up as an indexed folder
        msg = f"Folder is not an indexed folder: {path}"
        assert ds.index is not None, msg

        # A tool/launcher must have been set up for this dataset
        msg = f"No {asset_type} has been set up for {path}"
        assert ds.index.get(asset_type) is not None, msg
        asset_name = ds.index.get(asset_type)

        # The user must specify a name to associate with the saved params
        msg = "Must specify a name to associate with the saved params"
        assert name is not None, msg

        msg = "Name cannot contain slashes or spaces"
        assert self.is_simple_name(name), msg

        # Read the params which have been saved for this asset
        self.log(f"Reading parameters for {asset_type} ({path})")
        params = ds.read_asset_params(asset_type)

        # Params must have been defined for this asset
        msg = f"No params have been set for {asset_type} in {path}"
        assert params is not None, msg

        # Construct the path to the folder which contains params for this asset
        params_folder = self._top_level_folder(
            self.filelib.path_join(
                "params",
                asset_type,       # 'tool' or 'launcher'
                asset_name       # The name of the tool/launcher
            )
        )

        self.log(f"Saving params to {params_folder}")

        # If the folder does not exist
        if not self.filelib.exists(params_folder):

            # Create it
            self.log(f"Creating folder {params_folder}")
            self.filelib.makedirs(params_folder)

        # Set up the path to use for saving the params
        params_fp = self.filelib.path_join(
            params_folder,
            f"{name}.json"        # Name of the params
        )

        # If the file already exists
        if self.filelib.exists(params_fp):

            # The overwrite flag must have been set
            assert overwrite, msg
            msg = f"Params have already been saved for {asset_type}/{asset_name}/{name}"

        # Write out the params in JSON format
        self.log(f"Saving params to {params_fp}")
        self.filelib.write_json(params, params_fp, indent=4, sort_keys=True)

    def read_tool_params(self, tool_name=None, params_name=None):
        """Read a set of parameters used to run the tool."""

        return self._read_asset_params(tool_name, "tool", params_name)

    def read_launcher_params(self, launcher_name=None, params_name=None):
        """Read a set of parameters used to run the launcher."""

        return self._read_asset_params(launcher_name, "launcher", params_name)

    def _read_asset_params(self, asset_name, asset_type, params_name):
        """Read a set of parameters used to run a tool or launcher."""

        # The user must specify the name of the asset
        msg = f"Must specify the {asset_type} name"
        assert asset_name is not None, msg

        # The user must specify the name of the params
        msg = f"Must specify the name used for this set of parameters"
        assert params_name is not None, msg

        # The params name must match an entry in the tool's param folder
        msg = f"No parameters named '{params_name}' found for {asset_type} {asset_name}"
        assert params_name in self._list_asset_params(
            asset_type=asset_type,
            name=asset_name
        ), msg

        # Set up the path to the saved params
        params_fp = self.filelib.path_join(
            self._top_level_folder("params"),
            asset_type,
            asset_name,
            f"{params_name}.json"
        )

        # Read the params which have been saved in JSON format
        self.log(f"Reading from {params_fp}")

        return self.filelib.read_json(params_fp)

    def list_tool_params(self, name=None):
        """List the parameters available to run the tool."""

        return self._list_asset_params("tool", name)

    def list_launcher_params(self, name=None):
        """List the parameters available to run the launcher."""

        return self._list_asset_params("launcher", name)

    def _list_asset_params(self, asset_type, name):
        """List the parameters available to run a tool or launcher."""

        # All params files are serialized in JSON format
        suffix = ".json"

        # Construct the path to the folder which contains params for this asset
        params_folder = self._top_level_folder(
            self.filelib.path_join(
                "params",
                asset_type, # 'tool' or 'launcher'
                name        # The name of the tool/launcher
            )
        )

        self.log(f"Listing params from {params_folder}")

        # If the folder does not exist
        if not self.filelib.exists(params_folder):

            # Return an empty list
            return []

        # If the folder does indeed exist

        # Return a list of all of the files which end in .json
        return [
            fp[:-len(suffix)]
            for fp in self.filelib.listdir(params_folder)
            if fp.endswith(suffix)
        ]

    def run_dataset(self, path=None):
        """Launch the tool which has been configured in a dataset."""

        # Copy all of the helpers to the dataset
        self._copy_helpers_to_dataset(path, overwrite=True)

        # Instantiate the dataset object
        ds = Dataset(path)

        # Run the dataset
        ds.run()

    def repository(self, name):
        """Instantiate a Repository object."""

        return Repository(
            name=name,
            home_folder=self.home_folder,
            filelib=self.filelib,
            logger=self.logger
        )

    def add_repo(self, name=None):
        """Clone/download a repository from GitHub if it does not already exist."""

        # Instantiate a Repository object
        self.log(f"Adding repository {name}")
        repo = self.repository(name)

        # If the repository does not already exist
        if not repo.exists():

            # Clone it
            self.log("Cloning repository")
            repo.clone()

        else:
            self.log("Repository already exists")

    def list_repos(self):
        """Return a list of the GitHub repositories which are available locally."""

        # Make a list of repositories
        repo_list = list()

        # Point to the base folder in which all repositories are saved
        repo_home = self._top_level_folder("repositories")

        # Iterate over each of the folders in "repositories/"
        for org_folder in self.filelib.listdir(repo_home):

            # Iterate over any subfolders
            for repo_folder in self.filelib.listdir(
                self.filelib.path_join(
                    repo_home,
                    org_folder
                )
            ):

                # The name of the repository should match the folders
                repo_name = f"{org_folder}/{repo_folder}"

                # Try to instantiate a repository object
                repo = self.repository(repo_name)

                # If the repository has been cloned
                if repo.exists():

                    # Add it to the list
                    repo_list.append(repo_name)

        return repo_list

    def list_linked_repos(self):
        """Return a list of the local repositories which have been linked."""

        return self.filelib.listdir(
            self._top_level_folder("linked_repositories")
        )

    def link_local_repo(self, path=None, name=None):
        """Link a local repository (containing a ._wb/ directory of tools and/or launchers)."""

        # The name cannot contain slashes or spaces
        msg = "The name can only contain letters and numbers"
        assert self.is_simple_name(name), msg

        # The name cannot have already been used for a local repository
        assert name not in self.list_linked_repos(), f"{name} has already been used"

        # The path to the local repository must exist
        assert self.filelib.exists(path), f"Path does not exist: {path}"

        # Make a link
        self.log(f"Linking to {path} as '{name}'")
        self.filelib.symlink(path, self._top_level_folder(f"linked_repositories/{name}"))

    def unlink_local_repo(self, name=None):
        """Remove a link to a local repository."""

        # The name must have already been used for a local repository
        assert name in self.list_linked_repos(), f"{name} is not a valid link"

        # Delete the link
        self.log(f"Removing link '{name}'")
        self.filelib.rm(self._top_level_folder(f"linked_repositories/{name}"))

    def update_repo(self, name=None):
        """Update a repository to the latest version."""

        # Instantiate a Repository object
        self.log(f"Setting up local repository for {name}")
        repo = self.repository(name)

        # If the repository does not already exist
        if not repo.exists():

            self.log(f"Cannot update {name}, repository has not yet been added")

        else:

            self.log("Updating repository {name}")
            repo.pull()

    def switch_branch(self, name=None, branch=None, force=True):
        """Switch to a different branch."""

        # Instantiate a Repository object
        self.log(f"Setting up local repository for {name}")
        repo = self.repository(name)

        # Switch to the branch
        self.log(f"Switching to branch {branch}")
        repo.switch_branch(branch, force=force)

    def delete_repo(self, name=None):
        """Delete the local copy of a repository, if it exists."""

        # Instantiate a Repository object
        self.log(f"Setting up local repository for {name}")
        repo = self.repository(name)

        # Delete the repository
        self.log(f"Deleting repository {name}")
        repo.delete()

    def is_simple_name(self, name):
        """Check that a name contains only alphanumeric and underscores."""

        assert isinstance(name, str), "Input to `is_simple_name` must be a string"
        return name.replace("_", "").isalnum()
