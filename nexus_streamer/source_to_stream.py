from time import time_ns
import asyncio
from nexus_streamer.data_source import LogDataSource, EventDataSource
from typing import Optional, Any, Union
from nexus_streamer.kafka_producer import KafkaProducer
from streaming_data_types.logdata_f142 import serialise_f142
from streaming_data_types.eventdata_ev42 import serialise_ev42


class LogSourceToStream:
    def __init__(
        self,
        source_name: str,
        source: LogDataSource,
        producer: KafkaProducer,
        output_topic: str,
        start_time_delta_ns: int,
        interval_s: float = 0.2,
    ):
        """
        :param source_name: name of data source
        :param source: log data source
        :param publisher: data from data source is given to the publisher at appropriate time
        :param start_time_delta_ns: diff between time publishing started and start time of the run in the data source
        :param interval_s: idle time between publishing data to allow other async tasks to run
        """
        self._source_name = source_name
        self._data_source = source
        self._producer = producer
        self._topic = output_topic
        self._interval = interval_s
        self._start_time_delta_ns = start_time_delta_ns
        self._cancelled = False
        self._publish_data: Optional[asyncio.Task[Any]] = None

    def start(self):
        self._cancelled = False
        self._publish_data = asyncio.create_task(self._publish_loop())

    def stop(self):
        if not self._cancelled:
            self._cancelled = True
            if self._publish_data is not None:
                self._publish_data.cancel()

    @property
    def done(self):
        return self._cancelled

    async def _publish_loop(self):
        last_timestamp_ns = 0
        get_data = self._data_source.get_data()
        while not self._cancelled:
            await asyncio.sleep(self._interval)
            current_run_time_ns = time_ns() - self._start_time_delta_ns
            while last_timestamp_ns < current_run_time_ns:
                value, last_timestamp_ns = next(get_data)
                if value is not None:
                    payload = serialise_f142(
                        value, self._source_name, last_timestamp_ns
                    )
                    await self._producer.produce(self._topic, payload)
                else:
                    self._cancelled = True
                    break


class EventSourceToStream:
    def __init__(
        self,
        source_name: str,
        source: EventDataSource,
        producer: KafkaProducer,
        output_topic: str,
        start_time_delta_ns: int,
        interval_s: float = 0.2,
    ):
        """
        :param source_name: name of data source
        :param source: event data source
        :param publisher: data from data source is given to the publisher at appropriate time
        :param start_time_delta_ns: diff between time publishing started and start time of the run in the data source
        :param interval_s: idle time between publishing data to allow other async tasks to run
        """
        self._source_name = source_name
        self._data_source = source
        self._producer = producer
        self._topic = output_topic
        self._interval = interval_s
        self._start_time_delta_ns = start_time_delta_ns
        self._cancelled = False
        self._publish_data: Optional[asyncio.Task[Any]] = None
        self._message_id = 0

    def start(self):
        self._cancelled = False
        self._publish_data = asyncio.create_task(self._publish_loop())

    def stop(self):
        if not self._cancelled:
            self._cancelled = True
            if self._publish_data is not None:
                self._publish_data.cancel()

    @property
    def done(self):
        return self._cancelled

    async def _publish_loop(self):
        last_timestamp_ns = 0
        get_data = self._data_source.get_data()
        while not self._cancelled:
            await asyncio.sleep(self._interval)
            current_run_time_ns = time_ns() - self._start_time_delta_ns
            while last_timestamp_ns < current_run_time_ns:
                time_of_flight, detector_id, last_timestamp_ns = next(get_data)
                if time_of_flight is not None:
                    payload = serialise_ev42(
                        self._source_name,
                        self._message_id,
                        last_timestamp_ns,
                        time_of_flight,
                        detector_id,
                    )
                    await self._producer.produce(self._topic, payload)
                    self._message_id += 1
                else:
                    self._cancelled = True
                    break


SourceToStream = Union[LogSourceToStream, EventSourceToStream]
