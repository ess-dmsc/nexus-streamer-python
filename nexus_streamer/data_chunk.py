from dataclasses import dataclass
import numpy as np
from typing import Union


@dataclass
class LogDataChunk:
    values: np.ndarray
    times: np.ndarray


@dataclass
class EventDataChunk:
    pulse_time: Union[int, float]
    time_of_flight: np.ndarray
    detector_id: np.ndarray
