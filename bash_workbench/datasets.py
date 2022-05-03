from .dataset import Dataset


class Datasets:
    """Collection of datasets with useful helper functions."""

    def __init__(self, wb):

        # Attach the workbench
        self.wb = wb
        
        # Key each Dataset by its uuid
        self.datasets = dict()

        # Keep track of the parent of each dataset
        self.parent_dict = dict()

        # Keep track of the absolute path of each dataset
        # abs_path -> uuid
        self.path_dict = dict()

        # Keep track of whether each dataset passes the filter
        self.passes_filter = dict()

        # Keep a list of all filters which have been applied
        self.filters = list()

        # Iterate over all of the datasets and collections linked to the home folder
        for ds in self.wb.walk_home_tree():

            # Add the dataset to the collection
            self.add(ds)

    def path_exists(self, path:str) -> bool:
        """Return a boolean indicating whether the path exists in the collection."""

        return self.path_dict.get(path) is not None

    def uuid_exists(self, uuid:str) -> bool:
        """Return a boolean indicating whether the uuid exists in the collection."""

        return self.datasets.get(uuid) is not None

    def from_path(self, path:str) -> Dataset:
        """Return a Dataset for a particular path."""

        # Get the absolute path
        path = self.wb.filelib.abs_path(path)

        # If the path has already been parsed
        if self.path_dict.get(path) is not None:

            # Return that dataset
            return self.path_dict.get(path)

        # If the path has not yet been parsed
        else:

            # Make a dataset object
            ds = Dataset(
                base_path=path,
                filelib=self.wb.filelib,
                logger=self.wb.logger,
                verbose=self.wb.verbose
            )

            # If the folder is already indexed
            if ds.complete:

                # Add it to the collection
                self.add(ds)

            # Return the dataset
            return ds

    def add(self, ds:Dataset) -> None:
        """Add a single dataset."""

        # If the dataset is not indexed
        if ds.index is None:

            # Index it
            ds.create_index()

        # Add the dataset attributes to the config object
        ds.index["path"] = ds.base_path
        ds.index["children"] = ds.children()

        # For each of the children of the dataset
        for child_uuid in ds.index["children"]:

            # Mark the parent of those datasets
            self.parent_dict[child_uuid] = ds.index["uuid"]

            # Mark the parent in the index of the child
            if self.datasets.get(child_uuid) is not None:
                self.datasets[child_uuid]["parent"] = ds.index["uuid"]

        # If the parent of this dataset is known, add it
        ds.index["parent"] = self.parent_dict.get(ds.index["uuid"])

        # Add it to the dict, keyed by uuid
        self.datasets[ds.index["uuid"]] = ds.index

        # Record the path -> uuid
        self.path_dict[ds.index["uuid"]] = ds.base_path

        # By default, all datasets initially pass the filter
        self.passes_filter[ds.index["uuid"]] = True

        # Apply any filters which have been set
        for (field, value) in self.filters:

            self._filter_one(ds.index["uuid"], field=field, value=value)

    def add_filter(self, field:str=None, value:str=None):
        """Add a filter to all datasets."""

        # Add the field, value tuple to the list of filters
        self.filters.append((field, value))

        # Apply the filter to all datasets
        self._filter_all(field=field, value=value)

    def remove_filter(self, field:str=None, value:str=None):
        """Remove a particular filter from the datasets."""

        # Remove the filter from the list of filters
        self.filters = [
            (f, v)
            for (f, v) in self.filters
            if f != field or v != value
        ]

        # Reset all filters for the datasets
        self._reset_filter_all()

        # Re-filter every dataset on the remaining filters
        self._apply_filters()

    def _apply_filters(self):
        """Apply all of the filters to all of the datasets."""

        for (field, value) in self.filters:

            self._filter_all(field=field, value=value)

    def _filter_one(self, ds_uuid, field:str=None, value:str=None):
        """Apply a filter to a single dataset."""

        # The ds_uuid must identify an entry in self.datasets
        assert ds_uuid in self.datasets, f"Dataset not found: {ds_uuid}"

        # If the dataset has already been filtered out
        if not self.passes_filter[ds_uuid]:

            # There is no need to evaluate it again
            return

        # Get the information for this dataset
        ds_info = self.datasets[ds_uuid]

        # For tags, the 'value' must be "{key}={value}"
        if field == "tag":

            msg = "To filter by tag, provide query in the format 'key=value'"
            assert "=" in value, msg
            assert value.endswith("=") is False, msg

            # parse the tag key and value
            key, value = value.split("=", 1)

            # Check if the tag has been set, and if the value matches
            self.passes_filter[ds_uuid] = ds_info.get("tags", {}).get(key) == value

        # For all other query fields
        else:

            # Check if the query is in the indicated field
            self.passes_filter[ds_uuid] = value in ds_info[field]

    def _reset_filter_one(self, ds_uuid:str):
        """Reset the filter for a single dataset."""

        # The ds_uuid must identify an entry in self.datasets
        assert ds_uuid in self.datasets, f"Dataset not found: {ds_uuid}"

        # Set the entry in passes_filter to True
        self.passes_filter[ds_uuid] = True

    def _filter_all(self, field:str=None, value:str=None):
        """Apply a filter to all datasets."""

        # Iterate over every dataset
        for ds_uuid in self.datasets:

            # Check the query
            self._filter_one(ds_uuid, field=field, value=value)

    def _reset_filter_all(self, field:str=None, value:str=None):
        """Reset the filter for all datasets."""

        # Iterate over every dataset
        for ds_uuid in self.datasets:

            # Reset the filter
            self._reset_filter_one(ds_uuid)

    def _get_filtered_uuids(self, incl_anc:bool=True):
        """
        Return the set of dataset UUIDs which pass the current filtering.
        By default, all datasets which contain those passing datasets will also
        be included. That behavior can be stopped by setting `incl_anc=False`
        """

        # Make a list of the datasets which pass the filter
        passing_uuids = [
            ds_uuid
            for ds_uuid in self.passes_filter
            if self.passes_filter[ds_uuid]
        ]

        # If we should keep all of the ancestors of those datasets
        if incl_anc:

            # Make a set of datasets to keep
            to_keep = set()

            # For each of the matching uuids
            for ds_uuid in passing_uuids:

                # Iterate over the chain of parents back to the root
                while ds_uuid is not None:

                    # Add it to the set
                    to_keep.add(ds_uuid)

                    # Move to the parent
                    ds_uuid = self.datasets[ds_uuid].get("parent")
        
        # Otherwise
        else:

            # Just keep the datasets which pass the filter
            to_keep = set(passing_uuids)

        return to_keep

    def filtered(self, incl_anc:bool=True):
        """
        Return the collection (dict) of datasets which pass the filter.
        By default, all datasets which contain those passing datasets will also
        be included. That behavior can be stopped by setting `incl_anc=False`
        """

        # Get the set of UUIDs to keep
        self.filtered_uuids = self._get_filtered_uuids(incl_anc=incl_anc)

        # Keep the datasets which are in this set
        datasets = {
            ds_uuid: dataset
            for ds_uuid, dataset in self.datasets.items()
            if ds_uuid in self.filtered_uuids
        }

        # Update the 'children' field of each to only contain datasets in the set
        for ds_uuid in datasets:

            # If there are any children
            if len(datasets[ds_uuid].get("children", [])) > 0:

                # Subset the list to only overlap with `self.filtered_uuids`
                datasets[ds_uuid]["children"] = list(set(datasets[ds_uuid]["children"]) & self.filtered_uuids)

        return datasets

    def filtered_len(self, incl_anc:bool=True):
        """
        Return the number of datasets which pass the filter.
        By default, all datasets which contain those passing datasets will also
        be included. That behavior can be stopped by setting `incl_anc=False`
        """

        return len(self._get_filtered_uuids(incl_anc=incl_anc))

    def filtered_paths(self, sep:str=" : "):
        """
        Return a list of filtered datasets in the format:
        <NAME_HIERARCHY> : <PATH_HIERARCHY>
        Where NAME_HIERARCHY is the <NAME>/<NAME>/etc. from root to the dataset, and
        where PATH_HIERARCHY is the <PATH>/<PATH>/etc. from root to the dataset.
        """

        # Get the dict of all filtered datasets
        ds_dict = self.filtered()

        # Make a dict of the name hierarchy for each dataset
        names = {
            k: "/".join([
                ds_dict[i]["name"]
                for i in self.path_to_root(ds_dict, k)
            ])
            for k in ds_dict
        }

        # Make a dict of the absolute paths to each dataset
        paths = {
            k: ds_dict[k]["path"]
            for k in ds_dict
        }

        # Make a list of the <NAME> : <PATH> combined strings if <NAME> != <PATH>
        # Otherwise just return the <PATH>
        name_path_list = [
            sep.join([names[k], paths[k]]) if names[k] != paths[k] else names[k]
            for k in ds_dict
        ]

        # Sort it
        name_path_list.sort()

        # Return the sorted list
        return name_path_list

    def path_to_root(self, d, k, reverse:bool=True):
        """
        For any dict, return the list of keys from the dict d
        which start from k and extend iteratively to each
        entry d[k]['parent'] (if that parent is not null).
        If reverse is True, return a list which starts from the
        root and ends at k.
        """

        l = list()
        while k is not None and k in d:
            l.append(k)
            k = d[k].get('parent')

        if reverse:
            return l[::-1]
        else:
            return l

    def format_dataset_tree(self):
        """Format a list of datasets as a tree."""

        # Get the set of UUIDs to keep
        self.filtered_uuids = self._get_filtered_uuids(incl_anc=True)

        # Find the uuids of all datasets which do not have parents
        root_datasets = [
            ds_uuid
            for ds_uuid, ds_info in self.datasets.items()
            if ds_info.get("parent") is None and ds_uuid in self.filtered_uuids
        ]

        # Recursively format each line of the tree
        return "\n".join([
            line
            for line in self.yield_dataset_tree_recursive(root_datasets)
        ])


    def yield_dataset_tree_recursive(self, ds_uuids, indentation=""):
        """Function to recursively print the directory structure."""

        # Get the number of datasets in the list
        dataset_n = len(ds_uuids)

        # For each dataset, set the `list_position` as 'single', 'first', 'middle', or 'last'
        # Also set the flag `has_children` as True/False

        # Iterate over each dataset
        for dataset_i, ds_uuid in enumerate(ds_uuids):

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

            # Get the list of children which also pass the filter
            ds_children = [
                child_uuid
                for child_uuid in self.datasets[ds_uuid].get("children", [])
                if child_uuid in self.filtered_uuids
            ]

            # Mark whether this dataset has children
            has_children = len(ds_children) > 0

            # Yield the dataset information with the specified prefix
            yield from self.yield_dataset_tree_single(
                ds_uuid,
                indentation=indentation,
                list_position=list_position,
                has_children=has_children
            )

            # Recursively repeat the process for any children of this dataset
            yield from self.yield_dataset_tree_recursive(
                ds_children,
                # If this dataset is followed by others in this group
                # Add a continuation character to the indentation
                # Otherwise, there are no more in this group, and so the indentation is blank
                indentation=indentation + "  │" if list_position in ["first", "middle"] else "   "
            )

    def yield_dataset_tree_single(
        self,
        ds_uuid:str,
        indentation:str="",
        list_position=None,
        has_children=None
    ):

        name_prefix = dict(
            single=" └─",
            first=" └┬",
            last="  └",
            middle="  ├"
        )[list_position]

        # Get the information for this dataset
        ds_info = self.datasets[ds_uuid]

        # Yield the name of the dataset
        yield f"{indentation}{name_prefix} {ds_info['name']}"

        # Make a separate prefix for any additional lines
        # If there are more items in the list, add a continuation
        addl_prefix = "  │" if list_position in ["first", "middle"] else "   "

        # Add another continuation if there are children below this dataset
        addl_prefix = f'{addl_prefix}{" │" if has_children else "  "}'

        # Print the uuid and any additional fields
        fields = [
            f"uuid: {ds_info['uuid']}",
            f"path: {ds_info['path']}",
        ]

        # If there is a description
        if len(ds_info['description']) > 0:
            fields.append(f"description: {ds_info['description']}")

        # If there are tags
        if len(ds_info.get("tags", {})) > 0:
            for k, v in ds_info["tags"].items():
                fields.append(f"tag: {k} = {v}")

        fields.append("")
        for field in fields:
            yield f"{indentation}{addl_prefix}  {field}"