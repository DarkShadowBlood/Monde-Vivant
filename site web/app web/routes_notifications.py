import datetime
import json
import random
import requests

from config import APP_WEB_DIR, MISTRAL_API_KEY
from lore import COACH_LORE, coach_styles
from utils import append_to_histoire_log, generate_llm_message, send_json_error

def handle_get_notifications(handler):
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

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(notifications).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la génération des notifications: {e}")

def handle_get_notifications_config(handler):
    config_path = APP_WEB_DIR / "notifications_config.json"
    if config_path.exists():
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        with open(config_path, 'rb') as f:
            handler.wfile.write(f.read())
    else:
        send_json_error(handler, 404, "Fichier de configuration des notifications non trouvé.")

def handle_post_notifications_config(handler):
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        config_path = APP_WEB_DIR / "notifications_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': 'Configuration sauvegardée.'}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la sauvegarde de la configuration: {e}")

def handle_post_generate_notifications(handler):
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

            message, success = generate_llm_message(coach, user_prompt, system_prompt_override=system_prompt)

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
                        append_to_histoire_log(f"Notification - {key.capitalize()}{' (Félicitations)' if '_congrats' in raw_key else ''}", coach, notif_message)
                        generated_count += 1
                except json.JSONDecodeError:
                    print(f"Erreur: La réponse de l'IA n'est pas un JSON valide malgré la contrainte. Réponse reçue:\n{message}")
                    generated_count = 0 # On indique qu'aucune notif n'a été générée

        # --- Save Cache if updated ---
        if cache_updated:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({
            'success': True, 
            'message': f"{generated_count} notifications IA générées et mises en cache."
        }).encode('utf-8'))

    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la génération des notifications: {e}")

def handle_post_generate_coach_message(handler):
    if not MISTRAL_API_KEY:
        send_json_error(handler, 500, "La clé API Mistral n'est pas configurée dans le fichier de configuration ou les variables d'environnement.")
        return
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        coach = data.get('coach')
        user_request = data.get('request')
        activities = data.get('activities', [])

        if not coach or not user_request:
            send_json_error(handler, 400, "Les champs 'coach' et 'request' sont requis.")
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
        append_to_histoire_log("Générateur de Notification", coach, generated_message)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': generated_message}).encode('utf-8'))

    except requests.exceptions.RequestException as e:
        print(f"Erreur API Mistral: {e}")
        send_json_error(handler, 502, f"Erreur de communication avec l'API Mistral: {e}")
    except Exception as e:
        print(f"Erreur API /api/generate-coach-message: {e}")
        send_json_error(handler, 500, f"Erreur interne du serveur: {e}")

def handle_post_generate_motivation(handler):
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)
        
        selected_coach = data.get('coach', 'Aléatoire')

        if selected_coach == 'Aléatoire':
            coach = random.choice(list(COACH_LORE.keys()))
        else:
            coach = selected_coach

        coach_lore = COACH_LORE.get(coach, f"Tu es un coach virtuel nommé {coach}.")
        
        today = datetime.date.today()
        date_str = today.strftime("%d %B %Y")

        system_prompt = f'''{coach_lore}
Tu dois générer un message de motivation matinal pour un utilisateur. Le message doit être court, percutant, et dans le ton du personnage. Il doit faire une référence à la date du jour ({date_str}) ou à la météo de manière humoristique ou philosophique. Le but est de donner un coup de fouet à l'utilisateur pour qu'il se bouge. Ta réponse doit être UNIQUEMENT un objet JSON valide avec une seule clé "message". Exemple de réponse attendue: {{ "message": "Un autre jour, une autre bataille. Le soleil se lève, et tes objectifs aussi. Ne les laisse pas tomber." }}'''
        user_prompt = "Génère le message de motivation du jour."

        message_str, success = generate_llm_message(coach, user_prompt, system_prompt_override=system_prompt)
        if not success:
            raise Exception("Échec de la génération du message par l'IA.")

        # La réponse de l'IA est un JSON string, on le parse
        message_data = json.loads(message_str)
        
        # Log de l'interaction
        append_to_histoire_log("Message du Jour", coach, message_data.get('message', '...'))

        # On construit la réponse finale pour le client
        response_data = {'success': True, 'coach': coach, 'message': message_data.get('message', '...')}
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la génération de la motivation: {e}")
