"Configuration module."

import logging
from pathlib import Path

from bennch.plot.io import model2dict, yaml
from bennch.plot.io.config.models import Config

log = logging.getLogger(__name__)


def load_config(filename="config.yaml") -> Config:
    "Load and parse config from given filename."
    log.debug("loading config from %s", filename)
    with Path(filename).open(encoding="utf8") as infile:
        return Config.model_validate(yaml.load(infile))


def save_config(config: Config, filename: str | Path = "config.yaml") -> None:
    "Load and parse config from given filename."
    log.debug("saving config to %s", filename)
    draft = Path(str(filename) + ".draft")
    log.debug("intermediate file %s", draft)
    with draft.open("w", encoding="utf8") as outfile:
        log.debug("writing...")
        yaml.dump(model2dict(config), outfile)
        log.debug("written.")
    # if above didn't raise anything
    try:
        log.debug("renaming %s to %s", draft, filename)
        draft.rename(filename)  # atomic move to the right file
    finally:
        if draft.exists():
            draft.unlink()  # remove remnants after failue.
