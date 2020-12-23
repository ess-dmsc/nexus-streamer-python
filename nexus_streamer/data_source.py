from typing import Union
from nexus_streamer.event_data_source import EventDataSource
from nexus_streamer.log_data_source import LogDataSource

DataSource = Union[LogDataSource, EventDataSource]
