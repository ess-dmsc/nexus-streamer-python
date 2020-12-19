from time import time_ns
import asyncio
from data_source import DataSource
from publisher import Publisher


class SourceToStream:
    def __init__(
        self,
        source_name: str,
        source: DataSource,
        publisher: Publisher,
        start_time_delta_ns: int,
        interval_s: float = 0.2,
    ):
        """
        :param source_name: name of data source
        :param source: data source, for example an NXlog in a NeXus file or a fake/simulated data source
        :param publisher: data from data source is given to the publisher at appropriate time
        :param start_time_delta_ns: diff between time publishing started and start time of the run in the data source
        :param interval_s: idle time between publishing data to allow other async tasks to run
        """
        self._source_name = source_name
        self._data_source = source
        self._publisher = publisher
        self._interval = interval_s
        self._start_time_delta_ns = start_time_delta_ns
        self._cancelled = False
        self._publish_data = None

    def start(self):
        self._cancelled = False
        self._publish_data = asyncio.create_task(self._publish_loop())

    def stop(self):
        if not self._cancelled:
            self._cancelled = True
            if self._publish_data is not None:
                self._publish_data.cancel()

    async def _publish_loop(self):
        last_timestamp_ns = 0
        while not self._cancelled:
            await asyncio.sleep(self._interval)
            current_run_time_ns = time_ns() - self._start_time_delta_ns
            while last_timestamp_ns < current_run_time_ns:
                data, last_timestamp_ns = self._data_source.get_data()
                self._publisher.publish(data)
