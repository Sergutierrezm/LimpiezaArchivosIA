# core/organizador.py
import logging
from pathlib import Path
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class OrganizadorExtensiones:
    def __init__(self):
        # Mapeo de carpetas destino y las extensiones que aceptan
        self.MAPEO_EXTENSIONES = {
            'PDFs': ['.pdf'],
            'CSVs': ['.csv'],
            'Ejecutables': ['.exe', '.msi'],
            'Documentos': ['.docx', '.xlsx', '.pptx', '.txt', '.md'],
            'Imagenes': ['.jpg', '.jpeg', '.png', '.gif', '.svg'],
            'Comprimidos': ['.zip', '.rar', '.tar', '.gz'],
            'Codigo': ['.java', '.py', '.js', '.html', '.css', '.sql']
        }

    def organizar_directorio(self, archivos: list[dict], ruta_base: str) -> dict:
        """
        Toma la lista de archivos ya escaneados y los organiza 
        en subcarpetas dentro de la ruta base (solo primer nivel).
        """
        p_base = Path(ruta_base)
        resumen = {cat: 0 for cat in self.MAPEO_EXTENSIONES.keys()}
        resumen['Otros/No movidos'] = 0

        for f in archivos:
            ruta_archivo = Path(f['path'])
            
            # 🌟 CAMBIO CLAVE: Si el archivo no está en la raíz de la ruta_base, lo saltamos.
            # Esto evita romper proyectos estructurados dentro de subcarpetas profundas.
            if ruta_archivo.parent != p_base:
                continue

            # Seguridad: Evitamos mover archivos que ya están organizados
            if ruta_archivo.parent.name in self.MAPEO_EXTENSIONES.keys():
                continue

            ext = f['ext']
            destino_encontrado = False

            for carpeta_destino, extensiones in self.MAPEO_EXTENSIONES.items():
                if ext in extensiones:
                    ruta_carpeta_destino = p_base / carpeta_destino
                    ruta_carpeta_destino.mkdir(exist_ok=True)
                    
                    destino_final = ruta_carpeta_destino / f['name']
                    
                    # Control de colisiones: si ya existe, metemos timestamp
                    if destino_final.exists():
                        prefix = datetime.now().strftime('%H%M%S')
                        destino_final = ruta_carpeta_destino / f"{prefix}_{f['name']}"
                    
                    try:
                        shutil.move(f['path'], str(destino_final))
                        logger.info(f"ORGANIZADOR: {f['path']} -> {destino_final}")
                        resumen[carpeta_destino] += 1
                    except Exception as e:
                        logger.error(f"ERROR ORGANIZADOR moviendo {f['name']}: {str(e)}")
                        
                    destino_encontrado = True
                    break
            
            if not destino_encontrado:
                resumen['Otros/No movidos'] += 1

        return resumen