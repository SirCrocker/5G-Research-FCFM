#!/usr/bin/bash

# Color and paths vars are imported
source "paths.cfg"

# Start time
tic=$(date +%s)

# Default values
serverType='Edge'
rlcBufferPer=10
tcpTypeId='TcpNewReno'
mobilityVal=0
build_ns3=1
pass_through=""
custom_name=""
open_folder=0

helpFunction()
{
   echo ""
   echo "Usage: $0 -t $tcpTypeId -s $serverType -r $rlcBufferPer -m $mobilityVal -b $build_ns3"
   echo -e "\t-t 'TcpNewReno' or 'TcpBbr' or 'TcpCubic' or 'TcpHighSpeed' or 'TcpBic' or 'TcpLinuxReno' or 'UDP'"
   echo -e "\t-s 'Remote' or 'Edge'"
   echo -e "\t-r RLC Buffer BDP Percentage 10 o 100"
   echo -e "\t-m Mobility 1 or 0"
   echo -e "\t-b Select if ns3 builds or not, default 1"
   echo -e "\t-p Pass through commands to the simulation, args must be inside quotes (\"{arg}\")"
   echo -e "\t-c Custom folder name for the simulation data"
   echo -e "\t-o Open folder with results at the end of simulation and processing"
   exit 1 # Exit script after printing help
}

while getopts "t:r:s:m:b:p:c:o:" opt
do
   case "$opt" in
      t ) tcpTypeId="$OPTARG" ;;
      s ) serverType="$OPTARG" ;;
      r ) rlcBufferPer="$OPTARG" ;;
      m ) mobilityVal="$OPTARG" ;;
      b ) build_ns3="$OPTARG" ;;
      p ) pass_through="$OPTARG" ;;
      c ) custom_name="$OPTARG" ;;
      o ) open_folder="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Validations
if [ "$serverType" != "Remote" ] && [ "$serverType" != "Edge" ]
then
   echo "ServerType \"$serverType\" not available";
   helpFunction
fi

if [ "$rlcBufferPer" != "10" ] && [ "$rlcBufferPer" != "100" ]
then
   echo "rlcBuffer \"$rlcBufferPer\" not available";
   helpFunction
fi

if [ "$mobilityVal" != "0" ] && [ "$mobilityVal" != "1" ]
then
   echo "mobilityVal \"$mobilityVal\" not available";
   helpFunction
fi

if [ "$tcpTypeId" != "UDP" ] && [ "$tcpTypeId" != "TcpNewReno" ] && [ "$tcpTypeId" != "TcpBbr" ] && [ "$tcpTypeId" != "TcpCubic" ] && [ "$tcpTypeId" != "TcpHighSpeed" ] && [ "$tcpTypeId" != "TcpBic" ] && [ "$tcpTypeId" != "TcpLinuxReno" ]
then
   echo "tcpTypeId \"$tcpTypeId\" not available";
   helpFunction
fi

if [ "$build_ns3" == "1" ]
then 
   "${RUTA_NS3}/ns3" build
   clear
   echo "NS3 was built!"
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
printf "Running... \nRLCBuffer: ${green}${rlcBufferPer}${clear}\t tcpTypeId: ${magenta}${tcpTypeId}${clear}\tServer: ${green}${serverType}${clear}\n"
echo

#backup run-sim and cc
outfolder="${RUTA_PROBE}/out"

oldname_path=""
if ([ "$custom_name" == "" ] || [[ $custom_name = *" "* ]])
then
   bkfolder=$tcpTypeId"-"$servertag"-"$buffertag"-"`date +%Y%m%d%H%M`
else
   bkfolder=$custom_name
   oldname_path=$outfolder/$bkfolder/$tcpTypeId"-"$servertag"-"$buffertag"-"`date +%Y%m%d%H%M`".oldname"
fi

me=`basename "$0"`

if [ ! -d "$outfolder" ];
then
	mkdir $outfolder
fi

if [ ! -d "$outfolder/$bkfolder" ];
then
	mkdir $outfolder/$bkfolder

   if [[ $oldname_path != "" ]]
   then
      touch $oldname_path
   fi

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
    --mobility=`echo $mobilityVal`
   `echo $pass_through`
    " --cwd `echo $outfolder/$bkfolder` --no-build

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

if [ "$open_folder" != "0" ]
then
   open $outfolder/$bkfolder
fi