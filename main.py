# main.py
from core.database import DatabaseManager
from core.auditor import AuditorEngine
from ui.menu import MenuPrincipal

def main():
    db = DatabaseManager()
    
    # IMPORTANTE: Asegúrate de que AuditorEngine en core/auditor.py 
    # tenga los métodos que el menú necesita.
    engine = AuditorEngine(db) 
    
    interface = MenuPrincipal(engine)
    
    try:
        interface.run() # <--- ¡Ahora este método sí existe!
    finally:
        db.close()

if __name__ == "__main__":
    main()