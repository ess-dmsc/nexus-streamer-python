from typing import Generator, Tuple, Optional, Callable

import h5py
import numpy as np
from pint import UndefinedUnitError

from .application_logger import get_logger
from .convert_units import get_to_nanoseconds_conversion_method
from .source_error import BadSource
from .convert_units import iso8601_to_ns_since_epoch


def _get_time_offset_in_ns(time_dataset: h5py.Group) -> int:
    """
    Gives an offset which, when added to data times, results in time relative to unix epoch
    """
    try:
        date_string = time_dataset.attrs["start"]
    except KeyError:
        # If no "start" attribute then times are already relative to unix epoch according to NeXus standard
        return 0
    return iso8601_to_ns_since_epoch(date_string)


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
            self._value_index_reached = -1
            self._value_dataset = self._group["value"]

            self._time_index_reached = -1
            self._time_dataset = self._group["time"]

            self._time_offset_ns = _get_time_offset_in_ns(self._time_dataset)
            self._data_are_chunked = True
            try:
                self._value_chunk_iter = self._value_dataset.iter_chunks()
                self._time_chunk_iter = self._time_dataset.iter_chunks()
            except TypeError:
                self._data_are_chunked = False
                return

            self._current_value_slice = next(self._value_chunk_iter)
            self._value_buffer = self._value_dataset[self._current_value_slice]

            self._current_time_slice = next(self._time_chunk_iter)
            self._time_buffer = self._time_dataset[self._current_time_slice]
        except (StopIteration, ValueError):
            self._logger.warn(
                f"Unable to publish data from NXlog at {self._group.name} due to empty value or time field"
            )
            raise BadSource()

    def get_data(self) -> Generator[Tuple[Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of data when there are no more data
        """
        while True:
            if self._data_are_chunked:
                self._value_index_reached += 1
                if self._value_index_reached == self._current_value_slice[0].stop:
                    self._value_index_reached = -1
                    # read next chunk
                    try:
                        self._current_value_slice = next(self._value_chunk_iter)
                    except StopIteration:
                        break
                    self._value_buffer = self._value_dataset[self._current_value_slice]

                self._time_index_reached += 1
                if self._time_index_reached == self._current_time_slice[0].stop:
                    self._time_index_reached = -1
                    # read next chunk
                    try:
                        self._current_time_slice = next(self._time_chunk_iter)
                    except StopIteration:
                        break
                    self._time_buffer = self._time_dataset[self._current_time_slice]

                yield self._value_buffer[self._value_index_reached], self._convert_time(
                    self._time_buffer[self._value_index_reached]
                ) + self._time_offset_ns
            else:
                self._value_index_reached += 1
                if (
                    self._value_index_reached == self._value_dataset.size
                    or self._value_index_reached == self._time_dataset.size
                ):
                    break
                yield self._value_dataset[
                    self._value_index_reached
                ], self._convert_time(
                    self._time_dataset[self._value_index_reached]
                ) + self._time_offset_ns

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
        group_name = self._group.name.split("/")[-1]
        # if group name is "value_log" then use parent group name instead
        # all sample env logs in ISIS files have name value_log...
        if group_name != "value_log":
            return group_name
        return self._group.name.split("/")[-2]
