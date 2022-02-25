import bash_workbench as wb
import uuid

class Dataset:
    """Object used to access and manipulate 'dataset' and 'collection' folders."""

    def __init__(self, path:str=None, filesystem="local"):

        # Attach the module used for this filesystem
        self.filelib = wb.utils.filesystem.__dict__.get(filesystem)

        # Record the absolute path to the folder
        self.path = self.filelib.abs_path(path)

        # The path must point to a directory
        assert self.filelib.isdir(self.path), f"Dataset must be a directory, not {self.path}"

        # Keep track of the filesystem being used
        self.filesystem = filesystem

        # Make a timestamp object
        self.timestamp = wb.utils.timestamp.Timestamp()

        # Attach the module used for this filesystem
        self.filelib = wb.utils.filesystem.__dict__.get(self.filesystem)

        # If there are files present in this folder which define the
        # properties of the dataset index, tool, or launcher,
        # read those files in and attach the data to the object
        self.read_configuration_files()

    def read_configuration_files(self):
        """Read in files associated with the dataset index, tool, and launcher."""

        # Read in the file (adding the prefix ._wb_), or assign
        # a null value if the file does not exist
        self.index = self.read_json("index.json")
        self.tool = self.read_json("tool_config.json")
        self.launcher = self.read_json("launcher_config.json")

    def read_json(self, fn):
        """
        Read in the file (adding the prefix ._wb_), or assign
        a null value if the file does not exist.
        """

        # Set up the path used for this asset
        fp = self.filepath(fn)

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
        fp = self.filepath(fn)

        # If the file exists
        if self.filelib.exists(fp):

            # Raise an error if overwrite is not True
            assert overwrite, f"File exists but overwrite was not set ({fp})"

        self.filelib.write_json(dat, fp, **kwargs)

    def filepath(self, filename, prefix="._wb_"):
        """Return the path to a file in the folder, adding a dedicated prefix."""
        return self.filelib.path_join(self.path, prefix + filename)

    def create_index(self, ix_type:str=None):
        """Add an index to a folder, can be either 'dataset' or 'collection'."""

        # Raise an error if there already is an index
        assert self.index is None, f"Already indexed, cannot overwrite ({self.path})"

        # ix_type can only be 'dataset' or 'collection'
        msg = "ix_type can only be 'dataset' or 'collection'"
        assert ix_type in ["dataset", "collection"]

        # Get the parent of this directory
        parent_dir = self.filelib.dirname(self.path)

        # Make a Dataset object, so that we can check if it has been indexed
        parent_dataset = Dataset(path=parent_dir)

        # The parent cannot be a dataset, since we cannot nest a
        # dataset or collection inside of a dataset
        msg = f"Cannot index a folder inside an existing dataset ({parent_dir})"
        assert parent_dataset.index is None or parent_dataset.index["type"] == "collection", msg

        # Create the index object, consisting of
        #  - the folder type (collection or dataset)
        #  - timestamp
        #  - unique identifier
        self.index = dict(
            uuid=str(uuid.uuid4()),
            type=ix_type,
            indexed_at=self.timestamp.encode(),
            name=self.path.rsplit("/", 1)[-1],
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

        # Write the params object to the appropriate path for the asset type
        self.write_json(
            f"{asset_type}_params.json",
            params,
            indent=indent,
            sort_keys=sort_keys,
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
        for subfolder in self.filelib.listdir(self.path):

            # Construct the complete path to the subfolder
            subfolder = self.filelib.abs_path(
                self.filelib.path_join(
                    self.path,
                    subfolder
                )
            )

            # If it is a directory
            if self.filelib.isdir(subfolder):

                # Get the index of the subfolder, if any exists
                ds = Dataset(subfolder)

                # If the subfolder has an index
                if ds.index is not None:

                    # Add the 'uuid' to the list
                    children_uuids.append(ds.index["uuid"])

        return children_uuids