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
from .publish_run_message import publish_run_start_message
from .generate_json_description import nexus_file_to_json_description
from .create_data_sources_from_nexus import get_recorded_run_start_time_ns
from typing import List
import asyncio
from time import time_ns
from .convert_units import ns_since_epoch_to_iso8601


async def publish_run(producer: KafkaProducer, run_id: int, args, logger):
    streamers: List[SourceToStream] = []
    try:
        with h5py.File(args.filename, "r") as nexus_file:
            log_data_sources, event_data_sources = create_data_sources_from_nexus_file(
                nexus_file, args.fake_events_per_pulse
            )

            if not log_data_sources and not event_data_sources:
                logger.critical("No valid data sources found in file, aborting")
                return

            last_timestamp = max(
                [
                    source.final_timestamp
                    for source in event_data_sources + log_data_sources  # type: ignore
                ]
            )

            (
                recorded_run_start_time_ns,
                run_start_ds_path,
            ) = get_recorded_run_start_time_ns(args.filename)

            # start_time_delta_ns = time difference between starting to stream with
            # NeXus Streamer and the run start time which was recorded in the NeXus
            # file, used as an offset for all timestamps so that output appears as
            # if the data is being produced live by the beamline.
            if args.slow:
                streamer_start_time = time_ns()
                start_time_delta_ns = streamer_start_time - recorded_run_start_time_ns
                stop_time_ns = last_timestamp + start_time_delta_ns
                run_duration = stop_time_ns - streamer_start_time
            else:
                # If we are publishing data into Kafka as fast as we can then we
                # must pretend the run has already happened. Make the current wall
                # clock time the run stop time. Otherwise consumers such as scippneutron
                # must wait until a run stop time in the future to be sure that they have
                # received all data.
                stop_time_ns = time_ns()
                run_duration = last_timestamp - recorded_run_start_time_ns
                streamer_start_time = stop_time_ns - run_duration
                start_time_delta_ns = streamer_start_time - recorded_run_start_time_ns

            logger.info(
                f"Run:\n"
                f"start: {ns_since_epoch_to_iso8601(streamer_start_time)}\n"
                f"stop: {ns_since_epoch_to_iso8601(stop_time_ns)}\n"
                f"duration: {run_duration/1e9} seconds"
            )

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

            map_det_ids = None
            map_spec_nums = None
            publish_run_start_message(
                args.instrument,
                run_id,
                args.broker,
                nexus_structure,
                producer,
                f"{args.instrument}_runInfo",
                map_det_ids,
                map_spec_nums,
                streamer_start_time,
                stop_time_ns,
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

    producer_config = {
        "bootstrap.servers": args.broker,
        "message.max.bytes": 1_000_000_000,  # Confluent Kafka lib tops out a 1 GB
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
