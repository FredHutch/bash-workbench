from .folder_hierarchy import FolderHierarchyBase
from .dataset import Dataset

class Asset(FolderHierarchyBase):
    """
    Object used to access and manipulate the files associated with a 'tool' or 'launcher'
    from a particular repository.
    """

    # Each asset must contain a configuration (JSON) and run script (BASH)
    structure = [
        {"name": "config.json"},
        {"name": "run.sh"},
    ]

    # Do not create any subfolders (since these are files)
    create_subfolders = False

    def read_contents(self):
        """Read in the configuration file and validate that it is formatted correctly."""

        # Read in the JSON
        self.config = self.filelib.read_json(self.path("config.json"))

        # Get the asset type and name from the final folder names
        _, self.asset_type, self.name = self.base_path.rsplit("/", 2)

        # Add the "key" as the self.name
        self.config["key"] = self.name

        # Validate that the asset is configured correctly
        self.validate_config()

    def validate_config(self):
        """Validate that the tool or launcher is configured correctly"""

        # The asset must contain a handful of elements
        for key, value_type in [
            ("key", str),
            ("name", str),
            ("description", str),
            ("args", dict)
        ]:

            assert key in self.config, f"Asset configuration must contain key '{key}'"
            assert isinstance(self.config[key], value_type), f"{key} must be of type {value_type}, not {type(self.config[key])}"

    def copy_to_dataset(self, dataset:Dataset, overwrite=False):
        """Copy the files from an asset to a Dataset."""

        # All  of the files will be copied to the folder
        # {dataset}._wb/{self.asset_type}/

        # Create the folder if it does not exist
        dataset.setup_asset_folder(self.asset_type)

        # For each of the files associated with this asset
        for fn in self.listdir():

            # Get the path to the destination, inside the folder set up above
            dest_path = dataset.wb_path(self.asset_type, fn)

            # If a file already exists in the destination
            if self.filelib.exists(dest_path):

                # And the overwrite flag was not set, raise an error
                assert overwrite, f"Cannot copy {fn} to {dest_path} - file exists"

            # Get the full path to the source file
            fp = self.path(fn)

            # Otherwise, copy those files to the dataset folder
            self.log(f"Copying {fp} to {dest_path}")
            self.filelib.copyfile(fp, dest_path)
