# NeXus Streamer

Streams event and metadata from a NeXus file into Kafka, mimicking data acquisition from a live instrument. This facilitates testing software which consume these data.

This Python implementation is intended to replace a C++ implementation (https://github.com/ess-dmsc/NeXus-Streamer) and should be much lower effort to maintain.

## Installation

Python 3.7 or higher is required. https://www.python.org/downloads/

To install from PyPi do
```commandline
pip install nexus-streamer
```

or to install with conda (does not work on Windows due to confluent-kafka package not supporting Windows)
```commandline
conda install -c conda-forge -c ess-dmsc nexus-streamer
```

and check installation was successful by running
```commandline
nexus_streamer --help
```
on Windows you may need to add your Python environment's `Script` directory to `PATH` for the command to work.

## Usage
```commandline
usage: nexus_streamer [-h]
                      [--graylog-logger-address GRAYLOG_LOGGER_ADDRESS]
                      [--log-file LOG_FILE] [-c CONFIG_FILE]
                      [-v {Trace,Debug,Warning,Error,Critical}] -f
                      FILENAME [--json-description JSON_DESCRIPTION] -b
                      BROKER -i INSTRUMENT [-s] [-z]
                      [-e FAKE_EVENTS_PER_PULSE]

NeXus Streamer

optional arguments:
  -h, --help            show this help message and exit
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
  -e FAKE_EVENTS_PER_PULSE, --fake-events-per-pulse FAKE_EVENTS_PER_PULSE
                        Generates this number of fake events per pulse
                        perevent data group instead of publishing real data
                        from file [env var: FAKE_EVENTS]

Args that start with '--' (eg. --graylog-logger-address) can also be set in a
config file (specified via -c). Config file syntax allows: key=value,
flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi).
If an arg is specified in more than one place, then commandline values
override environment variables which override config file values which
override defaults.
```

The fake events generated if `--fake-events-per-pulse` is used are a random 
detector id, selected from the detector's ids, and a random time-of-flight
between 10 and 10000 milliseconds. The intention is to provide a specified quantity
of data for performance testing consuming applications.

### Minimum requirements of the file

The NeXus file used must have an [NXentry](https://manual.nexusformat.org/classes/base_classes/NXentry.html#nxentry)
group containing a `start_time` dataset containing the run start time as an iso8601 string.

`NXevent_data` and `NXlog` groups will be found wherever they are in the file and streamed to Kafka.
All `time` and `value` datasets must have a `units` attribute.

If `--fake-events-per-pulse` is used then each `NXevent_data` group must be in an
`NXdetector` with a `detector_number` dataset.

## Developer information

See [README-dev.md](README-dev.md)
