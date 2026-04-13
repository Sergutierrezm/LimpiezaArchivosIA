from pathlib import Path


def scan_folder(path: str) -> list[dict]:
    files = []

    for file in Path(path).rglob('*'):
        if file.is_file():
            files.append({
                'path': str(file),
                'name': file.name,
                'ext':  file.suffix.lower(),
                'size': file.stat().st_size
            })

    return files



if __name__ == '__main__':
    resultado = scan_folder('/Users/sergiogutierrez/Downloads')  # pon una ruta real
    for f in resultado[:5]:  # muestra solo los 5 primeros
        print(f)