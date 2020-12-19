import h5py
from typing import Union, Tuple, Dict, List
from data_source import DataSource, LogDataSource, EventDataSource


def find_by_nx_class(
        nx_class_names: Tuple[str, ...],
        root: Union[h5py.File, h5py.Group]) -> Dict[str, h5py.Group]:
    groups_with_requested_nx_class = {
        class_name: []
        for class_name in nx_class_names
    }

    def _match_nx_class(_, h5_object):
        if isinstance(h5_object, h5py.Group):
            try:
                if h5_object.attrs["NX_class"].decode(
                        "utf8") in nx_class_names:
                    groups_with_requested_nx_class[h5_object.attrs[
                        "NX_class"].decode("utf8")].append(h5_object)
            except AttributeError:
                pass

    root.visititems(_match_nx_class)
    return groups_with_requested_nx_class


def create_data_sources_from_nexus_file(nexus_file: h5py.File) -> List[DataSource]:
    nx_log = "NXlog"
    nx_event_data = "NXevent_data"
    groups = find_by_nx_class((nx_log, nx_event_data), nexus_file)
    data_sources: List[DataSource]
    data_sources = [LogDataSource(group) for group in groups[nx_log]]
    data_sources.extend([EventDataSource(group) for group in groups[nx_event_data]])
    return data_sources
