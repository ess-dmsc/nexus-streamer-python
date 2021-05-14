# NeXus Streamer

Streams event and metadata from a NeXus file into Kafka, mimicking data acquisition from a live instrument. This facilitates testing software which consume these data.

This Python implementaation is intended to replace a C++ implementation (https://github.com/ess-dmsc/NeXus-Streamer) and should be much lower effort to maintain. The C++ implmentation is not yet obsolete; features missing from this implementation are documented in tickets.

## Usage
```
usage: launch_nexus_streamer.py [-h] [--version]
                                [--graylog-logger-address GRAYLOG_LOGGER_ADDRESS]
                                [--log-file LOG_FILE] [-c CONFIG_FILE]
                                [-v {Trace,Debug,Warning,Error,Critical}] -f
                                FILENAME [--json-description JSON_DESCRIPTION]
                                -b BROKER -i INSTRUMENT [-s] [-z]

NeXus Streamer Args that start with '--' (eg. --version) can also be set in a
config file (specified via -c). Config file syntax allows: key=value,
flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi).
If an arg is specified in more than one place, then commandline values
override environment variables which override config file values which
override defaults.

optional arguments:
  -h, --help            show this help message and exit
  --version             Print application version and exit [env var: VERSION]
  --graylog-logger-address GRAYLOG_LOGGER_ADDRESS
                        <host:port> Log to Graylog [env var:
                        GRAYLOG_LOGGER_ADDRESS]
  --log-file LOG_FILE   Log filename [env var: LOG_FILE]
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Read configuration from an ini file [env var:
                        CONFIG_FILE]
  -v {Trace,Debug,Warning,Error,Critical}, --verbosity {Trace,Debug,Warning,Error,Critical}
                        Set logging level [env var: VERBOSITY]
  -f FILENAME, --filename FILENAME
                        NeXus file to stream data from [env var: FILENAME]
  --json-description JSON_DESCRIPTION
                        If provided use this JSON template instead of
                        generating one from the NeXus file [env var:
                        JSON_FILENAME]
  -b BROKER, --broker BROKER
                        <host[:port]> Kafka broker to forward data into [env
                        var: BROKER]
  -i INSTRUMENT, --instrument INSTRUMENT
                        Used as prefix for topic names [env var: INSTRUMENT]
  -s, --slow            Stream data into Kafka at approx realistic rate (uses
                        timestamps from file) [env var: SLOW]
  -z, --single-run      Publish only a single run (otherwise repeats until
                        interrupted) [env var: SINGLE_RUN]

```

## Installing dependencies

Python 3.7 or higher is required. https://www.python.org/downloads/

Runtime Python dependencies are listed in `requirements.txt` at the root of the
repository. They can be installed from a terminal by running
```
pip install -r requirements.txt
```

## Developer information

### Development dependencies

Development dependencies (including all runtime dependencies) can be installed by using the following command

```
pip install -r requirements-dev.txt
```

`black`, `flake8` and `mypy` can be used as a pre-commit hook (installed by [pre-commit](https://pre-commit.com/)).
You need to run
```
pre-commit install
```
once to activate the pre-commit check.
To test the hooks run
```
pre-commit run --all-files
```
This command can also be used to run the hooks manually.
