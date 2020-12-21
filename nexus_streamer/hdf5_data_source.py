import h5py
from typing import Tuple, Optional, Generator, Callable
import numpy as np
from nexus_streamer.application_logger import get_logger
from nexus_streamer.convert_units import get_to_nanoseconds_conversion_method
from pint.errors import UndefinedUnitError
from nexus_streamer.source_error import BadSource


class LogDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data from NXlog in NeXus file
        """
        self._group = group
        self._logger = get_logger()

        if self._has_missing_fields():
            raise BadSource()
        try:
            self._convert_time = self._get_time_unit_converter()
        except UndefinedUnitError:
            self._logger.error(
                f"Unable to publish data from NXlog at {self._group.name} due to unrecognised "
                f"or missing units for time field"
            )
            raise BadSource()

        try:
            self._value_index_reached = 0
            self._value_dataset = self._group["value"]
            self._value_chunk_iter = self._value_dataset.iter_chunks()
            self._current_value_slice = next(self._value_chunk_iter)
            self._value_buffer = self._value_dataset[self._current_value_slice]

            self._time_index_reached = 0
            self._time_dataset = self._group["time"]
            self._time_chunk_iter = self._time_dataset.iter_chunks()
            self._current_time_slice = next(self._time_chunk_iter)
            self._time_buffer = self._time_dataset[self._current_time_slice]
        except StopIteration:
            self._logger.error(
                f"Unable to publish data from NXlog at {self._group.name} due to empty value or time field"
            )
            raise BadSource()

    def get_data(self) -> Generator[Tuple[Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        while True:
            print("yield")
            yield self._value_buffer[self._value_index_reached], self._convert_time(
                self._time_buffer[self._value_index_reached]
            )

            print(f"{self._value_index_reached} of {self._current_value_slice[2]}")

            self._value_index_reached += 1
            if self._value_index_reached == self._current_value_slice[2]:
                self._value_index_reached = 0
                # read next chunk
                try:
                    self._current_value_slice = next(self._value_chunk_iter)
                except StopIteration:
                    break
                self._value_buffer = self._value_dataset[self._current_value_slice]

            self._time_index_reached += 1
            if self._time_index_reached == self._current_time_slice[2]:
                self._time_index_reached = 0
                # read next chunk
                try:
                    self._current_time_slice = next(self._time_chunk_iter)
                except StopIteration:
                    break
                self._time_buffer = self._time_dataset[self._current_time_slice]

        yield None, 0

    def _has_missing_fields(self) -> bool:
        missing_field = False
        required_fields = (
            "time",
            "value",
        )
        for field in required_fields:
            if field not in self._group:
                self._logger.error(
                    f"Unable to publish data from NXlog at {self._group.name} due to missing {field} field"
                )
                missing_field = True
        return missing_field

    def _get_time_unit_converter(self) -> Callable:
        try:
            units = self._group["time"].attrs["units"]
        except AttributeError:
            raise UndefinedUnitError
        return get_to_nanoseconds_conversion_method(units)

    @property
    def name(self):
        return self._group.name.split("/")[-1]


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

    def get_data(
        self,
    ) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        event_time_zero = self._group["event_time_zero"][...]
        event_index = self._group["event_index"][...]
        event_index = np.append(
            event_index, np.array([self._group["event_id"].len() - 1])
        )
        for pulse_number in range(self._group["event_index"].len()):
            pulse_time = self._convert_pulse_time(event_time_zero[pulse_number])
            yield self._convert_event_time(
                self._group["event_time_offset"][
                    event_index[pulse_number] : event_index[pulse_number + 1]
                ]
            ), self._group["event_id"][
                event_index[pulse_number] : event_index[pulse_number + 1]
            ], pulse_time
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
