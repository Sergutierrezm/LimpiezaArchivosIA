import sqlite3
import json
import chromadb
import threading

class DatabaseManager:
    def __init__(self, db_path="archivos_ia.db"):
        self.db_path = db_path
        # Inicializamos la tabla una sola vez al principio
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT,
                embedding TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        # ChromaDB es seguro para hilos por defecto (Thread-safe)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="archivos_embeddings")

    def _get_conn(self):
        """Crea una conexión nueva y única para el hilo que la pida"""
        conn = sqlite3.connect(self.db_path, timeout=10) # 10 segundos de espera por bloqueos
        return conn

    def save_embedding(self, file_hash, file_path, embedding, file_name):
        embedding_json = json.dumps(embedding)
        
        # Usamos un bloque 'with' para asegurar que la conexión se cierre sola
        try:
            with self._get_conn() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO embeddings (file_hash, file_path, embedding)
                    VALUES (?, ?, ?)
                ''', (file_hash, file_path, embedding_json))
                conn.commit()

            # ChromaDB maneja su propia concurrencia
            self.collection.upsert(
                ids=[file_hash],
                embeddings=[embedding],
                metadatas=[{"path": file_path, "name": file_name}]
            )
        except Exception as e:
            # Aquí podrías usar console.print si quieres verlo con estilo
            pass 

    def get_embedding(self, file_hash):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT embedding FROM embeddings WHERE file_hash = ?', (file_hash,))
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
        except Exception:
            return None
        return None

    def close(self):
        # Ya no necesitamos cerrar una conexión global
        pass