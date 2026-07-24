"Loader for CSV data files."

import logging

import pandas as pd
from numpy import nan

log = logging.getLogger(__name__)


def load_data(data_file, aggregation: dict[str, str | list[str]]):
    """
    Load data to dataframe, to be used later when plotting.

    Group the data by specified operations.

    Attributes
    ----------
    data_file : str
        data file to be loaded and later plotted

    Raises
    ------
    ValueError
    """
    df = pd.read_csv(data_file, delimiter=",")

    for py_timer in ["py_time_create", "py_time_connect"]:
        if py_timer not in df:
            df[py_timer] = nan
            log.warning("Python timers are not found. Construction time measurements will not be accurate.")

    return (
        df.drop("rng_seed", axis=1)
        .groupby(["num_nodes", "threads_per_task", "tasks_per_node", "model_time_sim"], as_index=False)
        .agg(aggregation)
    )
