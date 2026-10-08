"I/O functions for interacting with data tarballs."

import logging
from subprocess import check_output

from bennch.plot.io.config.models import Config, SourceConfig, VarConfig
from bennch.plot.models import UuidSet

log = logging.getLogger(__name__)


def get_variable_value(uuid: str, var: VarConfig, source: SourceConfig) -> float | None:
    "Get the triggering pipeline ID of the given simulation."
    log.debug("Getting variable from %s with %s from %s", uuid, var.parser, var.path)
    tar = f"tar --wildcards -zxOf {uuid}.tgz {var.path}"
    output = check_output(f"ssh {source.host} 'cd {source.path}; {tar} | {var.parser}'", shell=True).strip()
    if not output:
        return None
    return float(output)


def get_variables(uuids: UuidSet, variables: list[str], config: Config):
    "Get multiple variables from multiple uuids."
    values = {}  # type: ignore[var-annotated]

    for uuid in uuids:
        values[uuid] = {}

        for var_name in variables:
            value = get_variable_value(
                str(uuid),
                config.vars[var_name],
                config.source,
            )

            if value is None:
                print(f"{var_name} not found for UUID {uuid}")

            values[uuid][var_name] = value

    return values
