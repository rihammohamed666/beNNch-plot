from bennchplot.io.config.models import VarConfig, SourceConfig
from subprocess import check_call
import logging

log = logging.getLogger(__name__)

def get_variable_value(uuid: str, var: VarConfig, source: SourceConfig) -> None:
    "Get the triggering pipeline ID of the given simulation."
    log.debug("Getting variable from %s with %s from %s", uuid, var.parser, var.path)
    tar = f'tar --wildcards -zxOf { uuid }.tgz {var.path}'
    check_call(f"ssh {source.host} 'cd {source.path}; { tar } | {var.parser}'", shell=True)
