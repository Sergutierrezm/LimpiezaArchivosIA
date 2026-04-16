from core.scanner import scan_folder
from core.hasher import find_exact_duplicates, hash_file
from core.embedder import get_embedding
from core.database import DatabaseManager 
from pathlib import Path
import pandas as pd

# 1. Inicialización
db = DatabaseManager()
PATH_A_REVISAR = '/Users/sergiogutierrez/Downloads'

print(f"🚀 Iniciando Auditoría en: {PATH_A_REVISAR}")
print("="*40)

# 2. Escaneo y Duplicados Exactos
archivos = scan_folder(PATH_A_REVISAR)
duplicados_exactos = find_exact_duplicates(archivos)
print(f"📁 Archivos detectados: {len(archivos)}")
print(f"👯 Duplicados exactos: {len(duplicados_exactos)}")

# 3. Preparación de Candidatos para IA
interesantes = ['.java', '.py', '.txt', '.md']
candidatos_ia = [f for f in archivos if Path(f['path']).suffix in interesantes]
print(f"🧠 Candidatos para análisis semántico: {len(candidatos_ia)}")

# 4. Fase de Indexación (Alimentar SQLite + ChromaDB)
print("\n🔍 Verificando índices en Base de Datos Vectorial...")
for f in candidatos_ia:
    file_hash = f.get('hash') or hash_file(f['path'])
    embedding = db.get_embedding(file_hash)
    
    if embedding is None or (isinstance(embedding, list) and len(embedding) == 0):
        try:
            with open(f['path'], 'r', errors='ignore') as file:
                contenido = file.read(2500) # Bajamos a 2500 para evitar errores de contexto
            
            if not contenido.strip(): continue
                
            print(f"  -> Generando embedding: {f['name']}")
            embedding = get_embedding(contenido)
            
            if embedding and len(embedding) > 0:
                db.save_embedding(file_hash, f['path'], embedding, f['name'])
        except Exception as e:
            print(f"❌ Error procesando {f['name']}: {e}")
            continue
    else:
        # Aseguramos que esté en ChromaDB con la extensión (UPSERT)
        if isinstance(embedding, list) and len(embedding) > 0:
            db.collection.upsert(
                ids=[file_hash],
                embeddings=[embedding],
                metadatas=[{
                    "path": f['path'], 
                    "name": f['name'], 
                    "extension": Path(f['path']).suffix or "txt"
                }]
            )

# 5. Búsqueda de Similitudes
print("\n🤖 Analizando sospechosos por IA (Búsqueda Vectorial)...")
resultados_similitud = []

for f in candidatos_ia:
    f_hash = f.get('hash') or hash_file(f['path'])
    emb = db.get_embedding(f_hash)
    
    if emb and len(emb) > 0:
        busqueda = db.collection.query(
            query_embeddings=[emb],
            n_results=2,
            include=['metadatas', 'distances']
        )
        
        if len(busqueda['ids'][0]) > 1:
            id_vecino = busqueda['ids'][0][1]
            if f_hash < id_vecino: 
                distancia = busqueda['distances'][0][1]
                similitud = round((1 - distancia) * 100, 2)
                
                if similitud > 85:
                    metadatos_vecino = busqueda['metadatas'][0][1]
                    # PROTECCIÓN: .get() evita el KeyError si el dato es viejo
                    resultados_similitud.append({
                        'archivo_a': f['name'],
                        'archivo_b': metadatos_vecino.get('name', 'Desconocido'),
                        'similitud': similitud,
                        'extension': metadatos_vecino.get('extension', 'N/A')
                    })

# 6. Reporte Final con Pandas
df = pd.DataFrame(resultados_similitud)

print("\n" + "="*40)
print(f"✅ ANÁLISIS COMPLETADO")
print(f"📁 Total archivos escaneados: {len(archivos)}")

if not df.empty:
    sospechosos = df[df['similitud'] > 90].sort_values(by='similitud', ascending=False)
    print(f"🤖 Sospechosos por IA (>90%): {len(sospechosos)}")
    print("-" * 40)
    print("TOP 5 ARCHIVOS MÁS PARECIDOS:")
    print(sospechosos[['archivo_a', 'archivo_b', 'similitud']].head(5).to_string(index=False))
    
    df.to_csv('reporte_ia_avanzado.csv', index=False)
    print("-" * 40)
    print(f"💾 Reporte generado: reporte_ia_avanzado.csv")
else:
    print("🤖 No se encontraron archivos similares significativos.")

print("="*40)
db.close()