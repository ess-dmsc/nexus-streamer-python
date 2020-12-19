from dataclasses import dataclass
import numpy as np


@dataclass
class LogDataChunk:
    values: np.ndarray
    times: np.ndarray


@dataclass
class EventDataChunk:
    pass
