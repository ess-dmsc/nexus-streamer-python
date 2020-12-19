from nexus_streamer.parse_commandline_args import parse_args, get_version
from nexus_streamer.application_logger import setup_logger

if __name__ == "__main__":
    args = parse_args()

    logger = setup_logger(
        level=args.verbosity,
        log_file_name=args.log_file,
        graylog_logger_address=args.graylog_logger_address,
    )
    version = get_version()
    logger.info(f"NeXus Streamer v{version} started")
