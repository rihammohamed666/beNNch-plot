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
from subprocess import check_call
import logging

from ruamel.yaml import YAML
from bennchplot import __version__
from pydantic import BaseModel, Field

yaml = YAML()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger("__main__")

class ModelType(StrEnum):
    microcircuit = auto()
    hpc_benchmark = auto()
    multi_area = auto()

class SourceConfig(BaseModel):
    host : str
    path : Path | str

class VarConfig(BaseModel):
    path : str
    parser: str

class Config(BaseModel):
    source : SourceConfig
    vars : dict[str, VarConfig]
    
def loadConfig(file_name = "config.yaml"):
    with Path(file_name).open(encoding="utf8") as in_file:
        return Config.model_validate(yaml.load(in_file))

@click.group()
def cli():
    "BeNNch-plot based plotting functions."


@cli.group(name="get")
def cli_get():
    "Fetch specific metadata from given UUIDs."


@cli_get.command("variable")
@click.argument("uuid")
@click.argument("var_name")
def cli_get_var(uuid: str, var_name: str) -> None:
    "Get the triggering pipeline ID of the given simulation."
    config = loadConfig()
    var = config.vars[var_name]
    tar = f'tar --wildcards -zxOf { uuid }.tgz {var.path}'
    check_call(f"ssh {config.source.host} 'cd {config.source.path}; { tar } | {var.parser}'", shell=True)


@cli.command("scaling")
@click.argument("csvfile", type=click.Path(dir_okay=False, exists=True, path_type=Path))
@click.option("--model", "-m", help="Style options for specific model.", type=click.Choice(ModelType), required=True)
@click.option("--output", "-o", type=click.Path(exists=False, path_type=Path))  # examples=[ 'hpc-v3.9-rc1.png']
def plot_docs(csvfile: TextIOWrapper, model: ModelType, output: Path) -> None:
    "Create a standard benchmark plot for the documentation."
    bplot = Plot(data_file=csvfile, x_axis=['num_nodes'], time_scaling=1e3, detailed_timers=False)

    fig = plt.figure(figsize=(12, 6), constrained_layout=False)
    spec = gridspec.GridSpec(ncols=2, nrows=1, figure=fig, hspace=0.2)

    ax1 = fig.add_subplot(spec[0, 0])

    trans = mtransforms.ScaledTranslation(-20 /
                                            72, 7 / 72, fig.dpi_scale_trans)

    bplot.plot_fractions(axis=ax1,
                    fill_variables=[
                        'time_construction_create+time_construction_connect',
                        'time_simulate', ],
                    interpolate=True,
                    step=None,
                    error=True)

    ax1.set_xlabel('Number of Nodes')
    ax1.set_ylabel(r'$T_{\mathrm{wall}}$ [s] for $T_{\mathrm{model}} =$'
                    + f'{np.unique(bplot.df.model_time_sim.values)[0]} s')

    handles1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(handles1[::-1], labels1[::-1])

    # Set the ylim for benchmark plots to make different runs of same model visually comparable
    if model == ModelType.microcircuit:
        ax1.set_ylim(0, 15)
    elif model == ModelType.hpc_benchmark:
        ax1.set_ylim(0, 420)
    elif model == ModelType.multi_area:
        ax1.set_ylim(0, 1500)
    else:
        pass # Let the ylim creation automatic for potential other models

    ax1.margins(x=0)
    bplot.simple_axis(ax1)

    ax2 = fig.add_subplot(spec[0, 1])

    bplot.plot_main(quantities=['sim_factor'], axis=ax2,
                error=True, fmt='-')

    ax2.set_xlabel('Number of Nodes')
    ax2.set_ylabel(r'real-time factor $T_{\mathrm{wall}}/$'
                    r'$T_{\mathrm{model}}$')

    # Set the xlim
    automatic_xlim = ax2.get_xlim()
    ax2.set_xlim(automatic_xlim[0], automatic_xlim[1])

    # Set the xlim
    automatic_xlim = ax2.get_xlim()
    ax2.set_xlim(automatic_xlim[0], automatic_xlim[1])

    # Set the ylim for benchmark plots to make different runs of same model visually comparable
    if model == ModelType.microcircuit:
        ax2.set_ylim(0, 1.)
        # explicitly show realtime factor of 1
        ax2.hlines(y=1, xmin=0, xmax=np.max(bplot.df[bplot.x_axis].values), color='gray', linestyle='--')
    elif model == ModelType.hpc_benchmark:
        ax2.set_ylim(0, 79)
    elif model == ModelType.multi_area:
        ax2.set_ylim(0, 120)
    else:
        pass # Let the ylim creation automatic for potential other models

    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles2[::-1], labels2[::-1])

    ax2.margins(x=0)
    bplot.simple_axis(ax2)

    """
    ax1.text(0.0, 1.0, 'A', transform=ax1.transAxes + trans,
            fontsize='medium', va='bottom', fontweight='bold')

    ax2.text(0.0, 1.0, 'bplot', transform=ax1.transAxes + trans,
            fontsize='medium', va='bottom', fontweight='bold')
    """
    show = False
    if output is None:
        log.warning("use --output to save as a file without opening a GUI.")
        output = csvfile.with_suffix(".png")
        show = True

    plt.savefig(output, dpi=400)
    log.info("saved as %s.", output)
    if show:
        plt.show()

if __name__ == '__main__':
    cli()
