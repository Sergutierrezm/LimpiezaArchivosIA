import hashlib

def hash_file(path: str) -> str:
    h = hashlib.sha256()

    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)

    return h.hexdigest()




def find_exact_duplicates(files: list[dict]) -> list[list[dict]]:
    hash_map = {}

    for f in files:
        h = hash_file(f['path'])
        f['hash'] = h
        if h not in hash_map:
            hash_map[h] = []
        hash_map[h].append(f)

    duplicates = [group for group in hash_map.values() if len(group) > 1]

    return duplicates
