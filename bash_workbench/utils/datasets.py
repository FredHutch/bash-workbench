from bash_workbench.utils import dataset


class Datasets:
    """Collection of datasets with useful helper functions."""

    def __init__(self):
        
        # Key each Dataset by its uuid
        self.datasets = dict()

        # Keep track of the parent of each dataset
        self.parent_dict = dict()

        # Keep track of whether each dataset passes the filter
        self.passes_filter = dict()

        # Keep a list of all filters which have been applied
        self.filters = list()

    def add(self, ds):
        """Add a single dataset."""

        # Add the dataset attributes to the config object
        ds.index["path"] = ds.path
        ds.index["children"] = ds.children()

        # For each of the children of the dataset
        for child_uuid in ds.index["children"]:

            # Mark the parent of those datasets
            self.parent_dict[child_uuid] = ds.index["uuid"]

        # If the parent of this dataset is known, add it
        ds.index["parent"] = self.parent_dict.get(ds.index["uuid"])

        # Add it to the dict, keyed by uuid
        self.datasets[ds.index["uuid"]] = ds.index

        # By default, all datasets initially pass the filter
        self.passes_filter[ds.index["uuid"]] = True

        # Apply any filters which have been set
        for (field, value) in self.filters:

            self._filter_one(ds.index["uuid"], field=field, value=value)

    def add_filter(self, field=None, value=None):
        """Add a filter to all datasets."""

        # Add the field, value tuple to the list of filters
        self.filters.append((field, value))

        # Apply the filter to all datasets
        self._filter_all(field=field, value=value)

    def remove_filter(self, field=None, value=None):
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

    def _filter_one(self, ds_uuid, field=None, value=None):
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

    def _reset_filter_one(self, ds_uuid):
        """Reset the filter for a single dataset."""

        # The ds_uuid must identify an entry in self.datasets
        assert ds_uuid in self.datasets, f"Dataset not found: {ds_uuid}"

        # Set the entry in passes_filter to True
        self.passes_filter[ds_uuid] = True

    def _filter_all(self, field=None, value=None):
        """Apply a filter to all datasets."""

        # Iterate over every dataset
        for ds_uuid in self.datasets:

            # Check the query
            self._filter_one(ds_uuid, field=field, value=value)

    def _reset_filter_all(self, field=None, value=None):
        """Reset the filter for all datasets."""

        # Iterate over every dataset
        for ds_uuid in self.datasets:

            # Reset the filter
            self._reset_filter_one(ds_uuid, field=field, value=value)

    def filtered(self, incl_anc=True):
        """
        Return the collection of datasets which pass the filter.
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

        # Keep the datasets which are in this set
        datasets = {
            ds_uuid: dataset
            for ds_uuid, dataset in self.datasets.items()
            if ds_uuid in to_keep
        }

        # Update the 'children' field of each to only contain datasets in the set
        for ds_uuid in datasets:

            # If there are any children
            if len(datasets[ds_uuid].get("children", [])) > 0:

                # Subset the list to only overlap with `to_keep`
                datasets[ds_uuid]["children"] = list(set(datasets[ds_uuid]["children"]) & to_keep)

        return datasets

    def format_dataset_tree(self):
        """Format a list of datasets as a tree."""

        # Find the uuids of all datasets which do not have parents
        root_datasets = [
            ds_uuid
            for ds_uuid, ds_info in self.datasets.items()
            if ds_info.get("parent") is None
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

            # Mark whether this dataset has children
            has_children = len(self.datasets[ds_uuid].get("children", [])) > 0

            # Yield the dataset information with the specified prefix
            yield self.yield_dataset_tree_single(
                ds_uuid,
                indentation=indentation,
                list_position=list_position,
                has_children=has_children
            )

            # Recursively repeat the process for any children of this dataset
            yield self.yield_dataset_tree_recursive(
                self.datasets[ds_uuid].get("children", []),
                # If this dataset is followed by others in this group
                # Add a continuation character to the indentation
                # Otherwise, there are no more in this group, and so the indentation is blank
                indentation=indentation + "  │" if list_position in ["first", "middle"] else "   "
            )

    def yield_dataset_tree_single(
        self,
        ds_uuid,
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