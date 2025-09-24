"""
Ce module fournit des fonctions utilitaires partagées par les différents modules de routes.

Il contient des fonctions pour :
- Envoyer des réponses d'erreur JSON standardisées.
- Gérer le fichier journal de l'application (histoire_log.json).
- Interagir avec l'API de Mistral pour la génération de texte par l'IA.
"""
import datetime
import json
import requests

from config import HISTOIRE_LOG_PATH, MISTRAL_API_KEY
import lore

def send_json_error(handler, code, message):
    """
    Envoie une réponse d'erreur standardisée au format JSON.

    Args:
        handler: L'objet gestionnaire de requêtes HTTP.
        code (int): Le code de statut HTTP de l'erreur (ex: 404, 500).
        message (str): Le message d'erreur à envoyer au client.
    """
    handler.send_response(code)
    handler.send_header('Content-type', 'application/json')
    handler.end_headers()
    error_response = {'success': False, 'error': message}
    handler.wfile.write(json.dumps(error_response).encode('utf-8'))

def append_to_histoire_log(source, coach, message):
    """
    Ajoute une nouvelle entrée au fichier journal principal de l'application.

    Ce journal (histoire_log.json) conserve une trace de toutes les interactions
    importantes (génération de notifications, planification, etc.).

    Args:
        source (str): L'origine de l'événement (ex: "Notification", "Planification").
        coach (str): Le nom du coach impliqué, si applicable.
        message (str): Le message ou le contenu de l'événement.
    """
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
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    
    # Insère la nouvelle entrée au début pour un accès plus rapide aux événements récents
    log_data.insert(0, log_entry)
    
    with open(HISTOIRE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def generate_llm_message(coach_name, prompt_context, system_prompt_override=None):
    """
    Génère un message en utilisant l'API de Mistral AI.

    Cette fonction encapsule l'appel à l'API, gère l'authentification et
    le formatage de la requête. Elle est conçue pour demander une réponse JSON
    afin de garantir des sorties plus fiables et faciles à parser.

    Args:
        coach_name (str): Le nom du coach pour lequel générer le message.
        prompt_context (str): Le prompt utilisateur principal.
        system_prompt_override (str, optional): Un prompt système personnalisé.
            Si non fourni, un prompt par défaut basé sur le lore du coach est utilisé.

    Returns:
        tuple[str, bool]: Le contenu du message généré et un booléen indiquant le succès.

    Raises:
        ValueError: Si la clé API n'est pas configurée.
        IOError: En cas d'erreur de communication avec l'API.
    """
    if not MISTRAL_API_KEY:
        raise ValueError("La clé API Mistral n'est pas configurée sur le serveur.")

    if system_prompt_override:
        system_prompt = system_prompt_override
        user_prompt = prompt_context
    else:
        # Construit un prompt système par défaut si aucun n'est fourni
        coach_lore = lore.COACH_LORE.get(coach_name, f"Tu es un coach virtuel nommé {coach_name}.")
        system_prompt = f"{coach_lore}\n\nTu dois répondre à la demande de l'utilisateur de manière concise et percutante pour une notification. Le message doit être court, direct et dans le ton du personnage."
        user_prompt = f"Génère une notification pour la situation suivante : '{prompt_context}'."
    
    try:
        api_response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'mistral-large-latest',
                'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                'response_format': {'type': 'json_object'} # Demande une réponse JSON
            },
            timeout=30,
            verify=False # ATTENTION: À n'utiliser qu'en développement local
        )
        api_response.raise_for_status()
        api_data = api_response.json()
        return api_data['choices'][0]['message']['content'].strip(), True
    except requests.exceptions.RequestException as e:
        print(f"Erreur API Mistral: {type(e).__name__}, Détails: {e}")
        raise IOError(f"Erreur de connexion à l'API Mistral: {e}")