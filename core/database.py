import sqlite3
import json
import chromadb # <--- Nueva pieza del motor

class DatabaseManager:
    def __init__(self, db_path="archivos_ia.db"):
        # 1. SQLite para metadatos (el de siempre)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()
        
        # 2. ChromaDB para búsqueda vectorial (el turbo)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="archivos_embeddings")

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT,
                embedding TEXT
            )
        ''')
        self.conn.commit()

    def save_embedding(self, file_hash, file_path, embedding, file_name):
        # Guardamos en SQLite (Persistencia tradicional)
        embedding_json = json.dumps(embedding)
        self.cursor.execute('''
            INSERT OR REPLACE INTO embeddings (file_hash, file_path, embedding)
            VALUES (?, ?, ?)
        ''', (file_hash, file_path, embedding_json))
        self.conn.commit()

        # Guardamos en ChromaDB (Para búsquedas instantáneas)
        # Nota: Chroma necesita que el ID sea un string (usamos el hash)
        self.collection.add(
            ids=[file_hash],
            embeddings=[embedding],
            metadatas=[{"path": file_path, "name": file_name}]
        )

    def get_embedding(self, file_hash):
        self.cursor.execute('SELECT embedding FROM embeddings WHERE file_hash = ?', (file_hash,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

    def buscar_similares(self, embedding_consulta, umbral_similitud=0.9):
        """
        ¡Aquí está la magia! ChromaDB busca en milisegundos sin bucles for.
        """
        # Distancia es lo contrario a similitud (0.1 distancia = 0.9 similitud)
        distancia_maxima = 1 - umbral_similitud
        
        results = self.collection.query(
            query_embeddings=[embedding_consulta],
            n_results=5,
            where_document=None # Aquí podrías filtrar por extensión si quisieras
        )
        return results

    def close(self):
        self.conn.close()