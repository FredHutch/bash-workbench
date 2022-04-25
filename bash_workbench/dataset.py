from typing import List
from .folder_hierarchy import FolderHierarchyBase
from .timestamp import Timestamp
from .filelib import FileWatcher
import subprocess
import uuid

class Dataset(FolderHierarchyBase):
    """Object used to access and manipulate dataset folders."""

    # All workbench items are contained within the subfolder ._wb/
    structure = [
        {"name": "._wb/"}
    ]

    # Do not create that folder if it does not already exist
    create_subfolders = False

    # Function runs when the dataset is initialized
    def read_contents(self) -> None:

        self.log(f"Reading contents of Dataset for {self.base_path}")

        # The path must point to a directory
        assert self.filelib.isdir(self.base_path), f"Dataset must be a directory, not {self.base_path}"

        # Make a timestamp object
        self.timestamp = Timestamp()

        # If there are files present in this folder which define the
        # properties of the dataset index, tool, or launcher,
        # read those files in and attach the data to the object
        self.read_index()

        # Read in configurations of the tool and launcher, if they exist
        self.read_asset_configs()

    def validate_asset_type_format(self, asset_type):
        """Make sure that the asset type string is valid."""

        # The asset type must be a simple string
        assert isinstance(asset_type, str), "Asset type must be a string"
        assert "/" not in asset_type, "Asset type must not contain a slash"
        assert " " not in asset_type, "Asset type must not contain a space"

    def setup_asset_folder(self, asset_type):
        """Set up a folders for the tool or launcher (etc.), if they do not exist."""

        # Make sure that the asset type string is valid
        self.validate_asset_type_format(asset_type)

        # Make the folder
        self.filelib.mkdir_p(self.wb_path(asset_type))

    def delete_asset_folder(self, asset_type):
        """Delete an asset folder, if it exists."""

        # Make sure that the asset type string is valid
        self.validate_asset_type_format(asset_type)

        # Remove the asset folder
        self.filelib.rmdir(self.wb_path(asset_type))

    def read_index(self):
        """Read in the dataset index."""

        # By default, the index is None
        self.index = None

        # If the wb_folder does not exist
        if not self.complete:

            # Then there cannot be any index within it
            # so we should stop now
            return

        # Read in the file (adding the prefix ._wb_), or assign
        # a null value if the file does not exist
        self.index = self.read_json("index.json")

    def read_asset_configs(self):
        """Read in files describing the dataset's tool and launcher."""

        self.tool = self.read_json("tool/config.json")
        self.launcher = self.read_json("launcher/config.json")

    def read_json(self, fn):
        """
        Read in the file (adding the prefix ._wb_), or assign
        a null value if the file does not exist.
        """

        # Set up the path used for this asset
        fp = self.wb_path(fn)

        # If the file exists
        if self.filelib.exists(fp):

            # Read it in and parse it as JSON
            return self.filelib.read_json(fp)

        # If the file does not exist
        else:

            # Return a null value
            return

    def write_json(self, fn, dat, overwrite=False, **kwargs):
        """Write out a JSON file with the prefix ._wb_ in the dataset folder."""

        # Set up the path to be written
        fp = self.wb_path(fn)

        # If the file exists
        if self.filelib.exists(fp):

            # Raise an error if overwrite is not True
            assert overwrite, f"File exists but overwrite was not set ({fp})"

        self.filelib.write_json(dat, fp, **kwargs)

    def write_text(self, fn, dat, overwrite=False, **kwargs):
        """Write out a text file with the prefix ._wb_ in the dataset folder."""

        # Set up the path to be written
        fp = self.wb_path(fn)

        # If the file exists
        if self.filelib.exists(fp):

            # Raise an error if overwrite is not True
            assert overwrite, f"File exists but overwrite was not set ({fp})"

        self.filelib.write_text(dat, fp, **kwargs)

    def wb_path(self, *subfolder_list) -> str:
        """Return the path to a file in the ._wb/."""

        return self.path("._wb", *subfolder_list)

    def wb_path_exists(self, *subfolder_list) -> bool:
        """Boolean indicating whether a file in the ._wb/ folder eixsts."""

        return self.filelib.exists(
            self.path("._wb", *subfolder_list)
        )

    def create_index(self):
        """Add an index to a folder."""

        # Raise an error if there already is an index
        assert self.index is None, f"Already indexed, cannot overwrite ({self.base_path})"

        # Set up the wb_folder for the index file to be placed within
        self.populate_folders()
    
        # Create the index object, consisting of
        #  - the folder type (collection or dataset)
        #  - timestamp
        #  - unique identifier
        self.index = dict(
            uuid=str(uuid.uuid4()),
            indexed_at=self.timestamp.encode(),
            name=self.base_path.rsplit("/", 1)[-1],
            description=""
        )

        # Write it to the file
        self.write_index()

    def write_index(self, indent=4, sort_keys=True, overwrite=False):
        """Write the dataset index to the filesystem."""

        # Write the index object to the index path
        self.write_json(
            "index.json",
            self.index,
            indent=indent,
            sort_keys=sort_keys,
            overwrite=overwrite
        )

    def write_asset_params(self, asset_type, params, indent=4, sort_keys=True, overwrite=False):
        """Write out the parameters for an asset in JSON format."""

        # Make sure that a folder exists for this asset type
        self.setup_asset_folder(asset_type)

        # Write the params object to the appropriate path for the asset type
        self.write_json(
            self.wb_path(asset_type, "params.json"),
            params,
            indent=indent,
            sort_keys=sort_keys,
            overwrite=overwrite
        )

    def read_asset_params(self, asset_type):
        """Read the parameters for an asset in JSON format."""

        # Write the params object to the appropriate path for the asset type
        return self.read_json(
            self.wb_path(asset_type, "params.json")
        )

    def write_asset_env(self, asset_type, env, overwrite=False):
        """Write out the parameters for an asset in JSON format."""

        # Make sure that a folder exists for this asset type
        self.setup_asset_folder(asset_type)

        # Format a script which will be used to set environment variables in BASH
        env_script = "\n\n".join(["#!/bin/bash", "set -e", "####"])
        for env_name, env_val in env.items():
            self.log(f"Environment: {env_name}='{env_val}'")
            env_script += "\n" + f"export {env_name}='{env_val}'"

        # Write the params object to the appropriate path for the asset type
        self.write_text(
            self.wb_path(asset_type, "env"),
            env_script,
            overwrite=overwrite
        )

    def set_attribute(self, key, value):
        """Add/modify a key,value pair to the index information for a folder in-place."""

        # Add the key/value
        self.index[key] = value

        # Write the index
        self.write_index(overwrite=True)

    def set_tag(self, key, value):
        """Add/modify a key,value pair to the tag information for a folder in-place."""

        # Make sure that there is a tag dict in the index
        self.index["tags"] = self.index.get("tags", {})

        # Add the key/value
        self.index["tags"][key] = value

        # Write the index
        self.write_index(overwrite=True)

    def delete_tag(self, key):
        """Delete a key from the tag information for a folder in-place."""

        # Make sure that there is a tag dict in the index
        self.index["tags"] = self.index.get("tags", {})

        # If the key exists
        if key in self.index["tags"]:

            # Delete it
            del self.index["tags"][key]

            # Write the index, if a modification was made
            self.write_index(overwrite=True)

    def children(self):
        """Return a list with the uuids of any indexed folders inside this one."""

        children_uuids = list()

        # Iterate over all of the paths inside this folder
        for subfolder in self.listdir():

            # Skip the ._wb/ folder
            if subfolder == "._wb":
                continue

            # Construct the complete path to the subfolder
            subfolder = self.path(subfolder)

            # If it is a directory
            if self.filelib.isdir(subfolder):

                # Get the index of the subfolder, if any exists
                ds = Dataset(
                    base_path=subfolder,
                    filelib=self.filelib,
                    verbose=self.verbose,
                    logger=self.logger
                )

                # If the subfolder has an index
                if ds.index is not None:

                    # Add the 'uuid' to the list
                    children_uuids.append(ds.index["uuid"])

        return children_uuids

    def run(self, wait:bool=False, interval:float=1.0) -> None:
        """Launch the tool which has been configured for this dataset."""

        # Start the process
        proc = subprocess.Popen(
            ["/bin/bash", self.wb_path("helpers/run_launcher")],
            start_new_session=True,
            cwd=self.base_path
        )

        # If the user elected to wait for the process to complete
        if wait:

            # While the process is running
            while proc.poll() is None:

                # Wait for the specified interval (seconds)
                try:
                    outs, errs = proc.communicate(timeout=interval)
                
                # If the process did not finish in this period
                except subprocess.TimeoutExpired:

                    # Get the logging messages anyway
                    outs, errs = proc.communicate()

                # Print the output and error messages
                self.print_lines(outs, prefix="OUTPUT")
                self.print_lines(errs, prefix="ERROR")

            # Once the process is done

            # Get the logging messages
            outs, errs = proc.communicate()

            # Print the output and error messages
            self.print_lines(outs, prefix="OUTPUT")
            self.print_lines(errs, prefix="ERROR")

            # Print the exit code
            self.print_lines(f"Exit code: {proc.poll()}", prefix="DONE")

    def print_lines(self, lines:str, prefix=None) -> None:
        """Print a set of lines, along with a prefix and timestamp."""

        # If any lines were provided
        if lines is not None:

            # Loop over each individual line
            for line in lines.split("\n"):

                print(self.timestamp.encode() + line)

    def has_logs(self) -> bool:
        """Boolean indicating whether any log files exist."""

        return len(self.log_types()) > 0

    def log_types(self) -> List[str]:
        """Return the types of logs available."""

        return [
            fn
            for fn in [
                "log",
                "output",
                "error"
            ]
            if self.wb_path_exists(f"{fn}.txt")
        ]

    def read_logs(self, log_type) -> str:
        """Read one of the log files."""

        msg = f"Does not contain logs: {log_type}"
        assert self.wb_path_exists(f"{log_type}.txt"), msg

        return self.read_text("._wb", f"{log_type}.txt")

    def file_watcher(self, path:str) -> FileWatcher:
        """Return a FileWatcher for a file in ._wb/"""

        return FileWatcher(f"._wb/{path}")

    def get_actions(self) -> List[str]:
        """Return the list of actions available."""

        # If the bin/ folder is not present
        if not self.wb_path_exists("bin"):

            # There are no actions
            return []

        else:

            # Return all non-hidden files
            return [
                fn
                for fn in self.listdir("._wb", "bin")
                if len(fn) > 0 and fn[0] != "."
            ]

    def run_action(self, action_name) -> None:
        """Run a specific action."""

        # Start the process
        subprocess.Popen(
            ["/bin/bash", self.wb_path(f"bin/{action_name}")],
            start_new_session=True,
            cwd=self.base_path
        )

