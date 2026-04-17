from core.scanner import scan_folder
from core.hasher import find_exact_duplicates, hash_file
from core.embedder import get_embedding
from core.database import DatabaseManager 
from pathlib import Path
import pandas as pd

#NUEVAS LIBRERÍAS PARA LA MEJORA VISUAL
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

console = Console()

# 1. Inicialización con Panel
db = DatabaseManager()
PATH_A_REVISAR = '/Users/sergiogutierrez/Downloads'

console.print(Panel.fit(
    f"[bold cyan]🚀 SISTEMA DE AUDITORÍA SEMÁNTICA[/bold cyan]\n[gray]Ruta objetivo: {PATH_A_REVISAR}[/gray]",
    border_style="blue"
))

# 2. Escaneo y Duplicados con Status (Spinner)
with console.status("[bold yellow]Escaneando archivos y verificando duplicados exactos...", spinner="dots"):
    archivos = scan_folder(PATH_A_REVISAR)
    duplicados_exactos = find_exact_duplicates(archivos)

rprint(f"[green]✔[/green] Archivos detectados: [bold]{len(archivos)}[/bold]")
rprint(f"[green]✔[/green] Duplicados exactos: [bold]{len(duplicados_exactos)}[/bold]")

# 3. Preparación de Candidatos
interesantes = ['.java', '.py', '.txt', '.md']
candidatos_ia = [f for f in archivos if Path(f['path']).suffix in interesantes]
rprint(f"[green]✔[/green] Candidatos para análisis IA: [bold]{len(candidatos_ia)}[/bold]")

# 4. Fase de Indexación y Análisis con BARRAS DE PROGRESO
resultados_similitud = []

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None, pulse_style="cyan"),
    TaskProgressColumn(),
    console=console
) as progress:
    
    # Tarea 1: Alimentar Base de Datos
    task_idx = progress.add_task("[cyan]Verificando e indexando vectores...", total=len(candidatos_ia))
    
    for f in candidatos_ia:
        file_hash = f.get('hash') or hash_file(f['path'])
        embedding = db.get_embedding(file_hash)
        
        if embedding is None or (isinstance(embedding, list) and len(embedding) == 0):
            try:
                with open(f['path'], 'r', errors='ignore') as file:
                    contenido = file.read(2500)
                
                if contenido.strip():
                    embedding = get_embedding(contenido)
                    if embedding and len(embedding) > 0:
                        db.save_embedding(file_hash, f['path'], embedding, f['name'])
            except Exception:
                continue
        else:
            if isinstance(embedding, list) and len(embedding) > 0:
                db.collection.upsert(
                    ids=[file_hash],
                    embeddings=[embedding],
                    metadatas=[{"path": f['path'], "name": f['name'], "extension": Path(f['path']).suffix or "txt"}]
                )
        progress.update(task_idx, advance=1)

    # Tarea 2: Búsqueda Semántica
    task_sim = progress.add_task("[magenta]Analizando similitudes semánticas...", total=len(candidatos_ia))
    
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
                        meta = busqueda['metadatas'][0][1]
                        resultados_similitud.append({
                            'archivo_a': f['name'],
                            'archivo_b': meta.get('name', 'Desconocido'),
                            'similitud': similitud
                        })
        progress.update(task_sim, advance=1)

# 6. Reporte Final con Tabla Rich
console.print("\n[bold green]✅ ANÁLISIS COMPLETADO[/bold green]")

if resultados_similitud:
    df = pd.DataFrame(resultados_similitud)
    sospechosos = df[df['similitud'] > 90].sort_values(by='similitud', ascending=False)
    
    # Crear Tabla Visual
    table = Table(title="[bold magenta]Top Archivos Similares Encontrados[/bold magenta]", header_style="bold cyan")
    table.add_column("Archivo Principal", style="white")
    table.add_column("Posible Duplicado", style="yellow")
    table.add_column("% Similitud", justify="right", style="bold green")

    for _, row in sospechosos.head(10).iterrows():
        table.add_row(row['archivo_a'], row['archivo_b'], f"{row['similitud']}%")
    
    console.print(table)
    
    df.to_csv('reporte_ia_avanzado.csv', index=False)
    console.print(f"\n[bold blue]💾 Reporte CSV generado satisfactoriamente.[/bold blue]")
else:
    console.print("[yellow]🤖 No se encontraron similitudes significativas.[/yellow]")

db.close()