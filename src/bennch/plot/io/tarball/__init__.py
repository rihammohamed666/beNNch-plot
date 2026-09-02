"I/O functions for interacting with data tarballs."

import logging
from shutil import which
from subprocess import PIPE, CalledProcessError, Popen, check_output
from typing import Any, Callable
from uuid import UUID

from bennch.plot.io.config.models import SourceConfig, VarConfig

log = logging.getLogger(__name__)


def get_variable_value(uuid: UUID, var: VarConfig, source: SourceConfig) -> Any:
    "Extract a variable from the given simulation."
    log.debug("Getting variable from %s with %s from %s", uuid, var.parser, var.path)
    tar = f"tar --wildcards -zxOf {uuid}.tgz {var.path}"
    cmd = [
        which("ssh") or "/usr/bin/ssh",
        source.host,
        f"cd {source.path}; {tar} | {var.parser}",
    ]
    log.debug("calling %s", cmd)
    value = check_output(cmd, encoding="utf8")
    casts: dict[str, Callable[[str], Any]] = {
        "str": lambda x: x,
        "int": int,
        "float": float,
        "strip": lambda s: s.strip(),
        "list[int]": lambda s: [int(x) for x in s.split()],
        "list[float]": lambda s: [int(x) for x in s.split()],
    }
    return casts[var.cast](value)


def list_files(uuid: UUID, pattern: str | None, source: SourceConfig) -> list[str]:
    "Get the list of files from given UUID."
    if pattern is None:
        pattern = "*"
    log.debug("Getting file list from %s with pattern %s from %s:%s", uuid, pattern, source.host, source.path)
    tar = f"tar --wildcards -tvzf {uuid}.tgz '{pattern}'"
    cmd = [
        which("ssh") or "/usr/bin/ssh",
        source.host,
        f"cd {source.path}; {tar}",
    ]
    log.debug("executing %s", str(cmd))
    with Popen(cmd, stdout=PIPE, stderr=PIPE, encoding="utf8") as tarlist:
        try:
            stdout, stderr = tarlist.communicate()
            if tarlist.returncode != 0:
                log.warning("Called process returned %s", tarlist.returncode)
            if stderr:
                log.warning("Called process produced stderr messages:\n%s", stderr)
            lines = [line for line in stdout.split("\n") if line.strip()]
            log.debug("got %d chars of stdout: %d lines", len(stdout), len(lines))
        except CalledProcessError:
            stdout, stderr = tarlist.communicate()
            log.error("tarlist has: %s", str(dir(tarlist)))
            # note that the which() may return bytes, hence the '!r'
            log.error("Calling %s failed:\n%s", tarlist.args, stderr)
            raise
    return lines
