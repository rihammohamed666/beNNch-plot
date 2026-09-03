"""Plot classes."""

import matplotlib.pyplot as plt


class ThreadScalingPlot:
    """Scaling plot with number of threads on the x-axis."""

    x_variable = "threads_per_task"

    required_variables = [
        "threads_per_task",
        # "tasks_per_node",
        # "num_nodes",
        # "model_time_sim",
        "time_simulate",
        # "py_time_create",
        # "py_time_connect",
        # "time_update",
        # "time_collocate_spike_data",
        # "time_communicate_spike_data",
        # "time_deliver_spike_data",
        # "time_omp_synchronization_simulation",
        # "time_mpi_synchronization",
    ]

    def plot(self, data):
        """Create a scatter plot of simulation time against thread count."""
        xvalues = [value[self.x_variable] for value in data.values()]
        yvalues = [value["time_simulate"] for value in data.values()]
        plt.scatter(xvalues, yvalues)
        plt.savefig("output.png")


class TaskScalingPlot:
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


class NodeScalingPlot:
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
