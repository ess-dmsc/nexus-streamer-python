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
from typing import List
import asyncio


async def publish_run(producer: KafkaProducer):
    streamers: List[SourceToStream] = []
    try:
        # TODO Need run start time from the file
        #  and other info to make run start message
        # start_time = time_ns()
        start_time_delta_ns = 0

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
                        source.name,
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
                        source.name,
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

    asyncio.run(publish_run(kafka_producer))
