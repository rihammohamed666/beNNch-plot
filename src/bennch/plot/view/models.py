"View models."

import logging
from enum import StrEnum

from pydantic import BaseModel

log = logging.getLogger(__name__)


class ModelType(StrEnum):
    "Enumeration of known model types."

    MICROCIRCUIT = "microcircuit"
    HPC_BENCHMARK = "hpc_benchmark"
    MULTI_AREA = "multi_area"


class ScalingPlotData(BaseModel):
    "Data model for a single scaling plot."

    num_nodes: list[int]
    time_simulate: list[float]
    time_construction_create: list[float]
    time_construction_connect: list[float]
    sim_factor: list[float]
