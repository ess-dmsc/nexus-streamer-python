from typing import Union
from nexus_streamer.hdf5_data_source import LogDataSource, EventDataSource

DataSource = Union[LogDataSource, EventDataSource]
