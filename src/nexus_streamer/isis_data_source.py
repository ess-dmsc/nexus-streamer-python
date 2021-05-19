from typing import Generator, Dict, Optional
import h5py
from .application_logger import get_logger
from logging import Logger
import numpy as np


def _get_log_data(
    logger: Logger, nexus_file: h5py.File, log_dataset_path: str, log_dataset_name: str
) -> Optional[np.ndarray]:
    try:
        log_dataset = nexus_file[log_dataset_path]
        return log_dataset[...]
    except KeyError:
        logger.warning(
            f"No {log_dataset_name} dataset found at {log_dataset_path} in ISIS file"
        )
    return None


class IsisDataSource:
    def __init__(self, nexus_file: h5py.File):
        logger = get_logger()

        self._proton_charge_log = _get_log_data(
            logger,
            nexus_file,
            "raw_data_1/framelog/proton_charge/value",
            "proton_charge",
        )
        self._period_log = _get_log_data(
            logger, nexus_file, "raw_data_1/framelog/period_log/value", "period_log"
        )

    def get_data(
        self,
    ) -> Generator[Dict, None, None]:
        isis_specific_data = {
            "period_number": 1,
            "run_state": 1,  # RUNNING
            "proton_charge": 0,
        }
        frame_number = 0
        while True:
            try:
                if self._proton_charge_log is not None:
                    isis_specific_data["proton_charge"] = self._proton_charge_log[
                        frame_number
                    ]
                else:
                    pass
            except IndexError:
                isis_specific_data["proton_charge"] = 0

            try:
                if self._period_log is not None:
                    isis_specific_data["period_number"] = self._period_log[frame_number]
                else:
                    pass
            except IndexError:
                isis_specific_data["period_number"] = 1

            yield isis_specific_data
            frame_number += 1
