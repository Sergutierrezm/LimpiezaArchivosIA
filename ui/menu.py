# ui/menu.py
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import pandas as pd

class MenuPrincipal:
    def __init__(self, engine):
        self.engine = engine
        self.console = Console()

    def mostrar_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.console.print(Panel.fit(
            "[bold cyan]🚀 AI AUDITOR MANAGER[/bold cyan]\n"
            "[dim]Gestión de Archivos con Inteligencia Semántica[/dim]",
            border_style="blue"
        ))

    def lanzar_organizacion(self):
        """Módulo de clasificación rápida por extensiones (Paso 0 de limpieza)"""
        ruta = Prompt.ask("\n📁 Ruta a organizar por extensiones", default="/Users/sergiogutierrez/Downloads")
        
        if not os.path.exists(ruta):
            self.console.print("[red]❌ La ruta no existe.[/red]")
            return

        # Reutilizamos tu mismo componente de progreso visual
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task_org = progress.add_task("[yellow]Clasificando archivos por extensión...", total=None)
            
            # Llamamos al método puente que creamos en el Paso 2 en el AuditorEngine
            resumen = self.engine.ejecutar_clasificacion_rapida(ruta)
            
            progress.update(task_org, completed=100, description="[green]Clasificación completada")

        # Construimos una tabla estilizada con Rich para mostrar el resultado del movimiento
        tabla = Table(title=f"\n[bold green]Reporte de Organización en:[/] {os.path.basename(ruta)}")
        tabla.add_column("Carpeta Destino", style="cyan", justify="left")
        tabla.add_column("Archivos Movidos", style="magenta", justify="right")
        
        archivos_movidos = False
        for carpeta, total in resumen.items():
            if total > 0:
                tabla.add_row(carpeta, str(total))
                archivos_movidos = True
        
        if archivos_movidos:
            self.console.print(tabla)
        else:
            self.console.print("\n[yellow]⚠️ No se encontraron archivos nuevos sueltos para clasificar en esta ruta.[/yellow]")

    def lanzar_auditoria(self):
        ruta = Prompt.ask("\n📂 Ruta a analizar semánticamente", default="/Users/sergiogutierrez/Downloads")
        
        if not os.path.exists(ruta):
            self.console.print("[red]❌ La ruta no existe.[/red]")
            return

        # Aquí usamos la lógica de progreso que tenías antes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            # 1. Escaneo (llamando al engine)
            task_scan = progress.add_task("[yellow]Escaneando carpeta...", total=None)
            archivos, candidatos = self.engine.preparar_candidatos(ruta)
            progress.update(task_scan, completed=100, description="[green]Escaneo completado")

            # 2. Indexación IA
            task_idx = progress.add_task("[cyan]Indexando vectores...", total=len(candidatos))
            # Aquí el engine procesa, y nosotros actualizamos la barra
            for f in candidatos:
                self.engine.procesar_archivo_ia(f)
                progress.update(task_idx, advance=1)

            # 3. Análisis de similitud
            task_sim = progress.add_task("[magenta]Analizando similitudes...", total=len(candidatos))
            resultados = self.engine.comparar_similitudes(candidatos)
            progress.update(task_sim, completed=len(candidatos))

        # Mostramos resultados
        self.mostrar_resultados(resultados)

    def mostrar_resultados(self, resultados):
        if not resultados:
            self.console.print("[yellow]🤖 No se encontraron duplicados significativos.[/yellow]")
            return

        table = Table(title="Top Archivos Similares", header_style="bold cyan")
        table.add_column("Archivo A", style="white")
        table.add_column("Archivo B", style="yellow")
        table.add_column("% Similitud", justify="right", style="bold green")

        for r in resultados[:10]: # Top 10
            table.add_row(r['archivo_a'], r['archivo_b'], f"{r['similitud']}%")
        
        self.console.print(table)

    def run(self):
        """Bucle principal de la interfaz con la suite de herramientas completa"""
        while True:
            self.mostrar_header()
            self.console.print("1. 📁 Clasificación Rápida (Mover a carpetas por Extensión)")
            self.console.print("2. 🔍 Auditoría Semántica e Indexación (Ollama IA)")
            self.console.print("3. 📜 Ver Logs")
            self.console.print("4. 🚪 Salir")
            
            opcion = Prompt.ask("\nSelecciona", choices=["1", "2", "3", "4"])

            if opcion == "1":
                self.lanzar_organizacion()
                input("\nPresiona Enter para volver...")
            elif opcion == "2":
                self.lanzar_auditoria()
                input("\nPresiona Enter para volver...")
            elif opcion == "3":
                self.console.print("[yellow]Funcionalidad de logs en desarrollo...[/yellow]")
                input("\nPresiona Enter para volver...")
            elif opcion == "4":
                self.console.print("[bold red]Saliendo del sistema... ¡Buen día![/]")
                break