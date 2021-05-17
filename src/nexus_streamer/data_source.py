from typing import Union
from .event_data_source import EventDataSource
from .log_data_source import LogDataSource

DataSource = Union[LogDataSource, EventDataSource]
