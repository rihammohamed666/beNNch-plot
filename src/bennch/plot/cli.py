#!/usr/bin/env python
"Translated script to be integrated, received by mail."

import logging
import sys
from io import TextIOWrapper
from itertools import product
from pathlib import Path
from typing import Any
from uuid import UUID

import rich_click as click
from rich.progress import track

from bennch.plot.io.config import Config, ConfigContext, load_config, save_config
from bennch.plot.io.tarball import get_variable_value, list_files
from bennch.plot.io.uuids import import_uuids
from bennch.plot.models import SetCache, UuidSet
from bennch.plot.view import rich_view
from bennch.plot.view.doc_plot import ScalingPlot
from bennch.plot.view.models import ModelType

# import matplotlib.transforms as mtransforms

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)


@click.group(result_callback=click.pass_context(rich_view))
@click.option("--debug", "-d", help="increase logging to DEBUG level for given module.", multiple=True)
@click.pass_context
def cli(ctx, debug: list[str] | None = None):
    "BeNNch-plot based plotting functions."
    if sys.stdout.isatty():
        log.setLevel(logging.INFO)
    if debug is not None:
        for modulename in debug:
            log.info("increasing debugging level on %s", modulename)
            logging.getLogger(modulename).setLevel(logging.DEBUG)

    ctx.obj = ctx.with_resource(ConfigContext())


@cli.group(name="get")
def cli_get():
    "Fetch specific metadata from given UUIDs."


@cli_get.command("variable")
@click.argument("uuid", type=UUID)
@click.argument("var_name")
def cli_get_var(uuid: UUID, var_name: str) -> None:
    "Get the variable value for the run with given UUID."
    config = load_config()
    return get_variable_value(uuid, config.vars[var_name], config.source)


@cli_get.command("variables")
@click.argument("var_names", nargs=-1, required=True)
@click.pass_obj
def cli_get_vars(config: Config, var_names: list[str]) -> dict[UUID, dict[str, Any]]:
    "Get the variable values for all runs in the current set."
    config = load_config()
    sets = SetCache()
    uset = sets.load(config.current_set.setid)

    data: dict[UUID, dict[str, Any]] = {}
    for uuid, var_name in track(product(uset, var_names), total=len(uset) * len(var_names)):
        data.setdefault(uuid, {})[var_name] = get_variable_value(uuid, config.vars[var_name], config.source)
    return data


@cli_get.command("list")
@click.option("--flat", is_flag=True, help="return result as flat ascii output")
@click.argument("pattern", required=False)
@click.argument("uuid", required=False, type=UUID, nargs=-1)
@click.pass_obj
def cli_get_list(
    config: Config, flat: bool = False, pattern: str = "*", uuid: list[UUID] | None = None
) -> dict[UUID, list[str]] | str:
    """
    Get a list of files available for the given UUID(s).

    If PATTERN is omitted '*' is implied. If no UUID is given then all UUIDs of
    the current set are queried.
    """
    if uuid:
        uset = UuidSet.model_validate(uuid)
    else:
        config = load_config()
        sets = SetCache()
        uset = sets.load(config.current_set.setid)
    log.debug("looking for files with pattern %s", pattern)
    log.debug("in list of uuids:\n    %s", "\n    ".join([str(u) for u in uset]))

    files: dict[UUID, list[str]] = {}
    for uid in uset:
        files[uid] = list_files(uid, pattern, config.source)
    if flat:
        return "\n".join("\n".join(lines) for lines in files.values())
    return files


@cli.group(name="set")
def cli_set():
    "Modify the currently active set of UUIDs."


@cli_set.command("reinit-cache")
def cli_set_init():
    "Initialize the cache directory."
    sets = SetCache()
    sets.reinit()
    log.debug("cache init done")


@cli_set.command(name="new")
@click.pass_obj
def cli_set_new(config: Config):
    "Set the current set of UUIDs to a new empty set."
    sets = SetCache()

    uset = UuidSet()

    sets.save(uset)
    config.current_set.setid = uset.key
    return config.current_set


@cli_set.command("add")
@click.argument("uuid", type=UUID)
@click.pass_obj
def cli_set_add(config: Config, uuid: UUID):
    "Add the given UUID to the current set."
    sets = SetCache()

    uset = sets.load(config.current_set.setid)
    uset = uset.add(uuid)

    sets.save(uset)
    config.current_set.setid = uset.key
    return config.current_set


@cli_set.command("select")
@click.argument("setid", type=str)
@click.pass_obj
def cli_set_select(config: Config, setid: str) -> str:
    "Select a known set."
    sets = SetCache()
    if setid in sets:
        config.current_set.setid = sets.load(setid).key
        assert config.current_set.setid == setid
        return setid
    candidates = sets.near_match(setid)
    if len(candidates) == 0:
        raise KeyError(f"No known set has setid='{setid}'")
    if len(candidates) > 1:
        raise KeyError(f"Multiple possible candidates for given setid pattern: {', '.join(candidates)}")
    setid = candidates[0]
    config.current_set.setid = sets.load(setid).key
    assert config.current_set.setid == setid
    return setid


@cli_set.command("like")
@click.argument("pattern", type=str)
def cli_set_like(pattern: str) -> str:
    """
    List sets with similar handles.

    This method may be used to implement tab-completion, or selection of
    approximate set names. Only valid set handles are returned. The returned
    list may be empty. The return value is newline separated to aid shell
    usage (e.g. for tab-completion).

    Does not change the *current set*.
    """
    return "\n".join(SetCache().near_match(pattern))


@cli_set.command(name="show")
@click.option(
    "--flat",
    is_flag=True,
    help="Dump the list as flat uuid-per-line string instead of the machine readable format.",
)
# @click.pass_obj
def cli_set_show(flat: bool = False):  # config):
    "Show the list of UUIDs in the current set."
    config = load_config()
    log.info("current set is %s", config.current_set)
    sets = SetCache()
    uset = sets.load(config.current_set.setid)
    if flat:
        return "\n".join([str(uuid) for uuid in uset])
    return uset


@cli_set.command(name="import")
@click.argument("infile", type=click.File("r"))
@click.pass_obj
def cli_set_import(config: Config, infile: TextIOWrapper):
    # For correct wrapping of numpy-docstrings use `\b`. See
    # https://click.palletsprojects.com/en/stable/documentation/#escaping-click-s-wrapping
    r"""
    Read UUIDs from file or stdin and form a new set.

    The input is read as a text file and all matches of the regular expression
    for UUIDs are added to a new set. Thus, the input does not need to be
    specially formatted. Note, that this also matches UUIDs in comments and
    other unexpected places.

    The new set is selected as the new *current set*.

    \b
    Parameters
    ----------
    infile: filename|-
        reads the given file and parses all found UUIDs. If filename is "-"
        input is taken from stdin.
    """
    log.debug("reading stdin...")
    sets = SetCache()
    uset = import_uuids(infile.read())
    sets.save(uset)
    config.current_set.setid = uset.key
    return uset.key


@cli_set.command("rm")
@click.argument("uuid", type=UUID)
def cli_set_remove(uuid: UUID):
    "Remove the given UUID from the current set."
    config = load_config()
    sets = SetCache()

    uset = sets.load(config.current_set.setid)
    uset = uset.remove(uuid)

    sets.save(uset)
    config.current_set.setid = uset.key
    save_config(config)
    return config.current_set


@cli.group(name="config")
def cli_config():
    "Group of configuration subcommands."


@cli_config.command("show")
@click.pass_obj
def cli_config_show(config) -> Config:
    "Display loaded configuration."
    return config


@cli.command(name="scaling")
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
