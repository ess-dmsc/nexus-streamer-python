import h5py
from typing import Tuple, Optional, Generator, Callable
import numpy as np
from nexus_streamer.application_logger import get_logger
from nexus_streamer.convert_units import get_to_nanoseconds_conversion_method
from pint.errors import UndefinedUnitError
from nexus_streamer.source_error import BadSource


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
        self._event_index = np.append(
            self._event_index,
            np.array([self._group["event_id"].len() - 1]).astype(
                self._event_index.dtype
            ),
        )

        self._tof_buffer_start_index = 0
        self._event_tof = self._group["event_time_offset"]
        self._tof_chunk_iter = self._event_tof.iter_chunks()
        self._current_tof_slice = next(self._tof_chunk_iter)
        self._tof_buffer = self._event_tof[self._current_tof_slice]

        self._id_buffer_start_index = 0
        self._event_id = self._group["event_id"]
        self._id_chunk_iter = self._event_id.iter_chunks()
        self._current_id_slice = next(self._id_chunk_iter)
        self._id_buffer = self._event_id[self._current_id_slice]

    def _get_tofs_for_pulse(self, pulse_number: int):
        start_index = int(
            self._event_index[pulse_number] - self._tof_buffer_start_index
        )
        end_index = int(
            self._event_index[pulse_number + 1] - self._tof_buffer_start_index
        )

        tof_for_pulse = np.array([], dtype=self._tof_buffer.dtype)
        while True:
            if self._tof_buffer_start_index + self._tof_buffer.size > end_index:
                return self._convert_event_time(
                    np.append(
                        tof_for_pulse,
                        self._convert_event_time(
                            self._tof_buffer[start_index:end_index]
                        ),
                    )
                )

            tof_for_pulse = np.append(
                tof_for_pulse, self._convert_event_time(self._tof_buffer[start_index:])
            )

            # We need to load more data
            self._tof_buffer_start_index += self._current_tof_slice[0].stop
            self._current_tof_slice = next(self._tof_chunk_iter)
            self._tof_buffer = self._event_tof[self._current_tof_slice]

    def _get_ids_for_pulse(self, pulse_number: int):
        start_index = int(self._event_index[pulse_number] - self._id_buffer_start_index)
        end_index = int(
            self._event_index[pulse_number + 1] - self._id_buffer_start_index
        )

        ids_for_pulse = np.array([], dtype=self._id_buffer.dtype)
        while True:
            if self._id_buffer_start_index + self._id_buffer.size > end_index:
                return np.append(
                    ids_for_pulse,
                    self._id_buffer[start_index:end_index],
                )

            ids_for_pulse = np.append(ids_for_pulse, self._id_buffer[start_index:])

            # We need to load more data
            self._id_buffer_start_index += self._current_id_slice[0].stop
            self._current_id_slice = next(self._id_chunk_iter)
            self._id_buffer = self._event_id[self._current_id_slice]

    def get_data(
        self,
    ) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        for pulse_number in range(self._group["event_index"].len()):
            if pulse_number == 82:
                print("break")
            pulse_time = self._convert_pulse_time(self._event_time_zero[pulse_number])
            yield self._get_tofs_for_pulse(pulse_number), self._get_ids_for_pulse(
                pulse_number
            ), pulse_time
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
