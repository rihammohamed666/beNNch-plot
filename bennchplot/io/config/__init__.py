from pathlib import Path
from bennchplot.io.config.models import Config

from bennchplot.io import yaml

def loadConfig(file_name = "config.yaml") -> Config:
    with Path(file_name).open(encoding="utf8") as in_file:
        return Config.model_validate(yaml.load(in_file))