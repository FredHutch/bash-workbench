import git

class Repository:
    """Class used to manage local copies of GitHub repositories."""

    def __init__(
        self,
        name:str=None,
        home_folder:str=None,
        filelib=None,
        method:str="https",
        logger=None,
        verbose:bool=False
    ):
        """Instantiate a repository."""

        assert name is not None, "Must provide `name`"
        assert home_folder is not None, "Must provide `home_folder`"
        assert filelib is not None, "Must provide `filelib`"

        self.verbose = verbose
        
        # Make sure that the method is valid
        valid_methods = ["https", "ftps", "git", "ssh"]
        assert method in valid_methods, f"method must be one of {', '.join(valid_methods)}, not {method}"
        self.method = method

        # Store the name of the repo
        self.name = name

        # The repository name must be of the format ORG/REPO
        msg = "Repository name must have the format ORG/REPO"
        assert "/" in name, msg
        assert " " not in name, msg
        assert len(name.split("/")) == 2

        # Attach the library used for manipulating the filesystem
        self.filelib = filelib

        # Format the local folder name by removing the '/' and making everything lowercase
        self.base_path = self.filelib.path_join(
            home_folder, "repositories", name
        )

        # Attach the logger
        self.logger = logger

        # Set up the repository, if it is present
        self.setup_repo()

    def log(self, msg):
        """Print a logging message using the logger if available, and the screen if `verbose`."""

        if self.logger is not None:
            self.logger.info(msg)

        if self.verbose:
            print(msg)

    def setup_repo(self):
        """Set up the local repository, if it exists."""

        # If the base path exists
        if self.filelib.exists(self.base_path):

            self.log(f"Local repository folder exists: {self.base_path}")

            # Try to set up the repository object
            try:

                self.log(f"Trying to read local repository")
                self.repo = git.Repo(self.base_path)

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

    def exists(self):
        """Return True if a valid GitHub repository has been cloned at the expected location."""

        return self.repo is not None

    def clone(self):
        """Clone a repository to the local folder."""

        # The repository may not already exist
        assert not self.exists(), f"Cannot clone repository -- already exists({self.base_path})"

        # If the folder does not already exist, create it
        self.filelib.mkdir_p(self.base_path)

        # Set up the URL for the repository
        repo_url = f"{self.method}://github.com/{self.name}"

        # Clone the repository
        self.log(f"Cloning repository from {repo_url} to {self.base_path}")
        self.repo = git.Repo.clone_from(
            repo_url,
            self.base_path
        )

    def pull(self):
        """Pull the most recent version of a repository."""

        assert self.exists(), "Cannot pull repository which has not yet been cloned."
        self.repo.git.pull()

    def switch_branch(self, branch_name, force=True):
        """Switch to a different branch."""

        self.repo.git.checkout(branch_name, force=force)

    def delete(self):
        """Delete a local copy of a repository."""

        self.log(f"Deleting local copy of repository: {self.name}")

        # If the folder exists
        if self.filelib.exists(self.base_path):

            # Delete it
            self.log(f"Deleting local folder: {self.base_path}")
            self.filelib.rmdir(self.base_path)

        else:

            self.log(f"Folder does not exist: {self.base_path}")