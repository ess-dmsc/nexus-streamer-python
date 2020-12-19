import h5py
import numpy as np
from os.path import join
from typing import Union, List, Dict


def find_by_nx_class(
        nx_class_names: List[str],
        root: Union[h5py.File, h5py.Group]) -> Dict[str, h5py.Group]:
    groups_with_requested_nx_class = {
        class_name: []
        for class_name in nx_class_names
    }

    def _match_nx_class(name, h5_object):
        if isinstance(h5_object, h5py.Group):
            try:
                if h5_object.attrs["NX_class"].decode(
                        "utf8") in nx_class_names:
                    groups_with_requested_nx_class[h5_object.attrs[
                        "NX_class"].decode("utf8")].append(h5_object)
            except AttributeError:
                pass

    root.visititems(_match_nx_class)
    return groups_with_requested_nx_class


def find_data_sources_in_nexus_file():
    pass
