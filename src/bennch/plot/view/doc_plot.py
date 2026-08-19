"Plots used in NEST performance documentation."

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec

from bennch.plot.bennchplot import Plot
from bennch.plot.io import yaml
from bennch.plot.io.csv import load_data
from bennch.plot.mpltools import simple_axis

from .models import ModelType, ScalingPlotData

log = logging.getLogger(__name__)


class ScalingPlot:
    "Scaling plot with fractions of construct and simulation times."

    def wants(self) -> list[str]:
        "Return the list of required variables."
        return list(ScalingPlotData.model_fields)

    def plot(self, csvfile: str | Path, model: ModelType):
        "Render the plot."
        with open("plotconfig.yaml", encoding="utf8") as infile:
            plotconfig = yaml.load(infile)

        bplot = Plot(
            x_axis=["num_nodes"],
            time_scaling=1e3,
            detailed_timers=False,
            label_params=plotconfig["parameter_labels"],
            df=load_data(csvfile, plotconfig["data_definition"]),
        )

        fig = plt.figure(figsize=(12, 6), constrained_layout=False)
        spec = gridspec.GridSpec(ncols=2, nrows=1, figure=fig, hspace=0.2)

        ax1 = fig.add_subplot(spec[0, 0])

        # trans = mtransforms.ScaledTranslation(-20 / 72, 7 / 72,
        # fig.dpi_scale_trans)

        bplot.plot_fractions(
            axis=ax1,
            fill_variables=[
                "time_construction_create+time_construction_connect",
                "time_simulate",
            ],
            interpolate=True,
            step=None,
            error=True,
        )

        ax1.set_xlabel("Number of Nodes")
        ax1.set_ylabel(
            r"$T_{\mathrm{wall}}$ [s] for $T_{\mathrm{model}} =$" + f"{np.unique(bplot.df.model_time_sim.values)[0]} s"
        )

        handles1, labels1 = ax1.get_legend_handles_labels()
        ax1.legend(handles1[::-1], labels1[::-1])

        # Set the ylim for benchmark plots to make different runs of same model
        # visually comparable
        if model == ModelType.MICROCIRCUIT:
            ax1.set_ylim(0, 15)
        elif model == ModelType.HPC_BENCHMARK:
            ax1.set_ylim(0, 420)
        elif model == ModelType.MULTI_AREA:
            ax1.set_ylim(0, 1500)
        else:
            pass  # Let the ylim creation automatic for potential other models

        ax1.margins(x=0)
        simple_axis(ax1)

        ax2 = fig.add_subplot(spec[0, 1])

        bplot.plot_main(quantities=["sim_factor"], axis=ax2, error=True, fmt="-")

        ax2.set_xlabel("Number of Nodes")
        ax2.set_ylabel(r"real-time factor $T_{\mathrm{wall}}/$ $T_{\mathrm{model}}$")

        # Set the xlim
        automatic_xlim = ax2.get_xlim()
        ax2.set_xlim(automatic_xlim[0], automatic_xlim[1])

        # Set the xlim
        automatic_xlim = ax2.get_xlim()
        ax2.set_xlim(automatic_xlim[0], automatic_xlim[1])

        # Set the ylim for benchmark plots to make different runs of same model
        # visually comparable
        if model == ModelType.MICROCIRCUIT:
            ax2.set_ylim(0, 1.0)
            # explicitly show realtime factor of 1
            ax2.hlines(y=1, xmin=0, xmax=np.max(bplot.df[bplot.x_axis].values), color="gray", linestyle="--")
        elif model == ModelType.HPC_BENCHMARK:
            ax2.set_ylim(0, 79)
        elif model == ModelType.MULTI_AREA:
            ax2.set_ylim(0, 120)
        else:
            pass  # Let the ylim creation automatic for potential other models

        handles2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(handles2[::-1], labels2[::-1])

        ax2.margins(x=0)
        simple_axis(ax2)
        return plt
