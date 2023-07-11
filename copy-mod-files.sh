#!/bin/bash
# This scripts copies all the files in the directory to_replace_src
# to their destination directory.
# To add a file place the name followed by its destination directory
# to the array "file_data".
#
# The only current way to restore the changed files is using git restore
# on the corresponding folder (ns3 or lena-nr)

source "paths.cfg"

# Source directory
source_dir="${PWD}/to_replace_in_src"
nr_model_dir="/contrib/nr/model"

# Define an array with intercalated filenames and corresponding destination paths
file_data=("lte-rlc-um.cc.txt" "/src/lte/model" 
           "lte-rlc-um.h.txt" "/src/lte/model"
           "nr-amc.cc.txt" "$nr_model_dir" 
           "nr-amc.h.txt" "$nr_model_dir"
           "nr-eesm-t1.cc.txt" "$nr_model_dir"
           )
# Add more entries as needed

# Loop through the files in the source directory
for file_path in "$source_dir"/*; do
    if [[ -f "$file_path" ]]; then
        file=$(basename "$file_path")
        found=false
        for ((i=0; i<${#file_data[@]}; i+=2)); do
            if [[ "$file" == "${file_data[i]}" ]]; then
                destination_dir="$RUTA_NS3${file_data[i+1]}"
                new_file="${file%.txt}"
                cp "$file_path" "$destination_dir/$new_file"
                printf "[${green}OK${clear}] Copied $new_file to $destination_dir/$new_file\n"
                found=true
                break
            fi
        done
        if ! $found; then
            printf "[${red}ER${clear}] No destination path set for file: $file\n"
        fi
    fi
done
