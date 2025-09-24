"""
Ce module gère toutes les routes liées aux données de santé de l'utilisateur.

Il inclut des fonctions pour :
- Lister les fichiers de logs de santé.
- Récupérer le contenu d'un fichier de santé spécifique.
- Sauvegarder de nouvelles données de santé.
- Récupérer la liste des exercices disponibles.
"""
import json
from urllib.parse import parse_qs
from config import SANTE_DIR, APP_WEB_DIR
from utils import send_json_error

def handle_sante_files(handler, context):
    """
    (GET /api/sante/files)
    Liste tous les fichiers de log de santé (sante_log_*.json) disponibles.

    Les fichiers sont triés par ordre antéchronologique pour afficher les plus récents en premier.
    """
    try:
        # Utilise glob pour trouver tous les fichiers correspondants et les trie
        files = sorted([f.name for f in SANTE_DIR.glob("sante_log_*.json")], reverse=True)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(files).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération des fichiers de santé: {e}")

def handle_sante_file(handler, context):
    """
    (GET /api/sante/file?name=...)
    Récupère et renvoie le contenu d'un fichier de log de santé spécifique.

    Le nom du fichier est passé en paramètre de la requête.
    """
    # Extrait le nom du fichier depuis les paramètres de l'URL
    parsed_path = parse_qs(handler.path.split('?', 1)[-1])
    filename = parsed_path.get('name', [None])[0]

    # Valide le nom du fichier pour des raisons de sécurité
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
        send_json_error(handler, 404, "Fichier de santé non trouvé.")

def handle_sante_save(handler, context):
    """
    (POST /api/sante/save)
    Sauvegarde les données de santé envoyées dans un nouveau fichier JSON.

    Le nom du fichier est généré à partir de la date fournie dans les données.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        # Crée un nom de fichier basé sur la date pour un archivage facile
        filename = f"sante_log_{data['date']}.json"
        if '..' in filename or filename.startswith('/'):
            send_json_error(handler, 400, "Nom de fichier invalide pour la sauvegarde.")
            return

        file_path = SANTE_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'status': 'ok', 'file': filename}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la sauvegarde du fichier de santé: {e}")

def handle_exercices(handler, context):
    """
    (GET /api/exercices)
    Récupère et renvoie la liste des exercices depuis le fichier exercices.json.

    Ce fichier est utilisé par le planificateur de notifications (ntfy_sender).
    """
    exercices_path = APP_WEB_DIR / "ntfy_sender" / "exercices.json"
    if exercices_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(exercices_path, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        print(f"ERREUR: Fichier d'exercices non trouvé à l'emplacement attendu : {exercices_path}")
        send_json_error(handler, 404, "Fichier exercices.json non trouvé sur le serveur.")