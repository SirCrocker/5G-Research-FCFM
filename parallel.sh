#!/bin/bash

# TODO: Actualmente paraleliza por tandas, hacer que pueda ir uno por uno (asignando una sim a 1 core)
# TODO: Implementar método para poder cancelar/matar a los subprocesos
# TODO: Revisar (y actualizar de ser necesario) para que sea compatible con linux y macos
# INFO: Ahora mismo solo corre numero_de_cores - 1 simulaciones
#       HAY que buildear antes de llamar, ya que no buildea ns3.

# Custom vars
source "paths.cfg"
os=$(uname)

# Parallelize simulations
parameters=("--amcAlgo=2 --blerTarget=0.2" "--amcAlgo=2 --blerTarget=1")
montecarlo=2
# Num of cores will be the number of parallel simulations
num_cores=$(nproc)

outdir=""
outpath==""
sim_num=1
nparam=0
custom_name=""
random=0

helpFunction()
{
   echo ""
   echo "Usage: $0 -m $montecarlo -c $custom_name -r"
   echo -e "\t-m Number of montecarlo iterations"
   echo -e "\t-c Custom folder name for the simulation data, the number of parameter will be prefixed"
   echo -e "\t-r Flag that sets that a random run is used so results are not deterministic"
   exit 1 # Exit script after printing help
}

while getopts "m:c:r" opt
do
   case "$opt" in
      m ) montecarlo="$OPTARG" ;;
      c ) custom_name="$OPTARG" ;;
      r ) random=1 ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

for param in "${parameters[@]}"; do

    if [ "$montecarlo" -gt 1 ]; then

        if ([ "$custom_name" == "" ] || [[ $custom_name = *" "* ]])
        then
            outdir="PAR${nparam}M${montecarlo}-"`date +%Y%m%d_%H%M%S`
        else
            outdir="$nparam-$custom_name"
        fi

        mkdir "$RUTA_PROBE/out/$outdir"
        mkdir "$RUTA_PROBE/out/$outdir/outputs"
        echo "$param" > "$RUTA_PROBE/out/$outdir/parameters.txt"

        ((nparam++))
    fi

    for ((mont_num=1; mont_num<=montecarlo; mont_num++)); do

        rem=$((sim_num % num_cores))

        param2=$param;
        if [ "$random" == "1" ]; then
            param2="$param --RngRun=$sim_num"
        fi

        stdoutTxt=$RUTA_PROBE/out/$outdir/outputs/sim${mont_num}.txt
        bash "cqi-probe.sh" -b -c "$outdir/SIM${mont_num}" -p "`echo $param2`" > "$stdoutTxt" && printf "Done $sim_num ${red}-${clear} Exit Status $?"&
        printf "[sim:${blue}${sim_num}${clear} pid:${cyan}$!${clear}] Called ${green}cqi-probe.sh -b -c \"SIM${mont_num}\" -p ${param2} ${clear}\n"

        if [ "$rem" == "$((num_cores-1))" ]; then
            jobs
            wait
        fi

        ((sim_num++))
    done
    
done

jobs
wait
