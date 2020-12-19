from typing import Union
from hdf5_data_source import LogDataSource, EventDataSource

DataSource = Union[LogDataSource, EventDataSource]
