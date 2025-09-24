# Configuration for the server
import os
from pathlib import Path

# --- Server Configuration ---
PORT = 8000
DIRECTORY = ".."

# --- API Configuration ---
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

# --- Path Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
SANTE_DIR = BASE_DIR / "information" / "santé"
APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
INFO_DIR = BASE_DIR / "information"
SCHEDULED_MESSAGES_PATH = APP_WEB_DIR / "ntfy_sender" / "scheduled_messages.json"
LORE_FILE_PATH = APP_WEB_DIR / "historique_objectifs" / "coach_engine_lore-chatgpt.md"
HISTOIRE_LOG_PATH = APP_WEB_DIR / "histoire_log.json"
