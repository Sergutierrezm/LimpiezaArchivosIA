from core.scanner import scan_folder
from core.hasher import find_exact_duplicates, hash_file
from core.embedder import get_embedding
from core.database import DatabaseManager 
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import pandas as pd  # <--- NUEVA LIBRERÍA PARA DATA ENGINEERING

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

embeddings_lista = []
for f in candidatos_ia[:50]:  # He subido a 50 para que el DataFrame tenga más juego
    file_hash = f.get('hash') or hash_file(f['path'])
    embedding = db.get_embedding(file_hash)
    
    if embedding is None:
        print(f"  -> Generando nuevo embedding para: {f['name']}")
        try:
            with open(f['path'], 'r', errors='ignore') as file:
                contenido = file.read(4000)
            embedding = get_embedding(contenido)
            db.save_embedding(file_hash, f['path'], embedding)
        except Exception as e:
            print(f"❌ Error leyendo {f['name']}: {e}")
            continue
    else:
        print(f"  ⚡️ Recuperado de DB: {f['name']}")
    
    embeddings_lista.append(embedding)

# --- INICIO BLOQUE PANDAS MEJORADO ---
resultados_similitud = []

if len(embeddings_lista) >= 2:
    print("\n🔍 PROCESANDO MATRIZ DE SIMILITUD CON PANDAS...")
    
    for i in range(len(embeddings_lista)):
        for j in range(i + 1, len(embeddings_lista)):
            
            # SEGURIDAD: Verificamos que ambos embeddings existan y no estén vacíos
            emb_i = embeddings_lista[i]
            emb_j = embeddings_lista[j]
            
            if emb_i is not None and emb_j is not None and len(emb_i) > 0 and len(emb_j) > 0:
                try:
                    sim = cosine_similarity([emb_i], [emb_j])[0][0]
                    
                    resultados_similitud.append({
                        'archivo_a': candidatos_ia[i]['name'],
                        'archivo_b': candidatos_ia[j]['name'],
                        'similitud': round(sim * 100, 2),
                        'tamanio_a_kb': round(candidatos_ia[i]['size'] / 1024, 2),
                        'extension': Path(candidatos_ia[i]['path']).suffix
                    })
                except Exception as e:
                    # Si falla un cálculo puntual, saltamos al siguiente sin romper el programa
                    continue

# Creamos el DataFrame
df = pd.DataFrame(resultados_similitud)

# --- FIN BLOQUE PANDAS ---

# 4. Reporte Final Profesional
print("\n" + "="*40)
print(f"✅ ANÁLISIS DE DATOS COMPLETADO")
print(f"📁 Total archivos: {len(archivos)}")
print(f"👯 Duplicados exactos: {len(duplicados_exactos)}")

if not df.empty:
    # 1. Filtrar los que son muy parecidos (Thresholding)
    sospechosos = df[df['similitud'] > 90].sort_values(by='similitud', ascending=False)
    
    print(f"🤖 Sospechosos por IA (>90%): {len(sospechosos)}")
    print("-" * 40)
    print("TOP 5 ARCHIVOS MÁS PARECIDOS:")
    print(sospechosos[['archivo_a', 'archivo_b', 'similitud']].head(5).to_string(index=False))
    
    # 2. Exportar a CSV (Entregable de ingeniería)
    df.to_csv('reporte_similitud.csv', index=False)
    print("-" * 40)
    print(f"💾 Reporte completo generado: reporte_similitud.csv")

print("="*40)

db.close()