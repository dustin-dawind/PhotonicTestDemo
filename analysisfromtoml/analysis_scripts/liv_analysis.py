from locale import normalize

import pandas as pd
from pathlib import Path
import numpy as np
from scipy.stats import linregress
import colorcet as cc
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.ticker import (
    FormatStrFormatter,
    FixedLocator
)

colormap = cc.glasbey_dark


def liv_analysis(data_path: Path, analysis_flags: dict[str, bool], plot_livs: bool):
    df = pd.read_csv(data_path)


def plot_grouped_livs(df: pd.DataFrame,
                      analyze_by: list[str] | str,
                      unique_identifiers: list[str] | str,
                      title: str = None,
                      ):
    grouped_df = df.groupby(by=analyze_by, as_index=False)
    mean_df = grouped_df.mean()
    # std_df = grouped_df.std()

    processed_data = {}
    all_labels = []
    fig, (ax0, ax1) = plt.subplots(2, 1, layout='tight', figsize=(10, 8))
    ax0_2 = ax0.twinx()
    ax1_2 = ax1.twinx()
    for idx, (name, group) in enumerate(mean_df.groupby(unique_identifiers, as_index=False)):
        label = ''
        if len(unique_identifiers) > 1:
            for i, name_part in enumerate(name):
                if i != len(name) - 1:
                    label += f"{unique_identifiers[i][0]}{name_part}\n"
                else:
                    label += f"{unique_identifiers[i][0]}{name_part} "
        else:
            label = f"{unique_identifiers[0][0]}{name[0]}"

        all_labels.append(label)

        fit_subset = group[group["Measured Current (mA)"] > 500]

        thresh_fit = linregress(fit_subset["Measured Current (mA)"],
                                fit_subset["Measured Power (mW)"],
                                alternative="greater"
                                )
        eff_fit = linregress(fit_subset["Measured Current (mA)"] * fit_subset["Measured Voltage (V)"],
                             fit_subset["Measured Power (mW)"],
                             alternative="greater"
                             )
        threshold = -thresh_fit.intercept / thresh_fit.slope
        threshold_uncertainty = ((thresh_fit.intercept_stderr / abs(thresh_fit.intercept)) + (thresh_fit.stderr / thresh_fit.slope)) * abs(threshold)
        processed_data[name] = {"Thresh": threshold,
                                "Thresh_unc": threshold_uncertainty,
                                "Slope_eff": eff_fit.slope,
                                "Slope_eff_unc": eff_fit.stderr
                                }

        ax0.plot(group["Measured Current (mA)"],
                    group["Measured Power (mW)"],
                    label=label,
                    color=colormap[idx]
                    )
        ax0_2.plot(group["Measured Current (mA)"],
                 group["Efficiency"],
                 ':',
                 color=colormap[idx]
                 )

        ax1.bar(idx - 0.125,
                   processed_data[name]["Thresh"],
                   width=0.25,
                   color='#DE4B65',
                   yerr=processed_data[name]["Thresh_unc"],
                   capsize=3,
                   zorder=10
                   )
        ax1_2.bar(idx + 0.125,
                   processed_data[name]["Slope_eff"],
                   width=0.25,
                   color='#612771',
                   yerr=processed_data[name]["Slope_eff_unc"],
                   capsize=3,
                   zorder=10
                   )

    # Formatting power plot
    ax0.grid(which='both', axis='both', color='#d9d9d9', zorder=0)
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

    # Formatting threshold plot
    all_thresh = [processed_data[name]["Thresh"] for name in processed_data.keys()]
    all_thresh_unc = [processed_data[name]["Thresh_unc"] for name in processed_data.keys()]
    all_slope_eff = [processed_data[name]["Slope_eff"] for name in processed_data.keys()]
    all_slope_eff_unc = [processed_data[name]["Slope_eff_unc"] for name in processed_data.keys()]

    ax1.grid(which='both', axis='y', color='#d9d9d9', zorder=0)
    norm_y_ticks_w_uncertainties(ax1, all_thresh, all_thresh_unc)
    ax1.set_xticks(range(len(all_labels)),all_labels, fontsize=10)
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    ax1.set_xlabel(','.join(unique_identifiers), fontsize=12)
    ax1.set_ylabel("Threshold Current (mA)", fontsize=12)

    # Formatting slope efficiency plot
    norm_y_ticks_w_uncertainties(ax1_2, all_slope_eff, all_slope_eff_unc)
    ax1_2.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax1_2.set_ylabel("Slope Efficiency", fontsize=12)


    # Formatting legends/figure
    device_handles_legend = ax0.legend(loc="lower right",
                                          ncols=len(all_labels) // 5,
                                          labelspacing=0.3,
                                          columnspacing=1,
                                          handlelength=1,
                                          draggable=True,
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
               draggable=True,
               )

    thresh_patch = mpatches.Patch(color='#DE4B65', label='$I_{Th}$')
    slope_patch = mpatches.Patch(color='#612771', label=r'$\frac{\Delta P}{\Delta I}$')
    ax1.legend(handles=[thresh_patch, slope_patch],
               loc="best",
               labelspacing=0.3,
               handlelength=1,
               fontsize=12
               )

    fig.suptitle(title, fontsize=16)

    plt.show()
    return fig


def norm_ytick_positions(ax: plt.Axes,
                         padding: float = 0.05
                         ):
    ax_data = []
    for line in ax.get_lines():
        ax_data.append(line.get_ydata())

    ax_ymin, ax_ymax = np.min(ax_data), np.max(ax_data)
    ax_padding = (ax_ymax- ax_ymin) * padding
    ax.set_ylim(ax_ymin - ax_padding, ax_ymax + ax_padding)
    ax.yaxis.set_major_locator(FixedLocator(np.linspace(0, ax_ymax, 9)))


def norm_y_ticks_w_uncertainties(ax: plt.Axes,
                                 values: list[float],
                                 value_uncertainties: list[float],
                                 padding: float = 0.05,
                                 ):
    max_value = max(values) + value_uncertainties[values.index(max(values))]
    min_value = min(values) - value_uncertainties[values.index(min(values))]

    ax_padding = (max_value - min_value) * padding

    ax.set_ylim(min_value - ax_padding, max_value + ax_padding)
    ax.yaxis.set_major_locator(FixedLocator(np.linspace(min_value, max_value, 9)))

if __name__ == '__main__':
    path = Path(r"C:\Users\Matt\PycharmProjects\Quintessent Presentation\resources\test_results\W1234_F1-10_D1-100_20240925-122833.csv")
    # path = Path(r"C:\Users\mlarkins\Local Data\Programming\Automation\resources\test_results\data.csv")
    test_df = pd.read_csv(path)

    plot_grouped_livs(test_df,
                      analyze_by=["Wafer ID", "Field ID", "Set Current (mA)"],
                      unique_identifiers=["Field ID"],
                      title="LIV Analysis - W1234_F1-10_D1-100"
                      )

    # # Groups all the data by wafer and field and then averages each set current for every device within each group
    # grouped_average = test_df.groupby(by=["Wafer ID", "Field ID", "Set Current (mA)"], as_index=False).mean()
    # for test_name, test_group in grouped_average.groupby(by=["Wafer ID", "Field ID"]):
    #     plt.plot(test_group["Measured Current (mA)"],
    #              test_group["Measured Power (mW)"],
    #              label=f"W: {test_name[0]}, F: {test_name[1]}"
    #              )
    # plt.legend(loc="upper left")
    # plt.show()



