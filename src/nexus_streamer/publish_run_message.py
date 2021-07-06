from streaming_data_types.run_start_pl72 import serialise_pl72, DetectorSpectrumMap
from uuid import uuid4
from .kafka_producer import KafkaProducer
from typing import Optional
import numpy as np


def publish_run_start_message(
    instrument_name: str,
    run_number: int,
    broker: str,
    nexus_structure: str,
    producer: KafkaProducer,
    topic: str,
    map_det_ids: Optional[np.ndarray],
    map_spec_nums: Optional[np.ndarray],
    streamer_start_time: int,
    stop_time_ns: int,
) -> str:
    filename = f"FromNeXusStreamer_{run_number}.nxs"
    job_id = str(uuid4())
    start_time_ms = int(streamer_start_time * 0.000001)
    det_spec_map = None
    if map_spec_nums is not None:
        det_spec_map = DetectorSpectrumMap(
            map_spec_nums, map_det_ids, map_spec_nums.size
        )

    def nanoseconds_to_milliseconds(ts_ns: int) -> int:
        return ts_ns // 1_000_000

    run_start_payload = serialise_pl72(
        job_id,
        filename,
        start_time=start_time_ms,
        stop_time=nanoseconds_to_milliseconds(stop_time_ns),
        run_name=str(run_number),
        nexus_structure=nexus_structure,
        instrument_name=instrument_name,
        broker=broker,
        detector_spectrum_map=det_spec_map,
    )
    producer.produce(topic, run_start_payload, streamer_start_time)
    return job_id
