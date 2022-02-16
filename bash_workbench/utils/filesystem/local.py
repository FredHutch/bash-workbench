import os
import logging

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
