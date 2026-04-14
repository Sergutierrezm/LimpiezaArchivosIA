from pathlib import Path

def scan_folder(path: str) -> list[dict]:
    files = []
    # Usamos Path(path).resolve() para rutas absolutas limpias
    for file in Path(path).rglob('*'):
        # Saltamos archivos ocultos de sistema (.DS_Store, etc)
        if file.is_file() and not file.name.startswith('.'):
            try:
                files.append({
                    'path': str(file.resolve()),
                    'name': file.name,
                    'ext':  file.suffix.lower(),
                    'size': file.stat().st_size
                })
            except Exception as e:
                print(f"⚠️ Error accediendo a {file}: {e}")

    return files