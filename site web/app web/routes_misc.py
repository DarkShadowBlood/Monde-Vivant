import json
import re
import markdown
from urllib.parse import parse_qs

from config import APP_WEB_DIR, INFO_DIR, HISTOIRE_LOG_PATH
from lore import COACH_LORE
from utils import append_to_histoire_log, send_json_error

def handle_get_request_templates(handler):
    request_templates_path = APP_WEB_DIR / "ntfy_sender" / "request_templates.json"
    if request_templates_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(request_templates_path, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        print(f"AVERTISSEMENT: Fichier non trouvé à l'emplacement attendu : {request_templates_path}")
        # Renvoyer un objet vide si le fichier n'existe pas pour éviter de casser le client
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(b'{}')

def handle_get_coaches(handler):
    try:
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(list(COACH_LORE.keys())).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération des coachs: {e}")

def handle_get_histoire(handler):
    if HISTOIRE_LOG_PATH.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(HISTOIRE_LOG_PATH, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(b'[]') # Renvoyer une liste vide si le fichier n'existe pas

def handle_get_aggregate_data(handler):
    parsed_path = parse_qs(handler.path.split('?', 1)[-1])
    start_date = parsed_path.get('start', [None])[0]
    end_date = parsed_path.get('end', [None])[0]

    if not start_date or not end_date:
        send_json_error(handler, 400, "Les paramètres 'start' et 'end' sont requis.")
        return
    
    aggregated_data = {}
    data_files = {
        "activities": "activities.json",
        "goals": "objectifs.json",
        "health": "sante.json"
    }

    for key, filename in data_files.items():
        file_path = APP_WEB_DIR / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Filtrer les données par date
                filtered = [
                    item for item in data 
                    if 'date' in item and start_date <= item['date'] <= end_date
                ]
                aggregated_data[key] = filtered
            except (json.JSONDecodeError, IOError) as e:
                print(f"Avertissement: Impossible de lire ou parser {filename}: {e}")
                aggregated_data[key] = []
        else:
            aggregated_data[key] = []
    
    handler.send_response(200)
    handler.send_header('Content-type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps(aggregated_data).encode('utf-8'))

def handle_post_save_file(handler):
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)

    relative_path = data.get('path')
    content = data.get('content')

    if not relative_path or '..' in relative_path or relative_path.startswith('/'):
        send_json_error(handler, 400, "Chemin de fichier invalide.")
        return

    file_path = INFO_DIR / relative_path
    try:
        # S'assurer que le dossier parent existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            # Si le contenu est un dictionnaire (reçu comme JSON), on le formate joliment.
            if isinstance(content, dict):
                json.dump(content, f, indent=2, ensure_ascii=False)
            else: # Sinon, on l'écrit comme une chaîne de caractères.
                f.write(str(content))
        
        # Logique spécifique pour le journal de l'histoire
        if relative_path.startswith('plans_entrainement/') and 'préparation' not in relative_path:
            # Le coach est hardcodé "Aegis" dans le prompt de plan_entrainement.html
            append_to_histoire_log("Générateur de Plan d'Entraînement", "Aegis", content)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        # Renvoyer un chemin relatif utilisable par le client
        relative_url = '/information/' + relative_path.replace('\\', '/')
        handler.wfile.write(json.dumps({'success': True, 'path': str(file_path), 'url': relative_url}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la sauvegarde du fichier : {e}")

def handle_post_inject_analysis(handler):
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)

    html_relative_path = data.get('html_path')
    # On attend maintenant une liste d'analyses
    analyses = data.get('analyses')

    if not html_relative_path or '..' in html_relative_path or not html_relative_path.endswith('.html'):
        send_json_error(handler, 400, "Chemin de fichier HTML invalide.")
        return
    
    if not isinstance(analyses, list):
        send_json_error(handler, 400, "Le champ 'analyses' doit être une liste.")
        return

    # Le chemin est relatif à /information/, donc on le reconstruit
    html_file_path = INFO_DIR / html_relative_path

    if not html_file_path.exists():
        send_json_error(handler, 404, f"Fichier HTML non trouvé : {html_file_path}")
        return

    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            modified_html = f.read()

        # Boucle sur chaque analyse à injecter
        for analysis in analyses:
            analysis_key = analysis.get('key')
            analysis_content = analysis.get('content')
            if analysis_key and analysis_content is not None:
                # Utilisation de json.dumps() pour un échappement robuste et standard du contenu.
                analysis_escaped = json.dumps(analysis_content)
                # Utilise une regex pour trouver la clé suivie de : null ou : ""
                target_pattern = re.compile(rf'"{analysis_key}":\s*(?:null|"")')

                # Log de l'analyse dans le journal de l'histoire
                append_to_histoire_log("Analyse d'Activité", analysis_key, analysis_content)

                # Utilisation d'une fonction lambda pour le remplacement afin d'éviter l'interprétation des backslashes.
                modified_html = target_pattern.sub(lambda m: f'"{analysis_key}": {analysis_escaped}', modified_html, 1)

        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_html)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        # Renvoyer l'URL du fichier modifié pour que le client puisse l'ouvrir
        relative_url = '/information/' + html_relative_path.replace('\\', '/')
        handler.wfile.write(json.dumps({'success': True, 'url': relative_url}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de l'injection de l'analyse : {e}")

def handle_post_process_analyses(handler):
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)
    
    activity_dir_path = data.get('activity_dir')
    if not activity_dir_path or '..' in activity_dir_path:
        send_json_error(handler, 400, "Chemin de dossier d'activité invalide.")
        return

    # Le chemin est relatif à /information/, donc on le reconstruit
    analysis_folder = INFO_DIR / activity_dir_path / "analysis"

    if not analysis_folder.exists() or not analysis_folder.is_dir():
        send_json_error(handler, 404, f"Dossier d'analyse non trouvé : {analysis_folder}")
        return

    try:
        processed_files = []
        # Trouve tous les fichiers JSON d'analyse
        for json_file in analysis_folder.glob("*_analysis_*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            markdown_content = analysis_data.get("analysis_markdown", "")
            base_name = json_file.stem

            # 1. Créer le fichier .md
            md_path = analysis_folder / f"{base_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            processed_files.append(md_path.name)

            # 2. Créer le fichier .html
            html_path = analysis_folder / f"{base_name}.html"
            html_content = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
            
            # Ajouter un style simple pour la lisibilité
            html_template = rf'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Analyse: {base_name}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; background-color: #f4f4f4; color: #333; }}
        h1, h2, h3 {{ color: #005a9c; }}
        code {{ background-color: #eee; padding: 2px 4px; border-radius: 4px; }}
        pre {{ background-color: #eee; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ccc; padding-left: 10px; color: #666; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            processed_files.append(html_path.name)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': f"{len(processed_files)} fichiers traités.", 'files': processed_files}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors du traitement des analyses : {e}")
