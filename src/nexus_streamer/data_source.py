from typing import Union
from .event_data_source import EventDataSource, FakeEventDataSource
from .log_data_source import LogDataSource
from .isis_data_source import IsisDataSource

DataSource = Union[LogDataSource, EventDataSource, FakeEventDataSource, IsisDataSource]
