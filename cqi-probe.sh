#!/usr/bin/bash

# Color and paths vars are imported
source "paths.cfg"

# Start time
tic=$(date +%s)

# Default values
serverType='Edge'
rlcBufferPer=10
tcpTypeId='TcpNewReno'
cqiHighGain=2

helpFunction()
{
   echo ""
   echo "Usage: $0 -g $cqiHighGain -t $tcpTypeId -s $serverType -r $rlcBufferPer"
   echo -e "\t-g 'CQI step 1-10'"
   echo -e "\t-t 'TcpNewReno' or 'TcpBbr' or 'TcpCubic' or 'TcpHighSpeed' or 'TcpBic' or 'TcpLinuxReno' or 'UDP'"
   echo -e "\t-s 'Remote' or 'Edge'"
   echo -e "\t-r RLC Buffer BDP Percentage 10 o 100"
   exit 1 # Exit script after printing help
}


while getopts "t:r:s:" opt
do
   case "$opt" in
      g ) cqiHighGain="$OPTARG" ;;
      t ) tcpTypeId="$OPTARG" ;;
      s ) serverType="$OPTARG" ;;
      r ) rlcBufferPer="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done
# Validations
if [ "$serverType" != "Remote" ] && [ "$serverType" != "Edge" ]
then
   echo "ServerType \"$serverType\" no available";
   helpFunction
fi

if [ "$rlcBufferPer" != "10" ] && [ "$rlcBufferPer" != "100" ]
then
   echo "rlcBuffer \"$rlcBufferPer\" no available";
   helpFunction
fi

if [ "$tcpTypeId" != "UDP" ] && [ "$tcpTypeId" != "TcpNewReno" ] && [ "$tcpTypeId" != "TcpBbr" ] && [ "$tcpTypeId" != "TcpCubic" ] && [ "$tcpTypeId" != "TcpHighSpeed" ] && [ "$tcpTypeId" != "TcpBic" ] && [ "$tcpTypeId" != "TcpLinuxReno" ]
then
   echo "tcpTypeId \"$tcpTypeId\" no available";
   helpFunction
fi

printf "\nRunning ${magenta}$0 -t ${tcpTypeId} -r ${rlcBufferPer} -s ${serverType}${clear}\n"

if [ "$tcpTypeId" == "UDP" ]
then
   flowType='UDP'
else
   flowType='TCP'
fi
servertag=${serverType:0:1}
if [ "$rlcBufferPer" == "10" ]
then
    buffertag="0$rlcBufferPer"
else
    buffertag="$rlcBufferPer"
fi


echo
printf "Running... \ncqiHighGain:${green}${cqiHighGain}${clear}\tRLCBuffer: ${green}${rlcBufferPer}${clear}\t tcpTypeId: ${magenta}${tcpTypeId}${clear}\tServer: ${green}${serverType}${clear}\n"
echo

#backup run-sim and cc
outfolder="${RUTA_PROBE}/out"
bkfolder=$cqiHighGain"-"$tcpTypeId"-"$servertag"-"$buffertag"-"`date +%Y%m%d%H%M`
me=`basename "$0"`

if [ ! -d "$outfolder" ];
then
	mkdir $outfolder
fi

if [ ! -d "$outfolder/$bkfolder" ];
then
	mkdir $outfolder/$bkfolder
fi

cp $me $outfolder/$bkfolder/$me.txt
cp $RUTA_CC $outfolder/$bkfolder/my-cqi-probe.cc.txt
cp "${RUTA_PROBE}/packet-error-rate.sh" $outfolder/$bkfolder/packet-error-rate.sh.txt
cp "${RUTA_PROBE}/graph.py" $outfolder/$bkfolder/graph.py.txt


"${RUTA_NS3}/ns3" run "${FILENAME}
    --flowType=`echo $flowType`
    --tcpTypeId=`echo $tcpTypeId`
    --serverType=`echo $serverType`
    --rlcBufferPerc=`echo $rlcBufferPer`
    --cqiHighGain=`echo $cqiHighGain`
    --mobility=1
    " --cwd `echo $outfolder/$bkfolder`

echo "Destination folder name: $bkfolder"

echo
printf "Running... Packet Error Rate Script\n"
echo
sh "${RUTA_PROBE}/packet-error-rate.sh" $outfolder/$bkfolder

echo
printf "Running... Graph Script\n"
echo

python3 "${RUTA_PROBE}/graph.py" $outfolder/$bkfolder $RUTA_PROBE

toc=$(date +%s)
printf "Simulation Processed in: "${magenta}$(($toc-$tic))${clear}" seconds\n"