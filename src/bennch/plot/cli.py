#!/usr/bin/env python
"Translated script to be integrated, received by mail."

import logging
from pathlib import Path

import rich_click as click

from bennch.plot.io.config import load_config
from bennch.plot.io.tarball import get_variable_value
from bennch.plot.view.doc_plot import ScalingPlot
from bennch.plot.view.models import ModelType

# import matplotlib.transforms as mtransforms

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger("__main__")


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
    config = load_config()
    get_variable_value(uuid, config.vars[var_name], config.source)


@cli.command("scaling")
@click.argument("csvfile", type=click.Path(dir_okay=False, exists=True, path_type=Path))
@click.option("--model", "-m", help="Style options for specific model.", type=click.Choice(ModelType), required=True)
@click.option("--output", "-o", type=click.Path(exists=False, path_type=Path))  # examples=[ 'hpc-v3.9-rc1.png']
def plot_docs(csvfile: Path, model: ModelType, output: Path) -> None:
    "Create a standard benchmark plot for the documentation."
    docplot = ScalingPlot()

    plt = docplot.plot(csvfile, model)

    show = False
    if output is None:
        log.warning("use --output to save as a file without opening a GUI.")
        output = csvfile.with_suffix(".png")
        show = True

    plt.savefig(output, dpi=400)
    log.info("saved as %s.", output)
    if show:
        plt.show()


if __name__ == "__main__":
    cli()
