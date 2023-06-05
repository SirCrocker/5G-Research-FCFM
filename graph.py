import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import AnnotationBbox,OffsetImage
import matplotlib.patches as mpatches
import pandas as pd
import time
import sys
import configparser
import os
import functools
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import rdpcap, TCP

# Set text colors
CLEAR='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'

# Set Background colors
BG_RED='\033[0;41m'
BG_GREEN='\033[0;42m'
BG_YELLOW='\033[0;43m'
BG_BLUE='\033[0;44m'
BG_MAGENTA='\033[0;45m'
BG_CYAN='\033[0;46m'

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
def info_n_time_decorator(name):

    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            
            print(CYAN + name + CLEAR, end="...", flush=True)
            tic=time.time()

            try:
                func_ret = func(*args, **kwargs)
            except Exception as e:
                if False:
                    print(f"Exception thrown: {e}")
                func_ret = False

            if func_ret:
                toc = time.time()
                print(f"\tProcessed in: %.2f" %(toc-tic))
            else:
                print(RED + "\tError while processing. Skipped." + CLEAR)
        
        return wrapper
    return actual_decorator

if (len(sys.argv)>2):
    HOMEPATH=sys.argv[1]+"/"
    mainprobe=sys.argv[2]
else:
    print("Not enough arguments. Put: {path_to_folder} {path_to_cqiprobe}")
    exit()

config = configparser.ConfigParser()
config.read(HOMEPATH + 'graph.ini')

# ----------------------------------------------------------
# graph.ini info | Configurations and env variables values
# ----------------------------------------------------------
NRTrace = config['general']['NRTrace']
TCPTrace = config['general']['TCPTrace']
flowType = config['general']['flowType']
tcpTypeId = config['general']['tcpTypeId']
resamplePeriod=int(config['general']['resamplePeriod'])
simTime = float(config['general']['simTime'])
AppStartTime = float(config['general']['AppStartTime'])
rlcBuffer = float(config['general']['rlcBuffer'])
rlcBufferPerc = int(config['general']['rlcBufferPerc'])
serverType = config['general']['serverType']

serverID = config['general']['serverID']
UENum = int(config['general']['UENum'])
SegmentSize = float(config['general']['SegmentSize'])

if config.has_option('general', 'dataRate'):
    dataRate = float(config['general']['dataRate'])
else:
    dataRate = 1000
thr_limit = dataRate*1.1

gNbNum = int(config['gNb']['gNbNum'])
gNbX = float(config['gNb']['gNbX'])
gNbY = float(config['gNb']['gNbY'])
gNbD = float(config['gNb']['gNbD'])

enableBuildings = int(config['building']['enableBuildings'])
gridWidth = int(config['building']['gridWidth'])
buildN = int(config['building']['buildN'])
buildX = float(config['building']['buildX'])
buildY = float(config['building']['buildY'])
buildDx = float(config['building']['buildDx'])
buildDy = float(config['building']['buildDy'])
buildLx = float(config['building']['buildLx'])
buildLy = float(config['building']['buildLy'])

SUBTITLE = str(rlcBufferPerc) + '% BDP - Server: ' + serverType

test = os.listdir(HOMEPATH)

# Rewrite existing images
for item in test:
    if item.endswith(".png"):
        os.remove(os.path.join(HOMEPATH, item))

SIM_PREFIX = tcpTypeId + '-'+ serverType + '-' + str(rlcBufferPerc) + '-'

# ----------------------------------------------------------
# Mobility
# ----------------------------------------------------------
@info_n_time_decorator("Mobility")
def graphMobility():
    fig, ax = plt.subplots()
    file="mobilityPosition.txt"
    title="Mobility"

    mob = pd.read_csv(HOMEPATH + file, sep = "\t")
    mob.set_index('Time', inplace=True)
    ax1= mob.plot.scatter( x='x',y='y', ax=ax,title=title)
    gNbicon=plt.imread(get_sample_data(f'{mainprobe}/gNb.png'))
    gNbbox = OffsetImage(gNbicon, zoom = 0.25)
    for g in range(gNbNum):
        gNbPos=[gNbX,(gNbY+5+g*gNbD)]
        gNbab=AnnotationBbox(gNbbox,gNbPos, frameon = False)
        ax.add_artist(gNbab)
    if (enableBuildings):
        for b in range(buildN):
            row, col = divmod(b,gridWidth)
            rect=mpatches.Rectangle((buildX+(buildLx+buildDx)*col,buildY+(buildLy+buildDy)*row),buildLx,buildLy, alpha=0.5, facecolor="red")
            plt.gca().add_patch(rect)

    UEicon=plt.imread(get_sample_data(f'{mainprobe}/UE.png'))
    UEbox = OffsetImage(UEicon, zoom = 0.02)

    for ue in mob['UE'].unique():
        UEPos=mob[mob['UE']==ue][['x','y']].iloc[-1:].values[0]+2
        UEab=AnnotationBbox(UEbox,UEPos, frameon = False)
        ax.add_artist(UEab)

    plt.xlim([min(0, mob['x'].min()) , max(100,mob['x'].max()+10)])
    plt.ylim([min(0, mob['y'].min()) , max(100,mob['y'].max()+10)])
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Distance [m]")


    fig.savefig(HOMEPATH + SIM_PREFIX + title +'.png')
    plt.close()

    return True

# ----------------------------------------------------------
# SINR Ctrl
# ----------------------------------------------------------
@info_n_time_decorator("SINR Control")
def graphSinrCtrl():
    fig, ax = plt.subplots()
    file="DlCtrlSinr.txt"
    title="SINR Control"

    SINR = pd.read_csv(HOMEPATH+file, sep = "\t")
    SINR.set_index('Time', inplace=True)
    SINR = SINR[SINR['RNTI']!=0]
    
    SINR.groupby('RNTI')['SINR(dB)'].plot(title=title)
    #plt.ylim([min(15, SINR['SINR(dB)'].min()) , max(30,SINR['SINR(dB)'].max())])
    ax.set_ylabel("SINR(dB)")
    ax.set_xlabel("Time(s)")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + "SinrCtrl" +'.png')
    plt.close()

    return True


# ----------------------------------------------------------
# SINR Data
# ----------------------------------------------------------
@info_n_time_decorator("SINR Data")
def graphSinrData():
    fig, ax = plt.subplots()
    file ="DlDataSinr.txt"
    title = "SINR Data"

    sinr = pd.read_csv(HOMEPATH+file, sep = "\t")
    sinr = sinr[sinr['RNTI']!=0]
    sinr=sinr.groupby(['Time','RNTI'])['SINR(dB)'].mean().reset_index()

    sinr.index=pd.to_datetime(sinr['Time'],unit='s')
    sinr.rename(
        columns={ "SINR(dB)":"sinr"},
        inplace=True,
    )
    sinr=pd.DataFrame(sinr.groupby('RNTI').resample(str(resamplePeriod)+'ms').sinr.mean())
    sinr=sinr.reset_index(level=0)

    sinr['Time']=sinr.index
    sinr['Time']=sinr['Time'].astype(np.int64)/1e9

    sinr.set_index('Time', inplace=True)

    sinr.groupby('RNTI')['sinr'].plot()

    #plt.ylim([min(30, sinr['sinr'].min()) , max(60,sinr['sinr'].max())])
    ax.set_ylabel("SINR(dB)")
    ax.set_xlabel("Time(s)")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + "SinrData" + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# CQI
# ----------------------------------------------------------
@info_n_time_decorator("CQI")
def graphCQI():
    fig, ax = plt.subplots()
    file="RxPacketTrace.txt"
    title="CQI"

    CQI = pd.read_csv(HOMEPATH+file, sep = "\t")
    CQI.set_index('Time', inplace=True)
    CQI = CQI[CQI['rnti']!=0]
    CQI = CQI[CQI['direction']=='DL']
    #print(SINR)
    CQI.groupby('rnti')['CQI'].plot(title=title)
    plt.ylim([0, 16])
    ax.set_ylabel("CQI")
    ax.set_xlabel("Time(s)")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + title +'.png')
    plt.close()

    return True

# ----------------------------------------------------------
# TBLER
# ----------------------------------------------------------
@info_n_time_decorator("TBLER")
def graphTbler():
    fig, ax = plt.subplots()
    file="RxPacketTrace.txt"
    title="BLER"

    cqi = pd.read_csv(HOMEPATH+file, sep = "\t")
    #CQI.set_index('Time', inplace=True)
    cqi = cqi[cqi['rnti']!=0]
    cqi = cqi[cqi['direction']=='DL']

    cqi.index=pd.to_datetime(cqi['Time'],unit='s')

    bler=pd.DataFrame(cqi.groupby('rnti').resample(str(resamplePeriod)+'ms').TBler.mean())

    bler=bler.reset_index(level=0)

    bler['Time']=bler.index
    bler['Time']=bler['Time'].astype(np.int64)/1e9
    bler=bler.set_index('Time')

    for i in range(bler['rnti'].max()):
        plt.semilogy(bler.index, bler[bler['rnti']==i+1].TBler, label=str(i+1))

    plt.xlabel("Time(s)")
    plt.ylabel("BLER")
    # ax.set_ylim([abs(min([(1e-20) ,BLER.TBler.min()*0.9])) , 1])
    # plt.legend()
    plt.title(title)
    plt.grid(True, which="both", ls="-")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'Tbler' + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# PATH LOSS
# ----------------------------------------------------------
@info_n_time_decorator("Path Loss")
def graphPathLoss():
    fig, ax = plt.subplots()
    file="DlPathlossTrace.txt"
    title="Path Loss"

    ploos = pd.read_csv(HOMEPATH+file, sep = "\t")
    ploos.set_index('Time(sec)', inplace=True)
    ploos = ploos.loc[ploos['IMSI']!=0]
    ploos = ploos[ploos['pathLoss(dB)'] < 0]

    ploos.groupby(['IMSI'])['pathLoss(dB)'].plot(title=file)
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + "PathLoss" + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# Throughput TX
# ----------------------------------------------------------
@info_n_time_decorator("Throughput TX")
def graphThrTx():
    fig, ax = plt.subplots()
    file="NrDlPdcpTxStats.txt"
    title=tcpTypeId[3:] + " "
    title=title+"Throughput TX"

    TXSTAT = pd.read_csv(HOMEPATH+file, sep = "\t")

    tx=TXSTAT.groupby(['time(s)','rnti'])['packetSize'].sum().reset_index()
    tx.index=pd.to_datetime(tx['time(s)'],unit='s')

    thrtx=pd.DataFrame(tx.groupby('rnti').resample(str(resamplePeriod)+'ms').packetSize.sum())
    thrtx=thrtx.reset_index(level=0)

    thrtx['InsertedDate']=thrtx.index
    thrtx['deltaTime']=thrtx['InsertedDate'].astype(np.int64)/1e9
    thrtx['Time']=thrtx['deltaTime']
    thrtx['deltaTime']=thrtx.groupby('rnti').diff()['deltaTime']

    thrtx.loc[~thrtx['deltaTime'].notnull(),'deltaTime']=thrtx.loc[~thrtx['deltaTime'].notnull(),'InsertedDate'].astype(np.int64)/1e9
    thrtx['throughput']= thrtx['packetSize']*8 / thrtx['deltaTime']/1e6
    thrtx=thrtx.set_index('Time')
    thrtx.groupby(['rnti'])['throughput'].plot()
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("throughput(Mb/s)")
    ax.set_ylim([0 , thrtx['throughput'].max()*1.1])
    plt.suptitle(title)
    plt.title(SUBTITLE)

    fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrTx' + '.png')
    plt.close()

    return True


# ----------------------------------------------------------
# Throughput RX
# ----------------------------------------------------------
@info_n_time_decorator("Throughput RX")
def graphThrRx():
    fig, ax = plt.subplots()
    file="NrDlPdcpRxStats.txt"
    title=tcpTypeId[3:] + " "

    title=title + "Throughput RX"

    rxStat = pd.read_csv(HOMEPATH+file, sep = "\t")

    rx=rxStat.groupby(['time(s)','rnti'])['packetSize'].sum().reset_index()
    rx.index=pd.to_datetime(rx['time(s)'],unit='s')

    thrrx=pd.DataFrame(rx.groupby('rnti').resample(str(resamplePeriod)+'ms').packetSize.sum())
    thrrx=thrrx.reset_index(level=0)

    thrrx['InsertedDate']=thrrx.index
    thrrx['deltaTime']=thrrx['InsertedDate'].astype(np.int64)/1e9
    thrrx['Time']=thrrx['deltaTime']

    thrrx['deltaTime']=thrrx.groupby('rnti').diff()['deltaTime']

    thrrx.loc[~thrrx['deltaTime'].notnull(),'deltaTime']=thrrx.loc[~thrrx['deltaTime'].notnull(),'InsertedDate'].astype(np.int64)/1e9
    thrrx['throughput']= thrrx['packetSize']*8 / thrrx['deltaTime']/1e6
    thrrx=thrrx.set_index('Time')

    if flowType=='TCP':
        rlcStat= pd.read_csv(HOMEPATH+"RlcBufferStat_1.0.0.2_.txt", sep = "\t")
        rlcStat['direction']='UL'
        rlcStat.loc[rlcStat['PacketSize'] > 1500,'direction']='DL'
        rlc = rlcStat[rlcStat['direction'] =='DL']
        rlc.index=pd.to_datetime(rlc['Time'],unit='s')

        rlcdrop=pd.DataFrame(rlc.resample(str(resamplePeriod)+'ms').dropSize.sum())
        rlcdrop['Time']=rlcdrop.index.astype(np.int64)/1e9
        rlcdrop=rlcdrop.set_index('Time')
        rlcdrop['state']=0
        rlcdrop.loc[rlcdrop['dropSize'] > 0,'state']=1

        rlcbuffer=pd.DataFrame(rlc.resample(str(resamplePeriod)+'ms').txBufferSize.max())
        rlcbuffer['Time']=rlcbuffer.index.astype(np.int64)/1e9
        rlcbuffer=rlcbuffer.set_index('Time')
        rlcbuffer['txBufferSize']=rlcbuffer['txBufferSize']/rlcBuffer
        rlcdrop['state']=rlcdrop['state']*rlcbuffer['txBufferSize']
        rlcbuffer.loc[rlcdrop['state'] > 0,'txBufferSize']=0

    # ax2 = ax.twinx()
    ax1 = thrrx.groupby(['rnti'])['throughput'].plot( ax=ax)
    
    if flowType=='TCP':
        ax2 = rlcdrop['state'].plot.area( secondary_y=True, ax=ax, alpha=0.2, color="red")
        ax3 = rlcbuffer['txBufferSize'].plot.area( secondary_y=True, ax=ax,  alpha=0.2, color="green")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Throughput [Mb/s]")
    ax.set_ylim([0 , max([0,thrrx['throughput'].max()*1.1])])
    
    if flowType=='TCP':
        ax2.set_ylabel("RLC Buffer [%]", loc='bottom')
        ax2.set_ylim(0,4)

        ax2.set_yticks([0,0.5,1])
        ax2.set_yticklabels(['0','50','100' ])

        ax3.set_ylim(0,rlcbuffer['txBufferSize'].max()*4)

    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrRx' + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# RLC Buffers | If FlowType TCP??
# ----------------------------------------------------------

@info_n_time_decorator('RLC Buffers')
def graphRlcBuffers():

    PREFIX = "RlcBufferStat"
    SUFFIX = ".txt"
    buffers = []

    # Find all buffers
    for file in os.listdir(HOMEPATH):
        if PREFIX in file and SUFFIX in file:
            buffers.append(file)

    if len(buffers) <= 0:
        #print(red + "\tNo files found. Terminated." + clear)
        return False

    num_buffers = len(buffers)
    fig, ax = plt.subplots(num_buffers, 1, sharex='all', figsize=(7, 2.4*num_buffers))

    plt.suptitle("RLC Buffers of UE(s) and Remote Host")

    for buffer, index in zip(buffers, range(0, len(buffers))):
        
        # Retrieve IP
        IP = buffer.replace(PREFIX + "_", "").replace("_" + SUFFIX, "")

        # Read data
        data = pd.read_csv(HOMEPATH + buffer, sep="\t")
        x = data['Time']
        y = data['NumOfBuffers']

        ax[index].plot(x, y)
        ax[index].fill_between(x, y, color='#539ecd')
        ax[index].tick_params('x', labelbottom=False)
        ax[index].set_ylabel("Num. of packets")
        ax[index].set_title("IP: " + IP)
    
    ax[index].tick_params('x', labelbottom=True)
    ax[index].set_xlabel("Time [s]")
    fig.savefig(HOMEPATH + SIM_PREFIX + "RlcBuffers.png")
    plt.close()

    return True

# ----------------------------------------------------------
# Delay | Only UDP
# ----------------------------------------------------------
@info_n_time_decorator("UDP Delay")
def graphUdpDelay():
    ###############
    ## Delay
    ###############
    fig, ax = plt.subplots()
    file="NrDlPdcpRxStats.txt"
    title=tcpTypeId + " "
    title=title+"Delay RX"

    RXSTAT = pd.read_csv(HOMEPATH+file, sep = "\t")
    rx=RXSTAT.groupby(['time(s)','rnti'])['delay(s)'].mean().reset_index()
    rx.rename(
        columns={ "delay(s)":"delay"},
        inplace=True,
    )
    rx.index=pd.to_datetime(rx['time(s)'],unit='s')

    ret=pd.DataFrame(rx.groupby('rnti').resample(str(resamplePeriod)+'ms').delay.mean())
    ret=ret.reset_index(level=0)

    ret['InsertedDate']=ret.index
    ret['Time']=ret['InsertedDate'].astype(np.int64)/1e9

    ret=ret.set_index('Time')
    ret.groupby(['rnti'])['delay'].plot(title=title)
    ax.set_ylabel("delay(s)")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'Delay1' + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# RTT | Only TCP
# ----------------------------------------------------------
@info_n_time_decorator("RTT")
def graphTcpDelay():
    ###############
    ## Delay 2
    ###############
    fig, ax = plt.subplots()
    file="tcp-delay.txt"
    title=tcpTypeId[3:] + " "

    title=title+"RTT"

    RXSTAT = pd.read_csv(HOMEPATH+file, sep = "\t")

    rx=RXSTAT.groupby(['Time'])['rtt'].mean().reset_index()

    rx.index=pd.to_datetime(rx['Time'],unit='s')

    rx = rx[(rx['Time']>=AppStartTime) & (rx['Time']<=simTime - AppStartTime)]

    ret=pd.DataFrame(rx.resample(str(resamplePeriod)+'ms').rtt.mean())
    ret['InsertedDate']=ret.index
    ret['Time']=ret['InsertedDate'].astype(np.int64)/1e9

    ret=ret.set_index('Time')
    ret['rtt']=ret['rtt']*1000
    ret['rtt'].plot()
    ax.set_ylabel("RTT [ms]")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'RTT' + '.png')
    plt.close()

    return True

# ----------------------------------------------------------
# CWND & Inflight bytes | Only TCP
# ----------------------------------------------------------
@info_n_time_decorator("CWND and Inflight Bytes")
def graphCWNDnInflightBytes():
    ###############
    # Congestion Window
    ###############
    for u in range(UENum):
        # print(u)
        fig, ax = plt.subplots()
        file="tcp-cwnd-"+serverID+"-"+str(u)+".txt"
        title=tcpTypeId + " "
        title=title+"Congestion Window"
        CWND = pd.read_csv(HOMEPATH+file, sep = "\t")

        CWND.set_index('Time', inplace=True)
        if (len(CWND.index)>0):
            CWND['newval'].plot(title=title)
            plt.suptitle(title)
            plt.title(SUBTITLE)

            fig.savefig(HOMEPATH + SIM_PREFIX + "Cwnd-UE" + str(u) + '.png')

    plt.close()

    ###############
    # inflight Bytes
    ###############
    for u in range(UENum):
        fig, ax = plt.subplots()

        file="tcp-inflight-"+serverID+"-"+str(u)+".txt"
        title=tcpTypeId + " "
            
        title=title + "inflight Bytes"
        inflight = pd.read_csv(HOMEPATH+file, sep = "\t")
        # INF.loc[INF['oldval']>0]['oldval']= INF.loc[INF['oldval']>0]['oldval']/SegmentSize
        # INF.loc[INF['newval']>0]['newval']= INF.loc[INF['newval']>0]['newval']/SegmentSize
    
        inflight['oldval']= inflight['oldval'] / SegmentSize
        inflight['newval']= inflight['newval'] / SegmentSize
    
        inflight.set_index('Time', inplace=True)
        if (len(inflight.index)>0):
            inflight['newval'].plot(title=title)
            plt.suptitle(title)
            plt.title(SUBTITLE)

            fig.savefig(HOMEPATH + SIM_PREFIX + "InflightBytes-UE" + str(u) + '.png')

    plt.close()

    return True

# ----------------------------------------------------------
# RTT 2 | Only TCP
# ----------------------------------------------------------
@info_n_time_decorator("RTT 2")
def get_RTT(pcap_filename):

    # Read the pcap file
    packets = rdpcap(pcap_filename)

    # Dictionary to store packet timestamps, rtt's and ack's received
    packet_timestamps = {}
    rtt_dict = {}
    ack_received = []

    # Iterate over each packet
    for packet in packets:
        if packet.haslayer(TCP):

            seq_num = packet[TCP].seq
            ack_num = packet[TCP].ack
            timestamp = packet.time
            TCP_payload = len(packet[TCP].payload)

            # Cases to skip
            case_1 = (seq_num == 0) # SYN
            case_2 = (seq_num == 1 and ack_num == 1 and TCP_payload == 0) # SYN, ACK
            case_3 = (ack_num in ack_received) # DUP ACK
            skip_packets = (case_1 or case_2 or case_3)

            if skip_packets:
                continue

            # Add timestamp of sending packet
            if seq_num not in packet_timestamps:
                packet_timestamps[seq_num] = timestamp
                rtt_dict[seq_num] = 0

            # Get Sequence Number from ACK
            recovered_seq_num = ack_num-1448
            
            # Check if a packet is ACK and the SEQ exists
            if (seq_num == 1) and  (recovered_seq_num in packet_timestamps):
                rtt = timestamp - packet_timestamps[recovered_seq_num]
                rtt_dict[recovered_seq_num] = rtt*1000
                ack_received.append(ack_num)
    
    new_rtt_dict = {int((key-1)/1448 + 1) : value for key, value in rtt_dict.items()}

    n_packet_array = list(new_rtt_dict.keys())
    rtt_array = list(new_rtt_dict.values())
    
    fig, ax = plt.subplots()
    plt.plot(n_packet_array, rtt_array)
    plt.xlabel('Packet Number')
    plt.ylabel('RTT [ms]')
    plt.title('RTT 2')
    plt.grid(True)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'RTT_2.png')

    return True

#   | * ---- * ---- * ---- * |
#   |  Call graph functions  |
#   | * ---- * ---- * ---- * |

# For all flows
graphMobility()
graphSinrCtrl()
graphSinrData()
graphCQI()
graphTbler()
graphPathLoss()
graphThrTx()
graphThrRx()

# For TCP only
if flowType == "TCP":
    graphRlcBuffers()
    graphTcpDelay()
    graphCWNDnInflightBytes()
    get_RTT(HOMEPATH + "mypcapfile-5-1.pcap")

# For UDP only
if flowType == "UDP":
    graphUdpDelay()