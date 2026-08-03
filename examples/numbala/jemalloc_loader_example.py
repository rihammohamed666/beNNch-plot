"Script received via mail – to be integrated."

#
# python3 -m venv venv
#
# source venv/bin/activate
# pip install -U pip
# pip install -r requirements.txt
#
#
# Save as plot_page_faults.py and run with: python plot_page_faults.py
import logging
import re
from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import colors
from rich.progress import track

# from scipy.stats import gaussian_kde

cm = 1 / 2.54  # pylint: disable=invalid-name


log = logging.getLogger(__name__)
logging.getLogger("matplotlib.font_manager").setLevel(logging.INFO)

parser = ArgumentParser()
parser.add_argument("--path", type=str, default="data/")
parser.add_argument("--output_path", type=str, default="data/")
parser.add_argument("--cutoff", type=float, default=6)
parser.add_argument("--machine", type=str, default="hambach")
parser.add_argument("--output_name", type=str, default="")
args = parser.parse_args()

data_path = Path(args.path)
output_path = Path(args.output_path)
cutoff = args.cutoff
machine = args.machine
output_name = args.output_name

# label_dict = {
# "before_prep_sim": "Before network\npreparation",
# "before_const": "Before network\nconstruction",
# "before_presim": "After netwrok\nconstruction",
# "before_sim": "Before network\nsimulation",
# "after_sim": "After network\nsimulation"
# }
label_dict = {
    "construction_pf": "After network\nconstruction",
    "presim_pf": "Before network\nsimulation",
    "simulation_pf": "After network\nsimulation",
}

label_array = list(label_dict.keys())


@dataclass
class Data:
    "Container for extraced data."

    cycle_time_dict: dict = field(default_factory=dict)
    spike_counter_dict: dict = field(default_factory=dict)
    sim_time_dict: dict = field(default_factory=dict)
    communicate_time_dict: dict = field(default_factory=dict)
    total_sim_time_per_proc: list = field(default_factory=list)
    minor_pf_dict: dict = field(default_factory=dict)
    ct_logfiles: list[Path] = field(default_factory=list)
    pf_logfiles: list[Path] = field(default_factory=list)
    t_wall: float = 0.0
    t_wall_2ndhalf: float = 0.0

    @property
    def mpi_processes(self):
        "Count number of data-rows in ct_logfiles."
        return len(self.ct_logfiles)


def find_recordings(basepath: Path) -> list[Path]:
    "Locate bad version of kernel status written via print."
    return list(
        basepath.glob(
            # "jube_results/000000/000*_bench/work/data/*/recordings/"
            # "000*_bench/work/data/*/recordings/"
            "**"
        )
    )


def find_logs(recording: Path, data_type: str) -> list[Path]:
    """
    Locate log files in recordings.

    Parameters
    ----------
    recording: Path
        Path to an extracted tarball.
    data_type: str
        filename base glob to search for, examples: "logfile",
        "cycle_time_log", "page_faults_log", etc.
    """
    return list(recording.glob(f"*{data_type}*"))


def npconcat(datadict: dict[int, np.ndarray]) -> np.ndarray:
    "Concatenate all items from a dictionary into one numpy array."
    _data_concat = np.zeros((0,))
    for _, spike_counts in sorted(datadict.items()):
        _data_concat = np.concatenate((_data_concat, spike_counts))
    return _data_concat


def get_rank(file: Path) -> int:
    "Get the trailing number (rank) after last '_'."
    return int(file.name.rsplit("_", 1)[1])


def load(path: Path):
    "Load data from given path to extracted UUID tarball."
    assert path.is_dir()
    log.info("loading data files from %s", path)
    data = Data()
    for p in find_recordings(path):
        if p.is_dir():
            data.ct_logfiles.extend(find_logs(p, "cycle_time_log"))
            data.pf_logfiles.extend(find_logs(p, "page_faults_log"))

    # The files in the two log lists have an arbitray order.  For later
    # correlation analysis we better sort them such that corresponding entries
    # in the two lists refer to the same rank. We achieve this by sorting both
    # lists according to rank

    data.ct_logfiles = sorted(data.ct_logfiles, key=get_rank)
    data.pf_logfiles = sorted(data.pf_logfiles, key=get_rank)

    for idx, filename in track(enumerate(data.ct_logfiles), total=len(data.ct_logfiles)):
        with open(filename, "r", encoding="utf8") as infile:
            ctdata = np.loadtxt(infile)
        data.cycle_time_dict[idx] = ctdata[:, 0] * 1000 - ctdata[:, 1] * 1000  # without communicate time and in ms
        data.spike_counter_dict[idx] = ctdata[:, -1]
        data.communicate_time_dict[idx] = ctdata[:, 1] * 1000

        data.total_sim_time_per_proc.append(np.sum(ctdata[:, 0] * 1000))
        data.sim_time_dict[idx] = ctdata[:, 0] * 1000

    presim_model = 5000
    sim_model = len(data.sim_time_dict[0]) - presim_model
    sim_start_2ndhalf = sim_model // 2

    t_wall: float = 0
    t_wall_2ndhalf: float = 0
    n = len(data.sim_time_dict)
    for t in data.sim_time_dict.values():
        t_wall += sum(t[presim_model:])
        t_wall_2ndhalf += sum(t[presim_model + sim_start_2ndhalf :])
    t_wall /= n
    t_wall_2ndhalf /= n

    data.t_wall = t_wall / 1000.0  # units of seconds
    data.t_wall_2ndhalf = t_wall_2ndhalf / 1000.0  # units of seconds
    # print(t_wall/10000)
    # print(t_wall_2ndhalf/5000)

    for idx, filename in track(enumerate(data.pf_logfiles), total=len(data.pf_logfiles)):
        data.minor_pf_dict[idx] = {}
        if filename.is_file():
            with filename.open(encoding="utf-8", mode="r") as fl:
                for line in fl:
                    for key in label_array:
                        if line.strip().startswith(key):
                            split = line.split(" ")
                            # label = label_dict[split[0].strip()]
                            minor_pf = int(split[1].strip())
                            # major_pf = int(split[2].strip())

                            data.minor_pf_dict[idx][key] = minor_pf
    log.info("loading complete.")
    return data


def heatmap(data, rtf, cutoff_factor: float = 2, filename: str = "plot.png") -> None:
    "Make a heatmap from extracted data and plot it."
    pre_sim = 5000
    fontsize = 8

    steps = np.arange(0, len(data.cycle_time_dict[0]), 1)
    procs = np.arange(0, int(data.mpi_processes), 1)
    htmap = np.zeros((len(steps), len(procs)))

    cutoff_value = int(round(cutoff_factor * 16 / data.mpi_processes))  # 1 cutoff value and 2 cutoff factor
    print("cutoff = " + str(cutoff))

    for idx, key in enumerate(data.cycle_time_dict.keys()):
        htmap[:, idx] = np.clip(data.cycle_time_dict[key], a_min=0, a_max=cutoff_value)

    # [X, Y] = np.meshgrid(steps, procs)
    np.meshgrid(steps, procs)
    fig = plt.figure(figsize=(10 * cm, 6 * cm))

    fig.subplots_adjust(bottom=0.2)
    fig.subplots_adjust(right=1.05)

    plt.title("wall-clock times of cycles (color code)", fontsize=fontsize)

    ax = sns.heatmap(htmap.T)
    mappable = ax.collections[0]
    mappable.set_clim(1, cutoff_value)

    ax.set_xlabel("cycle / 10,000", fontsize=fontsize)
    ax.set_ylabel("rank", fontsize=fontsize)

    ticks = np.arange(pre_sim, steps[-1] + pre_sim, 10000)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{int((t - pre_sim) / 10000):d}" for t in ticks], rotation=0)  # type: ignore[operator]
    ax.tick_params(axis="y", labelrotation=0)
    ax.tick_params(axis="both", which="major", labelsize=fontsize)

    cbar = mappable.colorbar
    cbar.update_normal(mappable)
    cbar.set_ticks([int(1 + i) for i in range(cutoff_value)])
    cbar.ax.tick_params(labelsize=fontsize)

    uuid = str(data.ct_logfiles[0].parts[0])

    ax.text(
        1.01,
        0.5,
        uuid,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        rotation="vertical",
        va="center",
        ha="left",
        color="black",
        fontsize=5,
        # fontweight="bold"
    )

    ax.text(
        0.9,
        0.98,
        rtf,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        va="top",
        ha="right",
        color="white",
        fontsize=8,
        fontweight="bold",
    )

    fig.savefig(filename, dpi=300)
    plt.close(fig)


def cycle_times_function(data, rtf, cutoff_factor: float = 2, filename: str = "plot.png") -> None:
    "Make a cycle-times plot of the extracted data and plot it."
    fontsize = 8

    cutoff_value = int(round(cutoff_factor * 16 / data.mpi_processes))
    print("cutoff = " + str(cutoff_value))

    cycle_time_concat = npconcat(data.cycle_time_dict)
    mask = cycle_time_concat < cutoff_value
    plt.figure(figsize=(10 * cm, 6.5 * cm))
    # counts, bins, patches = plt.hist(cycle_time_concat[mask], bins=1000,
    # density=True, color="limegreen")
    plt.hist(cycle_time_concat[mask], bins=1000, density=True, color="limegreen")

    # bin_centers = (bins[1:] + bins[:-1]) / 2

    n_cycle_times = len(cycle_time_concat)
    n_cycle_times_considered = len(cycle_time_concat[mask])
    n_cycle_time_considered_frac_str = format(n_cycle_times_considered / n_cycle_times * 100, ".2f")

    print("cycle times considered: " + n_cycle_time_considered_frac_str + "%")

    min_ = np.around(np.min(cycle_time_concat), 2)
    mean_ = np.around(np.mean(cycle_time_concat), 2)
    max_ = np.around(np.max(cycle_time_concat), 2)

    # this keeps the green area covered by the distributions the same visual
    # size
    ylim = 2.5 * data.mpi_processes / 16

    plt.ylim(0, ylim)
    plt.xlim(0, cutoff_value)

    plt.title(f"min {min_}, mean {mean_}, max {max_}", fontsize=fontsize)
    plt.xlabel("cycle time (ms)", fontsize=fontsize)
    plt.ylabel("density (1/ms)", fontsize=fontsize)

    plt.tight_layout()

    uuid = str(data.ct_logfiles[0].parts[0])

    ax = plt.gca()

    ax.tick_params(axis="both", which="major", labelsize=fontsize)

    ax.text(
        0.99,
        0.5,
        uuid,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        rotation="vertical",
        va="center",
        ha="right",
        color="black",
        fontsize=5,
        # fontweight="bold"
    )

    ax.text(
        0.9,
        0.98,
        rtf,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        va="top",
        ha="right",
        color="black",
        fontsize=8,
        # fontweight="bold"
    )

    ax.text(
        mean_,
        0.5,
        n_cycle_time_considered_frac_str,
        va="center",
        ha="center",
        color="black",
        fontsize=8,
        # fontweight="bold"
    )

    plt.savefig(filename, dpi=300)
    plt.close()


def page_faults_plot(data, rtf, filename: str = "plot.png"):
    "Make a page-faults plot of the extracted data and plot it."
    fontsize = 8

    minor_pfs = data.minor_pf_dict

    concat_data_presim = []
    concat_data_sim = []
    for dic in minor_pfs.items():
        for key, val in dic.items():
            # if key == "before_sim":
            if key == "presim_pf":
                concat_data_presim.append(val)
            # elif key == "after_sim":
            elif key == "simulation_pf":
                concat_data_sim.append(val)

    presim_dur = 0.5
    sim_dur = 10.0

    ranks = list(range(len(minor_pfs.keys())))
    pre_contrib = [ps / presim_dur for ps in concat_data_presim]
    sim_contrib = [s / sim_dur for s in concat_data_sim]

    plt.figure(figsize=(11 * cm, 6.5 * cm))
    plt.bar(ranks, pre_contrib, label=f"pre-sim (/s over {presim_dur}s)")
    plt.bar(ranks, sim_contrib, bottom=pre_contrib, label=f"simulation (/s over {sim_dur}s)")
    plt.xticks(ranks, [f"{r}" for r in ranks])

    plt.ylabel("pages fault rate (1/s)", fontsize=fontsize)
    plt.xlabel("rank", fontsize=fontsize)
    plt.title("page faults by rank", fontsize=fontsize)
    # plt.grid(axis="y", linestyle=":", linewidth=0.7, alpha=0.6)

    # Overall average line

    plt.legend(fontsize=5)  # type: ignore[call-arg]  # unexpected keyword argument??

    plt.tight_layout()

    if any(x > 5000 for x in pre_contrib):
        plt.ylim(0, 4e7)
    else:
        plt.ylim(0, 5000)

    uuid = str(data.ct_logfiles[0].parts[0])

    ax = plt.gca()

    ax.tick_params(axis="both", which="major", labelsize=fontsize)

    ax.text(
        0.99,
        0.5,
        uuid,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        rotation="vertical",
        va="center",
        ha="right",
        color="black",
        fontsize=5,
        # fontweight="bold"
    )

    ax.text(
        0.9,
        0.98,
        rtf,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        va="top",
        ha="right",
        color="black",
        fontsize=8,
        # fontweight="bold"
    )

    plt.savefig(filename, dpi=300)
    plt.close()


def pagefaults_vs_cycletime_plot(data, filename: str = "plot.png"):
    "Make a page-faults vs. cycle-times plot."
    log.info("ploting page faults against cycle_times")
    cycle_times = data.cycle_time_dict
    minor_pfs = data.minor_pf_dict

    t_presim = 500  # in ms
    delta_t = 0.1  # in ms
    total_presim_cycle_times = []
    for idx in cycle_times.items():
        total_presim_cycle_times.append(np.sum(cycle_times[idx][: int(t_presim / delta_t)]))

    concat_data_presim = []
    for idx, dic in minor_pfs.items():
        for key, val in dic.items():
            # if key == "before_sim":
            if key == "presim_pf":
                concat_data_presim.append(val)

    # x: presim page faults per rank (already computed from data_str)
    x = np.array(concat_data_presim, dtype=float)

    # y: total cycle time per rank in ms (already computed from ranks)
    y = np.array(total_presim_cycle_times, dtype=float)

    # normalize total cycle time to time per cycle in ms
    y /= 5000

    assert x.shape == y.shape, "presim_pf and totals_ms must have same length"

    _, ax = plt.subplots()
    ax.scatter(x, y)

    # label each point with its rank index
    for i, (xi, yi) in enumerate(zip(x, y)):
        ax.annotate(str(i), (xi, yi), xytext=(3, 3), textcoords="offset points", fontsize=8)

    ax.set_xlabel("Presim page faults")
    ax.set_ylabel("Total cycle time of presim without communication(ms)")

    plt.ylim(0, 6)

    # Overall average line

    #   plt.legend()

    plt.tight_layout()
    # plt.ylim(y_lim)
    # plt.xlim(x_lim)
    plt.savefig(filename)
    plt.close()

    log.info("saved as %s", filename)


def correlation_spikes_plot_halfs(data, filename: str = "plot.png"):
    "Make a spike-count vs. cycle-time plot of the extracted data and plot it."
    log.info("ploting spike count - cycle-times correlation")
    spike_counter_concat = npconcat(data.spike_counter_dict)
    cycle_time_concat = npconcat(data.cycle_time_dict)

    x_lim = (0, 200)
    y_lim = (1, 6)

    s = spike_counter_concat[1:][::1]
    c = cycle_time_concat[:-1][::1]
    n = len(s) // 2

    print("number of data points: " + str(n))

    #    s = s[1000000:]
    #    c = c[1000000:]

    plt.figure(figsize=(15, 8))
    plt.plot(s[:n], c[:n], ".", alpha=1, color="orange")
    plt.plot(s[n:], c[n:], ".", alpha=0.1, color="blue")
    plt.ylabel("cycle time in ms")
    plt.xlabel("spike counter")
    plt.xlim(x_lim)
    plt.ylim(y_lim)
    plt.savefig(filename)
    plt.close()

    log.info("saved as %s", filename)


def correlation_spikes_plot(data, filename: str = "plot.png"):
    "Make a spike-count vs. cycle-time plot of the extracted data and plot it."
    log.info("ploting spike count - cycle-times correlation")
    spike_counter_concat = npconcat(data.spike_counter_dict)
    cycle_time_concat = npconcat(data.cycle_time_dict)

    x_lim = (0, 200)
    y_lim = (1, 6)

    s = spike_counter_concat[1:][::1]
    c = cycle_time_concat[:-1][::1]

    d = 1
    s = s[::d]
    c = c[::d]

    # sc = np.vstack([s, c])
    #    z = gaussian_kde(sc)(sc)
    #    z = gaussian_kde(sc,bw_method=0.001)(sc)

    # Sort the points by density, so that the densest points are plotted last
    #    i = z.argsort()
    #    x, y, z = s[i], c[i], z[i]

    #    plt.figure(figsize=(15, 8))
    _, ax = plt.subplots()
    #    a = ax.scatter(x, y, c=z, s=5, cmap='viridis')
    ax.scatter(s, c, c="orange", s=1)

    #    plt.colorbar(a, label='Point Density')
    plt.ylabel("cycle time in ms")
    plt.xlabel("spike counter")
    plt.xlim(x_lim)
    plt.ylim(y_lim)

    uuid = str(data.ct_logfiles[0].parts[0])

    ax.text(
        0.98,
        0.5,
        uuid,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        rotation="vertical",
        va="center",
        ha="right",
    )

    plt.savefig(filename)
    plt.close()

    log.info("saved as %s", filename)


def cycletime_vs_spikecount(data, rtf, filename: str | Path = "plot.png"):
    "Make a spike-count vs. cycle-time plot of the extracted data and plot it."
    spike_counter_concat = npconcat(data.spike_counter_dict)
    cycle_time_concat = npconcat(data.cycle_time_dict)

    time_lim = int(round(6 * 16 / data.mpi_processes))
    count_lim = int(round(200 * 16 / data.mpi_processes))

    x = spike_counter_concat[1:][::1]
    y = cycle_time_concat[:-1][::1]

    H, _ = np.histogram2d(x, y, bins=100, range=[[0, count_lim], [0, time_lim]])

    fig, ax = plt.subplots()

    # Transpose H so x is horizontal, y is vertical
    Z = H.T

    norm = colors.LogNorm(vmin=Z[Z > 0].min(), vmax=Z.max())
    im = ax.imshow(
        Z,
        norm=norm,
        cmap="viridis",
        origin="lower",
        extent=[0, count_lim, 0, time_lim],
        aspect="auto",
        #        vmax = 1000
    )

    fig.colorbar(im, ax=ax, label="counts")

    ax.set_xlabel("spike count")
    ax.set_ylabel("cycle time")
    ax.set_title("log density histogram")

    uuid = str(data.ct_logfiles[0].parts[0])

    ax.text(
        0.98,
        0.5,
        uuid,
        transform=ax.transAxes,  # axes coords: (0,0)=bottom-left, (1,1)=top-right
        rotation="vertical",
        va="center",
        ha="right",
    )

    ax.text(
        0.9, 0.98, rtf, transform=ax.transAxes, va="top", ha="right"  # axes coords: (0,0)=bottom-left, (1,1)=top-right
    )

    plt.savefig(filename)
    plt.close()


def main():
    "Run all plots in this script."
    #    logging.basicConfig(level=logging.DEBUG)

    data = load(data_path)

    print("working in path: ", data_path)

    try:
        r = next(data_path.rglob("benchmark_results.csv"))
    except StopIteration:
        print("benchmark_results.csv not available in this data set")
        try:
            r = next(data_path.rglob("stdout"))
        except StopIteration:
            print("stdout not available in this set")
        else:
            print("stdout found")
            pattern = re.compile(r"Simulated network in ([0-9.+-eE]+) seconds\.")
            values = []
            with r.open(encoding="utf-8") as f:
                for line in f:
                    m = pattern.search(line)
                    if m:
                        values.append(float(m.group(1)))
                t_wall = sum(values) / len(values)
            try:
                r = next(data_path.rglob("default_params.py"))
            except StopIteration:
                print("default_params.py not available in this set")
            else:
                print("default_params.py")
                t = r.read_text(encoding="utf-8")
                m = re.search(r"'t_sim':\s*([-+0-9.eE]+)", t)
                if m:
                    t_model = float(m.group(1))

    else:
        d = pd.read_csv(r)
        t_wall = d["time_simulate"].iloc[0]
        t_model = d["model_time_sim"].iloc[0] / 1000

    print("t_wall  = " + str(t_wall))
    print("t_model = " + str(t_model))

    print("from data object:")
    print("t_wall = " + str(data.t_wall))
    print("t_wall_2ndhalf = " + str(data.t_wall_2ndhalf))

    rtf = (
        "RTF = "
        + format(data.t_wall / t_model, ".2f")
        + " ("
        + format(data.t_wall_2ndhalf / (t_model / 2.0), ".2f")
        + ")"
    )

    print(rtf)

    output_path.mkdir(parents=True, exist_ok=True)

    uuid = str(data.ct_logfiles[0].parts[0])

    output_ct_heatmap = output_path / f"{uuid}_{output_name}_heatmap.png"
    output_ct_corr_hist = output_path / f"{uuid}_{output_name}_cycle_times_correlation_hist.png"
    output_pf = output_path / f"{uuid}_{output_name}_page_faults.png"
    output_ct = output_path / f"{uuid}_{output_name}_cycle_times.png"

    # output_ct_corr = output_path/f"{output_name}_cycle_times_correlation.png"
    # output_ct_pf = output_path / f"{output_name}_cycletimes_pagefaults.png"

    heatmap(data, rtf, cutoff_factor=float(cutoff), filename=str(output_ct_heatmap))
    cycletime_vs_spikecount(data, rtf, output_ct_corr_hist)
    page_faults_plot(data, rtf, filename=str(output_pf))

    cycle_times_function(data, rtf, cutoff_factor=float(cutoff), filename=str(output_ct))

    # pagefaults_vs_cycletime_plot(
    #    data,
    #    filename=output_ct_pf,
    #    machine_name=machine
    # )

    print(output_ct_heatmap)


if __name__ == "__main__":
    main()
