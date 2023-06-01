import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import AnnotationBbox,OffsetImage
import matplotlib.patches as mpatches
import math
import pandas as pd
from datetime import datetime
import time
import sys
import configparser
import os
from os import listdir
import functools
from scapy.all import *

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
#   pass
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

tic=time.time()

myhome="/home/jsandova/ns-3-dev"
if (len(sys.argv)>2):
    myhome=sys.argv[1]+"/"
    mainprobe=sys.argv[2]
else:
    print("Not enough arguments.")
    exit()

config = configparser.ConfigParser()
config.read(myhome+'graph.ini')

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

subtitle = str(rlcBufferPerc) + '% BDP - Server: ' + serverType

test = os.listdir(myhome)

for item in test:
    if item.endswith(".png"):
        os.remove(os.path.join(myhome, item))


prefix = tcpTypeId + '-'+ serverType + '-' + str(rlcBufferPerc) + '-'

# ----------------------------------------------------------
# Mobility
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="mobilityPosition.txt"
title="Mobility "
print(CYAN + title + CLEAR, end="...", flush=True)

mob = pd.read_csv(myhome+file, sep = "\t")
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


fig.savefig(myhome+prefix +file+'.png')
plt.close()

toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# SINR Ctrl
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="DlCtrlSinr.txt"
title="SINR Control"
print(CYAN + title + CLEAR, end="...", flush=True)

SINR = pd.read_csv(myhome+file, sep = "\t")
SINR.set_index('Time', inplace=True)
SINR = SINR[SINR['RNTI']!=0]
#print(SINR)
SINR.groupby('RNTI')['SINR(dB)'].plot(legend=True, title=title)
plt.ylim([min(15, SINR['SINR(dB)'].min()) , max(30,SINR['SINR(dB)'].max())])
ax.set_ylabel("SINR(dB)")
ax.set_xlabel("Time(s)")
plt.suptitle(title)
plt.title(subtitle)
fig.savefig(myhome+file+'.png')
plt.close()

toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc


# ----------------------------------------------------------
# SINR Data
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="DlDataSinr.txt"
title="SINR Data"
print(CYAN + title + CLEAR, end="...", flush=True)

SINR = pd.read_csv(myhome+file, sep = "\t")
SINR = SINR[SINR['RNTI']!=0]
SINR=SINR.groupby(['Time','RNTI'])['SINR(dB)'].mean().reset_index()

SINR.index=pd.to_datetime(SINR['Time'],unit='s')
SINR.rename(
    columns={ "SINR(dB)":"sinr"},
    inplace=True,
)
SINR=pd.DataFrame(SINR.groupby('RNTI').resample(str(resamplePeriod)+'ms').sinr.mean())
SINR=SINR.reset_index(level=0)

SINR['Time']=SINR.index
SINR['Time']=SINR['Time'].astype(np.int64)/1e9

SINR.set_index('Time', inplace=True)

SINR.groupby('RNTI')['sinr'].plot()

plt.ylim([min(30, SINR['sinr'].min()) , max(60,SINR['sinr'].max())])
ax.set_ylabel("SINR(dB)")
ax.set_xlabel("Time(s)")
plt.suptitle(title)
plt.title(subtitle)
fig.savefig(myhome+file+'.png')
plt.close()
toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc


# ----------------------------------------------------------
# CQI
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="RxPacketTrace.txt"
title="CQI"
print(CYAN + title + CLEAR, end="...", flush=True)

CQI = pd.read_csv(myhome+file, sep = "\t")
CQI.set_index('Time', inplace=True)
CQI = CQI[CQI['rnti']!=0]
CQI = CQI[CQI['direction']=='DL']
#print(SINR)
CQI.groupby('rnti')['CQI'].plot(legend=True, title=title)
plt.ylim([0, 16])
ax.set_ylabel("CQI")
ax.set_xlabel("Time(s)")
plt.suptitle(title)
plt.title(subtitle)
fig.savefig(myhome+file+'.png')
plt.close()

toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# TBLER
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="RxPacketTrace.txt"
title="BLER"
print(CYAN + title + CLEAR, end="...", flush=True)

CQI = pd.read_csv(myhome+file, sep = "\t")
#CQI.set_index('Time', inplace=True)
CQI = CQI[CQI['rnti']!=0]
CQI = CQI[CQI['direction']=='DL']

CQI.index=pd.to_datetime(CQI['Time'],unit='s')

BLER=pd.DataFrame(CQI.groupby('rnti').resample(str(resamplePeriod)+'ms').TBler.mean())

BLER=BLER.reset_index(level=0)

BLER['Time']=BLER.index
BLER['Time']=BLER['Time'].astype(np.int64)/1e9
BLER=BLER.set_index('Time')

for i in range(BLER['rnti'].max()):
    plt.semilogy(BLER.index, BLER[BLER['rnti']==i+1].TBler, label=str(i+1))

plt.xlabel("Time(s)")
plt.ylabel("BLER")
# ax.set_ylim([abs(min([(1e-20) ,BLER.TBler.min()*0.9])) , 1])
# plt.legend()
plt.title(title)
plt.grid(True, which="both", ls="-")
plt.suptitle(title)
plt.title(subtitle)
fig.savefig(myhome+file+'-tbler'+'.png')
plt.close()

toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# PATH LOSS
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="DlPathlossTrace.txt"
title="Path Loss"
print(CYAN + title + CLEAR, end="...", flush=True)

PLOOS = pd.read_csv(myhome+file, sep = "\t")
PLOOS.set_index('Time(sec)', inplace=True)
PLOOS = PLOOS.loc[PLOOS['IMSI']!=0]
PLOOS = PLOOS[PLOOS['pathLoss(dB)'] < 0]

PLOOS.groupby(['IMSI'])['pathLoss(dB)'].plot(legend=True,title=file)
plt.suptitle(title)
plt.title(subtitle)
fig.savefig(myhome+file+'.png')
plt.close()
toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# Throughput TX
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="NrDlPdcpTxStats.txt"
title=tcpTypeId[3:] + " "
title=title+"Throughput TX"
print(CYAN + title + CLEAR, end="...", flush=True)

TXSTAT = pd.read_csv(myhome+file, sep = "\t")

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
plt.title(subtitle)

fig.savefig(myhome + prefix + 'ThrTx' + '.png')

toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc


# ----------------------------------------------------------
# Throughput RX
# ----------------------------------------------------------
fig, ax = plt.subplots()
file="NrDlPdcpRxStats.txt"
title=tcpTypeId[3:] + " "

title=title + "Throughput RX"
print(CYAN + title + CLEAR, end="...", flush=True)

RXSTAT = pd.read_csv(myhome+file, sep = "\t")

rx=RXSTAT.groupby(['time(s)','rnti'])['packetSize'].sum().reset_index()
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
    RLCSTAT= pd.read_csv(myhome+"RlcBufferStat_1.0.0.2_.txt", sep = "\t")
    RLCSTAT['direction']='UL'
    RLCSTAT.loc[RLCSTAT['PacketSize'] > 1500,'direction']='DL'
    rlc = RLCSTAT[RLCSTAT['direction'] =='DL']
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
plt.title(subtitle)
fig.savefig(myhome + prefix + 'ThrRx' + '.png')
plt.close()
toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# RLC Buffers | If FlowType TCP??
# ----------------------------------------------------------

@info_n_time_decorator('RLC Buffers')
def graphRlcBuffers():

    PREFIX = "RlcBufferStat"
    SUFFIX = ".txt"
    buffers = []

    # Find all buffers
    for file in os.listdir(myhome):
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
        data = pd.read_csv(myhome + buffer, sep="\t")
        x = data['Time']
        y = data['NumOfBuffers']

        ax[index].plot(x, y)
        ax[index].fill_between(x, y, color='#539ecd')
        ax[index].tick_params('x', labelbottom=False)
        ax[index].set_ylabel("Num. of packets")
        ax[index].set_title("IP: " + IP)
    
    ax[index].tick_params('x', labelbottom=True)
    ax[index].set_xlabel("Time [s]")
    fig.savefig(myhome + prefix + "RlcBuffers.png")
    plt.close()

    return True

graphRlcBuffers()

# ----------------------------------------------------------
# Delay | Only UDP
# ----------------------------------------------------------
if flowType=='UDP':
    ###############
    ## Delay
    ###############
    fig, ax = plt.subplots()
    file="NrDlPdcpRxStats.txt"
    title=tcpTypeId + " "
    title=title+"Delay RX"
    print(CYAN + title + CLEAR, end="...", flush=True)

    RXSTAT = pd.read_csv(myhome+file, sep = "\t")
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
    ret.groupby(['rnti'])['delay'].plot(legend=True,title=title)
    ax.set_ylabel("delay(s)")
    plt.suptitle(title)
    plt.title(subtitle)
    fig.savefig(myhome + prefix + 'Delay1' + '.png')
    plt.close()

    toc=time.time()
    print(f"\tProcessed in: %.2f" %(toc-tic))
    tic=toc
else:
    ###############
    ## Delay 2
    ###############
    fig, ax = plt.subplots()
    file="tcp-delay.txt"
    title=tcpTypeId[3:] + " "

    title=title+"RTT"
    print(CYAN + title + CLEAR, end="...", flush=True)

    RXSTAT = pd.read_csv(myhome+file, sep = "\t")

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
    plt.title(subtitle)
    fig.savefig(myhome + prefix + 'RTT' + '.png')
    plt.close()



# ----------------------------------------------------------
# CWND & Inflight bytes | Only TCP
# ----------------------------------------------------------
if flowType=="TCP":
    ###############
    # Congestion Window
    ###############
    for u in range(UENum):
        # print(u)
        fig, ax = plt.subplots()
        file="tcp-cwnd-"+serverID+"-"+str(u)+".txt"
        title=tcpTypeId + " "
        title=title+"Congestion Window"
        CWND = pd.read_csv(myhome+file, sep = "\t")

        CWND.set_index('Time', inplace=True)
        if (len(CWND.index)>0):
            CWND['newval'].plot(legend=True, title=title)
            plt.suptitle(title)
            plt.title(subtitle)

            fig.savefig(myhome+file+str(u)+'.png')

    plt.close()

    ###############
    # inflight Bytes
    ###############
    for u in range(UENum):
        fig, ax = plt.subplots()

        file="tcp-inflight-"+serverID+"-"+str(u)+".txt"
        title=tcpTypeId + " "
            
        title=title + "inflight Bytes"
        INF = pd.read_csv(myhome+file, sep = "\t")
        # INF.loc[INF['oldval']>0]['oldval']= INF.loc[INF['oldval']>0]['oldval']/SegmentSize
        # INF.loc[INF['newval']>0]['newval']= INF.loc[INF['newval']>0]['newval']/SegmentSize
    
        INF['oldval']= INF['oldval']/SegmentSize
        INF['newval']= INF['newval']/SegmentSize
    
        INF.set_index('Time', inplace=True)
        if (len(INF.index)>0):
            INF['newval'].plot(legend=True, title=title)
            plt.suptitle(title)
            plt.title(subtitle)

            fig.savefig(myhome+file+str(u)+'.png')

    plt.close()

#plt.show()
toc=time.time()
print(f"\tProcessed in: %.2f" %(toc-tic))
tic=toc

# ----------------------------------------------------------
# RTT 2
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
    fig.savefig(myhome + 'RTT_2.png')

    return True

if flowType=="TCP":
    get_RTT(myhome + "mypcapfile-5-1.pcap")

exit()


###############
## SINR Data
###############
fig, ax = plt.subplots()
file="DlDataSinr.txt"
title="SINR Data "+file

SINR = pd.read_csv(myhome+file, sep = "\t")
SINR.set_index('Time', inplace=True)
SINR = SINR[SINR['RNTI']!=0]
#print(SINR)

SINR.groupby('RNTI')['SINR(dB)'].plot(legend=True, title=title)
ax.set_ylabel("SINR(dB)")
ax.set_xlabel("Time(s)")
fig.savefig(myhome+file+'.png')
plt.close()


fig, ax = plt.subplots()
u=0

file="tcp-inflight-"+serverID+"-"+str(u)+".txt"
title=tcpTypeId + " "
    
title=title + "inflight Bytes " + file
INF = pd.read_csv(myhome+file, sep = "\t")
INF.loc[INF['oldval']>0,'oldval']=INF.loc[INF['oldval']>0,'oldval']/SegmentSize
INF.loc[INF['newval']>0,'newval']=INF.loc[INF['newval']>0,'newval']/SegmentSize

INF.set_index('Time', inplace=True)
INF['newval'].plot(legend=True, title=title)
fig.savefig(myhome+file+str(u)+'.png')
















serverID = config['general']['serverID']
UENum = int(config['general']['UENum'])



a=pd.DataFrame(thrtx['packetSize'])
a.rename(columns={"packetSize": "bytesTx"}, inplace=True)
a['Time']=a.index
b=pd.DataFrame(thrrx['packetSize'])
b.rename(columns={"packetSize": "bytesRx"}, inplace=True)
b['Time']=b.index
pd.concat([a,b], axis=1)