import h5py
from typing import Tuple, Optional, Generator, Callable
import numpy as np
from nexus_streamer.application_logger import get_logger
from nexus_streamer.convert_units import get_to_nanoseconds_conversion_method
from pint.errors import UndefinedUnitError
from nexus_streamer.source_error import BadSource


class ChunkCache:
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


class EventDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        :raises BadSource if there is a critical problem with the data source
        """
        self._group = group
        self._logger = get_logger()

        if self._has_missing_fields():
            raise BadSource()
        try:
            self._convert_pulse_time = self._get_pulse_time_unit_converter()
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

        self._tof_loader = ChunkCache(self._group["event_time_offset"])
        self._id_loader = ChunkCache(self._group["event_id"])

    def get_data(
        self,
    ) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        # -1 as last event index is the end index of the last pulse, not start of a new pulse
        for pulse_number in range(self._group["event_index"].len() - 1):
            pulse_time = self._convert_pulse_time(self._event_time_zero[pulse_number])
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
            "event_index",
            "event_time_offset",
        )
        for field in required_fields:
            if field not in self._group:
                self._logger.error(
                    f"Unable to publish data from NXevent_data at {self._group.name} due to missing {field} field"
                )
                missing_field = True
        return missing_field

    def _get_pulse_time_unit_converter(self) -> Callable:
        try:
            units = self._group["event_time_zero"].attrs["units"]
        except AttributeError:
            raise UndefinedUnitError
        return get_to_nanoseconds_conversion_method(units)

    def _get_event_time_unit_converter(self) -> Callable:
        try:
            units = self._group["event_time_offset"].attrs["units"]
        except AttributeError:
            raise UndefinedUnitError
        return get_to_nanoseconds_conversion_method(units)

    @property
    def name(self):
        return self._group.name.split("/")[-1]
