import pint
from typing import Callable, Union, Optional

ureg = pint.UnitRegistry()
SECONDS = ureg("seconds")
MILLISECONDS = ureg("milliseconds")
MICROSECONDS = ureg("microseconds")
NANOSECONDS = ureg("nanoseconds")


def seconds_to_nanoseconds(input_value: Union[float, int]):
    return int(input_value / 1_000_000_000)


def milliseconds_to_nanoseconds(input_value: Union[float, int]):
    return int(input_value / 1_000_000)


def microseconds_to_nanoseconds(input_value: Union[float, int]):
    return int(input_value / 1_000)


def nanoseconds_to_nanoseconds(input_value: Union[float, int]):
    return int(input_value)


def get_to_nanoseconds_conversion_method(units: str) -> Optional[Callable]:
    input_units = ureg(units)

    if input_units == SECONDS:
        print("seconds")
        return seconds_to_nanoseconds
    elif input_units == MILLISECONDS:
        print("milliseconds")
        return milliseconds_to_nanoseconds
    elif input_units == MICROSECONDS:
        print("microseconds")
        return microseconds_to_nanoseconds
    elif input_units == NANOSECONDS:
        print("nanoseconds")
        return nanoseconds_to_nanoseconds
    return None
