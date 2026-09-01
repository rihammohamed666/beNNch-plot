"UUID import/export functions."

import logging
import re
from uuid import UUID

from bennch.plot.models import UuidSet

log = logging.getLogger(__name__)

uuid_re = re.compile(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}")


def import_uuids(text: str) -> UuidSet:
    """
    Extract all UUIDs from a given text via regex.

    Returns a UuidSet with all UUIDs found in text.
    """
    return UuidSet(frozenset(UUID(match.group()) for match in uuid_re.finditer(text)))
