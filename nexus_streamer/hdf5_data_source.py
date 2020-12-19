from nexus_streamer.data_chunk import LogDataChunk, EventDataChunk
import h5py
from typing import Tuple, Optional


class LogDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one chunk at a time from NXlog in NeXus file
        """
        self._group = group

    def get_data(self) -> Tuple[Optional[LogDataChunk], int]:
        """
        Returns None instead of a data chunk when there is no more data
        """
        return None, 0

    @property
    def name(self):
        return self._group.name


class EventDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        """
        self._group = group

    def get_data(self) -> Tuple[Optional[EventDataChunk], int]:
        """
        Returns None instead of a data chunk when there is no more data
        """
        return None, 0

    @property
    def name(self):
        return self._group.name
