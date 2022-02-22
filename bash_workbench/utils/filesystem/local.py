from distutils.command.config import config
import json
import os
import shutil
import uuid


def setup_root_folder(WB):
    """Ensure that the root folder contains the required assets, and create them if necessary."""

    WB.log(f"Setting up root folder at {WB.home_folder}")

    # If the root folder does not exist
    if not os.path.exists(WB.home_folder):

        # Create it
        os.makedirs(WB.home_folder)
        WB.log(f"Created {WB.home_folder}")
    
    else:

        WB.log(f"Exists {WB.home_folder}")

    # For each of a series of subfolders
    for subfolder in ["data", "launchers", "tools", "helpers"]:

        # Construct the path for this subfolder inside the root folder
        fp = os.path.join(WB.home_folder, subfolder)

        # If the path does not exist
        if not os.path.exists(fp):

            # Create it
            os.makedirs(fp)
            WB.log(f"Created {fp}")

        else:
            WB.log(f"Exists: {fp}")

    # Provide each of the tools and launchers defined in the repository,
    # if they do not already exist
    update_base_toolkit(WB, overwrite=False)

def index_collection(
    WB,
    path:str=None
):
    """Add a collection index to a folder in the filesystem."""

    assert path is not None, "Must provide --path for folder to index"

    WB.log(f"Preparing to index collection located at {path}")

    # Run the method which can be used to index either a collection or a collection
    return _index_folder(
        WB,
        ix_type="collection",
        path=path
    )


def index_dataset(
    WB,
    path:str=None
):
    """Add a dataset index to a folder in the filesystem."""

    assert path is not None, "Must provide --path for folder to index"

    WB.log(f"Preparing to index dataset located at {path}")

    # Run the method which can be used to index either a collection or a dataset
    return _index_folder(
        WB,
        ix_type="dataset",
        path=path
    )


def _index_folder(
    WB,
    ix_type:str=None,
    path:str=None
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
    #  - unique identifier
    index = dict(
        uuid=str(uuid.uuid4()),
        type=ix_type,
        indexed_at=WB.timestamp.encode(),
        name=_sanitize_path(path).rsplit("/", 1)[-1],
        description=""
    )

    # Write it to the file
    _write_folder_index(path, index)
    
    WB.log(f"Wrote out index for {path}")

    # Finally, link this dataset to the home folder if it is not already
    # nested below a collection which is similarly linked
    _add_to_home_tree(WB, path=path)

    return index


def _add_to_home_tree(WB, path=None):
    """If a folder is not already contained in the home tree, add it."""

    assert path is not None, "Must provide --path of folder to add to home"
    assert WB.base_folder is not None, "Must provide --base_folder of home directory"
    assert WB.profile is not None, "Must provide --profile of home directory"

    # Resolve symlinks and remove any terminal slashes
    path = _sanitize_path(path)

    WB.log(f"Making sure that folder is present in home tree: {path}")

    # Keep track of whether we've seen this path
    path_seen = False

    # Iterate over each of the folders in the home tree
    for wb_folder in _walk_home_tree(WB):

        # If we come across this folder
        if wb_folder == path:

            # Mark this path as seen
            path_seen = True

            # Break the loop
            break

    # If the path was found
    if path_seen:

        WB.log(f"Path already contained in home tree ({path})")

    # If it was not found
    else:

        # Link the folder to the home directory
        _link_to_home(WB, path=path)

        WB.log(f"Link for path added to home tree ({path})")


def _walk_home_tree(WB):
    """Walk through all of the indexed folders which are linked anywhere within the home folder."""

    # Keep track of all of the folders which we've found before
    seen_folders = set()

    # Keep a list of folders that we need to walk through
    folders_to_check = list()

    # To start, add the home folder to the list of folders to check
    folders_to_check.append(WB._top_level_folder("data"))

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
                yield os.path.abspath(subpath)

                # Add the subpath to the list of paths to check next
                folders_to_check.append(subpath)


def _links_from_home_directory(WB):
    """Return the list of folders which are linked from the home data directory."""

    # Assemble the path to the home data directory
    data_home = WB._top_level_folder("data")

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


def _link_to_home(WB, path=None):
    """Add a symlinnk of a path to the home directory."""

    # Resolve symlinks and remove any terminal slashes
    path = _sanitize_path(path)

    # If there is a link to this folder already in the home directory
    if path in _links_from_home_directory(WB):

        # No need to take any further action
        return

    # Get the folder name
    folder_name = path.rsplit("/", 1)[1]

    # Get the path to the symlink
    home_symlink = WB._top_level_folder(f"data/{folder_name}")

    # To prevent collisions, add a suffix to make it unique (if not already)
    n = 0
    while os.path.exists(home_symlink):

        # Increment the counter to make a new suffix
        n += 1

        # Make a new the path to the symlink
        home_symlink = WB._top_level_folder(f"{folder_name}_{n}")

    # Add a symlink
    os.symlink(path, home_symlink)


def _sanitize_path(path):
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
            ix = json.load(handle)

        # Make sure that the index has a uuid and a type
        for k in ["uuid", "type"]:
            assert k in ix, f"Missing key ({k}) in index {ix_path}"

        return ix


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


def _map_wb_file_path(folder, filename, workbench_prefix="._wb_"):
    """All Workbench files share a common prefix to prevent collision."""

    # The only real utility of this formulation is to prevent
    # needless copying of the prefix "._wb_" in the library code
    return os.path.join(folder, workbench_prefix + filename)


def show_datasets(
    WB,
    show_tree=False
):
    """Print a list of all datasets linked from the home folder."""

    # Get the list of all datasets linked from the home folder
    datasets = _list_datasets(WB)

    # If the tree representation was requested
    if show_tree:

        # Print the tree
        _print_dataset_tree(datasets)

    # Otherwise
    else:

        # Return the list of datasets found
        return datasets


def _print_dataset_tree(datasets):
    """Print the list of datasets as a tree."""

    # Find the uuids of all datasets which do not have parents
    root_datasets = [
        dataset["uuid"]
        for dataset in datasets.values()
        if dataset.get("parent") is None
    ]

    # Recursively print each of those datasets
    _print_dataset_tree_recursive(root_datasets, datasets)
    

def _print_dataset_tree_recursive(dataset_uuids, datasets_dict, indentation=""):
    """Function to recursively print the directory structure."""

    # Get the number of datasets in the list
    dataset_n = len(dataset_uuids)

    # For each dataset, set the `list_position` as 'single', 'first', 'middle', or 'last'
    # Also set the flag `has_children` as True/False

    # Iterate over each dataset
    for dataset_i, dataset_uuid in enumerate(dataset_uuids):

        # If this dataset is a singlet
        if dataset_n == 1:
            list_position = "single"

        # If there are multiple datasets, and this is the first one
        elif dataset_i == 0:
            list_position = "first"

        # If this is the last one in the list
        elif dataset_i == dataset_n - 1:
            list_position = "last"

        # Otherwise, we are in the middle of a list
        else:
            list_position = "middle"

        # Mark whether this dataset has children
        has_children = len(datasets_dict[dataset_uuid].get("children", [])) > 0

        # Print the dataset information with the specified prefix
        _print_dataset_tree_single(
            datasets_dict[dataset_uuid],
            indentation=indentation,
            list_position=list_position,
            has_children=has_children
        )

        # Recursively repeat the process for any children of this dataset
        _print_dataset_tree_recursive(
            datasets_dict[dataset_uuid].get("children", []),
            datasets_dict,
            # If this dataset is followed by others in this group
            # Add a continuation character to the indentation
            # Otherwise, there are no more in this group, and so the indentation is blank
            indentation=indentation + "  │" if list_position in ["first", "middle"] else "   "
        )


def _print_dataset_tree_single(
    dataset_info,
    indentation="",
    list_position=None,
    has_children=None
):

    name_prefix = dict(
        single=" └─",
        first=" └┬",
        last="  └",
        middle="  ├"
    )[list_position]

    # Print the name of the dataset
    print(f"{indentation}{name_prefix} {dataset_info['name']}")

    # Make a separate prefix for any additional lines
    # If there are more items in the list, add a continuation
    addl_prefix = "  │" if list_position in ["first", "middle"] else "   "

    # Add another continuation if there are children below this dataset
    addl_prefix = f'{addl_prefix}{" │" if has_children else "  "}'

    # Print the uuid and any additional fields
    fields = [
        f"uuid: {dataset_info['uuid']}",
        f"path: {dataset_info['path']}",
    ]

    # If there is a description
    if len(dataset_info['description']) > 0:
        fields.append(f"description: {dataset_info['description']}")

    # If there are tags
    if len(dataset_info.get("tags", {})) > 0:
        for k, v in dataset_info["tags"].items():
            fields.append(f"tag: {k} = {v}")

    fields.append("")
    for field in fields:
        print(f"{indentation}{addl_prefix}  {field}")
    

def _list_datasets(WB):
    """Return the list of all datasets and collections linked from the home folder."""

    # Get the list of all folders which are linked under the home directory and have an index
    datasets = list(_walk_home_tree(WB))

    # Get the details for each one, and add information about each subfolder
    dataset_info = [
        dict(
            path=fp,
            children=_list_children(fp),
            **_read_folder_index(fp)
        )
        for fp in datasets
    ]

    # Format datasets as a dict, keyed by uuid
    dataset_info = {
        dataset["uuid"]: dataset
        for dataset in dataset_info
    }

    # Add the parent information to the dataset field
    # Iterate over each dataset
    for dataset_uuid in dataset_info:

        # Iterate over its children
        for child_uuid in dataset_info[dataset_uuid]["children"]:

            # Add the dataset uuid to the 'parent' field in the child
            dataset_info[child_uuid]["parent"] = dataset_uuid

    WB.log(f"Found {len(dataset_info):,} indexed folders")

    return dataset_info


def _list_children(fp):
    """Return a list with the uuid's of any indexed folders inside this one."""

    children_uuids = list()

    # Iterate over all of the paths inside this folder
    for subfolder in os.listdir(fp):

        # Construct the complete path to the subfolder
        subfolder = _sanitize_path(os.path.join(fp, subfolder))

        # If it is a directory
        if os.path.isdir(subfolder):

            # Get the index of the subfolder, if any exists
            subfolder_ix = _read_folder_index(subfolder)

            # If the subfolder has an index
            if subfolder_ix is not None:

                # Add the 'uuid' to the list
                children_uuids.append(subfolder_ix["uuid"])

    return children_uuids


def change_name(
    WB,
    uuid=None,
    path=None,
    name=None,
):
    """Modify the name of a folder (dataset or collection)."""

    return _change_folder_attribute(
        WB,
        uuid=uuid,
        path=path,
        key="name",
        # The `name` will be provided as a list (broken on whitespaces)
        value=" ".join(name)
    )


def change_description(
    WB,
    uuid=None,
    path=None,
    description=None,
):
    """Modify the description of a folder (dataset or collection)."""

    return _change_folder_attribute(
        WB,
        uuid=uuid,
        path=path,
        key="description",
        # The `description` will be provided as a list (broken on whitespaces)
        value=" ".join(description)
    )


def _find_folder(
    WB,
    uuid=None,
    path=None
):
    """Find the dataset using either the path or uuid (not both)"""

    msg = "Must provide either uuid or path to indicate dataset"
    assert uuid is not None or path is not None, msg

    msg = "Must provide either uuid or path to indicate dataset, but not both"
    assert uuid is None or path is None, msg

    # First try finding the folder by path
    if path is not None:

        # Get the type of object this points to
        path_type = _get_path_type(path)

        # If the user specified a folder which is not yet indexed
        msg = f"The indicated folder is not yet indexed ({path})"
        assert path_type != "folder", msg

        # If the user specified a file, and not a folder
        msg = f"Please specify a folder, not a file ({path})"
        assert path_type != "folder", msg

        # At this point, the path must be a dataset or collection
        assert path_type in ["dataset", "collection"], f"Unrecognized: {path_type}"

        # Read in the index for the folder
        ix = _read_folder_index(path)

    # Otherwise, try finding by uuid
    else:

        assert uuid is not None

        path, ix = _find_folder_by_uuid(WB, uuid=uuid)

    return path, ix


def _change_folder_attribute(
    WB,
    uuid=None,
    path=None,
    key=None,
    value=None
):
    """Modify the attribute of a folder."""

    # Find the dataset using either the path or uuid (not both)
    path, ix = _find_folder(
        WB,
        uuid=uuid,
        path=path
    )

    # At this point, `path` contains the folder location with the index
    # object `ix` that has 'uuid' set to `uuid`

    WB.log(f"Found dataset {ix['uuid']} at {path}")
    
    # Update the attribute
    WB.log(f"Changing {key} to {value}")
    ix[key] = value

    # Save the index
    WB.log("Saving index")
    _write_folder_index(path, ix, overwrite=True)

    return ix

        
def update_tag(
    WB,
    uuid=None,
    path=None,
    key=None,
    value=None
):
    """Modify the value of a tag applied to a folder."""

    # Find the dataset using either the path or uuid (not both)
    path, ix = _find_folder(
        WB,
        uuid=uuid,
        path=path
    )

    # At this point, `path` contains the folder location with the index
    # object `ix` that has 'uuid' set to `uuid`

    WB.log(f"Found dataset {ix['uuid']} at {path}")

    # Make sure that there is a dict of "tags" in the index
    ix["tags"] = ix.get("tags", dict())

    assert isinstance(ix["tags"], dict), "Index entry 'tags' must be a dict"
    
    # Update the attribute
    WB.log(f"Changing tag {key} to {value}")
    ix["tags"][key] = value

    # Save the index
    WB.log("Saving index")
    _write_folder_index(path, ix, overwrite=True)

    # Return the updated index
    return ix


def delete_tag(
    WB,
    uuid=None,
    path=None,
    key=None
):
    """Delete the value of a tag applied to a folder, if it exists."""

    # Find the dataset using either the path or uuid (not both)
    path, ix = _find_folder(
        WB,
        uuid=uuid,
        path=path
    )

    # At this point, `path` contains the folder location with the index
    # object `ix` that has 'uuid' set to `uuid`

    WB.log(f"Found dataset {ix['uuid']} at {path}")

    # Make sure that there is a dict of "tags" in the index
    ix["tags"] = ix.get("tags", dict())

    assert isinstance(ix["tags"], dict), "Index entry 'tags' must be a dict"
    
    # If the tag is present
    if key in ix["tags"]:

        # Delete it
        WB.log(f"Deleting tag {key}")

        del ix["tags"][key]

    else:
        WB.log(f"Tag {key} is not set")

    # Save the index
    WB.log("Saving index")
    _write_folder_index(path, ix, overwrite=True)

    # Return the updated index
    return ix

def _find_folder_by_uuid(
    WB,
    uuid=None
):
    assert uuid is not None, "Must provide uuid"

    # Walk through all of the indexed folders in the home tree
    found_path = False
    for path in _walk_home_tree(WB):

        # Read the index
        ix = _read_folder_index(path)

        # If the uuid is a match
        if ix["uuid"] == uuid:

            # Indicate that we found the path
            found_path = True

            # And stop looking
            break

    assert found_path, f"Could not find any dataset with uuid={uuid}"

    return path, ix


def find_datasets(
    WB,
    name=None,
    description=None,
    tag=None,
    show_tree=False
):
    """Find any datasets which match the provided queries."""

    # The user must specify a query for one of name, description, or tag
    msg = "Specify a query term for one of name, description, or tag"
    assert name is not None or description is not None or tag is not None, msg

    # Get the list of all datasets linked from the home folder
    datasets = _list_datasets(WB)

    # If a query name was provided
    if name is not None:

        # If the name is provided as a list, collapse it into a string
        if isinstance(name, list):
            name = " ".join(name)

        WB.log(f"Querying datasets by name={name}")

        # Only keep folders which match this query, or their parent collections
        datasets = _filter_datasets(datasets, field="name", value=name)

    # If a query description was provided
    if description is not None:

        # If the description is provided as a list, collapse it into a string
        if isinstance(description, list):
            description = " ".join(description)

        WB.log(f"Querying datasets by description={description}")

        # Only keep folders which match this query, or their parent collections
        datasets = _filter_datasets(datasets, field="description", value=description)

    # If a query tag was provided
    if tag is not None:

        # If the tag is not a list, make a list of 1
        if not isinstance(tag, list):
            tag = [tag]

        # Iterate over the multiple tags which may have been provided
        for tag_item in tag:

            WB.log(f"Querying datasets by tag {tag_item}")

            # Only keep folders which match this query, or their parent collections
            datasets = _filter_datasets(datasets, field="tag", value=tag_item)

    WB.log(f"Number of datasets matching query: {len(datasets):,}")

    # If the tree representation was requested
    if show_tree:

        # Print the tree
        _print_dataset_tree(datasets)

    # Otherwise
    else:

        # Return the list of datasets found
        return datasets


def _filter_datasets(datasets, field=None, value=None):
    """Filter by a single query term."""

    # For tags, the 'value' must be "{key}={value}"
    if field == "tag":

        msg = "To filter by tag, provide query in the format 'key=value'"
        assert "=" in value, msg
        assert value.endswith("=") is False, msg

        # parse the tag key and value
        key, value = value.split("=", 1)

        # Get the list of uuids for datasets which contain this term
        matching_uuids = [
            dataset_uuid
            for dataset_uuid, dataset in datasets.items()
            if dataset.get("tags", {}).get(key) == value
        ]

    # For all other query fields
    else:

        # Get the list of uuids for datasets which contain this term
        matching_uuids = [
            dataset_uuid
            for dataset_uuid, dataset in datasets.items()
            if value in dataset[field]
        ]

    # Make a set of datasets to keep
    to_keep = set()

    # For each of the matching uuids
    for dataset_uuid in matching_uuids:

        # Iterate over the chain of parents back to the root
        while dataset_uuid is not None:

            # Add it to the set
            to_keep.add(dataset_uuid)

            # Move to the parent
            dataset_uuid = datasets[dataset_uuid].get("parent")

    # Keep the datasets which are in this path
    datasets = {
        dataset_uuid: dataset
        for dataset_uuid, dataset in datasets.items()
        if dataset_uuid in to_keep
    }

    # Update the 'children' field of each to only contain datasets in the path
    for dataset_uuid in datasets:

        # If there are any children
        if len(datasets[dataset_uuid].get("children", [])) > 0:

            # Subset the list to only overlap with `to_keep`
            datasets[dataset_uuid]["children"] = list(set(datasets[dataset_uuid]["children"]) & to_keep)

    return datasets


def update_base_toolkit(WB, overwrite=False):
    """Copy all tools and launchers from the repository into the home directory."""

    # Copy all files in helpers/ which end with .sh
    for filename in os.listdir(os.path.join(WB.assets_folder, "helpers")):

        if not filename.endswith(".sh"):
            WB.log(f"File does not end with .sh, skipping ({filename})")
            continue

        # Copy the asset from the package to the home directory
        _copy_asset(WB, "helpers", filename, overwrite=overwrite)

    # Copy the folders within the launchers/ and tools/ folders
    for asset_type in ["launchers", "tools"]:

        # Iterate over each of the tools or launchers
        for asset_name in os.listdir(os.path.join(WB.assets_folder, asset_type)):

            # Reconstruct the full path
            asset_path = os.path.join(WB.assets_folder, asset_type, asset_name)

            # If the asset is not a folder
            if not os.path.isdir(asset_path):
                # Skip it
                continue

            # Iterate over each of the files in that folder
            for filename in os.listdir(asset_path):

                # Copy the asset from the package to the home directory
                _copy_asset(
                    WB,
                    f"{asset_type}/{asset_name}",
                    filename,
                    overwrite=overwrite
                )


def _copy_asset(WB, folder, filename, overwrite=False):

    # The destination folder is in the home directory
    destination_folder = os.path.join(WB.home_folder, folder)
    destination_path = os.path.join(destination_folder, filename)

    # If the folder does not exist
    if not os.path.exists(destination_folder):

        # Create it
        os.makedirs(destination_folder)

    # If the path to the folder does exist
    else:

        # Make sure the path does point to a folder
        assert os.path.isdir(destination_folder), f"Expected to find a folder: {destination_folder}"

    # If the file already exists
    if os.path.exists(destination_path):

        # If the overwrite flag was not set
        if not overwrite:

            # Do not take any action
            WB.log(f"File already exists: {destination_path}")
            return

    # At this point, either the destination_path does not exist, or --overwrite was set
    source_path = os.path.join(WB.assets_folder, folder, filename)

    # Copy the file
    WB.log(f"Copying {source_path} to {destination_path}")
    shutil.copyfile(source_path, destination_path, follow_symlinks=True)


def list_tools(WB):
    """List the tools available for creating datasets."""

    return _list_assets(WB, "tools")


def list_launchers(WB):
    """List the launchers available for creating datasets."""

    return _list_assets(WB, "launchers")


def _list_assets(WB, asset_type):

    assert asset_type in ["tools", "launchers"]

    # Set up a list for all of the tools
    asset_list = []

    # Iterate over the folders in the tools/ or launchers/ directory
    for asset_key in os.listdir(WB._top_level_folder(asset_type)):

        # Read in the configuration for this asset
        asset_config = _read_asset_config(WB, asset_type, asset_key)

        # Add to the list
        asset_list.append(asset_config)

    return asset_list


def _read_asset_config(WB, asset_type, asset_key):
    """Read the configuration for a particular type of asset."""

    asset_folder = os.path.join(WB.home_folder, asset_type, asset_key)

    assert os.path.isdir(asset_folder), f"Expected a directory: {asset_folder}"

    # The configuration of the tool/launcher is defined in config.json
    config_fp = os.path.join(asset_folder, "config.json")

    # The configuration file must exist
    if not os.path.exists(config_fp):
        WB.log(f"Could not find {config_fp}")

    # Read the configuration
    WB.log(f"Parsing {config_fp}")
    with open(config_fp, "r") as handle:
        asset_config = json.load(handle)

    _validate_asset_config(WB, asset_config)

    return asset_config


def _validate_asset_config(WB, asset_config):
    """Validate that the tool or launcher is configured correctly"""

    # The asset must contain a handful of elements
    for key, value_type in [
        ("name", str),
        ("description", str),
        ("args", list)
    ]:

        assert key in asset_config, f"Asset configuration must contain key '{key}'"
        assert isinstance(asset_config[key], value_type), f"{key} must be of type {value_type}"
