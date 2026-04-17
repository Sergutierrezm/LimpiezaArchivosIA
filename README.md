# 🔍 AI-Powered File Auditor & Cleaner

Una herramienta profesional de ingeniería de datos diseñada para auditar grandes volúmenes de archivos (6,000+) mediante **análisis semántico e identidad de bits**. Olvídate de los nombres de archivo; este sistema entiende el *contenido*.

## 🚀 Características Principales

* **Identidad de Bits (Hashing):** Detecta duplicados exactos al instante mediante SHA-256 sin importar el nombre del archivo.
* **Búsqueda Semántica (IA):** Utiliza **Ollama** para generar embeddings y encontrar archivos similares aunque el contenido haya sido parafraseado o modificado ligeramente.
* **Caché de Alto Rendimiento:** Implementa una arquitectura de doble base de datos:
    * **SQLite:** Persistencia a largo plazo de metadatos y vectores.
    * **ChromaDB:** Motor de búsqueda vectorial para comparaciones espaciales ultrarrápidas.
* **Interfaz Profesional:** Experiencia de usuario mejorada con **Rich**, incluyendo barras de progreso en tiempo real, paneles y tablas de resultados estilizadas.

## 🛠️ Stack Tecnológico

- **Language:** Python 3.10+
- **AI Engine:** Ollama (Nomic-Embed-Text)
- **Vector DB:** ChromaDB
- **Metadata DB:** SQLite
- **Data Analysis:** Pandas
- **UI/UX:** Rich
