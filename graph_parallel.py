import os
import sys
import numpy as np
import configparser
import matplotlib.pyplot as plt
from OtherScripts.simutil import *

# TODO: ALL FOLDERS MUST BE OF THE SAME TYPE OF SIMULATION FIX THAT
# TODO: THE RESULT IS SAVED INSIDE THE OUT FOLDER (MAYBE FIX)
# TODO: CURRENTLY ONLY A VIOLIN PLOT FOR SCENARIO 2 IS CREATED
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
                            thr_match.append(float(line.replace("Mean flow throughput: ", "").strip()))
                        elif "Mean flow delay: " in line:
                            delay_match.append(float(line.replace("Mean flow delay: ", "").strip()))
                        else:
                            pass

    return (thr_match, delay_match)

def getArrayForViolin():
    folders = search_outputs_folder(PATH)

    tempThr = []
    tempDelay = []

    delayArray = {'data':[], 'labels': []}
    thrArray = {'data':[], 'labels': []}

    for simFolder in folders:
        thr, delay = read_flow_output(simFolder)
        sim1Root = os.path.join(simFolder, "SIM1", "graph.ini")
        targetBler = configparser.ConfigParser()
        targetBler.read(sim1Root)
        targetBler = targetBler["general"]["blerTarget"]
        
        tempThr.append({targetBler:thr})
        tempDelay.append({targetBler:delay})

    tempThr.sort(key=lambda x:list(x)[0])
    tempDelay.sort(key=lambda x:list(x)[0])

    thrArray["data"] = [list(x.values())[0] for x in tempThr]
    thrArray["labels"] = [list(x)[0] for x in tempThr]
 
    delayArray["data"] = [list(x.values())[0] for x in tempDelay]
    delayArray["labels"] = [list(x)[0] for x in tempDelay]

    return (thrArray, delayArray)


@info_n_time_decorator("Throughput Violin", True)
def violinGraphThr(data):    

    plt.violinplot(data["data"], showmeans=True)
    plt.suptitle("Comparison of throughput in scenario 2")
    plt.title("Values of target BLER are changed.")
    plt.xlabel("Target BLER")
    plt.ylabel("Throughput [Mb/s]")
    plt.xticks(np.arange(1, len(data["labels"])+1), labels=data["labels"])
    plt.savefig(os.path.join(PATH, "Thr-Violin-Par.png"), dpi=300)
    plt.close()

    return True

@info_n_time_decorator("Delay Violin", debug=True)
def violinGraphDelay(data):    

    plt.violinplot(data["data"], showmeans=True)
    plt.suptitle("Comparison of Delay in scenario 2")
    plt.title("Values of target BLER are changed.")
    plt.xlabel("Target BLER")
    plt.ylabel("Delay [s]")
    plt.xticks(np.arange(1, len(data["labels"])+1), labels=data["labels"])
    plt.savefig(os.path.join(PATH, "Delay-Violin-Par.png"), dpi=300)
    plt.close()

    return True

if __name__ == "__main__":
    if len(sys.argv) == 2:
        PATH = sys.argv[1]
    else:
        raise ArgumentError(f"{RED}Incorrect number of arguments, given {len(sys.argv)} expected 1{CLEAR}")
    
    t, d = getArrayForViolin()
    violinGraphThr(t)
    violinGraphDelay(d)