# Configuration for the server
import os
from pathlib import Path

# --- Server Configuration ---
PORT = 8000
DIRECTORY = ".."

# --- API Configuration ---
# Récupère la clé API depuis une variable d'environnement nommée 'MISTRAL_API_KEY'.
# Si elle n'est pas trouvée, utilise la valeur codée en dur comme solution de repli.
# ATTENTION: Il est déconseillé de stocker des clés API directement dans le code pour des raisons de sécurité.
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', 'czBBdZtL4WA8DF5FmkD3SUVDZrPBNM0u')

# --- Path Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
SANTE_DIR = BASE_DIR / "information" / "santé"
APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
INFO_DIR = BASE_DIR / "information"
SCHEDULED_MESSAGES_PATH = APP_WEB_DIR / "ntfy_sender" / "scheduled_messages.json"
LORE_FILE_PATH = APP_WEB_DIR / "historique_objectifs" / "coach_engine_lore-chatgpt.md"
HISTOIRE_LOG_PATH = APP_WEB_DIR / "histoire_log.json"
