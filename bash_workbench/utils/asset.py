class Asset:
    """Object used to access and manipulate the files associated with a 'tool' or 'launcher'."""

    def __init__(self, WB=None, asset_type=None, asset_name=None):

        assert WB is not None, "Must provide WB=Workbench()"
        assert asset_type is not None, "Must provide asset_type"
        assert asset_name is not None, "Must provide asset_name"

        # Attach the provided objects to the instance
        self.WB = WB
        self.asset_type = asset_type
        self.name = asset_name

        # Get the path to the asset directory
        self.path = self.WB.filelib.path_join(
            self.WB._top_level_folder(asset_type),
            asset_name
        )

        # Get the path to the config JSON
        self.config_fp = self.WB.filelib.path_join(
            self.path,
            "config.json"
        )

        # The config file must exist
        self.log(f"Reading configuration from {self.config_fp}")
        assert self.WB.filelib.exists(self.config_fp)

        # Read in the config
        self.read_config()

    def read_config(self):
        """Read in the configuration file and validate that it is formatted correctly."""

        # Read in the JSON
        self.config = self.WB.filelib.read_json(self.config_fp)

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

    def log(self, msg):
        """Emit a logging message with a prefix describing this asset."""
        self.WB.log(f"[{self.asset_type}: {self.name}] {msg}")

    def file_path(self, filename):
        """Return the full path to a file in the asset folder."""

        return self.WB.filelib.path_join(self.path, filename)

    def list_files(self):
        """Return a list of the files present in the asset folder."""

        return [
            fn
            for fn in self.WB.filelib.listdir(self.path)
        ]

    def copy_to_dataset(self, dataset, overwrite=False):
        """Copy the files from an asset to a Dataset."""

        # All  of the files will be copied to the folder
        # {dataset.wb_folder}/{self.asset_type}/
        dest_folder = self.WB.filelib.path_join(dataset.wb_folder, self.asset_type)

        # Create the folder if it does not exist
        dataset.setup_asset_folder(self.asset_type)

        # For each of the files associated with this asset
        for fn in self.list_files():

            # Get the path to the destination, inside the folder set up above
            dest_path = self.WB.filelib.path_join(dest_folder, fn)

            # If a file already exists in the destination
            if self.WB.filelib.exists(dest_path):

                # And the overwrite flag was not set, raise an error
                assert overwrite, f"Cannot copy {fn} to {dest_path} - file exists"

            # Get the full path to the source file
            fp = self.WB.filelib.path_join(self.path, fn)

            # Otherwise, copy those files to the dataset folder
            self.log(f"Copying {fp} to {dest_path}")
            self.WB.filelib.copyfile(fp, dest_path)
