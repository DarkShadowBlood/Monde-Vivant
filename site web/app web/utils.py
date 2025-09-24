import datetime
import json
import requests

from config import HISTOIRE_LOG_PATH, MISTRAL_API_KEY
from lore import COACH_LORE


def send_json_error(handler, code, message):
    """Envoie une réponse d'erreur standardisée au format JSON."""
    handler.send_response(code)
    handler.send_header('Content-type', 'application/json')
    handler.end_headers()
    error_response = {'success': False, 'error': message}
    handler.wfile.write(json.dumps(error_response).encode('utf-8'))

def append_to_histoire_log(source, coach, message):
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

def generate_llm_message(coach_name, prompt_context, system_prompt_override=None):
    """Helper function to generate a message from the LLM API."""
    if not MISTRAL_API_KEY:
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
