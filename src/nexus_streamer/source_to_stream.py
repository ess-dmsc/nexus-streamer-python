from time import time_ns
import asyncio
from .data_source import (
    EventDataSource,
    LogDataSource,
    FakeEventDataSource,
    IsisDataSource,
)
from typing import Optional, Any, Union
from .kafka_producer import KafkaProducer
from streaming_data_types.logdata_f142 import serialise_f142
from streaming_data_types.eventdata_ev42 import serialise_ev42
import numpy as np


class LogSourceToStream:
    def __init__(
        self,
        source: LogDataSource,
        producer: KafkaProducer,
        output_topic: str,
        start_time_delta_ns: int,
        interval_s: float = 0.2,
        slow_mode: bool = False,
    ):
        """
        :param source: log data source
        :param producer: Kafka producer to use to publish data
        :param output_topic: Kafka topic to publish data to
        :param start_time_delta_ns: diff between time publishing started and start time of the run in the data source
        :param interval_s: idle time between publishing data to allow other async tasks to run
        """
        self._source_name = source.name
        self._data_source = source
        self._producer = producer
        self._topic = output_topic
        self._interval = interval_s
        self._start_time_delta_ns = start_time_delta_ns
        self._cancelled = False
        self._publish_data: Optional[asyncio.Task[Any]] = None
        self._slow_mode = slow_mode

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
        current_run_time_ns = np.iinfo(np.int64).max
        while not self._cancelled:
            if self._slow_mode:
                current_run_time_ns = time_ns()
            while last_timestamp_ns < current_run_time_ns:
                value, data_timestamp_ns = next(get_data)
                if value is not None:
                    if data_timestamp_ns < 0:
                        continue
                    last_timestamp_ns = data_timestamp_ns + self._start_time_delta_ns
                    payload = serialise_f142(
                        value,
                        self._source_name,
                        last_timestamp_ns,
                    )
                    self._producer.produce(
                        self._topic,
                        payload,
                        last_timestamp_ns,
                    )
                else:
                    self._cancelled = True
                    break
            await asyncio.sleep(self._interval)


class EventSourceToStream:
    def __init__(
        self,
        source: Union[EventDataSource, FakeEventDataSource],
        producer: KafkaProducer,
        output_topic: str,
        start_time_delta_ns: int,
        interval_s: float = 0.2,
        slow_mode: bool = False,
        isis_data_source: Optional[IsisDataSource] = None,
    ):
        """
        :param source: event data source
        :param producer: Kafka producer to use to publish data
        :param output_topic: Kafka topic to publish data to
        :param start_time_delta_ns: diff between time publishing started and start time of the run in the data source
        :param interval_s: idle time between publishing data to allow other async tasks to run
        """
        self._source_name = source.name
        self._data_source = source
        self._producer = producer
        self._topic = output_topic
        self._interval = interval_s
        self._start_time_delta_ns = start_time_delta_ns
        self._cancelled = False
        self._publish_data: Optional[asyncio.Task[Any]] = None
        self._message_id = 0
        self._slow_mode = slow_mode
        self._isis_data_source = isis_data_source

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
        if self._isis_data_source is not None:
            get_isis_data = self._isis_data_source.get_data()
        current_run_time_ns = np.iinfo(np.int64).max
        isis_data = None
        while not self._cancelled:
            if self._slow_mode:
                current_run_time_ns = time_ns()
            while last_timestamp_ns < current_run_time_ns:
                time_of_flight, detector_id, data_timestamp_ns = next(get_data)
                if self._isis_data_source is not None:
                    isis_data = next(get_isis_data)
                if time_of_flight is not None:
                    last_timestamp_ns = data_timestamp_ns + self._start_time_delta_ns
                    payload = serialise_ev42(
                        self._source_name,
                        self._message_id,
                        last_timestamp_ns,
                        time_of_flight,
                        detector_id,
                        isis_specific=isis_data,
                    )
                    self._producer.produce(
                        self._topic,
                        payload,
                        last_timestamp_ns,
                    )
                    self._message_id += 1
                else:
                    self._cancelled = True
                    break
            await asyncio.sleep(self._interval)


SourceToStream = Union[LogSourceToStream, EventSourceToStream]
