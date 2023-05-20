# ProbeCQI
 
### INFORMACIÓN

##### Sobre la simulación

- Versión de ns3: ns3.38
- Versión de LENA-NR: 2.4.y
- La implementación es 5G Non-Standalone (NSA).

##### Pasos importantes

1. Hay que duplicar el archivo `paths_default.cfg` a `paths.cfg` y cambiar el valor de la variable `RUTA_NS3` dentro del archivo a la ruta de la carpeta `ns-3-dev`  (`paths.cfg` es propio de cada instalación y se encuentra dentro del gitignore).

2. Se debe correr el script `copy-mod-files.sh` para copiar las librerías modificadas a la instalación de ns3 (las librerías originales se borran, pero se pueden recuperar haciendo `git restore .` en la carpeta correspondiente. 