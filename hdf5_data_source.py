from data_chunk import LogDataChunk, EventDataChunk


class LogDataSource:
    def __init__(self):
        """
        Load data, one chunk at a time from NXlog in NeXus file
        """
        pass

    def get_data(self) -> (LogDataChunk, int):
        pass


class EventDataSource:
    def __init__(self):
        """
        Load data, one pulse at a time from NXevent_data in NeXus file
        """
        pass

    def get_data(self) -> (EventDataChunk, int):
        pass
