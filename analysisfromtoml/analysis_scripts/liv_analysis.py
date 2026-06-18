import sys
from datetime import datetime
import pandas as pd
from pathlib import Path
import numpy as np
from scipy.stats import linregress
from rich import print
import colorcet as cc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.ticker import (
    FormatStrFormatter,
    FixedLocator
)

from test_class.test_class import file_timestamp_format

is_frozen = getattr(sys, 'frozen', False)
if is_frozen:
    cwd = Path(sys._MEIPASS)
else:
    cwd = Path.cwd()

save_dir = cwd / "resources" / "analysis_results"


colormap = cc.glasbey_dark


def liv_analysis(data_path: Path,
                 analysis_flags: dict[str, bool],
                 analysis_groupings: dict[str, bool]
                 ) -> Path:
    df = pd.read_csv(data_path)

    analyze_by = [k for k in analysis_groupings.keys() if analysis_groupings[k] is True] + ["Set Current (mA)"]
    grouped_df = df.groupby(by=analyze_by,
                            as_index=False
                            )
    mean_df = grouped_df.mean()

    title = generate_title(data_path)

    return plot_mean_livs(mean_df,
                          analysis_flags=analysis_flags,
                          analysis_groupings=analysis_groupings,
                          title=title,
                          filename=get_filename(data_path)
                          )


def generate_title(data_path: Path):
    filename = data_path.name
    filename = filename.split(".")[0].split("_")
    timestamp = filename[-1]
    timestamp = datetime.strptime(timestamp, file_timestamp_format)
    title = f"Mean LIV Analysis \u2014 {' '.join(filename[:-1])} \u2014 " + timestamp.strftime("%X %x")
    return title


def get_filename(data_path: Path):
    return data_path.name.split(".")[0]


def plot_mean_livs(df: pd.DataFrame,
                   analysis_flags: dict[str, bool],
                   analysis_groupings: dict[str, bool],
                   title: str = None,
                   filename: Path | str = None
                   ) -> Path:
    analysis_groupings = [k for k in analysis_groupings.keys() if analysis_groupings[k] is True]

    if len(analysis_groupings) > 0:
        fig, (ax0, ax1) = plt.subplots(2, 1, layout='tight', figsize=(10, 8))
        ax1_2 = ax1.twinx()
    else:
        fig, (ax0, ax1) = plt.subplots(1, 1, layout='tight', figsize=(10, 8))

    ax0_2 = ax0.twinx()
    fig.suptitle(title,
                 fontsize=16
                 )
    ax0.grid(which='both',
             axis='both',
             zorder=0
             )
    ax1.grid(which='both',
             axis='y',
             zorder=0
             )

    processed_data = {}
    all_labels = []
    for idx, (name, group) in enumerate(df.groupby(analysis_groupings, as_index=False)):
        processed_data[name] = {"threshold": None,
                                "thresh_unc": None,
                                "slope_efficiency": None,
                                "slope_eff_unc": None
                                }
        label = ''
        if len(analysis_groupings) > 1:
            for i, name_part in enumerate(name):
                label += f"{analysis_groupings[i][0]}{name_part} "
        else:
            label = f"{analysis_groupings[0][0]}{name[0]}"

        all_labels.append(label)

        ax0.plot(group["Measured Current (mA)"],
                 group["Measured Power (mW)"],
                 label=label,
                 color=colormap[idx],
                 zorder=2
                 )
        ax0_2.plot(group["Measured Current (mA)"],
                   group["Efficiency"],
                   ':',
                   color=colormap[idx],
                   zorder=2
                   )

        fit_subset = group[group["Measured Current (mA)"] > 500]

        if analysis_flags["threshold"]:
            thresh_fit = linregress(fit_subset["Measured Current (mA)"],
                                    fit_subset["Measured Power (mW)"],
                                    alternative="greater"
                                    )
            threshold = -thresh_fit.intercept / thresh_fit.slope
            threshold_uncertainty = ((thresh_fit.intercept_stderr / abs(thresh_fit.intercept)) + (thresh_fit.stderr / thresh_fit.slope)) * abs(threshold)
            processed_data[name]["threshold"] = threshold
            processed_data[name]["thresh_unc"] = threshold_uncertainty

            ax1.bar(idx - 0.125,
                    processed_data[name]["threshold"],
                    width=0.25,
                    color='#DE4B65',
                    yerr=processed_data[name]["thresh_unc"],
                    capsize=3,
                    zorder=2.1
                    )

        if analysis_flags["slope_efficiency"]:
            eff_fit = linregress(fit_subset["Measured Current (mA)"] * fit_subset["Measured Voltage (V)"],
                                 fit_subset["Measured Power (mW)"],
                                 alternative="greater"
                                 )

            processed_data[name]["slope_efficiency"] = eff_fit.slope
            processed_data[name]["slope_eff_unc"] = eff_fit.stderr

            if analysis_flags["threshold"]:
                ax1_2.bar(idx + 0.125,
                          processed_data[name]["slope_efficiency"],
                          width=0.25,
                          color='#612771',
                          yerr=processed_data[name]["slope_eff_unc"],
                          capsize=3,
                          zorder=2
                          )
            else:
                ax1.bar(idx + 0.125,
                        processed_data[name]["slope_efficiency"],
                        width=0.25,
                        color='#612771',
                        yerr=processed_data[name]["slope_eff_unc"],
                        capsize=3,
                        zorder=2
                        )

    # Formatting power plot
    ax0.set_axisbelow(True)
    ax0.xaxis.minorticks_on()
    x_data = ax0.get_lines()[0].get_xdata()
    min_x, max_x = np.min(x_data), np.max(x_data)
    x_axis_padding = (max_x - min_x) * 0.01
    ax0.set_xlim(0 - x_axis_padding, max_x + x_axis_padding)
    norm_ytick_positions(ax0)
    ax0.set_xlabel("Current (mA)", fontsize=12)
    ax0.set_ylabel("Power (mW)", fontsize=12)

    # Formatting efficiency plot
    norm_ytick_positions(ax0_2)
    ax0_2.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax0_2.set_ylabel("Efficiency", fontsize=12)

    # Formatting legends/figure
    device_handles_legend = ax0.legend(loc="lower right",
                                       ncols=len(all_labels) // 5 if len(all_labels) > 5 else 1,
                                       labelspacing=0.3,
                                       columnspacing=1,
                                       handlelength=1,
                                       )
    ax0.add_artist(device_handles_legend)

    power_line = mlines.Line2D([],
                               [],
                               color='black',
                               linestyle='-',
                               label='Power'
                               )
    eff_line = mlines.Line2D([],
                             [],
                             color='black',
                             linestyle=':',
                             label='Efficiency'
                             )
    ax0.legend(handles=[power_line, eff_line],
               loc="lower right",
               labelspacing=0.3,
               bbox_to_anchor=(1, 0.33),
               )

    if analysis_flags["threshold"]:
        format_threshold_plot(ax1,
                              processed_data,
                              analysis_groupings,
                              all_labels
                              )
        thresh_patch = mpatches.Patch(color='#DE4B65',
                                      label='$I_{Th}$',
                                      zorder=2
                                      )
    else:
        thresh_patch = None

    if analysis_flags["slope_efficiency"]:
        ax_to_pass = ax1_2 if analysis_flags["threshold"] else ax1
        format_slope_eff_plot(ax_to_pass,
                              processed_data,
                              analysis_groupings,
                              all_labels
                              )
        slope_patch = mpatches.Patch(color='#612771',
                                     label=r'$\frac{\Delta P}{\Delta I}$',
                                     zorder=2
                                     )
    else:
        slope_patch = None

    thresh_slope_handles = [handle for handle in [thresh_patch, slope_patch] if handle is not None]
    if len(thresh_slope_handles) > 0:
        ax1.legend(handles=thresh_slope_handles,
                   loc="best",
                   labelspacing=0.3,
                   handlelength=1,
                   fontsize=12
                   )
    full_filename = save_dir / f"{filename}.png"
    Path.mkdir(save_dir, exist_ok=True)
    fig.savefig(full_filename)
    print("[bright_magenta]Figure saved as:[/]", f"[bright_green]{full_filename}[/]")
    return full_filename


def format_threshold_plot(ax: plt.Axes,
                          processed_data: dict,
                          analysis_groupings: list[str] | str,
                          data_labels: list[str] | str
                          ):
    all_thresh = [processed_data[name]["threshold"] for name in processed_data.keys()]
    all_thresh_unc = [processed_data[name]["thresh_unc"] for name in processed_data.keys()]

    norm_y_ticks_w_uncertainties(ax,
                                 all_thresh,
                                 all_thresh_unc
                                 )
    ax.set_xticks(range(len(data_labels)),
                  data_labels,
                  fontsize=10
                  )
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    ax.set_xlabel(', '.join(analysis_groupings),
                  fontsize=12
                  )
    ax.set_ylabel("Threshold Current (mA)",
                  fontsize=12
                  )


def format_slope_eff_plot(ax: plt.Axes,
                          processed_data: dict,
                          analysis_groupings: list[str] | str,
                          data_labels: list[str] | str
                          ):
    all_slope_eff = [processed_data[name]["slope_efficiency"] for name in processed_data.keys()]
    all_slope_eff_unc = [processed_data[name]["slope_eff_unc"] for name in processed_data.keys()]

    ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax.set_xlabel(', '.join(data_labels),
                  fontsize=12
                  )
    ax.set_ylabel("Slope Efficiency",
                  fontsize=12
                  )

    if "threshold" not in analysis_groupings:
        ax.set_axisbelow(True)
        ax.grid(which='both',
                axis='y',
                color='#d9d9d9',
                )
        norm_y_ticks_w_uncertainties(ax,
                                     all_slope_eff,
                                     all_slope_eff_unc
                                     )

        ax.set_xticks(range(len(data_labels)),
                      data_labels,
                      fontsize=10
                      )


def norm_ytick_positions(ax: plt.Axes,
                         padding: float = 0.05
                         ):
    ax_data = []
    for line in ax.get_lines():
        ax_data.append(line.get_ydata())

    ax_ymin, ax_ymax = np.min(ax_data), np.max(ax_data)
    ax_padding = (ax_ymax - ax_ymin) * padding
    ax.set_ylim(ax_ymin - ax_padding, ax_ymax + ax_padding)
    ax.yaxis.set_major_locator(FixedLocator(np.linspace(0, ax_ymax, 9)))


def norm_y_ticks_w_uncertainties(ax: plt.Axes,
                                 values: list[float],
                                 value_uncertainties: list[float],
                                 padding: float = 0.05,
                                 ):
    max_value = np.max(values) + value_uncertainties[values.index(max(values))]
    min_value = min(values) - value_uncertainties[values.index(min(values))]

    ax_padding = (max_value - min_value) * padding

    ax.set_ylim(min_value - ax_padding, max_value + ax_padding)
    ax.yaxis.set_major_locator(FixedLocator(np.linspace(min_value, max_value, 9)))


if __name__ == '__main__':
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        cwd = Path(sys._MEIPASS)
    else:
        cwd = Path.cwd()
    test_path = cwd / "resources" / "test_results" / "W1234_F1-10_D1-10_20240926-183603.csv"

    liv_analysis(test_path,
                 analysis_flags={"threshold": True, "slope_efficiency": True},
                 analysis_groupings={"Wafer ID": False, "Field ID": True}
                 )
