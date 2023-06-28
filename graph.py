import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import AnnotationBbox,OffsetImage
import matplotlib.patches as mpatches
import pandas as pd
import sys
import configparser
import os
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import rdpcap, TCP

from OtherScripts.simutil import *

if (len(sys.argv)>2):
    HOMEPATH=sys.argv[1]+"/"    # Where to save the images
    MAINPROBE=sys.argv[2]       # Where the images are located
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
addNoise = config['general']['addNoise']

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

# Simulation Prefix
SIM_PREFIX = tcpTypeId + '-'+ serverType + '-' + str(rlcBufferPerc) + '-'

# Other stuff
RESAMPLED_DF = pd.timedelta_range("0s", f"{simTime}s", freq=f"{resamplePeriod}ms").to_frame(name="Time")

if tcpTypeId=="TcpNewReno":
    points=np.array([2, 15, 21, 35, 39])
    parts=np.array([[ 1, 20, "1-20"],
                    [20, 40, "20-40"],
                    [ 0, 60,"0-60"],
                ])
elif tcpTypeId=="TcpCubic":
    tcpTypeId = "TcpCUBIC"
    points=np.array([1, 2, 6, 20.5])
    parts=np.array([[ 1, 22, "1-22"],
                [ 0, 60,"0-60"],
                ])
else:
    if tcpTypeId == "TcpBbr":
        tcpTypeId = "TcpBBR"

    points=np.array([2, 15])
    parts=np.array([[ 1, 20, "1-20"],
                [ 0, 60,"0-60"],
                ])

# Default values for matplotlib
plt.rc('lines', linewidth=2)

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
    gNbicon=plt.imread(get_sample_data(f'{MAINPROBE}/gNb.png'))
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

    UEicon=plt.imread(get_sample_data(f'{MAINPROBE}/UE.png'))
    UEbox = OffsetImage(UEicon, zoom = 0.02)

    for ue in mob['UE'].unique():
        UEPos=mob[mob['UE']==ue][['x','y']].iloc[-1:].values[0]+2
        UEab=AnnotationBbox(UEbox,UEPos, frameon = False)
        ax.add_artist(UEab)

    plt.xlim([min(0, mob['x'].min()) , max(100,mob['x'].max()+10)])
    plt.ylim([min(0, mob['y'].min()) , max(100,mob['y'].max()+10)])
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Distance [m]")


    fig.savefig(HOMEPATH + SIM_PREFIX + title +'.png', dpi=300)
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
    fig.savefig(HOMEPATH + SIM_PREFIX + "SinrCtrl" +'.png', dpi=300)
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
    fig.savefig(HOMEPATH + SIM_PREFIX + "SinrData" + '.png', dpi=300)
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
    fig.savefig(HOMEPATH + SIM_PREFIX + title +'.png', dpi=300)
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
        plt.semilogy(bler.index, bler[bler['rnti']==i+1].TBler, label='BLER')

    # Trazar línea horizontal en y = 0.1
    plt.axhline(y=0.1, color='green', linestyle='--', label='BLER = 0.1')
    # Trazar línea horizontal en y = 0.5
    plt.axhline(y=0.5, color='red', linestyle='--', label='BLER = 0.5')
    
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xlabel("Time(s)")
    plt.ylabel("BLER")
    plt.ylim(bottom=None, top=10**0)
    # ax.set_ylim([abs(min([(1e-20) ,BLER.TBler.min()*0.9])) , 1])
    # plt.legend()
    plt.title(title)
    plt.grid(True, which="both", ls="-")
    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'Tbler' + '.png', dpi=300, bbox_inches='tight')
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
    fig.savefig(HOMEPATH + SIM_PREFIX + "PathLoss" + '.png', dpi=300)
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
    ax.set_ylabel("Throughput [Mb/s]")
    ax.set_ylim([0 , thrtx['throughput'].max()*1.1])
    plt.suptitle(title)
    plt.title(SUBTITLE)

    fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrTx' + '.png', dpi=300)
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
    
    ax1 = thrrx.groupby(['rnti'])['throughput'].plot( ax=ax)
    
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Throughput [Mb/s]")
    ax.set_ylim([0 , max([0,thrrx['throughput'].max()*1.1])])

    plt.suptitle(title)
    plt.title(SUBTITLE)
    fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrRx' + '.png', dpi=300)
    plt.close()

    return True

# ----------------------------------------------------------
# Throughput RX vs RLC Buffer | TCP Only
# ----------------------------------------------------------
# It currently isnt working, keyerror on line mytext="("+...
@info_n_time_decorator("THR Rx vs RLC_B")
def graphThrRxRlcBuffer():
    fig, ax = plt.subplots()
    file="NrDlPdcpRxStats.txt"
    title=tcpTypeId[3:] + " "

    title=title + "Throughput RX vs RLC Buffer"

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
    
    for p in range(parts.shape[0] ):
    
        [x, y, z] = parts[p,:]
        fig, ax = plt.subplots()

        ax1 = thrrx.loc[x:y].groupby(['rnti'])['throughput'].plot( ax=ax)
        if p<parts.shape[0]-1:
            for d in range(points.shape[0]):
                if (points[d]>=int(x)) & (points[d] <= int(y)):
                    mytext="("+str(points[d])+","+str(round(thrrx.loc[points[d]]['throughput'],2)) +")"
                    ax.annotate( mytext, (points[d] , thrrx.loc[points[d]]['throughput']))
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
        fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrRx-' + z + '.png', dpi=300)
        plt.close()

    return True

# ----------------------------------------------------------
# Throughput RX vs PER | If TCP
# ----------------------------------------------------------
@info_n_time_decorator("THR Rx vs PER")
def graphThrRxPer():
    
    title=tcpTypeId[3:] + " Throughput vs PER"
    file="tcp-per.txt"
    if os.path.exists(HOMEPATH+file):
        tx_ = pd.read_csv(HOMEPATH+file, sep = "\t")
    else:
        file =  file + ".gz"
        tx_ = pd.read_csv(HOMEPATH+file, compression='gzip', sep = "\t")
    tx_.index=pd.to_datetime(tx_['Time'],unit='s')
    tx_thr=pd.DataFrame(tx_.resample(str(resamplePeriod)+'ms').BytesTx.sum())
    tx_drp=pd.DataFrame(tx_.resample(str(resamplePeriod)+'ms').BytesDroped.sum())
    tx_drp['PacketsTx']=pd.DataFrame(tx_.resample(str(resamplePeriod)+'ms').PacketsTx.sum())
    tx_drp['PacketsDroped']=pd.DataFrame(tx_.resample(str(resamplePeriod)+'ms').PacketsDroped.sum())

    tx_thr=tx_thr.reset_index(level=0)
    tx_thr['Throughput']= tx_thr['BytesTx']*8 / 0.1/1e6
    tx_thr['Time']=tx_thr['Time'].astype(np.int64)/1e9
    tx_thr=tx_thr.set_index('Time')

    tx_drp=tx_drp.reset_index(level=0)
    # tx_drp['Throughput']= tx_drp['BytesTx']*8 / 0.1/1e6
    tx_drp['PER']= tx_drp['PacketsDroped']/tx_drp['PacketsTx']
    tx_drp['Time']=tx_drp['Time'].astype(np.int64)/1e9
    tx_drp=tx_drp.set_index('Time')

    for p in range(parts.shape[0] ):
        
        [x, y, z] = parts[p,:]
        fig, ax = plt.subplots()
        
        if p<parts.shape[0]-1:
            # plt.plot(tx_thr.loc[x:y].index, tx_thr['Throughput'].loc[x:y], '-o', markevery=tx_thr.loc[x:y].index.get_indexer(points, method='nearest'))
            ax1 = tx_thr['Throughput'].loc[x:y].plot(ax=ax, markevery=tx_thr.loc[x:y].index.get_indexer(points, method='nearest'))
            for d in range(points.shape[0]):
                if (points[d]>=int(x)) & (points[d] <= int(y)):
                    mytext="("+str(points[d])+","+str(round(tx_thr.loc[points[d]]['Throughput'],2)) +")"
                    ax.annotate( mytext, (points[d] , tx_thr.loc[points[d]]['Throughput']))
        else:
            ax1 = tx_thr['Throughput'].loc[x:y].plot(ax=ax)
        # ax2 = tx_drp['Throughput'].plot.area(  ax=ax,  alpha=0.2, color="red")
        ax2 = tx_drp['PER'].loc[x:y].plot.area(  secondary_y=True, ax=ax,  alpha=0.2, color="red")

        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Throughput [Mb/s]")
        ax.set_ylim([0 , max([thr_limit,tx_thr['Throughput'].loc[x:y].max()*1.1])])

        ax2.set_ylabel("PER [%]", loc='bottom')
        ax2.set_ylim(0,4)

        ax2.set_yticks([0,0.5,1])
        ax2.set_yticklabels(['0','50','100' ])

        plt.suptitle(title)
        plt.title(SUBTITLE)
        fig.savefig(HOMEPATH + SIM_PREFIX + 'ThrDrp' +'-'+ z+ '.png', dpi=300)
        plt.close()
    
    return True

# ----------------------------------------------------------
# RLC Buffers | If FlowType TCP
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
    
    if num_buffers > 1:   # TCP
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
        fig.savefig(HOMEPATH + SIM_PREFIX + "RlcBuffers.png", dpi=300)
        plt.close()
    
    else:       # UDP
        plt.suptitle("RLC Buffers of UE(s) and Remote Host")
        plt.title(SUBTITLE)
        buffer = buffers.pop()
        IP = buffer.replace(PREFIX + "_", "").replace("_" + SUFFIX, "")
        data = pd.read_csv(HOMEPATH + buffer, sep="\t")
        x = data['Time']
        y = data['NumOfBuffers']
        plt.plot(x, y)
        plt.fill_between(x, y, color='#539ecd')
        plt.ylabel("Num. of packets")
        plt.xlabel("IP: " + IP)
        plt.savefig(HOMEPATH + SIM_PREFIX + "RlcBuffers.png", dpi=300)
        plt.close()

    return True

# ----------------------------------------------------------
# Delay | Only UDP | Uses NrDlPdcpRxStats.txt
# ----------------------------------------------------------
@info_n_time_decorator("PDCP Delay")
def graphPdcpDelay():
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
    fig.savefig(HOMEPATH + SIM_PREFIX + 'PdcpDelay' + '.png', dpi=300)
    plt.close()

    return True

# ----------------------------------------------------------
# Delay | Only UDP | Uses delay by UDPServerHelper
# ----------------------------------------------------------
@info_n_time_decorator("UDP Delay")
def graphUdpDelay():
    
    # We assume that there is only 1 UE
    filepath = HOMEPATH + "UdpRecv_Node1.txt"
    title = "Application Packet Delay"

    udpstats = pd.read_csv(filepath, sep="\t")

    time = udpstats["Time (s)"]
    delay = udpstats["Delay"]

    plt.plot(time, delay)
    plt.suptitle(title)
    plt.title(SUBTITLE)
    plt.ylabel("Delay [s]")
    plt.xlabel("Time [s]")
    plt.savefig(HOMEPATH + SIM_PREFIX + "AppDelay" + ".png", dpi=300)
    plt.close()

    return True

# ----------------------------------------------------------
# Retransmission | Both
# ----------------------------------------------------------
@info_n_time_decorator("RTX", True)
def graphRetransmissions():
    
    filepath = HOMEPATH + "RxPacketTrace.txt"
    df = pd.read_csv(filepath, sep="\t")

    rtxs = df[["Time", "rv", "corrupt"]].copy()
    rtxs["Time"] = pd.to_timedelta(rtxs["Time"], unit="s")
    rtxs.index += 5
    rtxs.loc[0] = [pd.Timedelta(0), 0, 0]
    rtxs.loc[1] = [pd.Timedelta(0), 1, 0]
    rtxs.loc[2] = [pd.Timedelta(0), 2, 0]
    rtxs.loc[3] = [pd.Timedelta(0), 3, 0]
    rtxs.loc[4] = [pd.Timedelta(0), 3, 1]
    rtxs = rtxs.sort_index()

    # Successful retransmissions
    succ_rtx = rtxs[rtxs["corrupt"] == 0]
    # Unsuccessful retransmissions
    fail_rtx = rtxs[(rtxs["rv"] == 3) & (rtxs["corrupt"] == 1)]

    succ_zero = succ_rtx[succ_rtx["rv"] == 0].copy().resample(f"{resamplePeriod}ms", on="Time").size().to_frame(name="Zero").copy()
    succ_zero.iloc[0] -= 1
    succ_once = succ_rtx[succ_rtx["rv"] == 1].copy().resample(f"{resamplePeriod}ms", on="Time").size().to_frame(name="One").copy()
    succ_once.iloc[0] -= 1
    succ_twice = succ_rtx[succ_rtx["rv"] == 2].copy().resample(f"{resamplePeriod}ms", on="Time").size().to_frame(name="Two").copy()
    succ_twice.iloc[0] -= 1
    succ_three = succ_rtx[succ_rtx["rv"] == 2].copy().resample(f"{resamplePeriod}ms", on="Time").size().to_frame(name="Three").copy()
    succ_three.iloc[0] -= 1
    failure = fail_rtx.resample(f"{resamplePeriod}ms", on="Time").size().to_frame(name="Fail").copy()
    failure.iloc[0] -= 1

    data = RESAMPLED_DF.join([succ_zero, succ_once, succ_twice, succ_three, failure]).drop("Time", axis=1).fillna(0)
    data["Total"] = data.sum(axis=1)
    data["S Total"] = data[["Zero", "One", "Two", "Three"]].sum(axis=1)

    data[["Zero", "One", "Two", "Three"]] = 100 * data[["Zero", "One", "Two", "Three"]].div(data["S Total"], axis=0).fillna(0)
    data[["S Total", "Fail"]] = 100 * data[["S Total", "Fail"]].div(data["Total"], axis=0).fillna(0)

    f, (ax_succ, ax_both) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
    plt.subplots_adjust(hspace=0.5)
    f.suptitle("Retransmissions in MAC Layer")
    succ_colors = ["#019875", "#72CC50", "#BFD834", "#00AEAD"]
    ax_succ.stackplot(data.index.total_seconds(), data["Zero"], data["One"], data["Two"], data["Three"], colors=succ_colors)
    ax_succ.legend(["0 RTX", "1 RTX", "2 RTX", "3 RTX"], loc="lower right")
    ax_succ.set_title("Number of RTX needed for a successful block reception")
    ax_succ.set_xlabel("Time [s]")
    ax_succ.set_ylabel("Percentage [%]")

    both_colors = ["#019875", "#BE0000"]
    ax_both.stackplot(data.index.total_seconds(), data["S Total"], data["Fail"], colors=both_colors)
    ax_both.legend(["Successful", "Failed"], loc="lower right")
    ax_both.set_title("Proportion of successful and failed retransmissions")
    ax_both.set_xlabel("Time [s]")
    ax_both.set_ylabel("Percentage [%]")
    ax_both.set_yticks((0, 50, 100))
    ax_both.yaxis.grid(True)
    f.savefig(HOMEPATH + SIM_PREFIX + "Rtx" + ".png", dpi=300)
    plt.close()
    return True

# ----------------------------------------------------------
# RTT | Only TCP
# ----------------------------------------------------------
ret = 0
@info_n_time_decorator("RTT")
def graphTcpDelay():
    ###############
    ## Delay 2
    ###############
    fig, ax = plt.subplots()
    title=tcpTypeId[3:] + " RTT"

    file="tcp-delay.txt"
    if os.path.exists(HOMEPATH+file):
        RXSTAT = pd.read_csv(HOMEPATH+file, sep = "\t")
    else:
        file =  file + ".gz"
        RXSTAT = pd.read_csv(HOMEPATH+file, compression='gzip', sep = "\t")

    rx=RXSTAT.groupby(['Time'])['rtt'].mean().reset_index()

    rx.index=pd.to_datetime(rx['Time'],unit='s')

    rx = rx[(rx['Time']>=AppStartTime) & (rx['Time']<=simTime - AppStartTime)]

    global ret
    ret=pd.DataFrame(rx.resample(str(resamplePeriod)+'ms').rtt.mean())
    ret['InsertedDate']=ret.index
    ret['Time']=ret['InsertedDate'].astype(np.int64)/1e9

    ret=ret.set_index('Time')
    ret['rtt']=ret['rtt']*1000
    for p in range(parts.shape[0] ):
        
        [x, y, z] = parts[p,:]
        fig, ax = plt.subplots()
      
        
        if p<parts.shape[0]-1:
            plt.plot(ret.loc[x:y].index, ret['rtt'].loc[x:y], '-o',markevery=ret.loc[x:y].index.get_indexer(points, method='nearest'))
            if (points[d]>=int(x)) & (points[d] <= int(y)):
                for d in range(points.shape[0]):
                    try:
                        mytext="("+str(points[d])+","+str(round(ret.loc[points[d]]['rtt'],2)) +")"
                        ax.annotate( mytext, (points[d] , ret.loc[points[d]]['rtt']))
                    except KeyError:
                        print(d)
        else:
            ret['rtt'].loc[x:y].plot()

        ax.set_ylabel("RTT [ms]")
        ax.set_ylim(0, ret['rtt'].loc[x:y].max()*1.1)
        plt.suptitle(title)
        plt.title(SUBTITLE)
        fig.savefig(HOMEPATH + SIM_PREFIX + 'RTT' +'-'+ z+ '.png', dpi=300)
        plt.close()

    return True

# ----------------------------------------------------------
# CWND & Inflight bytes | Only TCP | MUST GRAPH RTT BEFORE
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
        CWND.index=pd.to_datetime(CWND['Time'],unit='s')

        CWND = CWND[(CWND['Time']>=AppStartTime) & (CWND['Time']<=simTime - AppStartTime)]

        CWND=pd.DataFrame(CWND.resample(str(resamplePeriod)+'ms').newval.mean())
        CWND['Time']=CWND.index.astype(np.int64)/1e9

        CWND=CWND.set_index('Time')
        CWND['newval']=CWND['newval']/1024

        for p in range(parts.shape[0] ):
            [x, y, z] = parts[p,:]
            if (len(CWND.loc[x:y].index)>0):
                fig, ax = plt.subplots()
                
                if p<parts.shape[0]-1:
                    plt.plot(CWND.loc[x:y].index, CWND['newval'].loc[x:y], '-o',markevery=ret.loc[x:y].index.get_indexer(points, method='nearest'))
                    for d in range(points.shape[0]):
                        try:
                            if (points[d]>=int(x)) & (points[d] <= int(y)):
                                mytext="("+str(points[d])+","+str(round(CWND.loc[points[d]]['newval'],1)) +")"
                                ax.annotate( mytext, (points[d] , CWND.loc[points[d]]['newval']))
                        except KeyError:
                            print(d)

                else:
                    CWND['newval'].loc[x:y].plot()

                plt.suptitle(title)
                plt.title(SUBTITLE)
                ax.set_ylabel("CWD [KBytes]")
 
                fig.savefig(HOMEPATH + SIM_PREFIX + 'cwnd-'+str(u)+'-'+ z+'.png', dpi=300)

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

            fig.savefig(HOMEPATH + SIM_PREFIX + "InflightBytes-UE" + str(u) + '.png', dpi=300)

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
    fig.savefig(HOMEPATH + SIM_PREFIX + 'RTT_2.png', dpi=300)

    return True

# ----------------------------------------------------------
# GoodPut | Only UDP | TODO: ARREGLARLO
# ----------------------------------------------------------
@info_n_time_decorator("GoodPut")
def graphGoodPut():
    
    timeCol = "Time (s)"

    # In this test we only have 1 UE, with NodeId=1
    filepath = HOMEPATH + "UdpRecv_Node1.txt"
    df = pd.read_csv(filepath, sep="\t")

    # We group the packets that arrived at the same time
    df = df.groupby(timeCol, as_index=False)["Packet Size"].sum()

    # We calculate the time between the last packet received and
    # the current
    arrivalTime = df[timeCol].copy()
    arrivalTime.iloc[1:] = arrivalTime[0:-1]
    df["Delta Time"] = df[timeCol] - arrivalTime

    # The first column has a time of 0.0 s, so we drop it to 
    # calculate the goodput
    df.drop(index=0, axis=1, inplace=True)
    df["GoodPut (Mbps)"] = (df["Packet Size"] * 8 / df['Delta Time']) / 1e6

    plt.plot(df[timeCol], df["GoodPut (Mbps)"])
    plt.title("GoodPut")
    plt.ylabel("Throughput (Mbps)")
    plt.xlabel("Time (s)")
    plt.savefig(HOMEPATH + SIM_PREFIX + "GoodPut.png", dpi=300)
    plt.close()

    return True

# ----------------------------------------------------------
# Phy Throughput | Both
# ----------------------------------------------------------
@info_n_time_decorator("Phy Thr")
def graphPhyThroughput():
    
    filepath = HOMEPATH + "RxPacketTrace.txt"
    df = pd.read_csv(filepath, sep="\t")

    df = df[["Time", "tbSize", "corrupt"]].copy()

    # Successful retransmissions
    df = df[df["corrupt"] == 0].copy()
    df["DeltaT"] = df["Time"].diff()    # RESAMPLE BEFORE, GET NUM OF BYTES IN THAT TIMEFRAME
    df.dropna(inplace=True)
    df['Mbps'] = (df["tbSize"] * 8 / df["DeltaT"]) / 1e6
    df.index = pd.to_datetime(df["Time"], unit="s")
    df = df.resample(f"{resamplePeriod}ms").mean()

    plt.plot(df.index.microsecond / 1e6 + df.index.second, df["Mbps"])
    plt.title("PHY Throughput vs Time")
    plt.suptitle(SUBTITLE)
    plt.xlabel("Time [s]")
    plt.ylabel("Throughput [Mbps]")
    plt.savefig(HOMEPATH + SIM_PREFIX + "Phy-ThrRx" + ".png", dpi=300)
    plt.close()

    return True

#   | * ---- * ---- * ---- * |
#   |  Call graph functions  |
#   | * ---- * ---- * ---- * |

if __name__ == "__main__":
    # For all flows
    graphMobility()
    graphSinrCtrl()
    graphSinrData()
    graphCQI()
    graphTbler()
    graphPathLoss()
    graphThrTx()
    graphThrRx()
    # graphPhyThroughput()
    graphRlcBuffers()
    graphRetransmissions()

    # For TCP only
    if flowType == "TCP":
        graphThrRxRlcBuffer()
        graphThrRxPer()
        graphTcpDelay()
        graphCWNDnInflightBytes()
        get_RTT(HOMEPATH + "mypcapfile-5-1.pcap")

    # For UDP only
    if flowType == "UDP":
        graphUdpDelay()
        graphPdcpDelay()
        # graphGoodPut()
        checkUdpLoss(HOMEPATH, addNoise)
        