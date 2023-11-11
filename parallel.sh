#!/bin/bash

# TODO: Actualmente paraleliza por tandas, hacer que pueda ir uno por uno (asignando una sim a 1 core)
# TODO: Propagar Ctrl-c
# INFO: Ahora mismo solo corre numero_de_cores - 1 simulaciones

# Custom vars
source "paths.cfg"
os=$(uname)

# Parallelize simulations
parameters=("--amcAlgo=0 --phyDistro=1 -simTime=3" 
            "--amcAlgo=0 --phyDistro=2 -simTime=3")
            # "--amcAlgo=2 --phyDistro=1 -simTime=3 --blerTarget=0.3"
            # "--amcAlgo=2 --phyDistro=2 -simTime=3 --blerTarget=0.3"
            # "--amcAlgo=3 --phyDistro=1 -simTime=3"
            # "--amcAlgo=3 --phyDistro=2 -simTime=3")

montecarlo=2
# Num of cores will be the number of parallel simulations
num_cores=$(nproc)

outdir=""
outpath==""
sim_num=1
nparam=0
custom_name=""
random=1
build_ns3=1

helpFunction()
{
   echo ""
   echo "Usage: $0 -m $montecarlo -c $custom_name -r -b"
   echo -e "\t-m Number of montecarlo iterations [default: ${montecarlo}]"
   echo -e "\t-c Custom folder name for the folder with the different simulations, the word \"PAR-\" will be prefixed"
   echo -e "\t-r Flag that sets that a random run is NOT used so results ARE deterministic"
   echo -e "\t-b Skips the build step of ns3, it always build by default"
   exit 1 # Exit script after printing help
}

while getopts "m:c:rb" opt
do
   case "$opt" in
      m ) montecarlo="$OPTARG" ;;
      c ) custom_name="$OPTARG" ;;
      r ) random=0 ;;
      b ) build_ns3=0 ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Build ns3 before simulating
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

for param in "${parameters[@]}"; do

    if [ "$montecarlo" -gt 1 ]; then

        if ([ "$custom_name" == "" ] || [[ $custom_name = *" "* ]])
        then
            batch_dir_name="PAR_BATCH-"`date +%Y%m%d_%H%M%S`
        else
            batch_dir_name="PAR-$custom_name"
        fi

        outdir="${batch_dir_name}/PARAM${nparam}MON${montecarlo}"

        mkdir -p "$RUTA_PROBE/out/$outdir/outputs"
        echo "$param" > "$RUTA_PROBE/out/$outdir/parameters.txt"

        ((nparam++))
    fi

    for ((mont_num=1; mont_num<=montecarlo; mont_num++)); do

        rem=$((sim_num % num_cores))

        param2=$param;
        if [ "$random" == "1" ]; then
            param2="$param --RngRun=$mont_num"
        fi

        stdoutTxt=$RUTA_PROBE/out/$outdir/outputs/sim${mont_num}.txt
        (bash "run-simulation.sh" -b -c "$outdir/SIM${mont_num}" -p "$param2" &> $stdoutTxt; printf "Done $sim_num ${red}-${clear} Exit Status $?\n") &
        printf "[sim:${blue}${sim_num}${clear} pid:${cyan}$!${clear}] Called ${green}run-simulation.sh -b -c \"SIM${mont_num}\" -p ${param2} ${clear}\n"

        if [ "$rem" == "$((num_cores-1))" ]; then
            jobs
            wait
        fi

        ((sim_num++))
    done
    
done

jobs
wait

printf "${cyan}Running Graph script...${clear}\n"
python3 "${RUTA_PROBE}/graph_parallel.py" "$RUTA_PROBE/out/$batch_dir_name"
