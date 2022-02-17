import datetime
import json
import os


def setup_root_folder(base_folder=None, profile=None, logger=None):
    """Ensure that the root folder contains the required assets, and create them if necessary."""

    # The user must provide the base folder
    assert base_folder is not None, "Must provide base_folder"

    # The user must provide the profile
    assert profile is not None, "Must provide profile"

    # Construct the root folder from the base folder and profile
    root_folder = os.path.join(base_folder, profile)

    if logger is not None:
        logger.info(f"Setting up root folder at {root_folder}")

    # If the root folder does not exist
    if not os.path.exists(root_folder):

        # Create it
        os.makedirs(root_folder)
        if logger is not None:
            logger.info(f"Created {root_folder}")
    
    else:

        if logger is not None:
            logger.info(f"Exists {root_folder}")

    # For each of a series of subfolders
    for subfolder in ["data", "configs", "tools"]:

        # Construct the path for this subfolder inside the root folder
        fp = os.path.join(root_folder, subfolder)

        # If the path does not exist
        if not os.path.exists(fp):

            # Create it
            os.makedirs(fp)
            if logger is not None:
                logger.info(f"Created {fp}")

        else:
            if logger is not None:
                logger.info(f"Exists: {fp}")


def index_collection(
    path:str=None,
    base_folder:str=None,
    profile:str=None,
    logger=None
):
    """Add a collection index to a folder in the filesystem."""

    assert path is not None, "Must provide --path for folder to index"

    if logger is not None:
        logger.info(f"Preparing to index collection located at {path}")

    # Run the method which can be used to index either a collection or a collection
    _index_folder(
        ix_type="collection",
        path=path,
        base_folder=base_folder,
        profile=profile,
        logger=logger
    )


def index_dataset(
    path:str=None,
    base_folder:str=None,
    profile:str=None,
    logger=None
):
    """Add a dataset index to a folder in the filesystem."""

    assert path is not None, "Must provide --path for folder to index"

    if logger is not None:
        logger.info(f"Preparing to index dataset located at {path}")

    # Run the method which can be used to index either a collection or a dataset
    _index_folder(
        ix_type="dataset",
        path=path,
        base_folder=base_folder,
        profile=profile,
        logger=logger
    )

def _index_folder(
    ix_type:str=None,
    path:str=None,
    base_folder:str=None,
    profile:str=None,
    logger=None
):

    # ix_type can only be 'dataset' or 'collection'
    msg = "ix_type can only be 'dataset' or 'collection'"
    assert ix_type in ["dataset", "collection"]

    # Get the type assigned to this directory, if any.
    # Options are collection, dataset, folder, and file
    path_type = _get_path_type(path)

    # Raise an error if the path points to a file
    msg = f"Cannot index files, only folders ({path})"
    assert path_type != "file", msg

    # Raise an error if there already is an index
    msg = f"Already indexed as a {path_type} ({path})"
    assert path_type not in ["collection", "dataset"], msg

    # Get the parent of this directory
    parent_dir = _get_path_parent(path)

    # The parent cannot be a dataset, since we cannot nest a
    # dataset or collection inside of a dataset
    msg = f"Cannot index a folder inside an existing dataset ({parent_dir})"
    assert _get_path_type(parent_dir) != "dataset", msg

    # Create the index object, consisting of
    #  - the folder type (collection or dataset)
    #  - timestamp
    index = dict(
        type=ix_type,
        indexed_at=_timestamp().encode(),
        name=_sanitize_path(path).rsplit("/", 1)[-1],
        description=""
    )

    # Write it to the file
    _write_folder_index(path, index)
    
    if logger is not None:
        logger.info(f"Wrote out index for {path}")

    # Finally, link this dataset to the home folder if it is not already
    # nested below a collection which is similarly linked
    _add_to_home_tree(path=path, base_folder=base_folder, profile=profile, logger=logger)


def _add_to_home_tree(path=None, base_folder=None, profile=None, logger=None):
    """If a folder is not already contained in the home tree, add it."""

    assert path is not None, "Must provide --path of folder to add to home"
    assert base_folder is not None, "Must provide --base_folder of home directory"
    assert profile is not None, "Must provide --profile of home directory"

    # Resolve symlinks and remove any terminal slashes
    path = _sanitize_path(path)

    # Keep track of whether we've seen this path
    path_seen = False

    # Iterate over each of the folders in the home tree
    for wb_folder in _walk_home_tree(base_folder=base_folder, profile=profile):

        # If we come across this folder
        if wb_folder["abs_path"] == path:

            # Mark this path as seen
            path_seen = True

            # Break the loop
            break

    # If the path was found
    if path_seen:

        if logger is not None:
            logger.info(f"Path already contained in home tree ({path})")

    # If it was not found
    else:

        # Link the folder to the home directory
        _link_to_home(path=path, base_folder=base_folder, profile=profile)

        if logger is not None:
            logger.info(f"Link for path added to home tree ({path})")


def _walk_home_tree(base_folder=None, profile=None):
    """Walk through all of the indexed folders which are linked anywhere within the home folder."""

    assert base_folder is not None, "Must provide --base_folder of home directory"
    assert profile is not None, "Must provide --profile of home directory"

    # Keep track of all of the folders which we've found before
    seen_folders = set()

    # Keep a list of folders that we need to walk through
    folders_to_check = list()

    # To start, add the home folder to the list of folders to check
    folders_to_check.append(
        os.path.join(base_folder, profile)
    )

    # Iterate while there are folders remaining to check
    while len(folders_to_check) > 0:

        # Get a folder to check, removing it from the list
        folder_to_check = folders_to_check.pop()

        # Iterate over each path within it
        for subpath in os.listdir(folder_to_check):

            # Construct the full path
            subpath = _sanitize_path(os.path.join(folder_to_check, subpath))

            # If the folder is a dataset or collection
            if _path_is_indexed(subpath):

                # If we've already seen it, there is some circular link which
                # must be resolved by the user
                msg = f"Encountered circular link: user must resolve (re: {subpath})"
                assert subpath not in seen_folders, msg

                # Add the subpath to the set of seen folders
                seen_folders.add(subpath)

                # Emit this path
                yield subpath

                # Add the subpath to the list of paths to check next
                folder_to_check.append(subpath)


def _links_from_home_directory(base_folder=None, profile=None):
    """Return the list of folders which are linked from the home data directory."""

    assert profile is not None, "Must provide --profile of home directory"
    assert base_folder is not None, "Must provide --base_folder of home directory"

    # Assemble the path to the home data directory
    data_home = os.path.join(base_folder, profile, "data")

    # Make a list of the linked folders
    linked_folders = list()

    # Iterate over the files in this folder
    for fp in os.listdir(data_home):

        # Construct the full path to each file
        fp = os.path.join(data_home, fp)

        # If the file is a symlink
        if os.path.islink(fp):

            # Add the target to the list
            linked_folders.append(
                _sanitize_path(
                    os.readlink(
                        fp
                    )
                )
            )

    # Return the list of all folders which are linked
    return linked_folders


def _link_to_home(path=None, base_folder=None, profile=None):
    """Add a symlinnk of a path to the home directory."""

    assert path is not None, "Must provide --path of folder to link to home"
    assert base_folder is not None, "Must provide --base_folder of home directory"
    assert profile is not None, "Must provide --profile of home directory"

    # Resolve symlinks and remove any terminal slashes
    path = _sanitize_path(path)

    # If there is a link to this folder already in the home directory
    if path in _links_from_home_directory(base_folder=base_folder, profile=profile):

        # No need to take any further action
        return

    # Get the folder name
    folder_name = path.rsplit("/", 1)[1]

    # Get the path to the symlink
    home_symlink = os.path.join(
        base_folder,
        profile,
        "data",
        folder_name
    )

    # To prevent collisions, add a suffix to make it unique (if not already)
    n = 0
    while os.path.exists(home_symlink):

        # Increment the counter to make a new suffix
        n += 1

        # Make a new the path to the symlink
        home_symlink = os.path.join(
            base_folder,
            profile,
            f"{folder_name}_{n}"
        )

    # Add a symlink
    os.symlink(path, home_symlink)


def _sanitize_path(path):
    """Return a path to a location which exists, is not a symlink, and has no terminal slash."""
    
    assert os.path.exists(path), f"Location does not exist: {path}"

    # If the path points to a link
    if os.path.islink(path):

        # Resolve the link
        path = os.readlink(path)

    # If there is a terminal slash in the pathname
    if path.endswith("/"):

        # Remove it
        path = path[:-1]

    # Resolve the absolute path
    path = os.path.abspath(path)

    return path


def _path_is_indexed(path):
    """Return a bool indicating if the path is a dataset or collection."""

    # While it's silly to have a one-line function, this keeps us from having
    # to copy and paste ["dataset", "collection"] and potentially introduce a typo
    return _get_path_type(path) in ["dataset", "collection"]


def _get_path_type(path):
    """
    Parse the location and contents of a path to return its time:
        - collection: a folder which has been indexed as a collection
        - dataset: a folder which has been indexed as a dataset
        - folder: a folder which has not been indexed
        - file: a file (which inherently cannot be indexed)
    """

    # Resolve symlinks, assert existance, trim terminal slashes
    path = _sanitize_path(path)

    # If the path does not point to a directory
    if not os.path.isdir(path):

        # It must be a file
        return 'file'

    # If it is a directory
    else:

        # Get the index, if any exists
        path_ix = _read_folder_index(path)

        # If no index exists
        if path_ix is None:

            # Then it is a 'folder'
            return 'folder'

        # If an index does already exist
        else:

            # The index must contain a 'type' field
            msg = f"Index unexpectedly does not contain a 'type' field ({path})"
            assert 'type' in path_ix, msg

            # The type may be 'collection' or 'dataset'
            msg = f"Index type may be collection or dataset, not '{path_ix['type']}'"
            assert path_ix['type'] in ['collection', 'dataset'], msg

            # Return the type
            return path_ix['type']


def _get_path_parent(path):
    """Return the directory above a path."""

    # Resolve symlinks, assert existance, trim terminal slashes
    path = _sanitize_path(path)

    # Return the path to the folder which contains this path
    return os.path.dirname(path)


def _read_folder_index(path):
    """Return the index information for a folder, if any exists."""

    assert os.path.isdir(path), f"Cannot read index from non-folder {path}"

    # The path to the index is canonical
    ix_path = _map_wb_file_path(path, "index.json")

    # If the file does not exist
    if not os.path.exists(ix_path):

        # Return a null value
        return

    # If the file does exist
    else:

        # Read in the contents of the file
        with open(ix_path, "r") as handle:

            # Note that this will raise an error if the
            # file is not in JSON format.
            # This behavior is intentional, because the
            # format of this file should always be JSON.
            json.load(handle)


def _write_folder_index(path, dat, overwrite=False, indent=4):
    """Write the index information for a folder in-place."""

    assert os.path.isdir(path), f"Cannot read index from non-folder {path}"

    # The path to the index is canonical
    ix_path = _map_wb_file_path(path, "index.json")

    # If we have not been directed to overwrite the file
    if not overwrite:

        # Then the file may not already exist
        msg = f"{ix_path} exists (use overwrite=True)"
        assert not os.path.exists(ix_path), msg
    
    # Open a file handle
    with open(ix_path, "w") as handle:

        # Encode the data as JSON
        json.dump(dat, handle, indent=indent)


class _timestamp():
    """Encode / decode a date and time to / from string format."""

    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %Z"):
        
        self.fmt = fmt

    def encode(self):
        """Return a string representation of the current date and time."""

        # Current date and time
        now = datetime.datetime.now(datetime.timezone.utc)

        # Return a string formatted using the pattern shown above
        return now.strftime(self.fmt)

    def decode(self, timestamp_str):
        """Return the date and time represented by a string."""

        return datetime.strptime(timestamp_str, self.fmt)


def _map_wb_file_path(folder, filename, workbench_prefix="._wb_"):
    """All Workbench files share a common prefix to prevent collision."""

    # The only real utility of this formulation is to prevent
    # needless copying of the prefix "._wb_" in the library code
    return os.path.join(folder, workbench_prefix + filename)

