import pandas as pd
from pathlib import Path


def liv_analysis(data_path: Path, analysis_flags: dict[str, bool], plot_livs: bool):
    df = pd.read_csv(data_path)


def plot_grouped_livs(df: pd.DataFrame,
                      analyze_by: list[str] | str,
                      unique_identifiers: list[str] | str,
                      ):
    mean_df =df.groupby(by=analyze_by, as_index=False).mean()

    fig, axs = plt.subplots(1, 2)
    for name, group in mean_df.groupby(by=unique_identifiers, as_index=False):
        label = ''
        if len(unique_identifiers) > 1:
            for i, name_part in enumerate(name):
                label += f"{unique_identifiers[i][0]}: {name_part} "
        else:
            label = f"{unique_identifiers[0][0]}: {name[0]}"
        axs[0].plot(group["Measured Current (mA)"],
                    group["Measured Power (mW)"],
                    label=label
                    )
        axs[1].plot(group["Measured Current (mA)"],
                    group["Efficiency"],
                    )

    fig.legend(loc="upper left")

    return fig


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    path = Path(r"C:\Users\Matt\PycharmProjects\Quintessent Presentation\resources\test_results\data.csv")
    test_df = pd.read_csv(path)

    fig = plot_grouped_livs(test_df,
                            analyze_by=["Wafer ID", "Field ID", "Set Current (mA)"],
                            unique_identifiers=["Wafer ID", "Field ID"]
                            )

    plt.show()

    # # Groups all the data by wafer and field and then averages each set current for every device within each group
    # grouped_average = test_df.groupby(by=["Wafer ID", "Field ID", "Set Current (mA)"], as_index=False).mean()
    # for test_name, test_group in grouped_average.groupby(by=["Wafer ID", "Field ID"]):
    #     plt.plot(test_group["Measured Current (mA)"],
    #              test_group["Measured Power (mW)"],
    #              label=f"W: {test_name[0]}, F: {test_name[1]}"
    #              )
    # plt.legend(loc="upper left")
    # plt.show()



