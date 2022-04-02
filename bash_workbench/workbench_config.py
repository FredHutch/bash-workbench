from .folder_hierarchy import FolderHierarchyBase

class WorkbenchConfig(FolderHierarchyBase):
    """Class defining the expected structure of the workbench folder."""

    # The expected subfolders in the base workbench directory
    structure = list(
        dict(name="data"),
        dict(name="params"),
        dict(name="repositories")
    )