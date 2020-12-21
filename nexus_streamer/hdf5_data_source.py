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

    def get_data(self) -> Generator[Tuple[Optional[np.ndarray], int], None, None]:
        """
        Returns None instead of a data when there is no more data
        """
        yield None, 0

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
                f"Unable to publish data from NXlog at {self._group.name} due to unrecognised "
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
                    f"Unable to publish data from NXlog at {self._group.name} due to missing {field} field"
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
