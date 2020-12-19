from data_chunk import LogDataChunk, EventDataChunk
import h5py


class LogDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one chunk at a time from NXlog in NeXus file
        """
        self._group = group

    def get_data(self) -> (LogDataChunk, int):
        pass


class EventDataSource:
    def __init__(self, group: h5py.Group):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        """
        self._group = group

    def get_data(self) -> (EventDataChunk, int):
        pass
