"UUID set management modules."

import logging
import os

import git
from bennchplot.config import XDG

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class UuidSet:
    "Set of UUIDs."

    pass


class SetsData:
    "Manage a SetsData storage repository."

    def __init__(self):
        log.debug("SetsData")
        self._path = XDG("bennchplot/sets").data_home

    def init(self):
        "Initialize a new repository."
        self._path.mkdir(parents=True, exist_ok=True)
        log.debug("Using UUID sets from %s", self._path)
        with git.repo(self._path) as repo:
            repo.init()

    def sync(self) -> None:
        "Make sure the default remote knows everything and we're uptodate."

    def add(self, uset: UuidSet) -> None:
        "Add given set to the storage."
        pass


# ./git-contributors/gitchanges/  → GitPython  2021
# ./git-remote-scan/src/gitremotescan/  → GitPython>=3  2026
# ../GitCount/gitcount/  → gitpython  2021
# ./docker/images/snakeflow/gittools.py  → GitPython  2018
# ./annex-folder-sync/test/conftest.py  → ?!
# ./snakeflow/Project.py:3:import git  → GitPython 2018
# ./bennch3/tests/test_imports.py  → gitlab
