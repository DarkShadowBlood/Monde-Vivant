import http.server
import socketserver
import os
import subprocess
import requests
import json
import markdown
import csv
import time
import re
import random
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import datetime


# --- Configuration ---
PORT = 8000
# Le serveur servira les fichiers du répertoire où le script est exécuté.
# Assurez-vous que ce script est dans votre dossier 'site web'.
DIRECTORY = ".."

# --- Configuration API ---
# Remplacez "YOUR_MISTRAL_API_KEY_HERE" par votre clé ou utilisez une variable d'environnement
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', "czBBdZtL4WA8DF5FmkD3SUVDZrPBNM0u")

# Chemin absolu vers le dossier 'santé'
# C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\information\santé
BASE_DIR = Path(__file__).resolve().parent.parent
SANTE_DIR = BASE_DIR / "information" / "santé"
APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
INFO_DIR = BASE_DIR / "information"
SCHEDULED_MESSAGES_PATH = APP_WEB_DIR / "ntfy_sender" / "scheduled_messages.json"
LORE_FILE_PATH = APP_WEB_DIR / "historique_objectifs" / "coach_engine_lore-chatgpt.md"
HISTOIRE_LOG_PATH = APP_WEB_DIR / "histoire_log.json"

# S'assurer que les dossiers existent
SANTE_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_json_error(self, code, message):
        """Envoie une réponse d'erreur standardisée au format JSON."""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = {'success': False, 'error': message}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def _append_to_histoire_log(self, source, coach, message):
        """Ajoute une nouvelle entrée au fichier journal de l'histoire."""
        now = datetime.datetime.now()
        log_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "source": source,
            "coach": coach,
            "message": message
        }
        
        log_data = []
        if HISTOIRE_LOG_PATH.exists():
            with open(HISTOIRE_LOG_PATH, 'r', encoding='utf-8') as f:
                try: log_data = json.load(f)
                except json.JSONDecodeError: log_data = []
        
        log_data.insert(0, log_entry) # Ajoute au début pour avoir le plus récent en premier
        
        with open(HISTOIRE_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    def _generate_llm_message(self, coach_name, prompt_context, system_prompt_override=None):
        """Helper function to generate a message from the LLM API."""
        if MISTRAL_API_KEY == "YOUR_MISTRAL_API_KEY_HERE":
            return f"({coach_name}) Clé API non configurée.", False

        if system_prompt_override:
            system_prompt = system_prompt_override
            user_prompt = prompt_context
        else:
            coach_lore = COACH_LORE.get(coach_name, f"Tu es un coach virtuel nommé {coach_name}.")
            system_prompt = f"{coach_lore}\n\nTu dois répondre à la demande de l'utilisateur de manière concise et percutante pour une notification dans une app. Le message doit être court, direct et parfaitement dans le ton du personnage. Ne mets pas de guillemets autour de ta réponse."
            user_prompt = f"Génère une notification pour la situation suivante : '{prompt_context}'."
        
        try:
            api_response = requests.post(
                'https://api.mistral.ai/v1/chat/completions',
                headers={'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'},
                json={ # Ajout du format de réponse JSON pour plus de fiabilité
                    'model': 'mistral-large-latest',
                    'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                    'response_format': {'type': 'json_object'}
                },
                timeout=30,
                verify=False # Attention: à utiliser seulement en développement local
            )
            api_response.raise_for_status()
            api_data = api_response.json()
            return api_data['choices'][0]['message']['content'].strip(), True
        except requests.exceptions.RequestException as e:
            print(f"Erreur API Mistral pour notification. Type: {type(e).__name__}, Détails: {e}")
            return f"({coach_name}) Erreur de connexion à l'API. Vérifiez la console du serveur.", False

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Ignorer poliment les requêtes pour le favicon
        if parsed_path.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if parsed_path.path == '/api/notifications':
            try:
                notifications = []
                today_str = datetime.datetime.now().date().isoformat()

                # --- Load Configs ---
                config_path = APP_WEB_DIR / "notifications_config.json"
                cache_path = APP_WEB_DIR / "notifications_cache.json"
                
                config = {}
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                cache = {}
                if cache_path.exists():
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        try:
                            cache = json.load(f)
                        except json.JSONDecodeError:
                            cache = {} # Reset cache if it's corrupted

                # --- Logique de notification simplifiée ---
                # Le GET se contente de lire le cache. La génération se fait dans le POST.
                
                notification_types = ["objectifs", "glycemie", "poids", "ventre"]
                for notif_key in notification_types:
                    # Vérifier si une notification est en cache pour aujourd'hui
                    if cache.get(notif_key, {}).get("date") == today_str:
                        notifications.append(cache[notif_key]["notification"])

                # Si aucune notification n'est en cache, afficher un message générique
                if not notifications and any(config.get(key, {}).get("enabled") for key in notification_types):
                    notifications.append({
                        'type': 'info',
                        'message': "Générez les notifications du jour depuis la page de configuration."
                    })

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(notifications).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur serveur lors de la génération des notifications: {e}")
            return

        if parsed_path.path == '/api/notifications/config':
            config_path = APP_WEB_DIR / "notifications_config.json"
            if config_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                with open(config_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_json_error(404, "Fichier de configuration des notifications non trouvé.")
            return

        # API pour lister les fichiers de santé
        if parsed_path.path == '/api/sante/files':
            try:
                files = sorted([f.name for f in SANTE_DIR.glob("sante_log_*.json")], reverse=True)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(files).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur serveur: {e}")
            return

        # API pour lire un fichier de santé
        if parsed_path.path == '/api/sante/file':
            params = parse_qs(parsed_path.query)
            filename = params.get('name', [None])[0]
            if not filename or '..' in filename or filename.startswith('/'):
                self.send_json_error(400, "Nom de fichier invalide.")
                return
            
            file_path = SANTE_DIR / filename
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_json_error(404, "Fichier non trouvé.")
            return

        # API pour lire le fichier d'exercices pour ntfy_sender
        if parsed_path.path == '/api/exercices':
            # Le fichier est dans app web/ntfy_sender/exercices.json
            exercices_path = APP_WEB_DIR / "ntfy_sender" / "exercices.json"
            if exercices_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                with open(exercices_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                print(f"ERREUR: Fichier non trouvé à l'emplacement attendu : {exercices_path}")
                self.send_json_error(404, "Fichier exercices.json non trouvé sur le serveur.")
            return

        # API pour lire les modèles de requêtes
        if parsed_path.path == '/api/request-templates':
            request_templates_path = APP_WEB_DIR / "ntfy_sender" / "request_templates.json"
            if request_templates_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                with open(request_templates_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                print(f"AVERTISSEMENT: Fichier non trouvé à l'emplacement attendu : {request_templates_path}")
                # Renvoyer un objet vide si le fichier n'existe pas pour éviter de casser le client
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{}')
            return

        # API pour lister les coachs disponibles depuis le lore
        if parsed_path.path == '/api/coaches':
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(list(COACH_LORE.keys())).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur serveur lors de la récupération des coachs: {e}")
            return

        # API pour lire le journal de l'histoire
        if parsed_path.path == '/api/histoire':
            if HISTOIRE_LOG_PATH.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                with open(HISTOIRE_LOG_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'[]') # Renvoyer une liste vide si le fichier n'existe pas
            return

        # API pour lister les tâches planifiées
        if parsed_path.path == '/api/list-tasks':
            try:
                # Exécute schtasks pour obtenir les tâches dans le dossier "Monde Vivant" au format CSV
                command = ['schtasks', '/query', '/tn', 'Monde Vivant\\', '/fo', 'CSV', '/v']
                result = subprocess.run(command, capture_output=True, text=True, encoding='latin-1', errors='ignore')

                # Gérer le cas où aucune tâche n'est trouvée (schtasks renvoie une erreur)
                if result.returncode != 0:
                    stderr_lower = result.stderr.lower()
                    # Si l'erreur indique que les tâches n'ont pas été trouvées, ce n'est pas une erreur fatale.
                    if "ne trouve pas" in stderr_lower or "not found" in stderr_lower or "aucun" in stderr_lower:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True, 'tasks': []}).encode('utf-8'))
                        return
                    else:
                        # Une autre erreur s'est produite
                        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
                
                # Le CSV peut commencer par un avertissement, on le nettoie
                csv_content = result.stdout
                if "AVERTISSEMENT:" in csv_content:
                    csv_content = csv_content.split('\n', 1)[1]

                # Utiliser le module CSV pour parser la sortie
                reader = csv.reader(csv_content.splitlines())
                header = next(reader)
                
                tasks = []
                for row in reader:
                    # Approche robuste basée sur la position des colonnes, insensible à la langue
                    if not row or len(row) < 4: continue
                    # On ne garde que le nom de la tâche, pas le chemin complet du dossier
                    task_name_full = row[1] # TaskName est la 2ème colonne (index 1)
                    task_name = task_name_full.split('\\')[-1] if '\\' in task_name_full else task_name_full
                    tasks.append({
                        'name': task_name,
                        'next_run': row[2], # Next Run Time est la 3ème colonne (index 2)
                        'status': row[3]   # Status est la 4ème colonne (index 3)
                    })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'tasks': tasks}).encode('utf-8'))
            except (subprocess.CalledProcessError, Exception) as e:
                self.send_json_error(500, f"Erreur lors de la récupération des tâches: {e}")
            return


        # API pour agréger les données sur une période
        if parsed_path.path == '/api/aggregateData':
            params = parse_qs(parsed_path.query)
            start_date = params.get('start', [None])[0]
            end_date = params.get('end', [None])[0]

            if not start_date or not end_date:
                self.send_json_error(400, "Les paramètres 'start' et 'end' sont requis.")
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
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(aggregated_data).encode('utf-8'))
            return


        # Pour toutes les autres requêtes, utiliser le comportement par défaut
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/notifications/generate':
            try:
                today_str = datetime.datetime.now().date().isoformat()
                generated_count = 0

                # --- Load Configs and Cache ---
                config_path = APP_WEB_DIR / "notifications_config.json"
                cache_path = APP_WEB_DIR / "notifications_cache.json"
                
                config = {}
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                cache = {}
                if cache_path.exists():
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        try: cache = json.load(f)
                        except json.JSONDecodeError: cache = {}

                default_config = {
                    "objectifs": {"enabled": True, "days_threshold": 4, "use_llm": True},
                    "glycemie": {"enabled": True, "days_threshold": 2, "use_llm": True},
                    "poids": {"enabled": True, "days_threshold": 3, "use_llm": True},
                    "ventre": {"enabled": True, "days_threshold": 3, "use_llm": True},
                    "targets": {"calories": 500, "steps": 8000, "distance": 5.0},
                }
                config = {**default_config, **config}

                # --- Logique de Génération (regroupée pour un seul appel API) ---
                cache_updated = False
                prompts_to_generate = {}

                # 1. Check Objectifs
                try:
                    if config.get("objectifs", {}).get("enabled") and config.get("objectifs", {}).get("use_llm"):
                        notif_key = "objectifs"
                        if cache.get(notif_key, {}).get("date") != today_str:
                            objectifs_path = APP_WEB_DIR / "objectifs.json"
                            if objectifs_path.exists():
                                with open(objectifs_path, 'r', encoding='utf-8') as f: objectifs_data = json.load(f)
                                valid_entries = [entry for entry in objectifs_data if 'date' in entry and entry['date']]
                                if valid_entries:
                                    latest_date = max(datetime.date.fromisoformat(entry['date']) for entry in valid_entries)
                                    days_since = (datetime.date.fromisoformat(today_str) - latest_date).days
                                    threshold = config["objectifs"]["days_threshold"]
                                    remaining_days = threshold - days_since
                                    if days_since > threshold:
                                        prompts_to_generate[notif_key] = f"L'utilisateur a dépassé la date limite pour ses objectifs de {days_since - threshold} jour(s). La limite était de {threshold} jours. C'est un rappel ferme."
                                    elif days_since >= 1:
                                        prompts_to_generate[notif_key] = f"L'utilisateur approche de la date limite pour ses objectifs. Il lui reste {remaining_days} jour(s) (J-{remaining_days}). C'est un rappel amical."
                                    else: # days_since == 0
                                        prompts_to_generate[f"{notif_key}_congrats"] = "L'utilisateur a bien enregistré ses objectifs aujourd'hui. Il faut le féliciter."
                except Exception as e:
                    print(f"Erreur lors de la génération de la notification 'objectifs': {e}")

                # 2. Check Health Data (Glycémie, Poids, Ventre)
                sante_path = APP_WEB_DIR / "sante.json"
                sante_data = []
                if sante_path.exists():
                    with open(sante_path, 'r', encoding='utf-8') as f:
                        try: sante_data = json.load(f)
                        except json.JSONDecodeError: print("Warning: sante.json is corrupted.")

                health_checks = {
                    "glycemie": {"data_key": "glycemie_mmol_l", "value_accessor": lambda e, key: e.get(key) is not None, "noun": "sa glycémie", "verb": "mesuré"},
                    "poids": {"data_key": "weight", "value_accessor": lambda e, key: e.get(key, {}).get('value') is not None, "noun": "son poids", "verb": "enregistré"},
                    "ventre": {"data_key": "waist", "value_accessor": lambda e, key: e.get(key, {}).get('value') is not None, "noun": "son tour de ventre", "verb": "mesuré"}
                }

                for notif_key, check_details in health_checks.items():
                    try:
                        notif_config = config.get(notif_key, {})
                        if notif_config.get("enabled") and notif_config.get("use_llm"):
                            if cache.get(notif_key, {}).get("date") != today_str:
                                valid_entries = sorted([e for e in sante_data if 'date' in e and e['date'] and check_details["value_accessor"](e, check_details["data_key"])], key=lambda x: x['date'], reverse=True)
                                if valid_entries:
                                    latest_date = datetime.date.fromisoformat(valid_entries[0]['date'])
                                    days_since = (datetime.date.fromisoformat(today_str) - latest_date).days
                                    threshold = notif_config.get("days_threshold", 3)
                                    remaining_days = threshold - days_since
                                    
                                    if days_since > threshold:
                                        prompts_to_generate[notif_key] = f"L'utilisateur a dépassé la date limite pour {check_details['noun']} de {days_since - threshold} jour(s). La limite était de {threshold} jours. C'est un rappel ferme."
                                    elif days_since >= 1:
                                        prompts_to_generate[notif_key] = f"L'utilisateur approche de la date limite pour {check_details['noun']}. Il lui reste {remaining_days} jour(s) (J-{remaining_days}). C'est un rappel amical."
                                    else: # days_since == 0
                                        prompts_to_generate[f"{notif_key}_congrats"] = f"L'utilisateur a bien {check_details['verb']} {check_details['noun']} aujourd'hui. Il faut le féliciter."
                                elif sante_data:
                                    prompts_to_generate[notif_key] = f"L'utilisateur n'a jamais {check_details['verb']} {check_details['noun']}. Il faut lui rappeler de commencer."
                                else: # sante.json does not exist or is empty
                                    prompts_to_generate[notif_key] = f"L'utilisateur n'a pas encore de fichier de santé. Il faut lui rappeler d'enregistrer {check_details['noun']}."
                    except Exception as e:
                        print(f"Erreur lors de la préparation de la notification '{notif_key}': {e}")

                # --- Appel unique à l'API si nécessaire ---
                if prompts_to_generate:
                    coach = random.choice(list(COACH_LORE.keys()))
                    coach_lore = COACH_LORE.get(coach, "")
                    
                    system_prompt = f"""{coach_lore}
Tu es un coach virtuel. Tu dois générer des notifications courtes et percutantes. Les contextes se terminant par '_congrats' sont pour féliciter l'utilisateur.
Tu recevras un objet JSON de contextes et tu dois répondre avec un objet JSON.
Les clés de l'objet JSON de sortie doivent correspondre aux clés des contextes d'entrée.
Les valeurs doivent être les messages de notification que tu as générés, dans le ton du personnage.
Ta réponse doit être UNIQUEMENT un bloc de code JSON valide, sans aucun texte ou explication avant ou après.

Exemple de réponse attendue:
{{
  "glycemie": "Le niveau de sucre dans ton sang semble bas. Pense à vérifier.",
  "objectifs": "Tes objectifs t'attendent. Ne les laisse pas tomber !",
  "poids_congrats": "Bien joué pour le suivi de ton poids, la régularité est la clé !"
}}"""

                    user_prompt = f"""Génère des notifications pour les contextes suivants :
{json.dumps(prompts_to_generate, indent=2)}"""

                    message, success = self._generate_llm_message(coach, user_prompt, system_prompt_override=system_prompt)

                    if success:
                        try:
                            # Le parsing devrait maintenant être direct et fiable grâce à response_format
                            generated_messages = json.loads(message)
                            for raw_key, notif_message in generated_messages.items():
                                if raw_key.endswith("_congrats"):
                                    key = raw_key.replace("_congrats", "")
                                    notif_type = 'success'
                                    source_text = f"Suivi {key.capitalize()}"
                                else:
                                    key = raw_key
                                    notif_type = 'warning' if key == 'objectifs' else 'info'
                                    source_text = key.capitalize()
                                
                                # Construction de la notification enrichie
                                new_notif = {
                                    "source": source_text,
                                    "notification": {
                                        "type": notif_type, "coach": coach, "message": notif_message
                                    }
                                }
                                cache[key] = {"date": today_str, "notification": new_notif}
                                cache_updated = True
                                self._append_to_histoire_log(f"Notification - {key.capitalize()}{' (Félicitations)' if '_congrats' in raw_key else ''}", coach, notif_message)
                                generated_count += 1
                        except json.JSONDecodeError:
                            print(f"Erreur: La réponse de l'IA n'est pas un JSON valide malgré la contrainte. Réponse reçue:\n{message}")
                            generated_count = 0 # On indique qu'aucune notif n'a été générée

                # --- Save Cache if updated ---
                if cache_updated:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, indent=2)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True, 
                    'message': f"{generated_count} notifications IA générées et mises en cache."
                }).encode('utf-8'))

            except Exception as e:
                self.send_json_error(500, f"Erreur serveur lors de la génération des notifications: {e}")
            return

        if self.path == '/api/schedule-startup-notifications':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                enable = data.get('enable', False)

                task_name = "Monde Vivant\\NotificationGeneratorOnStartup"

                if enable:
                    # Créer le script PowerShell qui appellera l'API de génération
                    script_name = "run_notification_generator.ps1"
                    script_path = SCHEDULED_TASKS_DIR / script_name
                    
                    # Ce script fait un simple appel web au serveur local
                    ps_script_content = f"""
# Script pour déclencher la génération de notifications au démarrage
$ErrorActionPreference = "Stop"

try {{
    # Attendre quelques secondes pour que le serveur web ait le temps de démarrer
    Start-Sleep -Seconds 15

    # Envoyer une requête POST pour générer les notifications
    Invoke-RestMethod -Uri "http://localhost:{PORT}/api/notifications/generate" -Method Post -ContentType "application/json" -Body "{{}}"
    Write-Host "Requête de génération de notifications envoyée avec succès."

}} catch {{
    # En cas d'erreur, l'écrire dans un fichier log pour le débogage
    $logPath = "{str(SCHEDULED_TASKS_DIR / 'startup_error.log').replace('\\', '/')}"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorMessage = "$timestamp - Erreur dans le script de démarrage: $($_.Exception.Message)"
    Add-Content -Path $logPath -Value $errorMessage
}}
"""
                    with open(script_path, 'w', encoding='utf-8-sig') as f:
                        f.write(ps_script_content)

                    # Créer la tâche planifiée pour s'exécuter à l'ouverture de session
                    command = [
                        'schtasks', '/create', '/tn', task_name,
                        '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                        '/sc', 'ONLOGON', '/f'
                    ]
                    subprocess.run(command, check=True, capture_output=True, text=True)
                    message = "La génération de notifications au démarrage est activée."
                else:
                    # Supprimer la tâche planifiée
                    command = ['schtasks', '/delete', '/tn', task_name, '/f']
                    subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore') # Ignore les erreurs si la tâche n'existe pas
                    message = "La génération de notifications au démarrage est désactivée."

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': message}).encode('utf-8'))
            except subprocess.CalledProcessError as e:
                error_message = f"Erreur de schtasks: {e.stderr.strip()}"
                self.send_json_error(500, error_message)
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la planification de la tâche de démarrage : {e}")
            return

        if self.path == '/api/notifications/config':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                config_path = APP_WEB_DIR / "notifications_config.json"
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': 'Configuration sauvegardée.'}).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la sauvegarde de la configuration: {e}")
            return

        if self.path == '/api/sante/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            filename = f"sante_log_{data['date']}.json"
            if '..' in filename or filename.startswith('/'):
                self.send_json_error(400, "Nom de fichier invalide pour la sauvegarde.")
                return

            file_path = SANTE_DIR / filename
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok', 'file': filename}).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la sauvegarde du fichier: {e}")
            return
        
        if self.path == '/api/generate-coach-message':
            if MISTRAL_API_KEY == "YOUR_MISTRAL_API_KEY_HERE":
                self.send_json_error(500, "La clé API Mistral n'est pas configurée dans serveur.py.")
                return
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                coach = data.get('coach')
                user_request = data.get('request')
                activities = data.get('activities', [])

                if not coach or not user_request:
                    self.send_json_error(400, "Les champs 'coach' et 'request' sont requis.")
                    return

                # Construire un prompt simple mais efficace pour l'IA
                activities_text = f"Pour les activités suivantes : {', '.join(activities)}." if activities else ""
                
                # Utiliser le lore détaillé si disponible
                coach_lore = COACH_LORE.get(coach, f"Tu es un coach virtuel nommé {coach}. Ton ton est {coach_styles.get(coach, 'direct et motivant')}.")
                system_prompt = f"{coach_lore}\n\nTu dois répondre à la demande de l'utilisateur de manière concise et percutante pour une notification push sur mobile. Le message doit être court, direct et parfaitement dans le ton du personnage."
                user_prompt = f"Génère une notification pour la demande suivante : '{user_request}'. {activities_text}"

                # Appel à l'API Mistral
                api_response = requests.post(
                    'https://api.mistral.ai/v1/chat/completions',
                    headers={'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'},
                    json={
                        'model': 'mistral-large-latest',
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ]
                    },
                    timeout=30
                )
                api_response.raise_for_status()
                api_data = api_response.json()
                generated_message = api_data['choices'][0]['message']['content']

                # Log de l'interaction
                self._append_to_histoire_log("Générateur de Notification", coach, generated_message)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': generated_message}).encode('utf-8'))

            except requests.exceptions.RequestException as e:
                print(f"Erreur API Mistral: {e}")
                self.send_json_error(502, f"Erreur de communication avec l'API Mistral: {e}")
            except Exception as e:
                print(f"Erreur API /api/generate-coach-message: {e}")
                self.send_json_error(500, f"Erreur interne du serveur: {e}")
            return

        if self.path == '/api/generate-motivation': # Changé en POST
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                selected_coach = data.get('coach', 'Aléatoire')

                if selected_coach == 'Aléatoire':
                    coach = random.choice(list(COACH_LORE.keys()))
                else:
                    coach = selected_coach

                coach_lore = COACH_LORE.get(coach, f"Tu es un coach virtuel nommé {coach}.")
                
                today = datetime.date.today()
                date_str = today.strftime("%d %B %Y")

                system_prompt = f"""{coach_lore}
Tu dois générer un message de motivation matinal pour un utilisateur. Le message doit être court, percutant, et dans le ton du personnage. Il doit faire une référence à la date du jour ({date_str}) ou à la météo de manière humoristique ou philosophique. Le but est de donner un coup de fouet à l'utilisateur pour qu'il se bouge. Ta réponse doit être UNIQUEMENT un objet JSON valide avec une seule clé "message". Exemple de réponse attendue: {{ "message": "Un autre jour, une autre bataille. Le soleil se lève, et tes objectifs aussi. Ne les laisse pas tomber." }}"""
                user_prompt = "Génère le message de motivation du jour."

                message_str, success = self._generate_llm_message(coach, user_prompt, system_prompt_override=system_prompt)
                if not success:
                    raise Exception("Échec de la génération du message par l'IA.")

                # La réponse de l'IA est un JSON string, on le parse
                message_data = json.loads(message_str)
                
                # Log de l'interaction
                self._append_to_histoire_log("Message du Jour", coach, message_data.get('message', '...'))

                # On construit la réponse finale pour le client
                response_data = {'success': True, 'coach': coach, 'message': message_data.get('message', '...')}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la génération de la motivation: {e}")
            return

        if self.path == '/api/preview-schedule':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                request_text = data.get('request')
                end_date_str = data.get('endDate')

                if not request_text or not end_date_str:
                    self.send_json_error(400, "La requête et la date de fin sont requises.")
                    return

                from datetime import date, timedelta
                start_date = date.today()
                end_date = date.fromisoformat(end_date_str)
                all_coaches = list(COACH_LORE.keys())

                prompts_to_generate = {}
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    chosen_coach = random.choice(all_coaches)
                    prompts_to_generate[date_str] = {"coach": chosen_coach, "request": request_text}
                    current_date += timedelta(days=1)

                system_prompt = f"""Tu es un générateur de messages de coach. Tu recevras un objet JSON où chaque clé est une date (YYYY-MM-DD) et la valeur contient le nom d'un coach et une requête.
Pour chaque date, tu dois générer un message de notification concis et percutant, en adoptant la personnalité du coach spécifié.
Le lore des coachs est le suivant: {json.dumps(COACH_LORE, indent=2)}

Ta réponse doit être UNIQUEMENT un objet JSON valide. Les clés de l'objet de sortie doivent être les mêmes dates que celles de l'entrée. La valeur pour chaque date doit être le message que tu as généré.

Exemple de réponse attendue:
{{ "2025-09-20": "Message généré pour le 20...", "2025-09-21": "Message généré pour le 21..." }}"""
                user_prompt = json.dumps(prompts_to_generate, indent=2)

                generated_messages_str, success = self._generate_llm_message("Aegis", user_prompt, system_prompt_override=system_prompt)
                if not success:
                    raise Exception("Erreur lors de la génération des messages par l'API Mistral.")

                try:
                    # La réponse de l'IA est un JSON contenant un JSON, nous devons parser deux fois.
                    # C'est un contournement pour la sortie parfois incorrecte de l'IA.
                    outer_json = json.loads(generated_messages_str)
                    generated_messages = outer_json
                except json.JSONDecodeError:
                    raise Exception(f"La réponse de l'IA n'était pas un JSON valide. Réponse: {generated_messages_str}")

                # Combiner les infos pour la réponse
                full_schedule = {}
                for date_str, message in generated_messages.items():
                    full_schedule[date_str] = {
                        "coach": prompts_to_generate[date_str]["coach"],
                        "message": message
                    }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'schedule': full_schedule}).encode('utf-8'))

            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la prévisualisation: {e}")
            return

        if self.path == '/api/confirm-schedule':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                task_name_prefix = data.get('taskName')
                time = data.get('time')
                trigger = data.get('trigger') # 'time' ou 'startup'
                schedule = data.get('schedule')

                if not all([task_name_prefix, time, schedule]):
                    self.send_json_error(400, "Données de planification incomplètes (préfixe, heure, et planning requis).")
                    return

                created_tasks_count = 0

                # Associer des icônes (tags ntfy) à chaque coach
                coach_tags = {
                    "Varkis": "boar",
                    "Kara": "wolf",
                    "Aegis": "robot_face",
                    "KaraOmbre": "wolf",
                    "KaraOmbreStable": "bell",
                    "KaraOmbreChaos": "skull",
                }
                
                # Sauvegarder les messages planifiés pour référence dans tous les cas
                with open(SCHEDULED_MESSAGES_PATH, 'w', encoding='utf-8-sig') as f:
                    json.dump(schedule, f, indent=2, ensure_ascii=False)

                if trigger == 'startup':
                    # --- Logique pour le déclenchement au démarrage ---
                    task_name = f"{task_name_prefix}_OnStartup"
                    safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                    script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

                    # Le script PowerShell est maintenant plus complexe
                    ps_script_content = f"""# Script de rappel au démarrage - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {{
    # --- Module BurntToast (pour notification Windows) ---
if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
    Write-Host "Module BurntToast non trouvé. Tentative d'installation..."
    Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
}}
Import-Module BurntToast

# 2. Logique pour exécution unique par jour
$lockFilePath = "{str(SCHEDULED_TASKS_DIR / (safe_filename + '_lock.txt')).replace('\\', '/')}"
$today = (Get-Date).ToString("yyyy-MM-dd")

if (Test-Path $lockFilePath) {{
    $lastRunDate = Get-Content $lockFilePath
    if ($lastRunDate -eq $today) {{
        Write-Host "Notification déjà envoyée aujourd'hui. Sortie."
        exit
    }}
}}

# 3. Lire le message du jour depuis le fichier JSON
$schedulePath = "{str(SCHEDULED_MESSAGES_PATH).replace('\\', '/')}"
$schedule = Get-Content -Raw -Path $schedulePath | ConvertFrom-Json
$messageData = $schedule.($today)

if ($null -ne $messageData) {{
    $coach = $messageData.coach
    $message = $messageData.message
    
    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{{
        "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
        "Title" = "Rappel de $coach";
        "Tags" = "{coach_tags.get('$coach', 'bell')}";
        "Click" = "http://localhost:8000/app%20web/index.html"
    }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

    # Mettre à jour le fichier de verrouillage
    Set-Content -Path $lockFilePath -Value $today
}}
}} catch {{
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    $_ | Format-List -Force
}} finally {{
    if ($Host.Name -eq "ConsoleHost") {{
        Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
    }}
}}
"""
                    # Utiliser utf-8-sig pour que PowerShell lise correctement les accents
                    with open(script_path, 'w', encoding='utf-8-sig') as f:
                        f.write(ps_script_content)

                    # Créer une seule tâche qui se lance à l'ouverture de session
                    command = [
                        'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                        '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                        '/sc', 'ONLOGON', '/f'
                    ]
                    subprocess.run(command, check=True, capture_output=True, text=True)
                    created_tasks_count = 1
                    success_message = f"Tâche '{task_name}' planifiée pour s'exécuter au démarrage de l'ordinateur."

                else: # Logique existante pour le déclenchement à heure fixe
                    for date_str, item in schedule.items():
                        current_date = datetime.date.fromisoformat(date_str)
                        coach_name = item['coach']
                        message = item['message']

                        # Log de la planification
                        self._append_to_histoire_log(f"Planification - {task_name_prefix}", coach_name, message)

                        # Créer le script PowerShell
                        date_suffix = current_date.strftime('%Y-%m-%d')
                        task_name = f"{task_name_prefix}_{date_suffix}"
                        safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                        script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

                        tag = coach_tags.get(coach_name, "bell")

                        # Utilisation du modèle unifié et robuste
                        ps_script_content = f"""# Script de rappel quotidien - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {{
    # --- Données du message ---
    $coach = '{coach_name.replace("'", "''")}'
    $message = @'
{message}
'@

    # --- Module BurntToast (pour notification Windows) ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }}
    Import-Module BurntToast

    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{{
    "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    "Title" = "Rappel de {coach_name}";
    "Tags" = "{tag}";
    "Click" = "http://localhost:8000/app%20web/index.html"
    }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

}} catch {{
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    $_ | Format-List -Force
    Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
}}"""
                        # Utiliser utf-8-sig pour que PowerShell lise correctement les accents
                        with open(script_path, 'w', encoding='utf-8-sig') as f:
                            f.write(ps_script_content)

                        # Créer la tâche planifiée
                        command = [
                            'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                            '/tr', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                            '/sc', 'ONCE', '/sd', current_date.strftime('%d/%m/%Y'), '/st', time, '/f'
                        ]
                        subprocess.run(command, check=True, capture_output=True, text=True)
                        created_tasks_count += 1
                    success_message = f"{created_tasks_count} tâches ont été planifiées avec succès."

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': success_message}).encode('utf-8'))

            except subprocess.CalledProcessError as e:
                error_message = f"Erreur lors de la création de la tâche: {e.stderr}"
                self.send_json_error(500, error_message)
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la confirmation de la planification: {e}")
            return

        if self.path == '/api/confirm-schedule-old':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                task_name_prefix = data.get('taskName')
                time = data.get('time')
                schedule = data.get('schedule')

                if not all([task_name_prefix, time, schedule]):
                    self.send_json_error(400, "Données de planification incomplètes.")
                    return

                created_tasks_count = 0
                for date_str, item in schedule.items():
                    current_date = datetime.date.fromisoformat(date_str)
                    coach_name = item['coach']
                    message = item['message']

                    # Log de la planification
                    self._append_to_histoire_log(f"Planification - {task_name_prefix}", coach_name, message)

                    # Créer le script PowerShell
                    date_suffix = current_date.strftime('%Y-%m-%d')
                    task_name = f"{task_name_prefix}_{date_suffix}"
                    safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                    script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

                    ps_message = message.replace("'", "''").replace('"', '`"')
                    tag = coach_tags.get(coach_name, "bell")

                    ps_script_content = f"""# Script généré automatiquement
$message = @'\n{ps_message}\n'@
$headers = @{{
    "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    "Title" = "Rappel de {coach_name}";
    "Tags" = "{tag}";
    "Click" = "http://localhost:8000/app%20web/index.html"
}}
Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $headers"""
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(ps_script_content)

                    # Créer la tâche planifiée
                    command = [
                        'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}", # Note: La date est en format US pour schtasks
                        '/tr', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                        '/sc', 'ONCE', '/sd', current_date.strftime('%d/%m/%Y'), '/st', time, '/f'
                    ]
                    subprocess.run(command, check=True, capture_output=True, text=True)
                    created_tasks_count += 1

                success_message = f"{created_tasks_count} tâches ont été planifiées avec succès."
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': success_message}).encode('utf-8'))

            except subprocess.CalledProcessError as e:
                error_message = f"Erreur lors de la création de la tâche: {e.stderr}"
                self.send_json_error(500, error_message)
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la confirmation de la planification: {e}")
            return

        if self.path == '/api/delete-task':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                task_name = data.get('taskName')

                if not task_name:
                    self.send_json_error(400, "Le nom de la tâche est requis.")
                    return

                command = ['schtasks', '/delete', '/tn', f"Monde Vivant\\{task_name}", '/f']
                subprocess.run(command, check=True, capture_output=True, text=True)

                # Supprimer également le fichier .ps1 associé
                safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                script_path_to_delete = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"
                if script_path_to_delete.exists():
                    script_path_to_delete.unlink()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': f"Tâche '{task_name}' supprimée."}).encode('utf-8'))
            except subprocess.CalledProcessError as e:
                error_message = f"Erreur lors de la suppression de la tâche planifiée: {e.stderr}"
                self.send_json_error(500, error_message)
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la suppression de la tâche: {e}")
            return

        if self.path == '/api/saveFile':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            relative_path = data.get('path')
            content = data.get('content')

            if not relative_path or '..' in relative_path or relative_path.startswith('/'):
                self.send_json_error(400, "Chemin de fichier invalide.")
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
                    self._append_to_histoire_log("Générateur de Plan d'Entraînement", "Aegis", content)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Renvoyer un chemin relatif utilisable par le client
                relative_url = '/information/' + relative_path.replace('\\', '/')
                self.wfile.write(json.dumps({'success': True, 'path': str(file_path), 'url': relative_url}).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de la sauvegarde du fichier : {e}")
            return

        if self.path == '/api/injectAnalysis':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            html_relative_path = data.get('html_path')
            # On attend maintenant une liste d'analyses
            analyses = data.get('analyses')

            if not html_relative_path or '..' in html_relative_path or not html_relative_path.endswith('.html'):
                self.send_json_error(400, "Chemin de fichier HTML invalide.")
                return
            
            if not isinstance(analyses, list):
                self.send_json_error(400, "Le champ 'analyses' doit être une liste.")
                return

            # Le chemin est relatif à /information/, donc on le reconstruit
            html_file_path = INFO_DIR / html_relative_path

            if not html_file_path.exists():
                self.send_json_error(404, f"Fichier HTML non trouvé : {html_file_path}")
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
                        self._append_to_histoire_log("Analyse d'Activité", analysis_key, analysis_content)

                        # Utilisation d'une fonction lambda pour le remplacement afin d'éviter l'interprétation des backslashes.
                        modified_html = target_pattern.sub(lambda m: f'"{analysis_key}": {analysis_escaped}', modified_html, 1)

                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_html)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Renvoyer l'URL du fichier modifié pour que le client puisse l'ouvrir
                relative_url = '/information/' + html_relative_path.replace('\\', '/')
                self.wfile.write(json.dumps({'success': True, 'url': relative_url}).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur lors de l'injection de l'analyse : {e}")
            return

        if self.path == '/api/processAnalyses':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            activity_dir_path = data.get('activity_dir')
            if not activity_dir_path or '..' in activity_dir_path:
                self.send_json_error(400, "Chemin de dossier d'activité invalide.")
                return

            # Le chemin est relatif à /information/, donc on le reconstruit
            analysis_folder = INFO_DIR / activity_dir_path / "analysis"

            if not analysis_folder.exists() or not analysis_folder.is_dir():
                self.send_json_error(404, f"Dossier d'analyse non trouvé : {analysis_folder}")
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
                    html_template = f"""<!DOCTYPE html>
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
</html>"""
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_template)
                    processed_files.append(html_path.name)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': f"{len(processed_files)} fichiers traités.", 'files': processed_files}).encode('utf-8'))
            except Exception as e:
                self.send_json_error(500, f"Erreur lors du traitement des analyses : {e}")
            return

        self.send_error(404, "Endpoint non trouvé.")

    def end_headers(self):
        # Ajoute des en-têtes pour désactiver le cache du navigateur
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

# --- Données pour le coach ---
coach_styles = {
    "Varkis": "brutal, direct, comme un guerrier survivant",
    "Kara": "mystique, poétique, comme une rôdeuse de l'ombre",
    "Aegis": "rationnel, analytique, comme une IA bienveillante"
}

COACH_LORE = {}

def load_coach_lore():
    """Charge les fiches de personnalité depuis le fichier de lore au démarrage."""
    global COACH_LORE
    if not LORE_FILE_PATH.exists():
        print(f"AVERTISSEMENT: Fichier de lore non trouvé à '{LORE_FILE_PATH}'. Utilisation des styles par défaut.")
        return

    try:
        with open(LORE_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = re.split(r'\n## ', content)
        personalities = {}
        for section in sections:
            if 'Archétype' in section:
                # Le nom du coach est la première partie du titre avant "–"
                title_line = section.split('\n')[0].strip()
                name = re.split(r'\s*–\s*', title_line)[0].strip()
                personalities[name] = "## " + section
        
        COACH_LORE = personalities
        print(f"Succès : {len(COACH_LORE)} fiches de lore chargées pour les coachs : {', '.join(COACH_LORE.keys())}")
    except Exception as e:
        print(f"ERREUR lors du chargement du fichier de lore : {e}")

# --- Démarrage du serveur ---
with socketserver.TCPServer(("", PORT), NoCacheHandler) as httpd:
    print(f"Serveur démarré sur http://localhost:{PORT}")
    print("Servez-vous de ce terminal pour voir les requêtes.")
    print("Faites Ctrl+C pour arrêter le serveur.")
    load_coach_lore() # Charger le lore au démarrage
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
        httpd.shutdown()

    def end_headers(self):
        # Ajoute des en-têtes pour désactiver le cache du navigateur
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
