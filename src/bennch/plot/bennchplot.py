"""
Class organizing benchmarking plots.

beNNch-plot - standardized plotting routines for performance benchmarks.

Copyright (C) 2021 Forschungszentrum Juelich GmbH, INM-6

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import matplotlib
import numpy as np

try:
    from . import plot_params as pp
except ImportError:
    import bennch.plot.plot_params as pp


class Plot:
    """
    Class organizing benchmarking plots.

    Attributes
    ----------
    x_axis : str or list
        variable to be plotted on x-axis
    x_ticks : str, optional
    matplotlib_params : dict, optional
        parameters passed to matplotlib
    color_params : dict, optional
        unique colors for variables
    additional_params : dict, optional
        additional parameters used for plotting
    label_params : dict, optional
        labels used when plotting
    time_scaling : int, optional
        scaling parameter for simulation time
    """

    def __init__(
        self,
        x_axis,
        df,
        label_params: dict[str, str],
        x_ticks="data",
        matplotlib_params=pp.matplotlib_params,
        color_params=pp.color_params,
        additional_params=pp.additional_params,
        time_scaling=1,
        detailed_timers=True,
    ):

        self.x_axis = x_axis
        self.x_ticks = x_ticks
        self.matplotlib_params = matplotlib_params
        self.additional_params = additional_params
        self.color_params = color_params
        self.label_params = label_params
        self.time_scaling = time_scaling
        self.df = df
        self.detailed_timers = detailed_timers
        self.compute_derived_quantities()

    def compute_derived_quantities(self):
        "Do computations to get parameters needed for plotting."
        self.df["num_nvp"] = self.df["threads_per_task"] * self.df["tasks_per_node"]
        self.df["model_time_sim"] /= self.time_scaling
        self.df["sim_factor"] = self.df["time_simulate"]["mean"].values / self.df["model_time_sim"].values.flatten()
        self.df["sim_factor_std"] = self.df["time_simulate"]["std"].values / self.df["model_time_sim"].values.flatten()
        self.df[("time_construction_create+time_construction_connect", "mean")] = (
            self.df["py_time_create"] + self.df["py_time_connect"]
        )["mean"].values
        self.df[("time_construction_create+time_construction_connect", "std")] = np.sqrt(
            (self.df["time_construction_create"]["std"] ** 2 + self.df["time_construction_connect"]["std"] ** 2)
        )
        self.df[("time_construction_create", "mean")] = self.df["py_time_create"]["mean"]
        self.df[("time_construction_connect", "mean")] = self.df["py_time_connect"]["mean"]
        self.df[("time_construction_create", "std")] = self.df["py_time_create"]["std"]
        self.df[("time_construction_connect", "std")] = self.df["py_time_connect"]["std"]
        if self.detailed_timers:
            self.df["time_phase_total"] = (
                # self.df['time_update_spike_data'] +
                self.df["time_communicate_spike_data"]
                + self.df["time_deliver_spike_data"]
                + self.df["time_collocate_spike_data"]
            )
            self.df["time_phase_total_std"] = np.sqrt(
                # self.df['time_update_spike_data_std']**2 +
                self.df["time_communicate_spike_data_std"] ** 2
                + self.df["time_deliver_spike_data_std"] ** 2
                + self.df["time_collocate_spike_data_std"] ** 2
            )
            self.df["phase_total_factor"] = self.df["time_phase_total"] / self.df["model_time_sim"]
            self.df["phase_total_factor_std"] = self.df["time_phase_total_std"] / self.df["model_time_sim"]

            for phase in ["update", "communicate", "deliver", "collocate"]:
                self.df["phase_" + phase + "_factor"] = (
                    self.df["time_" + phase + "_spike_data"] / self.df["model_time_sim"]
                )

                self.df["phase_" + phase + "_factor" + "_std"] = (
                    self.df["time_" + phase + "_spike_data" + "_std"] / self.df["model_time_sim"]
                )

                self.df["frac_phase_" + phase] = (
                    100 * self.df["time_" + phase + "_spike_data"] / self.df["time_phase_total"]
                )

                self.df["frac_phase_" + phase + "_std"] = (
                    100 * self.df["time_" + phase + "_spike_data" + "_std"] / self.df["time_phase_total"]
                )
        self.df["total_memory_per_node"] = (
            self.df["total_memory"]["mean"].values / self.df["num_nodes"].values.flatten()
        )
        self.df["total_memory_per_node_std"] = (
            self.df["total_memory"]["std"].values / self.df["num_nodes"].values.flatten()
        )

    def plot_fractions(self, axis, fill_variables, interpolate=False, step=None, log=False, alpha=1.0, error=False):
        """
        Fill area between curves.

        axis : Matplotlib axes object
        fill_variables : list
            variables (e.g. timers) to be plotted as fill  between graph and
            x axis
        interpolate : bool, default
            whether to interpolate between the curves
        step : {'pre', 'post', 'mid'}, optional
            should the filling be a step function
        log : bool, default
            whether the x-axes should have logarithmic scale
        alpha, int, default
            alpha value of fill_between plot
        error : bool
            whether plot should have error bars
        """
        fill_height = np.zeros(len(np.squeeze(self.df[self.x_axis].values)))
        for fill in fill_variables:
            axis.fill_between(
                self.df[self.x_axis].to_numpy().squeeze(axis=1),
                fill_height,
                self.df[fill]["mean"].values + fill_height,
                label=self.label_params[fill],
                facecolor=self.color_params[fill],
                interpolate=interpolate,
                step=step,
                alpha=alpha,
                linewidth=0.5,
                edgecolor="#444444",
            )
            if error:
                axis.errorbar(
                    self.df[self.x_axis].values,
                    self.df[fill]["mean"].values + fill_height,
                    yerr=self.df[fill]["std"].values,
                    capsize=3,
                    capthick=1,
                    color="k",
                    fmt="none",
                )
            fill_height += self.df[fill]["mean"].values

        if self.x_ticks == "data":
            axis.set_xticks(np.squeeze(self.df[self.x_axis].values))
        else:
            axis.set_xticks(self.x_ticks)

        if log:
            axis.set_xscale("log")
            axis.tick_params(bottom=False, which="minor")
            axis.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

    def plot_main(self, quantities, axis, log=(False, False), error=False, fmt="none", label=None, color=None):
        """
        Create the full plot.

        This is the main plotting function.

        Attributes
        ----------
        quantities : list
            list with plotting quantities
        axis : axis object
            axis object used when plotting
        log : tuple of bools, default
            whether x and y axis should have logarithmic scale
        error : bool, default
            whether or not to plot error bars
        fmt : string
            matplotlib format string (fmt) for defining line style
        """
        for y in quantities:
            label = self.label_params[y] if label is None else label
            color = self.color_params[y] if color is None else color
            axis.plot(
                self.df[self.x_axis].to_numpy().squeeze(axis=1),
                self.df[y].to_numpy(),
                marker=None,
                label=label,
                color=color,
                linewidth=2,
            )
            if error:
                axis.errorbar(
                    self.df[self.x_axis].to_numpy().squeeze(axis=1),
                    self.df[y].to_numpy(),
                    yerr=self.df[y + "_std"].to_numpy(),
                    marker=None,
                    capsize=3,
                    capthick=1,
                    color=color,
                    fmt=fmt,
                )

        if self.x_ticks == "data":
            axis.set_xticks(np.squeeze(self.df[self.x_axis].values))
        else:
            axis.set_xticks(self.x_ticks)

        if log[0]:
            axis.set_xscale("log")
        if log[1]:
            axis.tick_params(bottom=False, which="minor")
            axis.set_yscale("log")
