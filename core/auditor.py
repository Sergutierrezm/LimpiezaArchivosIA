# core/auditor.py
from pathlib import Path
from core.scanner import scan_folder
from core.hasher import hash_file
from core.embedder import get_embedding

class AuditorEngine:
    def __init__(self, db_manager):
        """
        Inicializa el motor de auditoría.
        :param db_manager: Instancia de DatabaseManager para gestionar SQLite y ChromaDB.
        """
        self.db = db_manager
        # Extensiones que la IA puede procesar semánticamente
        self.interesantes = ['.java', '.py', '.txt', '.md', '.pdf', '.js', '.html', '.css']

    def preparar_candidatos(self, ruta):
        """
        Escanea la carpeta y filtra los archivos por extensión.
        """
        archivos = scan_folder(ruta)
        candidatos = [
            f for f in archivos 
            if Path(f['path']).suffix.lower() in self.interesantes
        ]
        return archivos, candidatos

    def procesar_archivo_ia(self, f):
        """
        Lógica de procesamiento con Caché Semántico.
        Si el archivo ya existe en la DB, salta directamente para ahorrar tiempo y CPU.
        """
        try:
            # 1. Generar Hash (DNI del archivo)
            file_hash = f.get('hash') or hash_file(f['path'])
            
            # 2. FILTRO DE CACHÉ: ¿Ya lo conocemos?
            # Consultamos primero la base de datos local (SQLite)
            embedding_existente = self.db.get_embedding(file_hash)
            
            if embedding_existente:
                # Si existe, devolvemos True inmediatamente. 
                # Esto hace que la barra de progreso "vuele".
                return True

            # 3. SI ES NUEVO: Leer contenido
            # Leemos solo los primeros 1500 caracteres para optimizar la respuesta de Ollama
            with open(f['path'], 'r', errors='ignore') as file:
                contenido = file.read(1500)
            
            if not contenido.strip():
                return False

            # 4. LLAMADA A OLLAMA (Capa de Inteligencia)
            emb = get_embedding(contenido)
            
            if emb:
                # 5. GUARDAR EN AMBAS BASES DE DATOS
                # save_embedding ya se encarga de SQLite y del upsert en ChromaDB
                self.db.save_embedding(file_hash, f['path'], emb, f['name'])
                return True
                
        except Exception:
            # Silenciamos errores de lectura de archivos específicos para no detener el bucle
            return False
        return False

    def comparar_similitudes(self, candidatos):
        """
        Analiza los archivos candidatos comparándolos con la base de datos vectorial.
        """
        resultados = []
        for f in candidatos:
            f_hash = f.get('hash') or hash_file(f['path'])
            # Recuperamos el embedding (desde el cache que acabamos de crear/actualizar)
            emb = self.db.get_embedding(f_hash)
            
            if emb and len(emb) > 0:
                # Buscamos en ChromaDB el vecino más cercano
                busqueda = self.db.collection.query(
                    query_embeddings=[emb], 
                    n_results=2, 
                    include=['metadatas', 'distances']
                )
                
                # Si hay más de un resultado (el propio archivo y otro similar)
                if len(busqueda['ids'][0]) > 1:
                    id_vecino = busqueda['ids'][0][1]
                    
                    # Evitamos comparar un archivo consigo mismo o duplicar el reporte (A-B vs B-A)
                    if f_hash < id_vecino:
                        distancia = busqueda['distances'][0][1]
                        # Convertimos la distancia de coseno en porcentaje de similitud
                        similitud = round((1 - distancia) * 100, 2)
                        
                        if similitud > 85:
                            meta_vecino = busqueda['metadatas'][0][1]
                            resultados.append({
                                'archivo_a': f['name'],
                                'ruta_a': f['path'],
                                'archivo_b': meta_vecino.get('name', 'Desconocido'),
                                'ruta_b': meta_vecino.get('path'),
                                'similitud': similitud
                            })
                            
        # Ordenamos por los más similares primero
        return sorted(resultados, key=lambda x: x['similitud'], reverse=True)