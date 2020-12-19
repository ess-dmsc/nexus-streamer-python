from typing import Union
from streaming_data_types.logdata_f142 import serialise_f142
from streaming_data_types.eventdata_ev42 import serialise_ev42
import numpy as np
from nexus_streamer.data_chunk import LogDataChunk, EventDataChunk
from nexus_streamer.kafka_producer import KafkaProducer


class LogDataPublisher:
    def __init__(self, producer: KafkaProducer, output_topic: str):
        self._producer = producer
        self._topic = output_topic

    async def publish(self, data: LogDataChunk, source_name: str):
        for time, value in np.column_stack((data.times, data.values)):
            await self._producer.produce(
                self._topic, serialise_f142(value, source_name, time)
            )


class EventDataPublisher:
    def __init__(self, producer: KafkaProducer, output_topic: str):
        self._producer = producer
        self._topic = output_topic
        self._message_id = 0

    async def publish(self, data: EventDataChunk, source_name: str):
        await self._producer.produce(
            self._topic,
            serialise_ev42(
                source_name,
                self._message_id,
                data.pulse_time,
                data.time_of_flight,
                data.detector_id,
            ),
        )
        self._message_id += 1


Publisher = Union[LogDataPublisher, EventDataPublisher]
