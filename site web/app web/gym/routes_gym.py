import json
from urllib.parse import parse_qs, urlparse

from config import APP_WEB_DIR
from utils import send_json_error

GYM_DB_PATH = APP_WEB_DIR / "gym" / "exercices_db.json"

def _load_gym_db():
    """Charge la base de données des exercices depuis le fichier JSON."""
    if not GYM_DB_PATH.exists():
        return None
    with open(GYM_DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def handle_get_muscle_groups(handler, context):
    """Renvoie la liste de tous les groupes musculaires."""
    try:
        db = _load_gym_db()
        if db is None:
            send_json_error(handler, 404, "La base de données d'exercices (exercices_db.json) est introuvable.")
            return
        
        groups = list(db.keys())
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': groups}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors du chargement des groupes musculaires: {e}")

def handle_get_exercises_by_group(handler, context):
    """Renvoie la liste des exercices pour un groupe musculaire donné."""
    try:
        query_components = parse_qs(urlparse(handler.path).query)
        group_name = query_components.get('group', [None])[0]

        if not group_name:
            send_json_error(handler, 400, "Le paramètre 'group' est manquant.")
            return

        db = _load_gym_db()
        if db is None:
            send_json_error(handler, 404, "La base de données d'exercices (exercices_db.json) est introuvable.")
            return

        exercises = db.get(group_name, [])
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': exercises}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors du chargement des exercices pour le groupe '{group_name}': {e}")