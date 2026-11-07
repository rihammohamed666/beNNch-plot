"""Plot classes."""

import matplotlib.pyplot as plt
from matplotlib import gridspec


class ThreadScalingPlot:
    """Scaling plot with number of threads on the x-axis."""

    x_variable = "local_num_threads"

    required_variables = [
        "local_num_threads",
        "py_time_create",
        "py_time_connect",
        "time_simulate",
        "model_time_sim",
        "time_update",
        "time_collocate_spike_data",
        "time_communicate_spike_data",
        "time_deliver_spike_data",
        "time_omp_synchronization_simulation",
        "time_mpi_synchronization",
    ]

    def aggregate_by_threads(self, data):
        """Aggregate by number of threads and take averages."""
        grouped: dict[int, list[dict[str, float | None]]] = {}
        for run in data.values():
            threads = int(run["local_num_threads"])
            if threads not in grouped:
                grouped[threads] = []
            grouped[threads].append(run)
        averaged: dict[int, dict[str, float | None]] = {}
        for threads, runs in grouped.items():
            averaged[threads] = {}
            for variable in self.required_variables:
                values = [run[variable] for run in runs if run[variable] is not None]  # type: ignore[list-item]
                if values:
                    averaged[threads][variable] = sum(values) / len(values)  # type: ignore
                else:
                    averaged[threads][variable] = None
        return averaged

    def compute_derived_quantities(self, data):
        """Do the necessary computations to plot."""
        for values in data.values():
            if values["py_time_create"] is not None and values["py_time_connect"] is not None:
                values["construction_time"] = values["py_time_create"] + values["py_time_connect"]
            else:
                values["construction_time"] = None
            values["time_communicate_spike_data"] = (
                values["time_communicate_spike_data"] - values["time_mpi_synchronization"]
            )

            phase_times = [
                values["time_update"],
                values["time_collocate_spike_data"],
                values["time_communicate_spike_data"],
                values["time_deliver_spike_data"],
                values["time_omp_synchronization_simulation"],
                values["time_mpi_synchronization"],
            ]
            if all(time is not None for time in phase_times):
                values["phase_total"] = sum(phase_times)

                values["phase_update"] = values["time_update"] / values["phase_total"]

                values["phase_collocate"] = values["time_collocate_spike_data"] / values["phase_total"]

                values["phase_communicate"] = values["time_communicate_spike_data"] / values["phase_total"]

                values["phase_deliver"] = values["time_deliver_spike_data"] / values["phase_total"]

                values["phase_omp_sync"] = values["time_omp_synchronization_simulation"] / values["phase_total"]

                values["phase_mpi_sync"] = values["time_mpi_synchronization"] / values["phase_total"]
            else:
                values["phase_total"] = None
                values["phase_update"] = None
                values["phase_collocate"] = None
                values["phase_communicate"] = None
                values["phase_deliver"] = None
                values["phase_omp_sync"] = None
                values["phase_mpi_sync"] = None

        return data

    def plot_runtime(self, ax, data):
        """Plot network construction and simulation time."""
        threads = sorted(data)
        construction = [data[t]["construction_time"] for t in threads]
        simulation = [data[t]["time_simulate"] for t in threads]

        ax.fill_between(
            threads,
            0,
            construction,
            label="Network construction",
        )
        ax.fill_between(
            threads,
            construction,
            [c + s for c, s in zip(construction, simulation)],
            label="State propagation",
        )
        ax.set_yscale("log")
        ax.legend()

    def plot_runtime_breakdown(self, ax, data):
        """Plot the real-time factor and scaling reference lines."""
        threads = sorted(data)

        sim_factors = []

        for thread in threads:
            simulation_time = data[thread]["time_simulate"]
            model_time = data[thread]["model_time_sim"]

            if simulation_time is not None and model_time is not None:
                if model_time > 0:
                    sim_factor = simulation_time / model_time
                else:
                    sim_factor = None
            else:
                sim_factor = None

            sim_factors.append(sim_factor)

        ax.plot(
            threads,
            sim_factors,
            marker="x",
            label="State propagation",
            color="black",
            linewidth=0,
        )
        ax.axhline(
            y=1,
            color="gray",
            linestyle="--",
            linewidth=1,
        )

        ax.axhline(
            y=0.5,
            color="gray",
            linestyle="--",
            linewidth=1,
        )
        valid_points = [
            (thread, factor) for thread, factor in zip(threads, sim_factors) if factor is not None and factor > 0
        ]

        if valid_points:
            x0, y0 = valid_points[0]
            x_diag = [threads[0], threads[-1]]

            ax.plot(
                x_diag,
                [y0 * x0 / x for x in x_diag],
                color="gray",
                linestyle="-",
                linewidth=1,
                label=r"#threads$^{-1}$",
            )

        ax.set_yscale("log")
        ax.legend(loc="upper right")

    def plot_fractions(self, ax, data):
        """Plot function for the fractioned plot."""
        threads = sorted(data)
        fill_height = [0] * len(threads)
        phase_variables = [
            "phase_update",
            "phase_collocate",
            "phase_communicate",
            "phase_deliver",
            "phase_omp_sync",
            "phase_mpi_sync",
        ]
        for variable in phase_variables:
            y = [data[t][variable] * 100 for t in threads]

            upper_height = [fill_height[i] + y[i] for i in range(len(y))]

            ax.fill_between(
                threads,
                fill_height,
                upper_height,
                label=variable,
            )

            fill_height = upper_height
            ax.set_ylim(0, 100)
            ax.legend(loc="upper center", bbox_to_anchor=(1.02, 0.5))

    def plot(self, data, set_id):
        """Execute the plot using other functions."""
        data = self.aggregate_by_threads(data)
        data = self.compute_derived_quantities(data)

        threads = sorted(data)

        fig = plt.figure(figsize=(12, 9), constrained_layout=True)

        spec = gridspec.GridSpec(
            ncols=2,
            nrows=2,
            figure=fig,
            width_ratios=[1, 1],
            height_ratios=[3, 1],
        )

        ax1 = fig.add_subplot(spec[:, 0])
        ax2 = fig.add_subplot(spec[0, 1])
        ax3 = fig.add_subplot(spec[1, 1])

        self.plot_runtime(ax1, data)
        self.plot_runtime_breakdown(ax2, data)
        self.plot_fractions(ax3, data)

        ax1.set_ylabel("Wall time [s]")
        ax2.set_ylabel("Real-time factor")
        ax3.set_ylabel("Relative wall time [%]")

        ax1.set_xlabel("Number of Threads")
        ax3.set_xlabel("Number of Threads")

        for ax in (ax1, ax2, ax3):
            ax.set_xscale("log", base=2)
            ax.set_xticks(threads)
            ax.margins(x=0)
        fig.text(
            0.99,
            0.5,
            f"SetID: {set_id}",
            rotation=90,
            va="center",
            ha="right",
            fontsize=8,
        )
        fig.savefig("thread_scaling_plot.png", dpi=300, bbox_inches="tight")
        return fig


class TaskScalingPlot:  # pylint: disable=too-few-public-methods
    """Scaling plot with number of MPI tasks on the x-axis."""

    x_variable = "tasks_per_node"

    required_variables = [
        "threads_per_task",
        "tasks_per_node",
        "num_nodes",
        "model_time_sim",
        "time_simulate",
        "py_time_create",
        "py_time_connect",
        "time_update",
        "time_collocate_spike_data",
        "time_communicate_spike_data",
        "time_deliver_spike_data",
        "time_omp_synchronization_simulation",
        "time_mpi_synchronization",
    ]


class NodeScalingPlot:  # pylint: disable=too-few-public-methods
    """Scaling plot with number of nodes on the x-axis."""

    x_variable = "num_nodes"
    required_variables = [
        "threads_per_task",
        "tasks_per_node",
        "num_nodes",
        "model_time_sim",
        "time_simulate",
        "py_time_create",
        "py_time_connect",
        "time_update",
        "time_collocate_spike_data",
        "time_communicate_spike_data",
        "time_deliver_spike_data",
        "time_omp_synchronization_simulation",
        "time_mpi_synchronization",
    ]
