#!/usr/bin/env python
from pathlib import Path
import rich_click as click
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from enum import StrEnum, auto
from bennchplot import Plot
import matplotlib as mpl
from matplotlib import gridspec
import matplotlib.transforms as mtransforms
from io import TextIOWrapper
import sys
from subprocess import check_call

import logging
from bennchplot.io.git import SetsData
from bennch.io import yaml
from bennchplot.config import XDG

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger("__main__")

class ModelType(StrEnum):
    microcircuit = auto()
    hpc_benchmark = auto()
    multi_area = auto()

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
    repo = SetsData()
    repo.init()

if __name__ == '__main__':
    cli()
