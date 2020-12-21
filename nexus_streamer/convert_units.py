import pint
from typing import Callable, Union
from pint.errors import UndefinedUnitError
import numpy as np

ureg = pint.UnitRegistry()
SECONDS = ureg("seconds")
MILLISECONDS = ureg("milliseconds")
MICROSECONDS = ureg("microseconds")
NANOSECONDS = ureg("nanoseconds")


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
