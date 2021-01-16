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
from typing import List
import asyncio


async def publish_run(producer: KafkaProducer, run_number: int):
    streamers: List[SourceToStream] = []
    try:
        # TODO Need run start time from the file
        # start_time = time_ns()
        # Alter start_time_delta_ns to change start time of run from the one recorded in the file,
        #  for example to appear as if the data is being produced by the beamline as the NeXus Streamer is running
        start_time_delta_ns = 0

        nexus_structure = "{}"
        job_id = publish_run_start_message(
            args.instrument,
            run_number,
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
                        f"{args.instrument}_sampleEnv",
                        start_time_delta_ns,
                    )
                    for source in log_data_sources
                ]
            )
            streamers.extend(
                [
                    EventSourceToStream(
                        source,
                        producer,
                        f"{args.instrument}_events",
                        start_time_delta_ns,
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
    except Exception as e:
        logger.critical(f"Error caused streaming to abort: {e}")
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

    producer_config = {"bootstrap.servers": args.broker}
    kafka_producer = KafkaProducer(producer_config)

    run_number = 0
    asyncio.run(publish_run(kafka_producer, run_number))
