import sys
import os

# --- ATTENZIONE: MODIFICA QUESTO PERCORSO ---
# Imposta il percorso corretto della cartella del tuo progetto su PythonAnywhere
# Sarà qualcosa come '/home/TuoNomeUtente/ZRL_MANAGER_V2.0'
path = '/home/robario/ZRL-Manager'
if path not in sys.path:
    sys.path.insert(0, path)

# Importa l'applicazione Flask
from run import app as application
