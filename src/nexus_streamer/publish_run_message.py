from streaming_data_types.run_start_pl72 import serialise_pl72
from streaming_data_types.run_stop_6s4t import serialise_6s4t
from uuid import uuid4
from time import time_ns
from .kafka_producer import KafkaProducer


def publish_run_start_message(
    instrument_name: str,
    run_number: int,
    broker: str,
    nexus_structure: str,
    producer: KafkaProducer,
    topic: str,
) -> str:
    filename = f"FromNeXusStreamer_{run_number}.nxs"
    job_id = str(uuid4())
    start_time_ns = time_ns()
    start_time_ms = int(start_time_ns * 0.000001)
    run_start_payload = serialise_pl72(
        job_id,
        filename,
        start_time=start_time_ms,
        run_name=str(run_number),
        nexus_structure=nexus_structure,
        instrument_name=instrument_name,
        broker=broker,
    )
    producer.produce(topic, run_start_payload, start_time_ns)
    return job_id


def publish_run_stop_message(
    job_id: str,
    producer: KafkaProducer,
    topic: str,
) -> str:
    """
    job_id must match the one used in the corresponding run start message
    """
    stop_time_ns = time_ns()
    stop_time_ms = int(stop_time_ns * 0.000001)
    run_stop_payload = serialise_6s4t(job_id, stop_time=stop_time_ms)
    producer.produce(topic, run_stop_payload, stop_time_ns)
    return job_id
