import gzip
import json
import os
import shutil
import textwrap


class FileLib:
    """Helper class used to interact with a file (or object storage) system."""

    def __init__(self, filesystem:str="local"):
        """Initialize the library of commands used to interact with the filesystem."""
        
        # Attach the type of filesystem being used
        self.filesystem = filesystem

        assert filesystem == "local", "The only filesystem currently supported is 'local'"

    def home(self) -> str:
        """Return the home directory for the user."""
        return os.path.expanduser("~")

    def exists(self, path) -> bool:
        """Path exists on the local filesystem."""
        return os.path.exists(path)

    def getsize(self, path) -> int:
        """Size of file object."""
        return os.path.getsize(path)

    def isdir(self, path) -> bool:
        """The path is a directory."""
        return os.path.isdir(path)

    def islink(self, path) -> bool:
        """The path is a link."""
        return os.path.islink(path)

    def makedirs(self, path) -> None:
        """Make a folder and all of its parents on the local filesystem."""
        os.makedirs(path)

    def mkdir_p(self, path) -> None:
        """Make a folder if it does not already exist, assert that it is a directory."""

        if not os.path.exists(path):
            os.makedirs(path)
        assert os.path.isdir(path), f"Must be a folder, not a file: {path}"

    def rmdir(self, path) -> None:
        """Delete a path (file or folder) and its contents, if any exist."""
        if os.path.exists(path):
            shutil.rmtree(path)

    def rm(self, path) -> None:
        """Delete a path, if it exists."""
        if os.path.exists(path):
            os.remove(path)

    def listdir(self, path) -> list:
        """List the contents of a directory."""
        return os.listdir(path)

    def path_join(self, *args) -> None:
        """Combine paths on the local filesystem."""
        return os.path.join(*args)

    def copyfile(self, source_path, dest_path, **kwargs) -> None:
        """Copy a file on the local filesystem."""
        shutil.copyfile(source_path, dest_path, **kwargs)

    def symlink(self, source, target) -> None:
        """Create a symlink."""
        os.symlink(source, target)

    def getcwd(self) -> str:
        """Return the current working directory."""
        return os.getcwd()

    def chdir(self, path:str) -> None:
        """Change working directories."""
        os.chdir(path)

    def read_json(self, path:str) -> dict:
        """Read a file in JSON format."""

        assert os.path.exists(path), f"Cannot read JSON, file does not exist {path}"

        if path.endswith(".gz"):

            with gzip.open(path, 'rt') as handle:
                return json.load(handle)

        else:

            with open(path, 'r') as handle:
                return json.load(handle)

    def write_json(self, dat, path, **kwargs) -> None:
        """Write a file in JSON format."""

        with open(path, mode='w') as handle:
            json.dump(dat, handle, **kwargs)

    def read_text(self, path:str) -> str:
        """Read a text file."""

        assert os.path.exists(path), f"Cannot read text, file does not exist {path}"

        if path.endswith(".gz"):

            with gzip.open(path, mode='rt') as handle:
                return handle.read()

        else:
            with open(path, mode='r') as handle:
                return handle.read()

    def write_text(self, dat, path) -> None:
        """Write a text file."""

        with open(path, 'w') as handle:
            handle.write(dat)

    def abs_path(self, path) -> str:
        """Return a path to a location which exists, is not a symlink, and has no terminal slash."""
        
        assert os.path.exists(path), f"Location does not exist: {path}"

        # If the path points to a link
        if os.path.islink(path):

            # Resolve the link
            path = os.readlink(path)

        assert not os.path.islink(path), "Cannot follow nested symlinks"

        # If there is a terminal slash in the pathname
        if path.endswith("/"):

            # Remove it
            path = path[:-1]

        # Resolve the absolute path
        path = os.path.abspath(path)

        return path

    def dirname(self, path) -> str:
        """Return the directory above a path."""

        return os.path.dirname(path)

    def navigate_text(self, path) -> str:
        """
        Advise the user how to manually inspect a directory.
        This text will be displayed whenever the workbench exits.
        """

        return textwrap.dedent(
            f"""
            To navigate to the last used working folder, run the command:
            cd {path}
            """
        )