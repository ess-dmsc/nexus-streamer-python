from .parse_commandline_args import parse_args
from .application_logger import setup_logger
from .create_data_sources_from_nexus import (
    create_data_sources_from_nexus_file,
)
import h5py
from .kafka_producer import KafkaProducer
from .source_to_stream import (
    LogSourceToStream,
    EventSourceToStream,
    SourceToStream,
)
from .publish_run_message import (
    publish_run_start_message,
    publish_run_stop_message,
)

from .generate_json_description import nexus_file_to_json_description
from .create_data_sources_from_nexus import get_recorded_run_start_time_ns
from typing import List
import asyncio
from time import time_ns
from .isis_data_source import IsisDataSource
from .read_detector_spectrum_map_file import read_map


async def publish_run(producer: KafkaProducer, run_id: int, args, logger):
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
        if args.json_description:
            with open(args.json_description, "r") as json_file:
                nexus_structure = json_file.read()
                nexus_structure = replace_placeholder_topic_names(
                    nexus_structure, log_data_topic, event_data_topic
                )
        else:
            nexus_structure = nexus_file_to_json_description(
                args.filename,
                event_data_topic,
                log_data_topic,
                streamer_start_time,
                run_start_ds_path,
            )

        map_det_ids = None
        map_spec_nums = None
        if args.det_spec_map is not None:
            map_det_ids, map_spec_nums = read_map(args.det_spec_map)

        job_id = publish_run_start_message(
            args.instrument,
            run_id,
            args.broker,
            nexus_structure,
            producer,
            f"{args.instrument}_runInfo",
            map_det_ids,
            map_spec_nums,
        )

        with h5py.File(args.filename, "r") as nexus_file:
            log_data_sources, event_data_sources = create_data_sources_from_nexus_file(
                nexus_file, args.fake_events_per_pulse
            )

            if not log_data_sources and not event_data_sources:
                logger.critical("No valid data sources found in file, aborting")
                return

            isis_data_source = None
            if args.isis_file:
                isis_data_source = IsisDataSource(nexus_file)

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
                        isis_data_source=isis_data_source,
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


def replace_placeholder_topic_names(nexus_structure, log_data_topic, event_data_topic):
    for topic in (
        ("SAMPLE_ENV_TOPIC", log_data_topic),
        ("EVENT_DATA_TOPIC", event_data_topic),
    ):
        nexus_structure = nexus_structure.replace(topic[0], topic[1])
    return nexus_structure


def launch_streamer():
    args = parse_args()
    logger = setup_logger(
        level=args.verbosity,
        log_file_name=args.log_file,
        graylog_logger_address=args.graylog_logger_address,
    )
    logger.info("NeXus Streamer started")

    if args.isis_file and not args.det_spec_map:
        logger.warning(
            "ISIS file was specified but no detector-spectrum map was provided,"
            "events may not be mapped to the correct detector pixel by consumer applications"
        )

    producer_config = {
        "bootstrap.servers": args.broker,
        "message.max.bytes": 200000000,
    }
    kafka_producer = KafkaProducer(producer_config)
    run_number = 0
    if args.single_run:
        asyncio.run(publish_run(kafka_producer, run_number, args, logger))
        logger.info(f"Completed streaming run {run_number}")
    else:
        while True:
            asyncio.run(publish_run(kafka_producer, run_number, args, logger))
            logger.info(f"Streamed run {run_number}")
            run_number += 1


if __name__ == "__main__":
    launch_streamer()
