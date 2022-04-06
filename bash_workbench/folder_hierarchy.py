from .filelib import FileLib

class FolderHierarchyBase:
    """
    Generic class to organize a data structure defined as a hierarchy of file objects.
    """

    # Class attribute intended to be overridden which
    # defines the hierarchy of folders expected beneath
    # the base path
    structure = list()

    # Flag determining whether subfolders should be created, or whether the entire
    # asset should just be marked incomplete when a folder is not found
    create_subfolders = True

    def __init__(
        self,
        # Library used to interact with the filesystem
        filelib:FileLib=None,
        # Base path
        base_path:str=None,
        # Logging instance
        logger=None,
        # Logging level
        verbose:bool=False
    ) -> None:

        # Attach the filelib
        assert filelib is not None
        self.filelib = filelib

        # Attach the base path
        assert base_path is not None
        self.base_path = base_path

        # Attach the logger
        self.logger = logger

        # Attach the verbosity level
        assert isinstance(verbose, bool), "verbose must be a bool"
        self.verbose = verbose

        # The file system is assumed complete until proven otherwise
        # self.complete will be marked False if an expected subfolder
        # is not present, and `create_subfolders` is False
        self.complete = True

        # Check to see if the folders exist
        self.check_folders()

        # As the final step of initiating the object, invoke read_contents()
        self.read_contents()

    def log(self, msg:str) -> None:
        """Print a logging message using the logger if available, and the screen if `verbose`."""

        if self.logger is not None:
            self.logger.info(msg)

        if self.verbose:
            print(msg)

    def check_folders(self) -> None:
        """Check to see if the subfolders exist, creating them if specified."""

        # The `structure` object must be a list of dicts, each
        # with a 'name' and an optional 'children' which would
        # contain another list of dicts
        assert isinstance(self.structure, list), "structure must be a list"

        # Recursively check each subfolder, starting with the top-level
        for folder in self.structure:
            self.check_folders_recursive(
                base_path=self.base_path,
                folder=folder
            )

    def populate_folders(self) -> None:
        """Add all of the folders expected within a structure, if they do not exist."""
        
        # Update the variable which determines that subfolders should be created
        self.create_subfolders = True

        # Create any subfolders which do not exist
        self.check_folders()

    def check_folders_recursive(
        self,
        base_path:str=None,
        folder:dict=None
    ) -> None:
        """Check to see if a subfolder exists."""

        # Each folder is a dict
        assert isinstance(folder, dict), f"Each folder must be a dict ({folder})"

        # The folder must have a name
        assert "name" in folder, f"Each folder must have a 'name' ({folder})"

        # The name must be a string
        assert isinstance(folder["name"], str), f"Each folder's name must be a string ({folder['name']})"

        # Construct the path to this folder
        folder_path = self.filelib.path_join(base_path, folder["name"])

        # If the folder does not exist
        if not self.filelib.exists(folder_path):

            # If it can be created
            if self.create_subfolders:

                # Create it
                self.log(f"Creating {folder_path}")
                self.filelib.makedirs(folder_path)

            # If it cannot be created
            else:

                self.log(f"Does not exist: {folder_path}")

                # Mark this asset as incomplete
                self.complete = False

            # If any children were defined
            if "children" in folder:

                # The children must be a list
                msg = f"Children of each folder must be a list ({folder['children']})"
                assert isinstance(folder["children"], list), msg

                # Recursively check those subfolders
                for child in folder["children"]:

                    self.check_folders_recursive(
                        base_path=folder_path,
                        folder=child
                    )

        # If the folder does exist
        else:

            self.log(f"Folder exists: {folder_path}")

    def path(self, *subfolder_list) -> str:
        """Return the absolute path to a subfolder."""

        return self.filelib.path_join(
            self.base_path,
            *list(subfolder_list)
        )

    def read_json(self, *subfolder_list):

        return self.filelib.read_json(
            self.path(*subfolder_list)
        )

    def read_text(self, *subfolder_list) -> str:

        return self.filelib.read_text(
            self.path(*subfolder_list)
        )

    def exists(self, *subfolder_list) -> bool:
        """Check whether a subfolder (or file) exists."""

        return self.filelib.exists(self.path(*subfolder_list))

    def listdir(self, *subfolder_list) -> list:
        """List the contents of a subfolder."""

        return self.filelib.listdir(self.path(*list(subfolder_list)))

    def read_contents(self) -> None:
        """
        Parses the contents of files within the subfolders.
        This function is invoked even if not all elements in the file hierarchy are present.
        Intended to be overridden by child classes.
        """

        pass
