"""
Ce module centralise toute la configuration de l'application.

Il contient :
- La configuration du serveur (port, répertoire des fichiers statiques).
- Les clés d'API pour les services externes (Mistral AI).
- Les chemins d'accès importants (dossiers de données, logs, etc.).

L'utilisation de ce module permet de modifier facilement les paramètres
de l'application sans avoir à chercher les valeurs dans tout le code.
"""
import os
from pathlib import Path

# --- Configuration du Serveur ---
PORT = 8000
# Le serveur sert les fichiers depuis le répertoire parent ('site web/')
# pour que les chemins comme /app web/index.html fonctionnent.
DIRECTORY = ".."

# --- Configuration de l'API ---
# Récupère la clé API depuis une variable d'environnement pour plus de sécurité.
# Utilise une valeur par défaut si la variable n'est pas définie (pour le développement local).
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', 'czBBdZtL4WA8DF5FmkD3SUVDZrPBNM0u')

# --- Configuration des Chemins ---
# Utilise pathlib pour une gestion robuste des chemins, indépendante de l'OS.
# BASE_DIR est le dossier 'site web'
BASE_DIR = Path(__file__).resolve().parent.parent
# APP_WEB_DIR est le dossier 'app web' où se trouve ce fichier
APP_WEB_DIR = Path(__file__).resolve().parent

# Chemins vers les dossiers et fichiers de données
SANTE_DIR = BASE_DIR / "information" / "santé"
INFO_DIR = BASE_DIR / "information"
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
SCHEDULED_MESSAGES_PATH = APP_WEB_DIR / "ntfy_sender" / "scheduled_messages.json"
LORE_FILE_PATH = APP_WEB_DIR / "historique_objectifs" / "coach_engine_lore-chatgpt.md"
HISTOIRE_LOG_PATH = APP_WEB_DIR / "histoire_log.json"