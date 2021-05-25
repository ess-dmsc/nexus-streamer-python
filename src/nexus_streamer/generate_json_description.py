import numpy as np
import nexusformat.nexus as nexus
import json
from .convert_units import ns_since_epoch_to_iso8601
from typing import Tuple, Union


# These datasets are always truncated, this avoids JSON descriptions
# of ISIS files in particular from becoming huge
_always_truncate_list = (
    "event_id",
    "event_index",
    "event_time_bins",
    "event_time_offset",
    "event_time_zero",
    "event_frame_number",
    "counts",
)


class NexusToDictConverter:
    """
    Class used to convert nexus format root to python dict
    """

    def __init__(
        self,
        truncate_large_datasets: bool = False,
        large: int = 10,
        event_data_topic: str = "EVENT_DATA_TOPIC",
        log_data_topic: str = "LOG_DATA_TOPIC",
    ):
        """
        :param truncate_large_datasets: if True truncates datasets with any dimension larger than large
        :param large: dimensions larger than this are considered large
        """
        self.truncate_large_datasets = truncate_large_datasets
        self.large = large
        self._event_data_topic = event_data_topic
        self._log_data_topic = log_data_topic

    def convert(self, nexus_root: nexus.NXroot) -> dict:
        """
        Converts the given nexus_root to dict
        """
        return {
            "children": [
                self._root_to_dict(entry) for _, entry in nexus_root.entries.items()
            ]
        }

    def _root_to_dict(self, root: nexus.NXgroup) -> dict:
        try:
            if hasattr(root, "entries"):
                root_dict = self._handle_group(root)
            else:
                root_dict = self._handle_dataset(root)

            root_dict = self._handle_attributes(root, root_dict)
        except nexus.tree.NeXusError:
            root_dict = {}
        return root_dict

    def truncate_if_large(self, size, data, name: str):
        if self.truncate_large_datasets:
            return self.truncate(data, size)
        if name in _always_truncate_list:
            return self.truncate(data, size)
        return data

    def truncate(self, data, size):
        size = list(size)
        for dim_number, dim_size in enumerate(size):
            if dim_size > self.large:
                size[dim_number] = self.large
        data_copy = np.copy(data[...])
        data_copy.resize(size)
        return data_copy

    def _get_data_and_type(self, root, name: str):
        size: Union[int, Tuple[int, ...]] = 1
        data = root.nxdata
        dtype = str(root.dtype)
        if isinstance(data, np.ndarray):
            size = data.shape
            data = self.truncate_if_large(size, data, name)
            if dtype[:2] == "|S":
                data = np.char.decode(data)
            data = data.tolist()
        if dtype[:2] == "|S":
            if not isinstance(data, list):
                data = data.decode("utf-8")
            dtype = "string"
        elif dtype == "float64":
            dtype = "double"
        elif dtype == "float32":
            dtype = "float"
        return data, dtype, size

    @staticmethod
    def _skip_isis_specific_nodes(root):
        if root.nxclass[:2] == "IX":
            return True
        return False

    def _handle_attributes(self, root, root_dict):
        if root.nxclass and root.nxclass != "NXfield" and root.nxclass != "NXgroup":
            root_dict["attributes"] = [{"name": "NX_class", "values": root.nxclass}]
        if root.attrs:
            if "attributes" not in root_dict:
                root_dict["attributes"] = []
            root_dict["attributes"] = []
            for attr_name, attr in root.attrs.items():
                data, dtype, size = self._get_data_and_type(attr, attr_name)
                new_attribute = {"name": attr_name, "values": data}
                if dtype != "object":
                    new_attribute["type"] = dtype
                root_dict["attributes"].append(new_attribute)
        return root_dict

    def _handle_group(self, root):
        root_dict = {"type": "group", "name": root.nxname, "children": []}
        # Add the entries
        entries = root.entries

        if not self._handle_stream(
            root, root_dict
        ) and not self._skip_isis_specific_nodes(root):
            if entries:
                for entry in entries:
                    child_dict = self._root_to_dict(entries[entry])
                    root_dict["children"].append(child_dict)

        return root_dict

    @staticmethod
    def _get_dtype(root) -> str:
        """
        Get the datatype as a string in the format expected by the file writer
        """
        dtype = str(root.dtype)
        if dtype[:2] == "|S":
            dtype = "string"
        elif dtype == "float64":
            dtype = "double"
        elif dtype == "float32":
            dtype = "float"
        return dtype

    def _handle_stream(self, root, root_dict: dict) -> bool:
        """
        Insert information to get this data from Kafka stream if it is of an NXclass supported by the NeXus-Streamer
        :param root:
        :param root_dict:
        :return: true if data will be streamed
        """
        stream_info = {}
        is_stream = False
        if isinstance(root, nexus.NXlog):
            stream_info["writer_module"] = "f142"
            is_stream = True
            if root.nxname == "value_log":
                # For ISIS files the parent of the NXlog has a more useful name
                # which the NeXus-Streamer uses as the source name
                stream_info["source"] = root.nxgroup.nxname
            else:
                stream_info["source"] = root.nxname
            stream_info["topic"] = self._log_data_topic
            try:
                stream_info["dtype"] = self._get_dtype(root.entries["value"])
            except KeyError:
                try:
                    stream_info["dtype"] = self._get_dtype(root.entries["raw_value"])
                except KeyError:
                    is_stream = False
            try:
                stream_info["unit"] = root.attrs["units"]
            except KeyError:
                pass
        elif isinstance(root, nexus.NXevent_data):
            stream_info["writer_module"] = "ev42"
            stream_info["topic"] = self._event_data_topic
            stream_info["source"] = "NeXus-Streamer"
            is_stream = True
        if is_stream:
            root_dict["children"].append({"type": "stream", "stream": stream_info})
        return is_stream

    def _handle_dataset(self, root):
        data, dataset_type, size = self._get_data_and_type(root, root.nxname)
        root_dict = {
            "type": "dataset",
            "name": root.nxname,
            "dataset": {"type": dataset_type},
            "values": data,
        }
        if size != 1:
            root_dict["dataset"]["size"] = size

        return root_dict


def _get_child_node(name: str, tree: dict) -> dict:
    for child in tree["children"]:
        try:
            if child["name"] == name:
                return child
        except KeyError:
            continue
    raise KeyError


def _replace_old_start_time_with_streamer_start_time(
    new_run_start_ns: int, run_start_dataset_path: str, json_tree: dict
):
    new_run_start_time = ns_since_epoch_to_iso8601(new_run_start_ns)
    run_start_dataset_path_list = run_start_dataset_path.split("/")[1:]
    for node_name in run_start_dataset_path_list:
        json_tree = _get_child_node(node_name, json_tree)
    json_tree["values"] = [new_run_start_time]


def nexus_file_to_json_description(
    filename: str,
    event_data_topic: str,
    log_data_topic: str,
    new_run_start_ns: int,
    run_start_dataset_path: str,
) -> str:
    nexus_file = nexus.nxload(filename)
    converter = NexusToDictConverter(
        truncate_large_datasets=False,
        event_data_topic=event_data_topic,
        log_data_topic=log_data_topic,
    )
    tree = converter.convert(nexus_file)
    _replace_old_start_time_with_streamer_start_time(
        new_run_start_ns, run_start_dataset_path, tree
    )

    return json.dumps(tree, indent=2, sort_keys=False)
