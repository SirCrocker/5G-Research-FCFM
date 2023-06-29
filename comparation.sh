#!/bin/bash
# Color and paths vars are imported
source "paths.cfg"

output_file=$RUTA_PROBE"/out/comparation.txt"
control_folder="${RUTA_PROBE}/control/"
control_thr=0

# Borra el contenido previo del archivo de comparación si existe
if [ -f "$output_file" ]; then
    rm "$output_file"
fi

# Imprime las líneas de encabezado en el archivo de comparación
echo "Comparación de Mean flow throughput"
echo "---------------------------------"
echo "Comparación de Mean flow throughput" >> "$output_file"
echo "---------------------------------" >> "$output_file"

# Verifica si existe la carpeta de control y el archivo FlowOutput.txt
if [ -d "$control_folder" ] && [ -f "$control_folder/FlowOutput.txt" ]; then
    control_thr=$(grep "Mean flow throughput" "$control_folder/FlowOutput.txt" | awk -F ": " '{print $2}')
fi

# Recorre todas las carpetas en /home/diego/ns-3-dev/scratch/ProbeCQI/out
for folder in "$RUTA_PROBE/out/"*; do
    if [[ -d "$folder" ]]; then
        folder_name=$(basename "$folder")  # Obtiene el nombre de la carpeta
        
        # Verifica si existe el archivo FlowOutput.txt en la carpeta actual
        if [ -f "$folder/FlowOutput.txt" ]; then
            # Obtiene la línea que contiene "Mean flow throughput" y su valor numérico
            throughput_line=$(grep "Mean flow throughput" "$folder/FlowOutput.txt")
            current_thr=$(echo "$throughput_line" | awk -F ": " '{print $2}')
            
            # Imprime la línea en la consola y resalta en verde, rojo o azul según la comparación
            if (( $(echo "$current_thr > $control_thr" | bc -l) )); then
                echo -e "\e[32m$folder_name: $current_thr\e[0m"  # Resalta en verde
            elif (( $(echo "$current_thr < $control_thr" | bc -l) )); then
                echo -e "\e[31m$folder_name: $current_thr\e[0m"  # Resalta en rojo
            else
                echo -e "\e[94m$folder_name: $current_thr\e[0m"  # Resalta en azul claro
            fi
            
            # Escribe la línea en el archivo de comparación
            echo "$folder_name: $current_thr" >> "$output_file"
        fi
    fi
done
