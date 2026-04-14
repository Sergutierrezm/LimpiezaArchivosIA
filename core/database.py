import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_path="archivos_ia.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # Creamos la tabla para guardar los embeddings
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT,
                embedding TEXT  -- Guardaremos la lista de números como un texto JSON
            )
        ''')
        self.conn.commit()

    def save_embedding(self, file_hash, file_path, embedding):
        # Guardamos el resultado de Ollama
        embedding_json = json.dumps(embedding)
        self.cursor.execute('''
            INSERT OR REPLACE INTO embeddings (file_hash, file_path, embedding)
            VALUES (?, ?, ?)
        ''', (file_hash, file_path, embedding_json))
        self.conn.commit()

    def get_embedding(self, file_hash):
        # Buscamos si ya lo conocemos
        self.cursor.execute('SELECT embedding FROM embeddings WHERE file_hash = ?', (file_hash,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

    def close(self):
        self.conn.close()