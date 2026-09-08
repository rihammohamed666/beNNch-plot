"Configuration module."

import logging
from pathlib import Path

from bennch.plot.io import model2dict, yaml
from bennch.plot.io.config.models import Config

log = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAME = "config.yaml"


def load_config(filename=DEFAULT_CONFIG_FILENAME) -> Config:
    "Load and parse config from given filename."
    log.debug("loading config from %s", filename)
    with Path(filename).open(encoding="utf8") as infile:
        return Config.model_validate(yaml.load(infile))


def save_config(config: Config, filename: str | Path = DEFAULT_CONFIG_FILENAME) -> None:
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


class ConfigContext:
    "Handle read and write of config object as context-manager."

    def __init__(self, filename: str | Path = DEFAULT_CONFIG_FILENAME):
        self._filename = Path(filename)
        self._config: Config | None = None
        if not self._filename.exists() and self._filename.is_file():
            log.warning("configuration file does not exist, or is not a file: %s", self._filename)

    def __enter__(self) -> Config:
        "Load config on entering the context."
        self._config = load_config(self._filename)
        return self._config

    def __exit__(self, exc, tb, stack):
        "Save config when exiting the context in non-exception case."
        if exc is not None:
            log.error("not saving config due to exception: %s", exc)
            return
        if not isinstance(self._config, Config):
            log.error("not saving config, as config object seems broken: %s", type(self._config))
            return
        save_config(self._config, self._filename)
