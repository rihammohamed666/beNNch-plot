"""Plot classes."""

import matplotlib.pyplot as plt


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

    # def plot_main(self, ax, data):
    #   ...

    def plot_fractions(self, ax, data):
        """Plot function for the fractioned plot."""
        fill_height = [0] * len(data)

        for variable in self.required_variables:
            x = list(data.keys())
            y = [data[threads][variable] for threads in x]
            ax.fill_between(
                x,
                fill_height,
                [fill_height + value for value in y],
                label=variable,
            )
            fill_height = [fill_height[i] + y[i] for i in range(len(y))]

    def plot(self, data):
        """Execute the plot using other functions."""
        data = self.aggregate_by_threads(data)
        data = self.compute_derived_quantities(data)

        _, ax = plt.subplots()
        # pylint: disable=too-many-function-args
        self.plot_fractions(
            ax,
            data,
            [
                "phase_update",
                "phase_collocate",
                "phase_communicate",
                "phase_deliver",
                "phase_omp_sync",
                "phase_mpi_sync",
            ],
        )  # type: ignore[call-arg]
        ax.set_xscale("log", base=2)
        ax.set_ylim(0, 1)
        ax.legend()
        plt.show()


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
