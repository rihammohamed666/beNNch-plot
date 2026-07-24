"View models."

import logging
from enum import StrEnum

log = logging.getLogger(__name__)


class ModelType(StrEnum):
    "Enumeration of known model types."

    MICROCIRCUIT = "microcircuit"
    HPC_BENCHMARK = "hpc_benchmark"
    MULTI_AREA = "multi_area"
