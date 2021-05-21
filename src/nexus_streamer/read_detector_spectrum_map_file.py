import numpy as np
from typing import Tuple


def read_map(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (detector ids, spectrum numbers)
    """
    det_spec_map = np.genfromtxt(file_path, skip_header=3, dtype=np.int32)
    return det_spec_map[:, 0], det_spec_map[:, 1]
