import h5py
from typing import Union, Tuple, Dict, List, Optional
from .data_source import EventDataSource, FakeEventDataSource
from .log_data_source import LogDataSource
from .source_error import BadSource
from .application_logger import get_logger
from .convert_units import iso8601_to_ns_since_epoch


def get_attr_as_str(h5_object, attribute_name: str):
    try:
        return h5_object.attrs[attribute_name].decode("utf8")
    except AttributeError:
        return h5_object.attrs[attribute_name]


def find_by_nx_class(
    nx_class_names: Tuple[str, ...], root: Union[h5py.File, h5py.Group]
) -> Dict[str, List[h5py.Group]]:
    groups_with_requested_nx_class: Dict[str, List[h5py.Group]] = {
        class_name: [] for class_name in nx_class_names
    }

    def _match_nx_class(_, h5_object):
        if isinstance(h5_object, h5py.Group):
            try:
                if get_attr_as_str(h5_object, "NX_class") in nx_class_names:
                    groups_with_requested_nx_class[
                        get_attr_as_str(h5_object, "NX_class")
                    ].append(h5_object)
            except KeyError:
                pass

    root.visititems(_match_nx_class)
    return groups_with_requested_nx_class


def create_data_sources_from_nexus_file(
    nexus_file: h5py.File,
    fake_events_per_pulse: Optional[int],
) -> Tuple[List[LogDataSource], List[Union[EventDataSource, FakeEventDataSource]]]:
    nx_log = "NXlog"
    nx_event_data = "NXevent_data"
    groups = find_by_nx_class((nx_log, nx_event_data), nexus_file)

    log_sources = []
    for group in groups[nx_log]:
        try:
            log_sources.append(LogDataSource(group))
        except BadSource:
            # Reason for error is logged in source init
            pass

    event_sources: List[Union[EventDataSource, FakeEventDataSource]] = []
    for group in groups[nx_event_data]:
        try:
            if fake_events_per_pulse is not None:
                event_sources.append(FakeEventDataSource(group, fake_events_per_pulse))
            else:
                event_sources.append(EventDataSource(group))
        except BadSource:
            # Reason for error is logged in source init
            pass

    return log_sources, event_sources


def get_recorded_run_start_time_ns(filename: str) -> Tuple[int, str]:
    logger = get_logger()
    with h5py.File(filename, "r") as nexus_file:
        # start_time dataset in the NXentry is method of recording run start supported by the standard
        nx_entry_class = "NXentry"
        entry_groups = find_by_nx_class((nx_entry_class,), nexus_file)
        if len(entry_groups) > 1:
            logger.warning(
                "More than one NXentry group found."
                "Note: NeXus Streamer will stream data from all groups as if it were one experiment run."
            )
        run_start_time_ns = None
        run_start_dataset_path = ""
        for entry_group in entry_groups[nx_entry_class]:
            try:
                start_time_dataset = entry_group["start_time"]
                found_start_time_ns = iso8601_to_ns_since_epoch(start_time_dataset[...])
                if run_start_time_ns is None or found_start_time_ns < run_start_time_ns:
                    run_start_time_ns = found_start_time_ns
                    run_start_dataset_path = start_time_dataset.name
            except KeyError:
                pass

        if run_start_time_ns is not None:
            return run_start_time_ns, run_start_dataset_path

        logger.error("No start_time dataset found in NXentry to use as run start time")
        raise RuntimeError("Found nothing to use as run start time")
        # TODO find earliest NXlog or NXevent_data timestamp and use that as run start...
