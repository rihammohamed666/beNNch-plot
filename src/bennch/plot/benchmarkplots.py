"Imported manual plot script – to be refactored."

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec

import bennch.plot.bennchplot as bp
from bennch.plot.io.csv import load_data
from bennch.plot.mpltools import simple_axis

# import matplotlib.transforms as mtransforms

PATH = "/home/mohamed/pythontest/results_file"  # with jemalloc
FILENAME_SAVE = "NEST-v3.9-rc1_Microcircuit_DOCS_0923.png"
BENCHMARK_MODEL = "microcircuit"

B = bp.Plot(
    df=load_data(PATH, aggregation={}),
    x_axis=["num_nodes"],
    time_scaling=1e3,
    detailed_timers=False,
    label_params={},
)


def plot_docs():
    "Create the plots for the NEST performance documentation."
    fig = plt.figure(figsize=(12, 6), constrained_layout=False)
    spec = gridspec.GridSpec(ncols=2, nrows=1, figure=fig, hspace=0.2)

    ax1 = fig.add_subplot(spec[0, 0])

    # trans = mtransforms.ScaledTranslation(-20 / 72, 7 / 72,
    # fig.dpi_scale_trans)

    B.plot_fractions(
        axis=ax1,
        fill_variables=[
            "time_construction_create+time_construction_connect",
            "time_simulate",
        ],
        interpolate=True,
        step=None,
        error=True,
    )
    # B.plot_main(quantities=['time_construction_create'], axis=ax1,
    # error=False, fmt='-')
    # B.plot_main(quantities=['time_construction_connect'], axis=ax1,
    # error=False, fmt= '-')

    ax1.set_xlabel("Number of Nodes")
    ax1.set_ylabel(
        r"$T_{\mathrm{wall}}$ [s] for $T_{\mathrm{model}} =$" + f"{np.unique(B.df.model_time_sim.values)[0]} s"
    )

    handles1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(handles1[::-1], labels1[::-1])
    # Set the ylim for benchmark plots to make different runs of same model
    # visually comparable
    if BENCHMARK_MODEL == "microcircuit":
        ax1.set_ylim(0, 15)
    elif BENCHMARK_MODEL == "hpc_benchmark":
        ax1.set_ylim(0, 55)
    elif BENCHMARK_MODEL == "multi_area":
        ax1.set_ylim(0, 1500)
    else:
        pass  # Let the ylim creation automatic for potential other models

    ax1.margins(x=0)
    simple_axis(ax1)

    ax2 = fig.add_subplot(spec[0, 1])

    B.plot_main(quantities=["sim_factor"], axis=ax2, error=True, fmt="-")

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
    if BENCHMARK_MODEL == "microcircuit":
        ax2.set_ylim(0, 1.0)
        # explicitly show realtime factor of 1
        ax2.hlines(y=1, xmin=0, xmax=np.max(B.df[B.x_axis].values), color="gray", linestyle="--")
    elif BENCHMARK_MODEL == "hpc_benchmark":
        ax2.set_ylim(0, 50)
    elif BENCHMARK_MODEL == "multi_area":
        ax2.set_ylim(0, 120)
    else:
        pass  # Let the ylim creation automatic for potential other models

    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles2[::-1], labels2[::-1])

    ax2.margins(x=0)
    simple_axis(ax2)

    # ax1.text(0.0, 1.0, 'A', transform=ax1.transAxes + trans,
    #         fontsize='medium', va='bottom', fontweight='bold')

    # ax2.text(0.0, 1.0, 'B', transform=ax1.transAxes + trans,
    #         fontsize='medium', va='bottom', fontweight='bold')

    plt.savefig(FILENAME_SAVE, dpi=400)


plot_docs()
