from pathlib import Path
import logging
from bennchplot.io.config.models import Config
from bennchplot.io import yaml

log = logging.getLogger(__name__)

def loadConfig(file_name = "config.yaml") -> Config:
    log.debug("loading config from %s", file_name)
    with Path(file_name).open(encoding="utf8") as in_file:
        return Config.model_validate(yaml.load(in_file))