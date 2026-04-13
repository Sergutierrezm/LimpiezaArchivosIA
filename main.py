from core.scanner import scan_folder
from core.hasher import find_exact_duplicates
from core.embedder import get_embedding
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# 1. Escaneo inicial
PATH_A_REVISAR = '/Users/sergiogutierrez/Downloads'
print(f"🚀 Escaneando: {PATH_A_REVISAR}...")
archivos = scan_folder(PATH_A_REVISAR)

# 2. Fase de Fuerza Bruta (Duplicados Exactos)
# Esto limpia el 80% de la basura rápido sin usar IA
print("🔍 Buscando duplicados exactos (Hashing)...")
duplicados_exactos = find_exact_duplicates(archivos)

# 3. Fase Inteligente (Selección de candidatos para IA)
# No queremos procesar todo. Solo archivos de texto o código que NO sean duplicados exactos.
print("🧠 Preparando análisis semántico con Ollama...")
interesantes = ['.java', '.py', '.txt', '.md']

# Corregimos convirtiendo a Path para poder usar .suffix
candidatos_ia = [f for f in archivos if Path(f['path']).suffix in interesantes]

if len(candidatos_ia) >= 2:
    f1, f2 = candidatos_ia[0], candidatos_ia[1]
    
    # Usamos f['path'] directamente porque open() acepta strings
    with open(f1['path'], 'r', errors='ignore') as file: text1 = file.read(4000)
    with open(f2['path'], 'r', errors='ignore') as file: text2 = file.read(4000)
    
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    
    # Calculamos similitud
    similitud = cosine_similarity([emb1], [emb2])[0][0]
    print(f"🧐 Similitud entre {f1['name']} y {f2['name']}: {similitud:.2%}")

# 4. Reporte Final
print("\n" + "="*30)
print(f"✅ ESCANEO FINALIZADO")
print(f"📁 Total archivos: {len(archivos)}")
print(f"👯 Grupos exactos: {len(duplicados_exactos)}")
print(f"💡 Candidatos para IA: {len(candidatos_ia)}")
print("="*30)   