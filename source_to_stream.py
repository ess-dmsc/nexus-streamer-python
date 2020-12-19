from time import time_ns
import asyncio


class SourceToStream:
    def __init__(self, source_name: str, source: DataSource, publisher: Publisher, interval_s: float = 0.2):
        self._start_time_ns = time_ns()
        self._source_name = source_name
        self._data_source = source
        self._publisher = publisher
        self._interval = interval_s
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
        last_timestamp = 0
        while not self._cancelled:
            await asyncio.sleep(self._interval)
            current_run_time = time_ns()
            while last_timestamp < current_run_time
                # TODO load data, one chunk at a time for NXlog, one pulse at a time for event data
                data, last_timestamp = source.get_data()
                publisher.publish(data)