#!/usr/bin/bash
tic=$(date +%s)

# Set text colors
clear='\033[0m'
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'

# Set Background colors
bg_red='\033[0;41m'
bg_green='\033[0;42m'
bg_yellow='\033[0;43m'
bg_blue='\033[0;44m'
bg_magenta='\033[0;45m'
bg_cyan='\033[0;46m'

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
outfolder="./scratch/cqiProbe/out"
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
cp scratch/cqiProbe/my-cqi-probe.cc $outfolder/$bkfolder/my-cqi-probe.cc.txt
cp packet-error-rate.sh $outfolder/$bkfolder/packet-error-rate.sh.txt
cp graph.py $outfolder/$bkfolder/graph.py.txt


./ns3 run "my-cqi-probe
    --flowType=`echo $flowType`
    --tcpTypeId=`echo $tcpTypeId`
    --serverType=`echo $serverType`
    --rlcBufferPerc=`echo $rlcBufferPer`
    --cqiHighGain=`echo $cqiHighGain`
    --mobility=1
    " --cwd `echo $outfolder/$bkfolder` 

echo $bkfolder

echo
printf "Running... Packet Error Rate Script\n"
echo
./packet-error-rate.sh $outfolder/$bkfolder

echo
printf "Running... Graph Script\n"
echo

python3 graph.py $outfolder/$bkfolder

toc=$(date +%s)
printf "Simulation Processed in: "${magenta}$(($toc-$tic))${clear}" seconds\n"