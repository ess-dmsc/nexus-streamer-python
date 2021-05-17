# NeXus Streamer

This is intended to replace https://github.com/ess-dmsc/NeXus-Streamer with a Python implementation which should be much lower effort to maintain. The C++ implmentation is not yet obsolete, missing features in this implementation are documented in tickets.

## Installation

Python 3.7 or higher is required. https://www.python.org/downloads/

To install from source with setuptools do
```commandline
python setup.py install
```

or to install from conda do
```commandline
conda install -c conda-forge -c ess-dmsc nexus-streamer
```

and check installation was successful by running
```commandline
nexus_streamer --help
```

## Usage
```commandline
usage: nexus_streamer [-h] [--version]
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

## Developer information

See [README-dev.md](README-dev.md)
