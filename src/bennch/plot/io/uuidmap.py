from shutil import which
from subprocess import PIPE, Popen

from bennch.plot.io.config.models import SourceConfig
from bennch.plot.io.uuids import export_uuids
from bennch.plot.models import UuidSet


def export_uuid_set(uset: UuidSet, source: SourceConfig) -> None:
    setid = uset.key

    cmd = [
        which("ssh") or "/usr/bin/ssh",
        source.host,
        (
            f"cd {source.path} && "
            f"mkdir {setid} && "
            f"cat > {setid}/uuidmap.txt"
        ),
    ]

    with Popen(
        cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        encoding="utf8",
    ) as process:
        _, stderr = process.communicate(
            input=export_uuids(uset)
        )

        if process.returncode != 0:
            raise RuntimeError(stderr)