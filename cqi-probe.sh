#!/usr/bin/bash

# Color and paths vars are imported
source "paths.cfg"

# Get the system type
system_type=$(uname)

# Start time
tic=$(date +%s)

# Default values
serverType='Edge'
tcpTypeId='UDP'
mobilityVal=0
build_ns3=1
pass_through=""
custom_name=""
open_folder=0

helpFunction()
{
   echo ""
   echo "Usage: $0 -t $tcpTypeId -s $serverType -m $mobilityVal -b -o -p \"--arg=val\""
   echo -e "\t-t 'TcpNewReno' or 'TcpBbr' or 'TcpCubic' or 'TcpHighSpeed' or 'TcpBic' or 'TcpLinuxReno' or 'UDP'"
   echo -e "\t-s 'Remote' or 'Edge'"
   echo -e "\t-m Mobility 1 or 0"
   echo -e "\t-b Skips the build step of ns3, it always build by default"
   echo -e "\t-p Pass through commands to the simulation, args must be inside quotes \"--arg=value\""
   echo -e "\t-c Custom folder name for the simulation data"
   echo -e "\t-o Open folder with results at the end of simulation and processing"
   exit 1 # Exit script after printing help
}

while getopts "t:r:s:m:bp:c:o" opt
do
   case "$opt" in
      t ) tcpTypeId="$OPTARG" ;;
      s ) serverType="$OPTARG" ;;
      m ) mobilityVal="$OPTARG" ;;
      b ) build_ns3=0 ;;
      p ) pass_through="$OPTARG" ;;
      c ) custom_name="$OPTARG" ;;
      o ) open_folder=1 ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Validations
if [ "$serverType" != "Remote" ] && [ "$serverType" != "Edge" ]
then
   echo "ServerType \"$serverType\" not available";
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
   
   if [ "$?" != "0" ]; then
      printf "${red}Error while building, simulation cancelled! ${clear}\n"
      exit 1
   fi

   clear
   echo "NS3 was built!"
fi

printf "\nRunning ${magenta}$0 -t ${tcpTypeId} -s ${serverType}${clear}\n"

if [ "$tcpTypeId" == "UDP" ]
then
   flowType='UDP'
else
   flowType='TCP'
fi
servertag=${serverType:0:1}


echo
printf "Running... \n tcpTypeId: ${magenta}${tcpTypeId}${clear}\tServer: ${green}${serverType}${clear}\tFolder: ${blue}${custom_name}${clear}\n"
echo

#backup run-sim and cc
outfolder="${RUTA_PROBE}/out"

oldname_path=""
if ([ "$custom_name" == "" ] || [[ $custom_name = *" "* ]])
then
   bkfolder=$tcpTypeId"-"$servertag"-"`date +%Y%m%d%H%M`
else
   bkfolder=$custom_name
   oldname_path=$outfolder/$bkfolder/$tcpTypeId"-"$servertag"-"`date +%Y%m%d%H%M`".oldname"
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
    --flowType=$flowType
    --tcpTypeId=$tcpTypeId
    --serverType=$serverType
    --mobility=$mobilityVal
   $pass_through
    " --cwd "$outfolder/$bkfolder" --no-build

   exit_status=$?
   if [ "$exit_status" != "0" ]; then
      printf "${red}Error ${exit_status} while simulating, simulation cancelled! ${clear}\n"
      echo "Graphs and post-processing script were not run."
      exit $exit_status
   fi

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

   # Check if the system is macOS
   if [[ "$system_type" == "Darwin" ]]; then
   open $outfolder/$bkfolder
   # Check if the system is Linux
   elif [[ "$system_type" == "Linux" ]]; then
   explorer $outfolder/$bkfolder
   # If neither macOS nor Linux
   else
   echo "Unable to open folder."
   fi

fi