from .asset import Asset
from typing import Dict
from .folder_hierarchy import FolderHierarchyBase
import git

AssetDict = Dict[str, Asset]

class Repository(FolderHierarchyBase):
    """Define the location of assets inside a repository."""

    # A repository will be complete (self.complete == True)
    # if it contains a folder named ._wb/
    structure = [
        {
            "name": "._wb"
        }
    ]
    create_subfolders = False

    def read_contents(self) -> None:
        """Read the configuration of all assets."""

        # Do not attempt to read the assets if ._wb/
        # does not exist
        if self.complete:

            # If any of the subfolders exist within ._wb/ with the
            # names 'tool' or 'launcher', read those as Assets
            self.assets = {
                asset_type: self.read_assets(asset_type=asset_type)
                for asset_type in ["tool", "launcher"]
            }

        # If ._wb/ does not exist
        else:

            # Create an empty dict
            self.assets = dict()

        # Try to set up a git object representing the contents of the repository,
        # if it is a valid git repository
        self.setup_repo()

    def read_assets(self, asset_type=None) -> AssetDict:
        """Read the assets present in a subfolder, if they exist."""

        assert asset_type is not None
        assert isinstance(asset_type, str)

        # Make a dict of assets
        asset_dict = dict()

        # If the folder exists
        if self.exists("._wb", asset_type):

            # Iterate over each subfolder
            for subfolder in self.listdir("._wb", asset_type):

                # Set up the asset
                asset = Asset(
                    base_path=self.path("._wb", asset_type, subfolder),
                    filelib=self.filelib,
                    logger=self.logger,
                    verbose=self.verbose
                )

                # If the asset is complete
                if asset.complete:

                    # add it to the dict
                    asset_dict[asset.name] = asset

        # Return the dict of assets
        return asset_dict

    def setup_repo(self):
        """Set up a git object representing the local repository, if it is valid."""

        # If the base path exists
        if self.exists(self.base_path):

            self.log(f"Local repository folder exists: {self.base_path}")

            # Try to set up the repository object
            try:

                self.log(f"Trying to read local repository")
                self.repo = git.Repo(self.base_path)
                self.log(f"Successfully read local repository")

            # If the repository is not set up
            except git.InvalidGitRepositoryError as e:

                self.log(f"Could not read repository ({str(e)}")

                # Set the repo object as null
                self.repo = None

        # If the base path does not exist
        else:

            self.log(f"Local folder does not exist: {self.base_path}")

            # Set the repo object as null
            self.repo = None

    def clone(
        self,
        repo_name:str=None,
        method:str="https",
        server:str="github.com"
    ):
        """Clone a remote repository to this folder."""

        # Make sure that the method is valid
        valid_methods = ["https", "ftps", "git", "ssh"]
        msg = f"method must be one of {', '.join(valid_methods)}, not {method}"
        assert method in valid_methods, msg

        # Set up the URL for the repository
        repo_url = f"{method}://{server}/{repo_name}"

        # Clone the repository
        self.log(f"Cloning repository from {repo_url} to {self.base_path}")
        self.repo = git.Repo.clone_from(
            repo_url,
            self.base_path
        )

        # Read the contents of the cloned repository
        self.read_contents()

        # Make sure that the repository is valid
        assert self.repo is not None, f"Error cloning repository '{repo_name}'"

    def pull(self):
        """Pull the most recent version of a repository."""

        assert self.exists(), "Cannot pull repository which has not yet been cloned."
        self.repo.git.pull()

    def switch_branch(self, branch_name, force=True):
        """Switch to a different branch."""

        self.repo.git.checkout(branch_name, force=force)

    def delete(self):
        """Delete a local copy of a repository."""

        self.log(f"Deleting local copy of repository: {self.base_path}")

        # If the base path is a symlink
        if self.filelib.islink(self.base_path):

            # Remove the link
            self.filelib.rm(self.base_path)

        # If the base path is not a list
        else:

            # Remove the entire directory
            self.filelib.rmdir(self.base_path)
