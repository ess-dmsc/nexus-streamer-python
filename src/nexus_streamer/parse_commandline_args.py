import logging
import configargparse


def parse_args():
    parser = configargparse.ArgumentParser(description="NeXus Streamer")
    parser.add_argument(
        "--graylog-logger-address",
        required=False,
        help="<host:port> Log to Graylog",
        type=str,
        env_var="GRAYLOG_LOGGER_ADDRESS",
    )
    parser.add_argument(
        "--log-file", required=False, help="Log filename", type=str, env_var="LOG_FILE"
    )
    parser.add_argument(
        "-c",
        "--config-file",
        required=False,
        is_config_file=True,
        help="Read configuration from an ini file",
        env_var="CONFIG_FILE",
    )
    log_choice_to_enum = {
        "Trace": logging.DEBUG,
        "Debug": logging.DEBUG,
        "Warning": logging.WARNING,
        "Error": logging.ERROR,
        "Critical": logging.CRITICAL,
    }
    parser.add_argument(
        "-v",
        "--verbosity",
        required=False,
        help="Set logging level",
        choices=log_choice_to_enum.keys(),
        default="Error",
        env_var="VERBOSITY",
    )
    parser.add_argument(
        "-f",
        "--filename",
        required=True,
        help="NeXus file to stream data from",
        env_var="FILENAME",
    )
    parser.add_argument(
        "--json-description",
        required=False,
        help="If provided use this JSON template instead of generating one from the NeXus file",
        env_var="JSON_FILENAME",
    )
    parser.add_argument(
        "-b",
        "--broker",
        required=True,
        help="<host[:port]> Kafka broker to forward data into",
        type=str,
        env_var="BROKER",
    )
    parser.add_argument(
        "-i",
        "--instrument",
        required=True,
        help="Used as prefix for topic names",
        type=str,
        env_var="INSTRUMENT",
    )
    parser.add_argument(
        "-s",
        "--slow",
        action="store_true",
        help="Stream data into Kafka at approx realistic rate (uses timestamps from file)",
        env_var="SLOW",
    )
    parser.add_argument(
        "-z",
        "--single-run",
        action="store_true",
        help="Publish only a single run (otherwise repeats until interrupted)",
        env_var="SINGLE_RUN",
    )
    parser.add_argument(
        "--isis-file",
        action="store_true",
        help="Include ISIS-specific data in event data messages and "
        "detector-spectrum map if found in file",
        env_var="ISIS_FILE",
    )
    parser.add_argument(
        "-e",
        "--fake-events-per-pulse",
        help="Generates this number of fake events per pulse per"
        "event data group instead of publishing real data from file",
        type=int,
        env_var="FAKE_EVENTS",
    )
    parser.add_argument(
        "-d",
        "--det-spec-map",
        help="Full path of a detector-spectrum map file which may be required for files from ISIS",
        env_var="DET_SPEC_MAP",
    )

    optargs = parser.parse_args()
    optargs.verbosity = log_choice_to_enum[optargs.verbosity]
    return optargs
