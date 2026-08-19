#!/usr/bin/env python
"Sandbox example to try UUID set stroage."

import logging
import sys

import rich_click as click

from bennch.plot.config import XDG
from bennch.plot.io import yaml
from bennch.plot.models import SetCache

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger("__main__")


@click.group()
def cli():
    "BeNNch-plot based plotting functions."


@cli.command(name="dirs")
def cli_dirs():
    "Print available XDG directories."
    xdg = XDG("bennchplot")
    print("---")
    yaml.dump(xdg.as_dict(), sys.stdout)
    print("...")


@cli.group(name="get")
def cli_get():
    "Fetch specific metadata from given UUIDs."


@cli.group(name="sets")
def cli_sets():
    "Manage the UUID sets data repository."


@cli_sets.command("init")
def cli_sets_init():
    "Initialize the local cache of UUID set data."
    repo = SetCache()
    repo.reinit()


if __name__ == "__main__":
    cli()
