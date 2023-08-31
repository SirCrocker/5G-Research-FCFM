import matplotlib.pyplot as plt
import pandas as pd
import functools
import time

# Set text colors
CLEAR = '\033[0m'
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'

# Set Background colors
BG_RED = '\033[0;41m'
BG_GREEN = '\033[0;42m'
BG_YELLOW = '\033[0;43m'
BG_BLUE = '\033[0;44m'
BG_MAGENTA = '\033[0;45m'
BG_CYAN = '\033[0;46m'


# Error for the number of arguments
class ArgumentError(BaseException):
    pass

# ----------------------------------------------------------
# Decorator for time
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# It calculates the time it takes to execute the function
# and prints its name (that must be passed as an argument)
# and the time it took to execute.
#
# e.g.
# @info_n_time_decorator("Custom function")
# def myfunc():
#   if works:
#       return True
#   else:
#       return False
#
# ----------------------------------------------------------
def info_n_time_decorator(name, debug=False):

    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            print(CYAN + name + CLEAR, end="...", flush=True)
            tic = time.time()

            func_ret = False
            try:
                func_ret = func(*args, **kwargs)
            except KeyboardInterrupt:
                print(f"{RED}User canceled.{CLEAR}", end="")
            except Exception as e:
                if debug:
                    print(f"Exception thrown: {e}")
            finally:
                plt.close()

            if func_ret:
                toc = time.time()
                print(f"\tProcessed in: %.2f" % (toc-tic))
            else:
                print(RED + "\tError while processing. Skipped." + CLEAR)

        return wrapper
    return actual_decorator

# Prints the number of lost packets and if noise was present or not
# in the simulation.
@info_n_time_decorator("UDP Loss")
def checkUdpLoss(homepath: str, noisePresent):

    # In this test we only have 1 UE, with NodeId=1
    filepath = homepath + "UdpRecv_Node1.txt"
    df = pd.read_csv(filepath, sep="\t")
    pcktSeqCopy = df["Packet Sequence"].copy()
    # To check differences between current packet number and last one
    pcktSeqCopy.iloc[1:] = pcktSeqCopy.iloc[0:-1] + 1
    df['Packets Lost'] = df["Packet Sequence"] - pcktSeqCopy
    
    print(f"{YELLOW}Number of packets lost:{CLEAR} {df['Packets Lost'].sum()} \
          \t{YELLOW}Noise:{CLEAR} {bool(int(noisePresent))}", flush=True)

    return True