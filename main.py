from core.scanner import scan_folder
from core.hasher import find_exact_duplicates, hash_file
from core.embedder import get_embedding
from core.database import DatabaseManager 
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# IMPORTACIÓN DEL NUEVO MÓDULO
from core.limpieza import mover_a_cuarentena

# LIBRERÍAS VISUALES
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

console = Console()

def procesar_archivo_ia(f, db_manager):
    try:
        file_hash = f.get('hash') or hash_file(f['path'])
        embedding = db_manager.get_embedding(file_hash)
        
        if embedding is None or (isinstance(embedding, list) and len(embedding) == 0):
            with open(f['path'], 'r', errors='ignore') as file:
                contenido = file.read(2500)
            
            if contenido.strip():
                embedding = get_embedding(contenido)
                if embedding:
                    db_manager.save_embedding(file_hash, f['path'], embedding, f['name'])
        
        if embedding and isinstance(embedding, list):
            db_manager.collection.upsert(
                ids=[file_hash],
                embeddings=[embedding],
                metadatas=[{"path": f['path'], "name": f['name'], "extension": Path(f['path']).suffix or "txt"}]
            )
            return {"hash": file_hash, "name": f['name']}
    except Exception:
        return None
    return None

# 1. Inicialización
db = DatabaseManager()
PATH_A_REVISAR = '/Users/sergiogutierrez/Downloads' # Ajusta tu ruta aquí

console.print(Panel.fit(
    f"[bold cyan]🚀 SISTEMA DE AUDITORÍA SEMÁNTICA[/bold cyan]\n[gray]Preparado para limpieza automática[/gray]",
    border_style="blue"
))

# 2. Escaneo
with console.status("[bold yellow]Escaneando archivos...", spinner="dots"):
    archivos = scan_folder(PATH_A_REVISAR)
    duplicados_exactos = find_exact_duplicates(archivos)

rprint(f"[green]✔[/green] Archivos detectados: [bold]{len(archivos)}[/bold]")

# 3. Preparación
interesantes = ['.java', '.py', '.txt', '.md']
candidatos_ia = [f for f in archivos if Path(f['path']).suffix in interesantes]

# 4. Fase de Indexación y Análisis CONCURRENTE
resultados_similitud = []

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None, pulse_style="cyan"),
    TaskProgressColumn(),
    console=console
) as progress:
    
    task_idx = progress.add_task("[cyan]Indexando vectores...", total=len(candidatos_ia))
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(procesar_archivo_ia, f, db) for f in candidatos_ia]
        for _ in as_completed(futures):
            progress.update(task_idx, advance=1)

    task_sim = progress.add_task("[magenta]Analizando similitudes...", total=len(candidatos_ia))
    for f in candidatos_ia:
        f_hash = f.get('hash') or hash_file(f['path'])
        emb = db.get_embedding(f_hash)
        
        if emb and len(emb) > 0:
            busqueda = db.collection.query(query_embeddings=[emb], n_results=2, include=['metadatas', 'distances'])
            
            if len(busqueda['ids'][0]) > 1:
                id_vecino = busqueda['ids'][0][1]
                if f_hash < id_vecino: 
                    distancia = busqueda['distances'][0][1]
                    similitud = round((1 - distancia) * 100, 2)
                    
                    if similitud > 85:
                        meta_vecino = busqueda['metadatas'][0][1]
                        resultados_similitud.append({
                            'archivo_a': f['name'],
                            'ruta_a': f['path'], # <--- GUARDAMOS RUTA PARA LIMPIAR
                            'archivo_b': meta_vecino.get('name', 'Desconocido'),
                            'ruta_b': meta_vecino.get('path'),
                            'similitud': similitud
                        })
        progress.update(task_sim, advance=1)

# 6. Reporte Final y Acción de Limpieza
console.print("\n[bold green]✅ ANÁLISIS COMPLETADO[/bold green]")

if resultados_similitud:
    df = pd.DataFrame(resultados_similitud)
    sospechosos = df[df['similitud'] > 90].sort_values(by='similitud', ascending=False)
    
    table = Table(title="[bold magenta]Top Archivos Similares[/bold magenta]", header_style="bold cyan")
    table.add_column("Archivo Principal", style="white")
    table.add_column("Posible Duplicado", style="yellow")
    table.add_column("% Similitud", justify="right", style="bold green")

    for _, row in sospechosos.head(10).iterrows():
        table.add_row(row['archivo_a'], row['archivo_b'], f"{row['similitud']}%")
    
    console.print(table)

    # --- LÓGICA DE LIMPIEZA FINAL ---
    a_limpiar = [r['ruta_a'] for r in resultados_similitud if r['similitud'] > 95]

    if a_limpiar:
        console.print(f"\n[bold red]⚠️ Se han detectado {len(a_limpiar)} archivos con >95% de similitud.[/bold red]")
        opcion = console.input("[bold white]¿Mover estos archivos a CUARENTENA? (s/n): [/bold white]")
        
        if opcion.lower() == 's':
            with console.status("[bold red]Vaciando escritorio...", spinner="dots"):
                total = mover_a_cuarentena(a_limpiar)
            console.print(f"[bold green]✔ {total} archivos movidos correctamente. Revisa la carpeta 'CUARENTENA_IA'.[/bold green]")
        else:
            console.print("[blue]Operación cancelada. No se han movido archivos.[/blue]")
else:
    console.print("[yellow]🤖 No se encontraron duplicados semánticos significativos.[/yellow]")

db.close()