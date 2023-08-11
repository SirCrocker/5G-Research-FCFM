# ProbeCQI

### INFORMACIÓN

#### Sobre la simulación

- Versión de ns3: ns3.39
- Versión de LENA-NR: 2.5.y
- La implementación es 5G Standalone (SA).

#### Pasos importantes antes de simular

1. Hay que duplicar el archivo `paths_default.cfg` a `paths.cfg` y cambiar el valor de la variable `RUTA_NS3` dentro del archivo a la ruta de la carpeta `ns-3-dev`  (`paths.cfg` es propio de cada instalación y se encuentra dentro del gitignore).
2. Se debe correr el script `copy-mod-files.sh` para copiar las librerías modificadas a la instalación de ns3 (las librerías originales se eliminan, pero se pueden recuperar haciendo `git restore .` en la carpeta correspondiente).
3. Crear la carpeta `out` dentro del directorio principal, donde se guardarán los resultados de las simulaciones.

#### Requerimientos Python

Python se utiliza en la generación de gráficos y en el análisis de algunos datos, las librerías utilizadas son las siguientes:

- Scapy
- Pandas
- matplotlib
- numpy

#### Como simular

##### Simulación simple (única realización)

To-Do

##### Múltiples simulaciones (en paralelo)

To-Do