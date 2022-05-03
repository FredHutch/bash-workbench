from typing import Dict, List, Union
from .asset import Asset
from .repository import Repository
from .dataset import Dataset
from .datasets import Datasets
from .folder_hierarchy import FolderHierarchyBase
from .timestamp import Timestamp
from importlib_resources import files

class Workbench(FolderHierarchyBase):
    """Object used to organize BASH Workbench attributes and methods."""

    # The expected subfolders in the base workbench directory
    # These folder will be created if they do not exist
    structure = [
        dict(name="data"),
        dict(name="params"),
        dict(name="repositories")
    ]

    def read_contents(self) -> None:
        """Function is executed immediately after the folder structure is populated."""

        # Class used to encode / decode timestamps
        self.timestamp = Timestamp()

        # Make sure that all of the appropriate directories exist
        self.setup_root_folder()

        # Set up all of the repositories which are present
        self.repositories = self.setup_repositories()

        # Parse all of the datasets contained within data/
        self.datasets = Datasets(self)

        # Get the folder which contains helpers installed with this package
        self.helpers_folder = files("bash_workbench").joinpath('helpers')
        
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

    def setup_root_folder(self) -> None:
        """Ensure that the root folder contains the required assets, and create them if necessary."""

        # Make sure that all of the required top-level directories exist
        self.populate_folders()

    def setup_repositories(self) -> Dict[str, Repository]:
        """Read the dict of repositories which are available."""

        # Parse the folders which are contained within repositories/
        # Each Repository contains an `assets` attriute which is a dict
        # with keys 'tool' and 'launcher' with the list of the Assets contained
        # in each repository, if any. 
        repositories = {
            folder_name: Repository(
                base_path=self.path("repositories", folder_name),
                logger=self.logger,
                verbose=self.verbose,
                filelib=self.filelib
            )
            for folder_name in self.listdir("repositories")
        }
        # Include all repositories in this dict, even if they do not contain
        # a folder ._wb/ (in which case Repository.complete == False)

        return repositories

    def index_folder(self, path:str=None) -> dict:

        assert path is not None, "Must provide --path for folder to index"

        self.log(f"Preparing to index folder: {path}")

        # Create a Dataset object
        ds = self.datasets.from_path(path)

        # If the index does not already exist
        if ds.index is None:

            # Create the index
            self.log(f"Indexing folder: {path}")
            ds.create_index()

        else:
            self.log("Index already exists")

        # Finally, link this dataset to the home folder if it is not already
        # nested below a collection which is similarly linked
        self.log(f"Adding to home tree: {path}")
        self.add_to_home_tree(ds, path)

        # Add it to the collection of datasets
        self.datasets.add(ds)

        return ds.index

    def add_to_home_tree(self, ds:Dataset, path:str):
        """If a folder is not already contained in the home tree, add it."""

        # Resolve symlinks and remove any terminal slashes
        path = self.filelib.abs_path(path)

        # Get the UUID for the dataset
        ds_uuid = ds.index["uuid"]

        # Write the path to the file named for the UUID
        self.filelib.write_text(
            path,
            self.path("data", ds_uuid)
        )

    def parse_reference(self, ds_uuid:str) -> Union[None, Dataset]:
        """Check to see if there is a valid reference to this dataset in the data/ folder."""

        # If there is no file with the name `ds_uuid` in ._wb/data/
        if not self.exists("data", ds_uuid):
            return

        # If the file is a symlink
        if self.filelib.islink(self.path("data", ds_uuid)):
            # Then it is not valid
            return

        # The file should contain the path to a folder which contains a dataset
        with open(self.path("data", ds_uuid)) as handle:
            ds_path = handle.readline()

        # If the file does not exist
        if len(ds_path) == 0 or self.filelib.exists(ds_path) is False:
            return

        # If the file does exist

        # Parse the Dataset
        ds = self.dataset(ds_path)

        # If it is not a valid dataset
        if not ds.complete or ds.index is None:
            return

        # If it is a valid dataset, make sure that the UUID is a match
        if ds_uuid == ds.index["uuid"]:
            return ds
        else:
            return
            
    def walk_home_tree(self):
        """Walk through all of the indexed folders which are linked to the home folder."""

        # Iterate over each of the files in data/, which are named for a dataset UUID
        for ds_uuid in self.listdir("data"):

            # Make a series of checks to see if this file is a valid dataset reference
            # If it is valid, return a Dataset object
            ds = self.parse_reference(ds_uuid)

            # If it is not a valid link
            if ds is None:

                # Remove the link
                self.filelib.rm(self.path("data", ds_uuid))

            # If it is valid
            else:

                yield ds

    def dataset(self, path:str) -> Dataset:
        """Generate a Dataset object for a particular path."""

        return Dataset(
            base_path=path,
            verbose=self.verbose,
            filelib=self.filelib,
            logger=self.logger
        )

    def link_to_home(self, path:str):
        """Add a symlinnk of a path to the home directory."""

        # If there is a link to this folder already in the home directory
        if path in self.links_from_home_directory():

            # No need to take any further action
            return

        # Get the folder name
        folder_name = path.rsplit("/", 1)[1]

        # Get the path to the symlink
        home_symlink = self.path("data", folder_name)

        # To prevent collisions, add a suffix to make it unique (if not already)
        n = 0
        while self.filelib.exists(home_symlink):

            # Increment the counter to make a new suffix
            n += 1

            # Make a new the path to the symlink
            home_symlink = self.path("data", f"{folder_name}_{n}")

        # Add a symlink
        self.filelib.symlink(path, home_symlink)

    def links_from_home_directory(self):
        """Return the list of folders which are linked from the home data directory."""

        # Make a list of the linked folders
        return [
            # Construct the full path to each file
            self.path("data", fp)
            # For each of the files in the data/ folder
            for fp in self.listdir(self.path("data"))
        ]

    def list_datasets(self):
        """Return a list of all datasets linked from the home folder."""

        # Return the simple dict of all datasets
        return self.datasets.datasets

    def find_datasets(
        self,
        name:str=None,
        description:str=None,
        tag:str=None
    ):
        """Find any datasets which match the provided queries."""

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

    def filter_datasets(self, name:str=None, description:str=None, tag:str=None):
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
        name:str=None,
        description:str=None,
        tag:str=None,
    ):
        """
        Return the list of datasets formatted as a tree.
        If any of name, description, or tag is provided, filter to just those
        datasets which match the provided pattern, as well as their parents
        """

        # Filter the datasets based on the name, description, and/or tag filters provided
        self.filter_datasets(
            name=name,
            description=description,
            tag=tag
        )

        # Format the list of dataset in tree format
        return self.datasets.format_dataset_tree()

    def change_name(self, path:str=None, name:str=None):
        "Modify the name of a folder (dataset or collection)."

        # Change the name, collapsing a list with spaces if needed
        return self.change_dataset_attribute(
            path=path,
            attribute="name",
            value=" ".join(name) if isinstance(name, list) else name
        )

    def change_description(self, path:str=None, description:str=None):
        "Modify the description of a folder (dataset or collection)."

        # Change the description, collapsing a list with spaces if needed
        return self.change_dataset_attribute(
            path=path,
            attribute="description",
            value=" ".join(description) if isinstance(description, list) else description
        )

    def change_dataset_attribute(self, path:str=None, attribute:str=None, value:str=None):
        """Change any attribute of a dataset."""

        assert path is not None
        assert attribute is not None
        assert value is not None

        # Read the dataset
        ds = self.datasets.from_path(path)

        # Set the attribute
        ds.set_attribute(attribute, value)

        # Return the updated configuration
        return ds.index

    def update_tag(
        self, 
        path:str=None,
        key:str=None,
        value:str=None
    ):
        "Modify the value of a tag applied to a folder."

        assert path is not None
        assert key is not None
        assert value is not None

        # Read the dataset
        ds = self.datasets.from_path(path)

        # Set the tag
        ds.set_tag(key, value)

        # Return the updated configuration
        return ds.index

    def delete_tag(
        self, 
        path:str=None,
        key:str=None,
    ):
        "Delete the value of a tag applied to a folder, if it exists."

        assert path is not None
        assert key is not None

        # Read the dataset
        ds = self.datasets.from_path(path)

        # Delete the tag
        ds.delete_tag(key)

        # Return the updated configuration
        return ds.index

    def _list_assets(self, asset_type:str) -> list:

        assert asset_type in ["tool", "launcher"]

        # Make a list for all of the tools as a tuple of repository, tool
        return [
            f"{repo_name}/{tool_name}"
            # Iterate over all of the folder in repositories/
            for repo_name, repo in self.repositories.items()
            # if that folder contains ._wb/
            if repo.complete
            # Iterate over every folder in ._wb/{asset_type}
            for tool_name, tool in repo.assets.get(asset_type, {}).items()
            # If that folder contains config.json and run.sh
            if tool.complete
        ]
    
    def list_launchers(self):
        """List the launchers available for creating datasets."""

        return self._list_assets("launcher")
    
    def list_tools(self):
        """List the tools available for creating datasets."""

        return self._list_assets("tool")

    def _copy_helpers_to_dataset(self, dataset_path:str):
        """Copy all of the helper scripts to a dataset inside the subfolder ._wb"""

        # Instantiate a Dataset object
        dataset = self.datasets.from_path(dataset_path)

        # All of the files will be copied to the folder
        # {dataset.wb_folder}/helpers/
        dest_folder = dataset.wb_path("helpers")

        # Create the folder if it does not exist
        self.filelib.mkdir_p(dest_folder)

        # Iterate over all of the files in the "helpers" folder
        # of the installed bash_workbench package
        for filename in self.filelib.listdir(self.helpers_folder):

            # Copy the repository asset from the package to the dataset
            self.filelib.copyfile(
                self.filelib.path_join(
                    self.helpers_folder,
                    filename
                ),
                self.filelib.path_join(
                    dest_folder,
                    filename
                )
            )

    def asset(self, asset_type:str=None, asset_name:str=None) -> Asset:
        """
        Return an Asset from a particular repository, identified by name.
        The clearest way to specify the asset is to provide the <repository>/<asset>.
        However, if the asset name is unique, then the user should be able to
        provide just <asset>.
        """

        # If the repository name was not provided
        if "/" not in asset_name:

            # Find all of the repos which contain an asset of this name
            matching_repos = [
                repo_name
                for repo_name, repo in self.repositories.items()
                if asset_name in repo.assets.get(asset_type, dict())
            ]

            # If no matching assets were found
            msg = f"No repositories found with the {asset_type} {asset_name}"
            assert len(matching_repos) > 0, msg

            # If multiple matching assets were found
            msg = f"Multiple repositories found with the {asset_type} {asset_name} ({', '.join(matching_repos)})"
            assert len(matching_repos) == 1, msg

            # At this point, only a single repository was found
            return self.repositories[
                matching_repos[0]
            ].assets[
                asset_type
            ][
                asset_name
            ]

        # Otherwise, the asset_name should be <repository>/<asset>
        else:

            msg = "Asset name must specify <repository>/<asset>"
            assert len(asset_name.split("/")) == 2, msg

            # Parse the repository and asset name
            repository, name = asset_name.split("/")

            # Get the Repository
            repo = self.repositories.get(repository)

            # Make sure that the repository name is valid
            assert repo is not None, f"Invalid repository: {repository}"

            # Make sure that the repository has any assets of this type
            assert asset_type in repo.assets, f"Repository does not contain any assets of type {asset_type}"

            # Make sure that there is an asset of the appropriate type and name
            assert name in repo.assets[asset_type], f"Repository {repository} does not contain any {asset_type} with the name {name}"

            # Return the asset
            return repo.assets[asset_type][name]
            
    def setup_dataset(self, path:str=None, tool:str=None, launcher:str=None, overwrite:bool=False):
        """Set up a dataset with a tool and a launcher."""

        self.log(f"Setting up a dataset for analysis at {path}")

        # Instantiate a Dataset object
        ds = self.datasets.from_path(path)

        # If the dataset is not indexed
        if ds.index is None:

            # Add an index
            self.datasets.add(ds)

        # Instantiate the tool and launcher, and copy assets to the dataset
        self.log(f"Using tool {tool} for analysis")
        tool = self.asset(asset_type="tool", asset_name=tool)
        tool.copy_to_dataset(ds, overwrite=overwrite)

        self.log(f"Using launcher {launcher} for analysis")
        launcher = self.asset(asset_type="launcher", asset_name=launcher)
        launcher.copy_to_dataset(ds, overwrite=overwrite)

        # Record the time at which the scripts were set up
        self.log("Recording tool and launcher in dataset index")
        ds.set_attribute("setup_at", self.timestamp.encode())
        ds.set_attribute("tool", tool.name)
        ds.set_attribute("launcher", launcher.name)

    def set_tool_params(self, path:str=None, overwrite:bool=False, **kwargs):
        """Set the parameters used to run the tool in a particular dataset."""

        self._set_asset_params(path, "tool", overwrite=overwrite, **kwargs)

    def set_launcher_params(self, path:str=None, overwrite:bool=False, **kwargs):
        """Set the parameters used to run the launcher in a particular dataset."""

        self._set_asset_params(path, "launcher", overwrite=overwrite, **kwargs)

    def _set_asset_params(self, path:str, asset_type:str, overwrite:bool=False, **kwargs):
        """Set the parameters used to run a tool or launcher in a particular dataset."""

        # Instantiate the dataset object
        ds = self.datasets.from_path(path)

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

        # Add the path to the repository which contains the tool
        env[f"{asset_type.upper()}_REPO"] = ds.index.get(f"{asset_type}_repo")

        # Iterate over the arguments in the configuration
        for param_name, param_def in asset_config["args"].items():

            # If the parameter is required
            if param_def.get("required", False):

                # It must be in the kwargs
                assert kwargs.get(param_name) is not None, f"Must provide {param_name}"

            # If the parameter was not provided
            if kwargs.get(param_name) is None:

                # If there is a default value
                if param_def.get("default") is not None:

                    # Use that value
                    param_value = param_def.get("default")

                # Otherwise, if there is no default value
                else:

                    # Skip it
                    continue

            # If a value was provided by the user
            else:

                # Use the value that was provided
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

    def save_tool_params(self, path:str=None, name:str=None, overwrite:bool=False):
        """Save the parameters used to run the tool in a particular dataset."""

        self._save_asset_params(path, "tool", name, overwrite=overwrite)

    def save_launcher_params(self, path:str=None, name:str=None, overwrite:bool=False):
        """Save the parameters used to run the launcher in a particular dataset."""

        self._save_asset_params(path, "launcher", name, overwrite=overwrite)

    def _save_asset_params(self, path:str, asset_type:str, name:str, overwrite:bool=False):
        """Save the parameters used to run a tool or launcher in a particular dataset."""

        # Instantiate the dataset object
        ds = self.datasets.from_path(path)

        # The folder must be set up as an indexed folder
        msg = f"Folder is not an indexed folder: {path}"
        assert ds.index is not None, msg

        # A tool/launcher must have been set up for this dataset
        msg = f"No {asset_type} has been set up for {path}"
        assert ds.index.get(asset_type) is not None, msg
        asset_name = ds.index.get(asset_type)

        # If there is a '/' in the asset name
        if "/" in asset_name:

            # Then it must be a repository/tool
            # Remove the repository, keep the tool
            asset_name = asset_name.split("/")[-1]

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

        # Write the params JSON to a file
        self._write_asset_params_json(
            asset_type=asset_type,
            asset_name=asset_name,
            name=name,
            params=params,
            overwrite=overwrite
        )

    def _write_asset_params_json(
        self,
        asset_type:str=None,
        asset_name:str=None,
        name:str=None,
        params:dict=None,
        overwrite:bool=True
    ):
        """Serialize a set of saved parameters to JSON."""

        # If there is a '/' in the asset name
        if "/" in asset_name:

            # Then it must be a repository/tool
            # Remove the repository, keep the tool
            asset_name = asset_name.split("/")[-1]

        # Construct the path to the folder which contains params for this asset
        params_folder = self.path(
            "params",
            asset_type,       # 'tool' or 'launcher'
            asset_name       # The name of the tool/launcher
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

    def read_tool_params(self, tool_name:str=None, params_name:str=None):
        """Read a set of parameters used to run the tool."""

        return self._read_asset_params(tool_name, "tool", params_name)

    def read_launcher_params(self, launcher_name:str=None, params_name:str=None):
        """Read a set of parameters used to run the launcher."""

        return self._read_asset_params(launcher_name, "launcher", params_name)

    def _read_asset_params(self, asset_name:str, asset_type:str, params_name:str):
        """Read a set of parameters used to run a tool or launcher."""

        # The user must specify the name of the asset
        msg = f"Must specify the {asset_type} name"
        assert asset_name is not None, msg

        # If there is a '/' in the asset name
        if "/" in asset_name:

            # Then it must be a repository/tool
            # Remove the repository, keep the tool
            asset_name = asset_name.split("/")[-1]

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
        params_fp = self.path(
            "params",
            asset_type,
            asset_name,
            f"{params_name}.json"
        )

        # Read the params which have been saved in JSON format
        self.log(f"Reading from {params_fp}")

        return self.filelib.read_json(params_fp)

    def delete_tool_params(self, tool_name:str=None, params_name:str=None) -> None:
        """Delete a set of saved parameters used to run the tool."""

        return self._delete_asset_params(tool_name, "tool", params_name)

    def delete_launcher_params(self, launcher_name:str=None, params_name:str=None) -> None:
        """Delete a set of saved parameters used to run the launcher."""

        return self._delete_asset_params(launcher_name, "launcher", params_name)

    def _delete_asset_params(self, asset_name:str, asset_type:str, params_name:str) -> None:
        """Delete a set of saved parameters used to run a tool or launcher."""

        # The user must specify the name of the asset
        msg = f"Must specify the {asset_type} name"
        assert asset_name is not None, msg

        # If there is a '/' in the asset name
        if "/" in asset_name:

            # Then it must be a repository/tool
            # Remove the repository, keep the tool
            asset_name = asset_name.split("/")[-1]

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
        params_fp = self.path(
            "params",
            asset_type,
            asset_name,
            f"{params_name}.json"
        )

        # Delete the file
        self.log(f"Deleting saved parameter file {params_fp}")

        self.filelib.rm(params_fp)

    def list_tool_params(self, name:str=None) -> List[str]:
        """List the parameters available to run the tool."""

        return self._list_asset_params("tool", name)

    def list_launcher_params(self, name:str=None) -> List[str]:
        """List the parameters available to run the launcher."""

        return self._list_asset_params("launcher", name)

    def _list_asset_params(self, asset_type:str, name:str) -> List[str]:
        """List the parameters available to run a tool or launcher."""

        # If there is a '/' in the asset name
        if "/" in name:

            # Then it must be a repository/tool
            # Remove the repository, keep the tool
            name = name.split("/")[-1]

        # All params files are serialized in JSON format
        suffix = ".json"

        # Construct the path to the folder which contains params for this asset
        params_folder = self.path(
            "params",
            asset_type, # 'tool' or 'launcher'
            name        # The name of the tool/launcher
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

    def run_dataset(self, path:str=None, wait:bool=False, **kwargs) -> None:
        """Launch the tool which has been configured in a dataset."""

        # If any additional parameters were provided
        if len(kwargs) > 0:

            # Use those arguments to set the tool and launcher
            for asset_type in ["tool", "launcher"]:
                self._set_asset_params(path, asset_type, overwrite=True, **kwargs)

        # Copy all of the helpers to the dataset
        self._copy_helpers_to_dataset(path)

        # Instantiate the dataset object
        ds = self.datasets.from_path(path)

        # Run the dataset
        ds.run(wait=wait)

    def repository(self, local_name:str=None) -> Repository:
        """Instantiate a Repository object."""

        return Repository(
            base_path=self.path("repositories", local_name),
            filelib=self.filelib,
            logger=self.logger,
            verbose=self.verbose
        )

    def list_repos(self) -> List[str]:
        """Return a list of the GitHub repositories which are available locally."""

        return list(self.repositories.keys())

    def add_repo(self, remote_name:str=None, method:str="https", server="github.com"):
        """
        Clone/download a repository from GitHub.
        Raise an error if it already exists locally.
        """

        # The remote_name must be of the format <org>/<repo>
        msg = "Remote name for repository must contain <organization>/<repository>"
        assert "/" in remote_name, msg
        assert len(remote_name.split("/")) == 2, msg

        # Instantiate a Repository object
        self.log(f"Adding repository {remote_name}")

        # Construct the local name to be used
        local_name = remote_name.replace("/", "_")

        # Make sure the local name has not been used before
        assert local_name not in self.repositories, f"Repository is already present: {remote_name}"

        # Instantiate the repository object
        repo = self.repository(local_name=local_name)

        # Clone the remote repository
        repo.clone(repo_name=remote_name, method=method, server=server)

    def link_local_repo(self, path:str=None, name=None):
        """Link a local repository (containing a ._wb/ directory of tools and/or launchers)."""

        # The name cannot contain slashes or spaces
        msg = "The name can only contain letters and numbers"
        assert self.is_simple_name(name), msg

        # The name cannot have already been used for a local repository
        assert name not in self.repositories, f"{name} has already been used"

        # The path to the local repository must exist
        assert self.filelib.exists(path), f"Path does not exist: {path}"

        # Make a link
        self.log(f"Linking to {path} as '{name}'")
        symlink_fp = self.path("repositories", name)
        self.filelib.symlink(path, symlink_fp)

        # Try to set up a git object
        repo = Repository(
            base_path=self.path("repositories", name),
            logger=self.logger,
            verbose=self.verbose,
            filelib=self.filelib
        )

        # If this is not a valid git folder
        if not repo.exists():

            # Tell the user
            self.log(f"Folder is not a valid git repository: {path}")
            
            # Remove the symbolic link
            self.filelib.rm(symlink_fp)

        # If this repository does not contain a folder ._wb/
        elif not repo.complete:

            # Tell the user
            self.log(f"Folder does not contain ._wb/: {path}")
            
            # Remove the symbolic link
            self.filelib.rm(symlink_fp)

        # If there are no problems
        else:

            # Add it to the collection of repositories
            self.repositories[name] = repo

    def unlink_local_repo(self, name=None):
        """Remove a link to a local repository."""

        # The name must have already been used for a local repository
        assert name in self.repositories, f"{name} is not a valid repository"

        # Get the location of the repository
        repo_fp = self.path("repositories", name)

        # The repository must be a link, not a cloned repository
        assert self.filelib.islink(repo_fp), f"Repository is not a link: {name}"

        # Delete the link
        self.log(f"Removing link '{name}'")
        self.filelib.rm(repo_fp)

        # Remove the repository from the local dict
        del self.repositories[name]

    def update_repo(self, name:str=None):
        """Update a repository to the latest version."""

        assert name is not None, "Must provide name"

        # The name must have already been used for a local repository
        assert name in self.repositories, f"{name} is not a valid repository"

        # Get the repository
        repo = self.repositories[name]

        # If the repository does not already exist
        if not repo.exists():

            self.log(f"Cannot update {name}, repository has not been set up")

        else:

            self.log(f"Updating repository {name}")
            repo.pull()

    def switch_branch(self, name:str=None, branch:str=None, force:bool=True):
        """Switch to a different branch."""

        assert name is not None, "Must provide name"

        # The name must have already been used for a local repository
        assert name in self.repositories, f"{name} is not a valid repository"

        # Get the repository
        repo = self.repositories[name]

        # Switch to the branch
        self.log(f"Switching to branch {branch}")
        repo.switch_branch(branch, force=force)

    def delete_repo(self, name=None):
        """Delete the local copy of a repository, if it exists."""

        assert name is not None, "Must provide name"

        # The name must have already been used for a local repository
        assert name in self.repositories, f"{name} is not a valid repository"

        # Get the repository
        repo = self.repositories[name]

        # Delete the repository
        self.log(f"Deleting repository {name}")
        repo.delete()

        # Remove the repository from the list of repositories
        del self.repositories[name]

    def is_simple_name(self, name):
        """Check that a name contains only alphanumeric and underscores."""

        assert isinstance(name, str), "Input to `is_simple_name` must be a string"
        return name.replace("_", "").replace("-", "").isalnum()
