import json
import traceback
from urllib.parse import parse_qs
from utils import send_json_error
from gamification import get_player_profile, claim_loot_for_character, craft_item, get_character_inventory, sell_item, buy_item, get_all_quests_status, claim_quest_reward, get_achievements_status, claim_achievement_reward

def handle_get_gamification_profile(handler, context):
    """
    Handles the request for a character's gamification profile.
    Expects a query parameter `character` (e.g., /api/gamification/profile?character=Varkis)
    """
    try:
        parsed_path = parse_qs(handler.path.split('?', 1)[-1])
        character_name = parsed_path.get('character', [None])[0]

        if not character_name:
            send_json_error(handler, 400, "Le paramètre 'character' est requis.")
            return

        profile = get_player_profile(character_name)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': profile}).encode('utf-8'))
    except (ValueError, FileNotFoundError) as e:
        send_json_error(handler, 404, str(e))
    except Exception as e:
        print(f"ERROR in handle_get_gamification_profile: {e}")
        traceback.print_exc()
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération du profil: {e}")

def handle_post_claim_loot(handler, context):
    """
    Handles the POST request to claim loot for an activity.
    Expects a JSON body with: { character: "name", activity_id: "id", loot: {...} }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character = body.get('character')
        activity_id = body.get('activity_id')
        loot = body.get('loot')

        if not all([character, activity_id, loot is not None]):
            send_json_error(handler, 400, "Paramètres manquants (character, activity_id, loot).")
            return

        # Appelle la fonction logique pour sauvegarder les données
        updated_char_data = claim_loot_for_character(character, activity_id, loot)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({
            'success': True, 
            'message': 'Butin réclamé avec succès.',
            'updated_currencies': updated_char_data.get('currencies', {})
        }).encode('utf-8'))

    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la réclamation du butin: {e}")

def handle_get_inventory(handler, context):
    """
    Handles the request for a character's inventory (currencies and items).
    Expects a query parameter `character`.
    """
    try:
        parsed_path = parse_qs(handler.path.split('?', 1)[-1])
        character_name = parsed_path.get('character', [None])[0]

        if not character_name:
            send_json_error(handler, 400, "Le paramètre 'character' est requis.")
            return

        inventory = get_character_inventory(character_name)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': inventory}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération de l'inventaire: {e}")

def handle_craft_item(handler, context):
    """
    Handles the POST request to craft an item.
    Expects a JSON body with: { character: "name", recipe_id: "id" }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character_name = body.get('character')
        recipe_id = body.get('recipe_id')

        if not character_name or not recipe_id:
            send_json_error(handler, 400, "Les paramètres 'character' et 'recipe_id' sont requis.")
            return

        # Appelle la fonction logique pour gérer la fabrication
        result_message = craft_item(character_name, recipe_id)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({
            'success': True, 
            'message': result_message
        }).encode('utf-8'))

    except ValueError as e: # Erreurs prévues (matériaux manquants, etc.)
        send_json_error(handler, 400, str(e))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la fabrication: {e}")

def handle_sell_item(handler, context):
    """
    Handles the POST request to sell an item.
    Expects a JSON body with: { character: "name", item_id: "id", quantity: 1 }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character_name = body.get('character')
        item_id = body.get('item_id')
        quantity = body.get('quantity')

        if not all([character_name, item_id, quantity]):
            send_json_error(handler, 400, "Les paramètres 'character', 'item_id' et 'quantity' sont requis.")
            return

        # Appelle la fonction logique pour gérer la vente
        result_message = sell_item(character_name, item_id, quantity)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': result_message}).encode('utf-8'))

    except ValueError as e: # Erreurs prévues (objet non possédé, etc.)
        send_json_error(handler, 400, str(e))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la vente: {e}")

def handle_buy_item(handler, context):
    """
    Handles the POST request to buy an item.
    Expects a JSON body with: { character: "name", item_id: "id", quantity: 1 }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character_name = body.get('character')
        item_id = body.get('item_id')
        quantity = body.get('quantity')

        if not all([character_name, item_id, quantity]):
            send_json_error(handler, 400, "Les paramètres 'character', 'item_id' et 'quantity' sont requis.")
            return

        # Appelle la fonction logique pour gérer l'achat
        result_message = buy_item(character_name, item_id, quantity)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': result_message}).encode('utf-8'))

    except ValueError as e: # Erreurs prévues (fonds insuffisants, etc.)
        send_json_error(handler, 400, str(e))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de l'achat: {e}")

def handle_get_quests(handler, context):
    """
    Handles the GET request for a character's daily quest status.
    Expects a query parameter `character`. Returns both daily and weekly quests.
    """
    try:
        parsed_path = parse_qs(handler.path.split('?', 1)[-1])
        character_name = parsed_path.get('character', [None])[0]

        if not character_name:
            send_json_error(handler, 400, "Le paramètre 'character' est requis.")
            return

        quest_status = get_all_quests_status(character_name)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': quest_status}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération des quêtes: {e}")

def handle_claim_quest(handler, context):
    """
    Handles the POST request to claim a daily quest reward.
    Expects a JSON body with: { character: "name", quest_id: "id" }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character_name = body.get('character')
        quest_id = body.get('quest_id')

        if not all([character_name, quest_id]):
            send_json_error(handler, 400, "Les paramètres 'character' et 'quest_id' sont requis.")
            return

        # Appelle la fonction logique pour gérer la réclamation
        result_message = claim_quest_reward(character_name, quest_id)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({
            'success': True, 
            'message': result_message
        }).encode('utf-8'))

    except ValueError as e: # Erreurs prévues (quête non complétée, etc.)
        send_json_error(handler, 400, str(e))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la réclamation de la quête: {e}")

def handle_get_achievements(handler, context):
    """
    Handles the GET request for a character's achievements status.
    Expects a query parameter `character`.
    """
    try:
        parsed_path = parse_qs(handler.path.split('?', 1)[-1])
        character_name = parsed_path.get('character', [None])[0]

        if not character_name:
            send_json_error(handler, 400, "Le paramètre 'character' est requis.")
            return

        status_data = get_achievements_status(character_name)
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'data': status_data}).encode('utf-8'))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la récupération des hauts faits: {e}")

def handle_claim_achievement(handler, context):
    """
    Handles the POST request to claim an achievement reward.
    Expects a JSON body with: { character: "name", achievement_id: "id" }
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        body = json.loads(post_data)

        character_name = body.get('character')
        achievement_id = body.get('achievement_id')

        if not all([character_name, achievement_id]):
            send_json_error(handler, 400, "Les paramètres 'character' et 'achievement_id' sont requis.")
            return

        # Appelle la fonction logique pour gérer la réclamation
        result_message = claim_achievement_reward(character_name, achievement_id)
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({
            'success': True, 
            'message': result_message
        }).encode('utf-8'))

    except ValueError as e: # Erreurs prévues (haut fait non débloqué, etc.)
        send_json_error(handler, 400, str(e))
    except Exception as e:
        send_json_error(handler, 500, f"Erreur serveur lors de la réclamation du haut fait: {e}")