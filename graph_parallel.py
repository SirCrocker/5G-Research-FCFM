import os
import sys
import numpy as np
import pandas as pd
import configparser
import matplotlib.pyplot as plt
from OtherScripts.simutil import *

# TODO: ALL FOLDERS MUST BE OF THE SAME TYPE OF SIMULATION FIX THAT
# TODO: THE RESULT IS SAVED INSIDE THE OUT FOLDER (MAYBE FIX)
# TODO: CHECK IF CODE IS NOT TOO MESSY

PATH = ""


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


@info_n_time_decorator("Throughput Violin", True)
def violinGraphThr(data):

    plt.violinplot(data["data"], showmeans=True, showextrema=True)
    plt.suptitle("Comparison of throughput showing the mean")
    plt.title("Combination of Algorithms-Scenarios.")
    plt.xlabel("Algorithm-Scenario")
    plt.ylabel("Throughput [Mb/s]")
    plt.xticks(np.arange(1, len(data["labels"])+1), labels=data["labels"])
    plt.savefig(os.path.join(PATH, "Thr-Violin-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Delay Violin", debug=True)
def violinGraphDelay(data):

    plt.violinplot(data["data"], showmeans=True)
    plt.suptitle("Comparison of Delay showing the mean")
    plt.title("Combination of Algorithms-Scenarios.")
    plt.xlabel("Algorithm-Scenario")
    plt.ylabel("Delay [ms]")
    plt.xticks(np.arange(1, len(data["labels"])+1), labels=data["labels"])
    plt.savefig(os.path.join(PATH, "Delay-Violin-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Retransmissions", True)
def stackedbar_graph_rtx():
    data_dict = data_from_file_to_dict('RxPacketTrace.txt')

    RTX_OPTIONS = pd.Series(0, index=range(-1, 4), dtype=np.float64)
    for i, df in enumerate(data_dict["data"]):
        df["rtxNum"] = df.loc[df['direction'] == 'DL', "rv"]
        df.loc[(df["rv"] == 3) &
               (df["corrupt"] == 1) &
               (df['direction'] == 'DL'), "rtxNum"] = -1

        to_add = (df["rtxNum"].value_counts(normalize=True)*100)\
            .sort_index()

        data_dict["data"][i] = RTX_OPTIONS.add(to_add, fill_value=0).to_list()

    colors = ["#BE0000", "#019875", "#72CC50", "#BFD834", "#00AEAD"]
    bottom = np.zeros(len(data_dict["labels"]))

    for i, nrtx in enumerate(["Failed", "No rtx", "1 rtx", "2 rtx", "3 rtx"]):
        values = np.array([x[i] for x in data_dict["data"]])
        plt.bar(data_dict["labels"], values, 0.69, label=nrtx,
                bottom=bottom, color=colors[i])
        bottom += values

    # plt.violinplot(data_dict["data"], showextrema=True)
    plt.suptitle("Percentage of successful and failed blocks transmission")
    plt.title("with number of retransmissions needed, in PHY layer")
    plt.xlabel("Algorithm-Scenario")
    plt.ylabel("Percentage of blocks sent")
    plt.legend()
    # plt.yticks([-1, 0, 1, 2, 3])
    # plt.xticks(np.arange(1, len(data_dict["labels"])+1),
    #            labels=data_dict["labels"])
    plt.savefig(os.path.join(PATH, "Rtx-Violin-Par.png"), dpi=300)
    plt.close()

    return True


@info_n_time_decorator("Violin BLER", True)
def violin_graph_bler():
    data_dict = data_from_file_to_dict('RxPacketTrace.txt')

    for i, df in enumerate(data_dict["data"]):
        data_dict["data"][i] = df.loc[(df["direction"] == "DL"), "TBler"]\
                                 .to_list()

    plt.violinplot(data_dict["data"], showmeans=True)
    plt.suptitle("Comparison of accumulated BLER showing the mean")
    plt.title("Combination of Algorithms-Scenarios.")
    plt.xlabel("Algorithm-Scenario")
    plt.ylabel("BLER")
    plt.yscale("log")
    plt.xticks(np.arange(1, len(data_dict["labels"])+1),
               labels=data_dict["labels"])
    plt.savefig(os.path.join(PATH, "BLER-Violin-Par.png"), dpi=300)
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
