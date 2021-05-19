import h5py
from typing import Tuple, Optional, Generator, Callable, Union
import numpy as np
from .application_logger import get_logger
from .convert_units import (
    get_to_nanoseconds_conversion_method,
    iso8601_to_ns_since_epoch,
)
from pint.errors import UndefinedUnitError
from .source_error import BadSource


class _ChunkDataLoader:
    def __init__(self, dataset: h5py.Dataset):
        self._dataset = dataset
        self._chunk_iterator = self._dataset.iter_chunks()
        next_slice = next(self._chunk_iterator)
        self._current_chunk = self._dataset[next_slice]
        self._start_index: int = 0

    def get_data_for_pulse(
        self, pulse_start_event: int, pulse_end_event: int
    ) -> np.ndarray:
        start_index = int(pulse_start_event - self._start_index)
        end_index = int(pulse_end_event - self._start_index)

        data_for_pulse = np.array([], dtype=self._current_chunk.dtype)
        while True:
            # If all the data we need is in the current, cached chunk,
            # then just append and return it
            if end_index < self._current_chunk.size:
                return np.append(
                    data_for_pulse, self._current_chunk[start_index:end_index]
                )
            # else...
            # we need all the data in the current chunk...
            data_for_pulse = np.append(
                data_for_pulse, self._current_chunk[start_index:]
            )
            # and at least some from the next chunk, so load the next chunk and continue
            end_index -= self._current_chunk.size
            start_index = 0
            self._start_index += self._current_chunk.size
            try:
                next_slice = next(self._chunk_iterator)
            except StopIteration:
                return data_for_pulse
            self._current_chunk = self._dataset[next_slice]


class _ContiguousDataLoader:
    def __init__(self, dataset: h5py.Dataset):
        self._dataset = dataset
        max_bytes_willing_to_load_into_memory = 100_000_000  # 100 MB
        if self._dataset.nbytes < max_bytes_willing_to_load_into_memory:
            self._dataset = self._dataset[...]
        elif self._dataset.compression is not None:
            get_logger().warning(
                f"{self._dataset.name} is larger than {max_bytes_willing_to_load_into_memory} bytes,"
                f"contiguous and compressed, it will be very slow to stream if these event data are from many pulses"
            )

    def get_data_for_pulse(
        self, pulse_start_event: int, pulse_end_event: int
    ) -> np.ndarray:
        return self._dataset[pulse_start_event:pulse_end_event]


_DataLoader = Union[_ChunkDataLoader, _ContiguousDataLoader]


def _get_pulse_time_offset_in_ns(pulse_time_dataset: h5py.Group) -> int:
    """
    Gives an offset which, when added to pulse times, results in time relative to unix epoch
    """
    try:
        date_string = pulse_time_dataset.attrs["offset"]
    except KeyError:
        # If no "offset" attribute then times are already relative to unix epoch according to NeXus standard
        return 0
    return iso8601_to_ns_since_epoch(date_string)


class EventDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        :raises BadSource if there is a critical problem with the data source
        """
        self._group = group
        self._logger = get_logger()
        self._tof_loader: _DataLoader
        self._id_loader: _DataLoader

        if self._has_missing_fields():
            raise BadSource()
        try:
            self._convert_pulse_time = _get_pulse_time_unit_converter(group)
            self._convert_event_time = self._get_event_time_unit_converter()
        except UndefinedUnitError:
            self._logger.error(
                f"Unable to publish data from NXevent_data at {self._group.name} due to unrecognised "
                f"or missing units for time field"
            )
            raise BadSource()

        self._event_time_zero = self._group["event_time_zero"][...]
        self._event_index = self._group["event_index"][...]

        # There is some variation in the last recorded event_index in files from different institutions
        # for example ISIS files often have what would be the first index of the next pulse at the end.
        # This logic hopefully covers most cases
        if self._event_index[-1] < self._group["event_id"].len():
            self._event_index = np.append(
                self._event_index,
                np.array([self._group["event_id"].len() - 1]).astype(
                    self._event_index.dtype
                ),
            )
        else:
            self._event_index[-1] = self._group["event_id"].len()

        try:
            self._group["event_time_offset"].iter_chunks()
            self._tof_loader = _ChunkDataLoader(self._group["event_time_offset"])
        except TypeError:
            self._tof_loader = _ContiguousDataLoader(self._group["event_time_offset"])

        try:
            self._group["event_id"].iter_chunks()
            self._id_loader = _ChunkDataLoader(self._group["event_id"])
        except TypeError:
            self._id_loader = _ContiguousDataLoader(self._group["event_id"])

        self._pulse_time_offset_ns = _get_pulse_time_offset_in_ns(
            self._group["event_time_zero"]
        )

    def get_data(
        self,
    ) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        # -1 as last index would be start of the next pulse after the end of the run
        for pulse_number in range(self._event_index.size - 1):
            pulse_time = (
                self._convert_pulse_time(self._event_time_zero[pulse_number])
                + self._pulse_time_offset_ns
            )
            start_event = self._event_index[pulse_number]
            end_event = self._event_index[pulse_number + 1]
            yield self._convert_event_time(
                self._tof_loader.get_data_for_pulse(start_event, end_event)
            ), self._id_loader.get_data_for_pulse(start_event, end_event), pulse_time
        yield None, None, 0

    def _has_missing_fields(self) -> bool:
        missing_field = False
        required_fields = (
            "event_time_zero",
            "event_index",
            "event_id",
            "event_time_offset",
        )
        for field in required_fields:
            if field not in self._group:
                self._logger.error(
                    f"Unable to publish data from NXevent_data at {self._group.name} due to missing {field} field"
                )
                missing_field = True
        return missing_field

    def _get_event_time_unit_converter(self) -> Callable:
        try:
            units = self._group["event_time_offset"].attrs["units"]
        except AttributeError:
            raise UndefinedUnitError
        return get_to_nanoseconds_conversion_method(units)

    @property
    def name(self):
        return self._group.name.split("/")[-1]


def _get_pulse_time_unit_converter(group: h5py.Group) -> Callable:
    try:
        units = group["event_time_zero"].attrs["units"]
    except AttributeError:
        raise UndefinedUnitError
    return get_to_nanoseconds_conversion_method(units)


class FakeEventDataSource:
    def __init__(self, group: h5py.Group, events_per_pulse: int):
        logger = get_logger()
        try:
            self._detector_ids = group.parent["detector_number"][...]
        except KeyError:
            logger.error(
                "detector_number dataset not found in parent group of "
                "NXevent_data, this must be present when using "
                "--fake-events-per-pulse"
            )
            raise BadSource()
        self._events_per_pulse = events_per_pulse

        self._event_time_zero = group["event_time_zero"][...]
        self._convert_pulse_time = _get_pulse_time_unit_converter(group)

        self._pulse_time_offset_ns = _get_pulse_time_offset_in_ns(
            group["event_time_zero"]
        )
        self._rng = np.random.default_rng(12345)

        self.name = group.name.split("/")[-1]

    def get_data(
        self,
    ) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        for pulse_number in range(self._event_time_zero.size):
            pulse_time = (
                self._convert_pulse_time(self._event_time_zero[pulse_number])
                + self._pulse_time_offset_ns
            )

            tofs = self._rng.integers(
                low=10000, high=10000000, size=self._events_per_pulse
            )
            detector_num_indices = self._rng.integers(
                low=0, high=self._detector_ids.size, size=self._events_per_pulse
            )
            ids = self._detector_ids[detector_num_indices]

            yield tofs, ids, pulse_time
        yield None, None, 0
