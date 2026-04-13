import ollama

def get_embedding(text: str) -> list[float]:
    """
    Convierte un texto en un vector numérico usando Ollama.
    """
    # 1. Limpieza básica: Eliminar espacios extra que ensucian el embedding
    clean_text = text.strip()
    
    # 2. Control de longitud: nomic-embed-text tiene un límite (context window)
    # Si el texto es demasiado largo, lo truncamos para evitar errores de la API
    max_chars = 8000 
    if len(clean_text) > max_chars:
        clean_text = clean_text[:max_chars]

    try:
        response = ollama.embeddings(
            model='nomic-embed-text',
            prompt=clean_text
        )
        return response['embedding']
    except Exception as e:
        print(f"❌ Error al conectar con Ollama: {e}")
        return []