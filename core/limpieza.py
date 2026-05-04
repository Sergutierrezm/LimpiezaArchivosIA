import os
import shutil
import logging
from datetime import datetime

# 1. Configuración de Logs (La huella digital de tu proceso)
log_dir = "logs"
if not os.path.exists(log_dir): 
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"limpieza_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def mover_a_cuarentena(lista_rutas, carpeta_destino="CUARENTENA_IA"):
    """Mueve archivos detectados a una carpeta segura y registra la acción."""
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    movidos = 0
    for ruta in lista_rutas:
        try:
            if os.path.exists(ruta):
                nombre = os.path.basename(ruta)
                destino = os.path.join(carpeta_destino, nombre)
                
                # Si el archivo ya existe en destino, añadimos timestamp para no sobreescribir
                if os.path.exists(destino):
                    prefix = datetime.now().strftime('%H%M%S')
                    destino = os.path.join(carpeta_destino, f"{prefix}_{nombre}")
                
                shutil.move(ruta, destino)
                logging.info(f"MOVIDO: {ruta} -> {destino}")
                movidos += 1
            else:
                logging.warning(f"ARCHIVO NO ENCONTRADO AL MOVER: {ruta}")
        except Exception as e:
            logging.error(f"ERROR CRÍTICO moviendo {ruta}: {str(e)}")
            
    return movidos