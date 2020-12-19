from nexus_streamer.data_chunk import LogDataChunk, EventDataChunk
import h5py
from typing import Tuple, Optional, Generator
import numpy as np


class LogDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one chunk at a time from NXlog in NeXus file
        """
        self._group = group

    def get_data(self) -> Generator[Tuple[Optional[LogDataChunk], int], None, None]:
        """
        Returns None instead of a data chunk when there is no more data
        """
        yield None, 0

    @property
    def name(self):
        return self._group.name


class EventDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        """
        self._group = group

    def get_data(self) -> Generator[Tuple[Optional[EventDataChunk], int], None, None]:
        """
        Returns None instead of a data chunk when there is no more data
        """
        event_time_zero = self._group["event_time_zero"][...]
        event_index = self._group["event_index"][...]
        event_index = np.append(
            event_index, np.array([self._group["event_id"].len() - 1])
        )
        for pulse_number in range(self._group["event_index"].len()):
            pulse_time = event_time_zero[pulse_number]
            # TODO convert pulse_time to nanoseconds if not already
            #  use pint?
            yield EventDataChunk(
                pulse_time,
                self._group["event_time_offset"][
                    event_index[pulse_number] : event_index[pulse_number + 1]
                ],
                self._group["event_id"][
                    event_index[pulse_number] : event_index[pulse_number + 1]
                ],
            ), pulse_time
        yield None, 0

    @property
    def name(self):
        return self._group.name
