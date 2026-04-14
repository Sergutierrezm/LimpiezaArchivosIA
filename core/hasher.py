import hashlib

def hash_file(path: str) -> str:
    # Usamos MD5 para la DB por ser más corto/rápido, 
    # pero SHA-256 está perfecto si prefieres máxima seguridad
    h = hashlib.md5() 
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def find_exact_duplicates(files: list[dict]) -> list[list[dict]]:
    # 1. Agrupar por tamaño primero (esto es instantáneo)
    size_map = {}
    for f in files:
        size = f['size']
        if size not in size_map: size_map[size] = []
        size_map[size].append(f)

    # 2. Solo calculamos Hash para los que tienen el mismo tamaño
    hash_map = {}
    for size, candidates in size_map.items():
        if len(candidates) > 1:
            for f in candidates:
                h = hash_file(f['path'])
                f['hash'] = h # Guardamos el hash en el dict para la DB
                if h not in hash_map: hash_map[h] = []
                hash_map[h].append(f)
        else:
            # Archivos únicos: les ponemos hash vacío o calculamos si lo quieres en DB
            candidates[0]['hash'] = None 

    duplicates = [group for group in hash_map.values() if len(group) > 1]
    return duplicates
