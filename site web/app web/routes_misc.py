"""
Ce module regroupe diverses routes qui ne rentrent pas dans les autres catégories.

Fonctionnalités :
- Récupérer des modèles de requêtes.
- Lister les coachs disponibles.
- Consulter l'historique des interactions.
- Agréger des données sur une période donnée.
- Sauvegarder des fichiers génériques.
- Injecter des analyses générées par l'IA dans des fichiers HTML.
- Traiter des fichiers d'analyse JSON pour les convertir en Markdown et HTML.
"""
import json
import re
import markdown
from urllib.parse import parse_qs

from config import APP_WEB_DIR, INFO_DIR, HISTOIRE_LOG_PATH
from utils import append_to_histoire_log, send_json_error
import lore

def handle_get_request_templates(handler, context):
    """
    (GET /api/request-templates)
    Récupère les modèles de requêtes pour le générateur de notifications.
    """
    request_templates_path = APP_WEB_DIR / "ntfy_sender" / "request_templates.json"
    if request_templates_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(request_templates_path, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        print(f"AVERTISSEMENT: Fichier de modèles de requêtes non trouvé: {request_templates_path}")
        # Renvoyer un objet vide pour éviter de casser le client
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(b'{}')

def handle_get_coaches(handler, context):
    """
    (GET /api/coaches)
    Liste les noms de tous les coachs disponibles chargés depuis le fichier de lore.
    """
    try:
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(list(context.coach_lore.keys())).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération des coachs: {e}")

def handle_get_histoire(handler, context):
    """
    (GET /api/histoire)
    Récupère le journal complet de l'histoire (interactions, notifications, etc.).
    """
    if HISTOIRE_LOG_PATH.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(HISTOIRE_LOG_PATH, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        # Si le fichier n'existe pas, renvoyer une liste vide
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(b'[]')

def handle_get_aggregate_data(handler, context):
    """
    (GET /api/aggregateData?start=...&end=...)
    Agrège les données (activités, objectifs, santé) sur une période donnée.
    """
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
                # Filtre les entrées pour ne garder que celles dans la plage de dates
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

def handle_post_save_file(handler, context):
    """
    (POST /api/saveFile)
    Sauvegarde un contenu générique dans un fichier.

    Attend un JSON avec 'path' (chemin relatif) et 'content'.
    Utilisé notamment pour sauvegarder les plans d'entraînement générés.
    """
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
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(content))
        
        # Logique spécifique pour les plans d'entraînement
        if relative_path.startswith('plans_entrainement/') and 'préparation' not in relative_path:
            append_to_histoire_log("Générateur de Plan d'Entraînement", "Aegis", content)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        relative_url = '/information/' + relative_path.replace('\\', '/')
        handler.wfile.write(json.dumps({'success': True, 'path': str(file_path), 'url': relative_url}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la sauvegarde du fichier : {e}")

def handle_post_inject_analysis(handler, context):
    """
    (POST /api/injectAnalysis)
    Injecte le contenu d'une analyse générée par l'IA dans un fichier HTML.

    Attend un JSON avec 'html_path' et une liste d''analyses' [{ 'key': ..., 'content': ...}].
    Recherche des clés spécifiques dans le HTML et remplace les valeurs `null` par le contenu fourni.
    """
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)

    html_relative_path = data.get('html_path')
    analyses = data.get('analyses')

    if not html_relative_path or '..' in html_relative_path or not html_relative_path.endswith('.html'):
        send_json_error(handler, 400, "Chemin de fichier HTML invalide.")
        return
    if not isinstance(analyses, list):
        send_json_error(handler, 400, "Le champ 'analyses' doit être une liste.")
        return

    html_file_path = INFO_DIR / html_relative_path
    if not html_file_path.exists():
        send_json_error(handler, 404, f"Fichier HTML non trouvé : {html_file_path}")
        return

    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            modified_html = f.read()

        for analysis in analyses:
            key = analysis.get('key')
            content = analysis.get('content')
            if key and content is not None:
                # Échappe le contenu pour l'injection et cible la clé suivie de 'null' ou '""'
                escaped_content = json.dumps(content)
                target_pattern = re.compile(rf'"{key}":\s*(?:null|"")')

                append_to_histoire_log("Analyse d'Activité", key, content)
                modified_html = target_pattern.sub(lambda m: f'"{key}": {escaped_content}', modified_html, 1)

        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_html)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        relative_url = '/information/' + html_relative_path.replace('\\', '/')
        handler.wfile.write(json.dumps({'success': True, 'url': relative_url}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de l'injection de l'analyse : {e}")

def handle_post_process_analyses(handler, context):
    """
    (POST /api/processAnalyses)
    Traite les fichiers JSON d'analyse pour générer des versions Markdown et HTML.

    Attend un JSON avec 'activity_dir' (chemin du dossier de l'activité).
    Cherche les fichiers *_analysis_*.json, en extrait le contenu Markdown, et
    crée des fichiers .md et .html correspondants.
    """
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = json.loads(post_data)
    
    activity_dir_path = data.get('activity_dir')
    if not activity_dir_path or '..' in activity_dir_path:
        send_json_error(handler, 400, "Chemin de dossier d'activité invalide.")
        return

    analysis_folder = INFO_DIR / activity_dir_path / "analysis"
    if not analysis_folder.exists() or not analysis_folder.is_dir():
        send_json_error(handler, 404, f"Dossier d'analyse non trouvé : {analysis_folder}")
        return

    try:
        processed_files = []
        for json_file in analysis_folder.glob("*_analysis_*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            markdown_content = analysis_data.get("analysis_markdown", "")
            base_name = json_file.stem

            # Crée un fichier .md
            md_path = analysis_folder / f"{base_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            processed_files.append(md_path.name)

            # Crée un fichier .html à partir du Markdown
            html_content = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
            html_path = analysis_folder / f"{base_name}.html"
            html_template = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Analyse: {base_name}</title>
<style>body{{font-family:sans-serif;line-height:1.6;padding:20px;max-width:800px;margin:auto;background-color:#f4f4f4;color:#333}}h1,h2,h3{{color:#005a9c}}code{{background-color:#eee;padding:2px 4px;border-radius:4px}}pre{{background-color:#eee;padding:10px;border-radius:4px;overflow-x:auto}}</style>
</head><body>{html_content}</body></html>"""
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            processed_files.append(html_path.name)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': f"{len(processed_files)} fichiers traités.", 'files': processed_files}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors du traitement des analyses : {e}")