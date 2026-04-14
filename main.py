from core.scanner import scan_folder
from core.hasher import find_exact_duplicates, hash_file
from core.embedder import get_embedding
from core.database import DatabaseManager  # Importamos tu nueva clase
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# Inicializamos la DB
db = DatabaseManager()

# 1. Escaneo inicial
PATH_A_REVISAR = '/Users/sergiogutierrez/Downloads'
print(f"🚀 Escaneando: {PATH_A_REVISAR}...")
archivos = scan_folder(PATH_A_REVISAR)

# 2. Fase de Duplicados Exactos
print("🔍 Buscando duplicados exactos...")
duplicados_exactos = find_exact_duplicates(archivos)

# 3. Fase Inteligente con persistencia
print("🧠 Analizando semántica (con memoria en SQLite)...")
interesantes = ['.java', '.py', '.txt', '.md']
candidatos_ia = [f for f in archivos if Path(f['path']).suffix in interesantes]

# Procesamos los candidatos para asegurar que tengan embedding
embeddings_lista = []
for f in candidatos_ia[:20]:  # Limitamos a 20 para la primera prueba real
    # Paso A: Asegurarnos de tener el hash (si find_exact_duplicates no lo hizo)
    file_hash = f.get('hash') or hash_file(f['path'])
    
    # Paso B: Consultar DB
    embedding = db.get_embedding(file_hash)
    
    if embedding is None:
        # No está en DB, llamamos a Ollama
        print(f"  -> Generando nuevo embedding para: {f['name']}")
        with open(f['path'], 'r', errors='ignore') as file:
            contenido = file.read(4000)
        embedding = get_embedding(contenido)
        # Guardamos para la próxima vez
        db.save_embedding(file_hash, f['path'], embedding)
    else:
        print(f"  ⚡️ Recuperado de DB: {f['name']}")
    
    embeddings_lista.append(embedding)

# Ejemplo de comparación entre los dos primeros después de procesar
# En lugar de comparar solo el 0 y el 1, hacemos un bucle inteligente
if len(embeddings_lista) >= 2:
    print("\n🔍 BUSCANDO ARCHIVOS CASI IDÉNTICOS...")
    
    # Comparamos todos contra todos
    for i in range(len(embeddings_lista)):
        for j in range(i + 1, len(embeddings_lista)):
            
            # Calculamos la similitud entre el archivo 'i' y el archivo 'j'
            sim = cosine_similarity([embeddings_lista[i]], [embeddings_lista[j]])[0][0]
            
            # Si se parecen más de un 85%, ¡es sospechoso!
            if sim > 0.85:
                nombre_a = candidatos_ia[i]['name']
                nombre_b = candidatos_ia[j]['name']
                print(f"⚠️ {sim:.2%} de similitud:")
                print(f"   📄 {nombre_a}")
                print(f"   📄 {nombre_b}\n")

# 4. Reporte Final
print("\n" + "="*30)
print(f"✅ PROCESO COMPLETADO")
print(f"📁 Archivos analizados: {len(archivos)}")
print(f"👯 Duplicados exactos: {len(duplicados_exactos)}")
print(f"💾 Memoria: Los vectores están guardados en archivos_ia.db")
print("="*30)

db.close()