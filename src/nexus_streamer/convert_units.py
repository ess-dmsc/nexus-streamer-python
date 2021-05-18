import pint
from typing import Callable, Union
from pint.errors import UndefinedUnitError
import numpy as np
from datetime import datetime, timezone
import dateutil.parser

ureg = pint.UnitRegistry()
SECONDS = ureg("seconds")
MILLISECONDS = ureg("milliseconds")
MICROSECONDS = ureg("microseconds")
NANOSECONDS = ureg("nanoseconds")


def iso8601_to_ns_since_epoch(iso8601_timestamp: Union[str, bytes]) -> int:
    try:
        iso8601_timestamp = str(iso8601_timestamp, encoding="utf8")  # type: ignore
    except TypeError:
        pass
    offset_datetime = dateutil.parser.parse(iso8601_timestamp)
    if offset_datetime.tzinfo is None:
        # Assume time is UTC if it was not explicit
        offset_datetime = offset_datetime.replace(tzinfo=timezone.utc)
    ns_since_unix_epoch = int(
        offset_datetime.timestamp() * 1_000_000_000
    )  # s float to ns int
    return ns_since_unix_epoch


def ns_since_epoch_to_iso8601(ns_since_epoch: int) -> str:
    dt = datetime.fromtimestamp(ns_since_epoch * 0.000000001)
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def seconds_to_nanoseconds(input_value: Union[float, int, np.ndarray]) -> np.ndarray:
    return (np.array(input_value) * 1_000_000_000).astype(int)


def milliseconds_to_nanoseconds(
    input_value: Union[float, int, np.ndarray]
) -> np.ndarray:
    return (np.array(input_value) * 1_000_000).astype(int)


def microseconds_to_nanoseconds(
    input_value: Union[float, int, np.ndarray]
) -> np.ndarray:
    return (np.array(input_value) * 1_000).astype(int)


def nanoseconds_to_nanoseconds(
    input_value: Union[float, int, np.ndarray]
) -> np.ndarray:
    return np.array(input_value).astype(int)


def get_to_nanoseconds_conversion_method(units: Union[str, bytes]) -> Callable:
    try:
        units = str(units, encoding="utf8")  # type: ignore
    except TypeError:
        pass
    input_units = ureg(units)

    if input_units == SECONDS:
        return seconds_to_nanoseconds
    elif input_units == MILLISECONDS:
        return milliseconds_to_nanoseconds
    elif input_units == MICROSECONDS:
        return microseconds_to_nanoseconds
    elif input_units == NANOSECONDS:
        return nanoseconds_to_nanoseconds
    else:
        raise UndefinedUnitError
