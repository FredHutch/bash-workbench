import os

def setup_root_folder(root_folder=None):
    """Ensure that the root folder contains the required assets, and create them if necessary."""

    # The user must provide the root folder
    assert root_folder is not None, "Must provide root_folder"

    # If the root folder does not exist
    if not os.path.exists(root_folder):

        # Create it
        os.makedirs(root_folder)

    # For each of a series of subfolders
    for subfolder in ["data", "configs", "tools"]:

        # Construct the path for this subfolder inside the root folder
        fp = os.path.join(root_folder, subfolder)

        # If the path does not exist
        if not os.path.exists(fp):

            # Create it
            os.makedir(fp)
