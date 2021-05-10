from nexus_streamer.parse_commandline_args import parse_args, get_version
from nexus_streamer.application_logger import setup_logger
from nexus_streamer.create_data_sources_from_nexus import (
    create_data_sources_from_nexus_file,
)
import h5py
from nexus_streamer.kafka_producer import KafkaProducer
from nexus_streamer.source_to_stream import (
    LogSourceToStream,
    EventSourceToStream,
    SourceToStream,
)
from nexus_streamer.publish_run_message import (
    publish_run_start_message,
    publish_run_stop_message,
)

from nexus_streamer.generate_json_description import nexus_file_to_json_description
from nexus_streamer.create_data_sources_from_nexus import get_recorded_run_start_time_ns
from typing import List
import asyncio
from time import time_ns


async def publish_run(producer: KafkaProducer, run_id: int):
    streamers: List[SourceToStream] = []
    try:
        recorded_run_start_time_ns, run_start_ds_path = get_recorded_run_start_time_ns(
            args.filename
        )
        # Time difference between starting to stream with NeXus Streamer and the run start time which was recorded
        # in the NeXus file, used as an offset for all timestamps so that output appears as if the data is being
        # produced live by the beamline
        streamer_start_time = time_ns()
        start_time_delta_ns = streamer_start_time - recorded_run_start_time_ns

        log_data_topic = f"{args.instrument}_sampleEnv"
        event_data_topic = f"{args.instrument}_events"
        nexus_structure = nexus_file_to_json_description(
            args.filename,
            event_data_topic,
            log_data_topic,
            streamer_start_time,
            run_start_ds_path,
        )

        job_id = publish_run_start_message(
            args.instrument,
            run_id,
            args.broker,
            nexus_structure,
            producer,
            f"{args.instrument}_runInfo",
        )

        with h5py.File(args.filename, "r") as nexus_file:
            log_data_sources, event_data_sources = create_data_sources_from_nexus_file(
                nexus_file
            )

            if not log_data_sources and not event_data_sources:
                logger.critical("No valid data sources found in file, aborting")
                return

            streamers.extend(
                [
                    LogSourceToStream(
                        source,
                        producer,
                        log_data_topic,
                        start_time_delta_ns,
                        slow_mode=args.slow,
                    )
                    for source in log_data_sources
                ]
            )
            streamers.extend(
                [
                    EventSourceToStream(
                        source,
                        producer,
                        event_data_topic,
                        start_time_delta_ns,
                        slow_mode=args.slow,
                    )
                    for source in event_data_sources
                ]
            )

            logger.info(
                f"Publishing log data sources: {[source.name for source in log_data_sources]}"
            )
            logger.info(
                f"Publishing event data sources: {[source.name for source in event_data_sources]}"
            )
            for streamer in streamers:
                streamer.start()

            while not all([streamer.done for streamer in streamers]):
                await asyncio.sleep(1.0)

            logger.info("Reached end of data sources")
        publish_run_stop_message(job_id, producer, f"{args.instrument}_runInfo")

    except KeyboardInterrupt:
        logger.info("%% Aborted by user")
    finally:
        for streamer in streamers:
            streamer.stop()
        producer.close()


if __name__ == "__main__":
    args = parse_args()

    logger = setup_logger(
        level=args.verbosity,
        log_file_name=args.log_file,
        graylog_logger_address=args.graylog_logger_address,
    )
    version = get_version()
    logger.info(f"NeXus Streamer v{version} started")

    producer_config = {
        "bootstrap.servers": args.broker,
        "message.max.bytes": 200000000,
    }
    kafka_producer = KafkaProducer(producer_config)

    run_number = 0
    asyncio.run(publish_run(kafka_producer, run_number))
