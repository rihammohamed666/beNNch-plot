"Configuration module."

import logging
from pathlib import Path

from bennch.plot.io import yaml
from bennch.plot.io.config.models import Config

log = logging.getLogger(__name__)


def load_config(file_name="config.yaml") -> Config:
    "Load and parse config from given filename."
    log.debug("loading config from %s", file_name)
    with Path(file_name).open(encoding="utf8") as in_file:
        return Config.model_validate(yaml.load(in_file))
