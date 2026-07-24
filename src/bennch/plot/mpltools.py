"Matplotlib tweaks that are commonly used."

import logging

log = logging.getLogger(__name__)


def simple_axis(ax):
    """
    Remove top and right spines.

    Attributes
    ----------
    ax : axes object
        axes object for which to adjust spines
    """
    # Hide the right and top spines
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position("left")
    ax.xaxis.set_ticks_position("bottom")


def merge_legends(ax1, ax2):
    """
    Merge legends from two axes, display them in the first.

    Attributes
    ----------
    ax1 : axes object
        first axis
    ax2 : axes object
        second axis
    """
    handles, labels = [(a + b) for a, b in zip(ax2.get_legend_handles_labels(), ax1.get_legend_handles_labels())]
    ax1.legend(handles, labels, loc="upper right")
