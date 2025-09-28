import json
from urllib.parse import parse_qs
from config import SANTE_DIR, APP_WEB_DIR
from utils import send_json_error

def handle_sante_files(handler, context):
    """Liste tous les fichiers de log de santé disponibles."""
    try:
        files = sorted([f.name for f in SANTE_DIR.glob("sante_log_*.json")], reverse=True)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(files).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur: {e}")

def handle_sante_file(handler, context):
    """Sert le contenu d'un fichier de log de santé spécifique."""
    parsed_path = parse_qs(handler.path.split('?', 1)[-1])
    filename = parsed_path.get('name', [None])[0]
    if not filename or '..' in filename or filename.startswith('/'):
        send_json_error(handler, 400, "Nom de fichier invalide.")
        return
    
    file_path = SANTE_DIR / filename
    if file_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(file_path, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        send_json_error(handler, 404, "Fichier non trouvé.")

def handle_sante_save(handler, context):
    """Sauvegarde les données de santé pour une date donnée dans un fichier JSON."""
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)

    filename = f"sante_log_{data['date']}.json"
    if '..' in filename or filename.startswith('/'):
        send_json_error(handler, 400, "Nom de fichier invalide pour la sauvegarde.")
        return

    file_path = SANTE_DIR / filename
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'status': 'ok', 'file': filename}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la sauvegarde du fichier: {e}")

def handle_exercices(handler, context):
    """Sert le fichier JSON contenant la liste des exercices."""
    # Le fichier est dans app web/ntfy_sender/exercices.json
    exercices_path = APP_WEB_DIR / "ntfy_sender" / "exercices.json"
    if exercices_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(exercices_path, 'rb') as f:
            data = json.load(f)
            handler.wfile.write(json.dumps({'success': True, 'data': data}).encode('utf-8'))
    else:
        print(f"ERREUR: Fichier non trouvé à l'emplacement attendu : {exercices_path}")
        send_json_error(handler, 404, "Fichier exercices.json non trouvé sur le serveur.")
