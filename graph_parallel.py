import os
import sys
import numpy as np
import pandas as pd
import configparser
import seaborn as sns
import matplotlib.pyplot as plt
from OtherScripts.simutil import *
from typing import TypedDict, List

# TODO: ALL FOLDERS MUST BE OF THE SAME TYPE OF SIMULATION FIX THAT
# TODO: THE RESULT IS SAVED INSIDE THE OUT FOLDER (MAYBE FIX)
# TODO: CHECK IF CODE IS NOT TOO MESSY

PATH = ""


class LabelsNdf(TypedDict):
    data: pd.DataFrame
    labels: str
    scene: str


def search_outputs_folder(directory):
    folders_with_outputs = []
    for root, dirs, _ in os.walk(directory):
        if 'outputs' in dirs:
            folders_with_outputs.append(root)
    return folders_with_outputs


def read_flow_output(directory):
    thr_match = []
    delay_match = []
    for root, dir, _ in os.walk(directory):
        for sim in dir:
            file_path = os.path.join(root, sim, 'FlowOutput.txt')
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    content = file.readlines()
                    for line in content:
                        if "Mean flow throughput: " in line:
                            thr_match.append(float(
                                line.replace("Mean flow throughput: ", "")
                                .strip()))
                        elif "Mean flow delay: " in line:
                            delay_match.append(float(
                                line.replace("Mean flow delay: ", "")
                                .strip()))
                        else:
                            pass

    return (thr_match, delay_match)


def get_array_for_violin():
    folders = search_outputs_folder(PATH)

    tempThr = []
    tempDelay = []

    delayArray = {'data': [], 'labels': []}
    thrArray = {'data': [], 'labels': []}

    for simFolder in folders:
        thr, delay = read_flow_output(simFolder)
        sim1Root = os.path.join(simFolder, "SIM1", "graph.ini")
        simLabel = configparser.ConfigParser()
        simLabel.read(sim1Root)
        simLabel = simLabel["general"]["simlabel"]

        tempThr.append({simLabel: thr})
        tempDelay.append({simLabel: delay})

    tempThr.sort(key=lambda x: list(x)[0])
    tempDelay.sort(key=lambda x: list(x)[0])

    thrArray["data"] = [list(x.values())[0] for x in tempThr]
    thrArray["labels"] = [list(x)[0] for x in tempThr]

    delayArray["data"] = [list(x.values())[0] for x in tempDelay]
    delayArray["labels"] = [list(x)[0] for x in tempDelay]

    return (thrArray, delayArray)


def data_from_file_to_dict(filename: str) -> dict:
    """
    From a datafile takes all the data and creates a join dataframe where all
    the values are saved. Returns a dictionary with a 'labels' and 'data' keys
    which have a list of labels and dataframes, respectively. The lists are
    sorted by the label and data in pos 'x' corresponds to label in pos 'x'
    """
    folders = search_outputs_folder(PATH)

    _dicts_with_df = []
    dicts_with_df = {"data": [],
                     "labels": []}
    # folders with a specific simulation is located (inside are the SIMX foldr)
    for sim_folder in folders:
        all_dfs = []
        for root, dir, _ in os.walk(sim_folder):
            for sim in dir:  # sim are the SIMX folders
                file_path = os.path.join(root, sim, filename)
                if os.path.isfile(file_path):
                    df = pd.read_csv(file_path, sep="\t")
                    all_dfs.append(df)

        # Get simulation label
        sim1Root = os.path.join(sim_folder, "SIM1", "graph.ini")
        simLabel = configparser.ConfigParser()
        simLabel.read(sim1Root)
        simLabel = simLabel["general"]["simlabel"]

        # Concatenate all the dataframes
        final_df = pd.concat(all_dfs)

        # Add the data to the final list
        _dicts_with_df.append({simLabel: final_df})

    _dicts_with_df.sort(key=lambda x: list(x)[0])

    dicts_with_df["data"] = [list(x.values())[0] for x in _dicts_with_df]
    dicts_with_df["labels"] = [list(x)[0] for x in _dicts_with_df]

    return dicts_with_df


def separate_by_scenario(data: LabelsNdf) -> List[LabelsNdf]:
    # Create a dict with possible labels
    scenarios = {}
    for pos, label in enumerate(data["labels"]):
        specs = [label[2*x:2*x+2] for x in range(len(label)//2)]

        for spec in specs:
            if "S" in spec:
                if spec not in scenarios.keys():
                    scenarios[spec] = {"labels": [], "data": [], "scene": []}

                scenarios[spec]["labels"].append(label.replace(spec, "")
                                                      .replace("A0", "A1"))  # >Cochinada por ahora, arreglar en simulación después !!
                scenarios[spec]["data"].append(data["data"][pos])
                scenarios[spec]["scene"] = spec

    return list(scenarios.values())


@info_n_time_decorator("Throughput Violin", True)
def violinGraphThr(data):

    data = separate_by_scenario(data)
    n_cols = len(data)

    fig, axes = plt.subplots(1, n_cols)

    axes[0].set_ylabel("Throughput [Mb/s]")
    # palettes = [sns.color_palette("Set1")[:4], sns.color_palette("Set1")[4:]]
    palettes = [sns.color_palette("Set1"), sns.color_palette("Pastel1")]
    for pos, ax in enumerate(axes):
        max_len = len(sorted(data[pos]["data"], key=lambda x: len(x))[-1])

        thrs = []
        for thr in data[pos]["data"]:
            if len(thr) < max_len:
                thr = thr + [np.nan] * (max_len - len(thr))
            thrs.append(thr)

        dii = dict(A1=r"$BLER_{10\%}$", A2=r"$BLER_{30\%}$",
                   A3=r"$BLER_{dyn}$", A4=r"$BLER_{hyb}$")
        aaa = list(map(lambda x: dii[x], data[pos]["labels"]))
        vals = np.array(thrs, dtype=float).T
        df = pd.DataFrame(data=vals, columns=aaa)

        sns.violinplot(data=df, ax=ax, cut=0, inner=None, palette=palettes[pos])
        sns.pointplot(data=df, estimator=np.mean, color="black", ax=ax,
                      linestyles="--", errorbar=None, scale=0.5, label="Mean")

        # Add text on top of the pointplots
        for p in zip(ax.get_xticks(),
                     np.round(np.nanmean(vals, axis=0), decimals=1)):
            # Distance from pointplot
            weight = 1.032 if p[1] > 50 else 1.25
            ax.text(p[0], p[1]*weight, p[1], color='black', ha='center',
                    bbox=dict(facecolor='white', alpha=0.4, boxstyle="round"))

        if pos == 1:
            ax.set_ylim([0, 65])

        ax.set_title(data[pos]["scene"].replace("S", "Scenario "))
        ax.set_xlabel("Algorithm")
        ax.legend()
        ax.set_xticks(ticks=range(4), labels=aaa, rotation=5, fontsize=9.2)

    fig.suptitle("Distribution of Throughput by Algorithm-Scenario")
    fig.savefig(os.path.join(PATH, "Thr-Violin-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Delay Violin", debug=True)
def violinGraphDelay(data):

    data = separate_by_scenario(data)
    n_cols = len(data)

    fig, axes = plt.subplots(1, n_cols)
    palettes = [sns.color_palette("Set1"), sns.color_palette("Pastel1")]
    axes[0].set_ylabel("Delay [ms]")
    for pos, ax in enumerate(axes):
        max_len = len(sorted(data[pos]["data"], key=lambda x: len(x))[-1])

        thrs = []
        for thr in data[pos]["data"]:
            if len(thr) < max_len:
                thr = thr + [np.nan] * (max_len - len(thr))
            thrs.append(thr)

        dii = dict(A1=r"$BLER_{10\%}$", A2=r"$BLER_{30\%}$",
                   A3=r"$BLER_{dyn}$", A4=r"$BLER_{hyb}$")
        aaa = list(map(lambda x: dii[x], data[pos]["labels"]))

        vals = np.array(thrs, dtype=float).T
        df = pd.DataFrame(data=vals, columns=aaa)
        df.replace(0, np.nan, inplace=True)
        # df.to_csv("DelayDf.txt", sep="\t", encoding="utf-8")

        sns.violinplot(data=df, ax=ax, cut=0, inner=None, palette=palettes[pos])
        sns.pointplot(data=df, estimator=np.mean, color="black", ax=ax,
                      linestyles="--", errorbar=None, scale=0.5, label="Mean")

        # Add text on top of the pointplots
        for p in zip(ax.get_xticks(),
                     np.round(np.nanmean(vals, axis=0), decimals=1)):
            # Distance from pointplot
            weight = 1.11 if p[1] > 50 else 1.045
            ax.text(p[0], p[1]*weight, p[1], color='black', ha='center',
                    bbox=dict(facecolor='white', alpha=0.4, boxstyle="round"))

        if pos == 0:
            ax.set_ylim([0, 20])
        if pos == 1:
            ax.set_ylim([0, 400])

        ax.set_title(data[pos]["scene"].replace("S", "Scenario "))
        ax.set_xlabel("Algorithm")
        ax.legend()

        ax.set_xticks(ticks=range(4), labels=aaa, rotation=5, fontsize=9.2)
    fig.suptitle("Distribution of Packet Delay by Algorithm-Scenario")
    fig.savefig(os.path.join(PATH, "Delay-Violin-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Retransmissions", True)
def stackedbar_graph_rtx():
    data_dict = data_from_file_to_dict('RxPacketTrace.txt')

    RTX_OPTIONS = pd.Series(0, index=range(-1, 4), dtype=np.float64)

    for i, df in enumerate(data_dict["data"]):
        df.reset_index(drop=True, inplace=True)
        df["rtxNum"] = df.loc[df['direction'] == 'DL', "rv"]
        df.loc[(df["rv"] == 3) &
               (df["corrupt"] == 1) &
               (df['direction'] == 'DL'), "rtxNum"] = -1

        to_add = (df["rtxNum"].value_counts(normalize=True)*100)\
            .sort_index()

        data_dict["data"][i] = RTX_OPTIONS.add(to_add, fill_value=0).to_list()

    colors = ["#BE0000", "#019875", "#72CC50", "#BFD834", "#00AEAD"]

    data = separate_by_scenario(data_dict)
    n_cols = len(data)
    fig, axes = plt.subplots(1, n_cols)

    axes[0].set_ylabel("Percentage of sent blocks [%]")
    for pos, ax in enumerate(axes):
        bottom = np.zeros(len(data[pos]["labels"]))

        dii = dict(A1=r"$BLER_{10\%}$", A2=r"$BLER_{30\%}$",
                   A3=r"$BLER_{dyn}$", A4=r"$BLER_{hyb}$")
        aaa = list(map(lambda x: dii[x], data[pos]["labels"]))

        for i, nrtx in enumerate(["Failed", "No Re-TX",
                                  "1 Re-TX", "2 Re-TX", "3 Re-TX"]):
            values = np.array([x[i] for x in data[pos]["data"]])
            ax.bar(data[pos]["labels"], values, 0.69, label=nrtx,
                   bottom=bottom, color=colors[i])
            bottom += values
        ax.set_title(data[pos]["scene"].replace("S", "Scenario "))
        ax.set_xlabel("Algorithm")
        ax.legend()
        ax.set_xticks(ticks=range(4), labels=aaa, rotation=5, fontsize=9.2)

    fig.suptitle("Percentage of successful and failed blocks transmission")
    fig.savefig(os.path.join(PATH, "Rtx-Bar-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Violin BLER", True)
def violin_graph_bler():
    data_dict = data_from_file_to_dict('RxPacketTrace.txt')

    for i, df in enumerate(data_dict["data"]):
        data_dict["data"][i] = df.loc[(df["direction"] == "DL"), "TBler"]\
                                 .to_list()

    data = separate_by_scenario(data_dict)
    n_cols = len(data)

    fig, axes = plt.subplots(1, n_cols)

    axes[0].set_ylabel("BLER")
    for pos, ax in enumerate(axes):
        max_len = len(sorted(data[pos]["data"], key=lambda x: len(x))[-1])

        thrs = []
        for thr in data[pos]["data"]:
            if len(thr) < max_len:
                thr = thr + [np.nan] * (max_len - len(thr))
            thrs.append(thr)

        vals = np.array(thrs, dtype=float).T
        df = pd.DataFrame(data=vals, columns=data[pos]["labels"])

        ax.grid(zorder=0)
        sns.violinplot(data=df, ax=ax, cut=0, inner=None)
        sns.pointplot(data=df, estimator=np.mean, color="black", ax=ax,
                      linestyles="--", errorbar=None, scale=.5, label="Mean")
        ax.set_title(data[pos]["scene"].replace("S", "Scenario "))
        ax.set_xlabel("Algorithm")
        ax.set_yscale("log")
        ax.legend()

    fig.suptitle("Distribution of BLER by Algorithm-Scenario")
    fig.savefig(os.path.join(PATH, "BLER-Violin-Par.png"), dpi=300)
    plt.close()

    return True


if __name__ == "__main__":
    if len(sys.argv) == 2:
        PATH = sys.argv[1]
    else:
        raise ArgumentError(f"{RED}Incorrect number of arguments, given "
                            f"{len(sys.argv)} expected 1{CLEAR}")

    t, d = get_array_for_violin()
    violinGraphThr(t)
    violinGraphDelay(d)
    stackedbar_graph_rtx()
    violin_graph_bler()
