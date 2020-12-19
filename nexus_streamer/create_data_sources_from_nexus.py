import h5py
from typing import Union, Tuple, Dict, List
from nexus_streamer.data_source import LogDataSource, EventDataSource


def get_attr_as_str(h5_object, attribute_name: str):
    try:
        return h5_object.attrs[attribute_name].decode("utf8")
    except AttributeError:
        return h5_object.attrs[attribute_name]


def find_by_nx_class(
    nx_class_names: Tuple[str, ...], root: Union[h5py.File, h5py.Group]
) -> Dict[str, h5py.Group]:
    groups_with_requested_nx_class: Dict[str, h5py.Group] = {
        class_name: [] for class_name in nx_class_names
    }

    def _match_nx_class(_, h5_object):
        if isinstance(h5_object, h5py.Group):
            try:
                if get_attr_as_str(h5_object, "NX_class") in nx_class_names:
                    groups_with_requested_nx_class[
                        get_attr_as_str(h5_object, "NX_class")
                    ].append(h5_object)
            except AttributeError:
                pass

    root.visititems(_match_nx_class)
    return groups_with_requested_nx_class


def create_data_sources_from_nexus_file(
    nexus_file: h5py.File,
) -> Tuple[List[LogDataSource], List[EventDataSource]]:
    nx_log = "NXlog"
    nx_event_data = "NXevent_data"
    groups = find_by_nx_class((nx_log, nx_event_data), nexus_file)
    return [LogDataSource(group) for group in groups[nx_log]], [
        EventDataSource(group) for group in groups[nx_event_data]
    ]
