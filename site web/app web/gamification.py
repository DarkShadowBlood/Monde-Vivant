import json
import re
from pathlib import Path
from datetime import datetime, timedelta
import threading
import random
from config import APP_WEB_DIR, LORE_FILE_PATH
from utils import load_json_file
def _parse_duration_to_minutes(duration_str: str) -> float:
    """Converts a 'HH:MM:SS' or 'MM:SS' string to total minutes."""
    if not isinstance(duration_str, str):
        return 0.0
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 3:
        h, m, s = parts
        return h * 60 + m + s / 60
    elif len(parts) == 2:
        m, s = parts
        return m + s / 60
    return 0.0

def _get_ranks():
    """Returns the rank structure."""
    return {
        0: "Novice", 5: "Initié", 10: "Adepte", 20: "Vétéran",
        30: "Maître", 40: "Légende", 50: "Mythe"
    }

def get_characters():
    """Loads character base data from the dedicated characters.json file."""
    characters_path = APP_WEB_DIR / "characters.json"
    if not characters_path.exists():
        return {}
    with open(characters_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_progression(activities, objectives, character_sheet):
    """
    Calculates total XP and currencies based on activities, objectives, and character stats.
    Now includes passive skill bonuses.
    """ 
    total_xp = 0
    character_stats = character_sheet.get('stats', {})
    character_name = character_sheet.get('name', '').split('–')[0].strip()

    # XP from activities
    for activity in activities:
        # --- Data extraction and conversion ---
        activity_xp = 0
        calories = float(activity.get('calories', 0))
        distance = float(activity.get('distance', 0))
        duration_min = _parse_duration_to_minutes(activity.get('duration', '0:0'))

        # Base XP
        activity_xp += (calories * 0.1)  # 1 XP per 10 calories
        activity_xp += (distance * 10)   # 10 XP per km

        # Stat bonuses (example)
        activity_xp += (calories * 0.01 * character_stats.get('force', 0))
        activity_xp += (duration_min * 0.1 * character_stats.get('endurance', 0))

        # --- Passive Skill Bonuses ---
        # Varkis: +10% XP on activities > 45 mins
        if character_name == 'Varkis' and duration_min > 45:
            activity_xp *= 1.10

        # KaraOmbreChaos: +15% XP on activities after 18:00 or before 6:00
        if character_name == 'KaraOmbreChaos':
            try:
                activity_time = datetime.strptime(activity.get('time', '12:00'), '%H:%M').time()
                if not (datetime.strptime('06:00', '%H:%M').time() <= activity_time < datetime.strptime('18:00', '%H:%M').time()):
                    activity_xp *= 1.15
            except ValueError:
                pass # Ignore if time format is wrong
        
        # --- Final XP for activity ---
        total_xp += activity_xp

    # XP from objectives
    for goal in objectives:
        goal_xp = 5 # Base 5 XP for each day an objective is logged
        
        # Aegis: +20% XP if a daily goal is met at 95-105%
        if character_name == 'Aegis':
            # Note: This is a simplified implementation. A real one would need target goals.
            # Let's assume a target of 8000 steps for the bonus.
            steps = int(goal.get('steps', 0))
            if 7600 <= steps <= 8400: # 8000 * 0.95 to 8000 * 1.05
                goal_xp *= 1.20

        total_xp += goal_xp

    return {"xp": int(total_xp)}

def get_player_profile(character_name: str):
    """
    Builds the full player profile, including calculated level and XP.
    """
    # 1. Load base character data
    all_characters = get_characters()
    base_profile = all_characters.get(character_name)
    if not base_profile:
        raise ValueError(f"Personnage '{character_name}' non trouvé dans characters.json.")

    # 2. Load activity and objective data
    activities_path = APP_WEB_DIR / "activities.json"
    objectives_path = APP_WEB_DIR / "objectifs.json"

    with open(activities_path, 'r', encoding='utf-8') as f:
        # This might be used later if we want to combine calculated progression with claimed loot
        activities = json.load(f)
    with open(objectives_path, 'r', encoding='utf-8') as f:
        objectives = json.load(f)

    # 3. Calculate XP
    progression = calculate_progression(activities, objectives, base_profile)
    current_xp = progression['xp']

    # 4. Load persistent data (currencies, claimed loot)
    data_path = APP_WEB_DIR / "gamification_data.json"
    persistent_data = {}
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            persistent_data = json.load(f)
    
    character_persistent_data = persistent_data.get(character_name, {})

    # S'assurer que `currencies` est un dictionnaire
    currencies_data = character_persistent_data.get('currencies')
    if not isinstance(currencies_data, dict):
        currencies_data = {}

    items_data = character_persistent_data.get('items')
    if not isinstance(items_data, dict):
        items_data = {}

    # 4. Calculate Level
    xp_per_level = 100
    current_level = current_xp // xp_per_level
    xp_in_level = current_xp % xp_per_level

    # 5. Build final profile
    ranks = _get_ranks()
    current_rank = "Inconnu"
    # Find the highest rank achieved
    for level_req, rank_name in sorted(ranks.items(), reverse=True):
        if current_level >= level_req:
            current_rank = rank_name
            break

    profile = {
        "name": base_profile['name'],
        "level": current_level,
        "rank": current_rank,
        "xp": xp_in_level,
        "xp_to_next_level": xp_per_level,
        "stats": base_profile['stats'],
        "passive_skill": base_profile.get('passive_skill'),
        "currencies": {
            "steel_shards": currencies_data.get('steel_shards', 0),
            "soul_gems": currencies_data.get('soul_gems', 0),
            "ancient_components": currencies_data.get('ancient_components', 0),
            "map_fragments": currencies_data.get('map_fragments', 0),
        },
        "items": items_data
    }

    # Cadeau de bienvenue si le joueur n'a rien
    if not any(profile["currencies"].values()):
        profile["currencies"]["steel_shards"] = 10
        profile["gift_message"] = "Un petit cadeau de bienvenue pour commencer votre aventure !"

    return profile

def get_character_inventory(character_name: str):
    """
    Retrieves a character's currencies and items from the persistent data file.
    """
    data_path = APP_WEB_DIR / "gamification_data.json"
    persistent_data = {}
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                persistent_data = json.load(f)
            except json.JSONDecodeError:
                pass # Fichier vide ou corrompu
    
    character_data = persistent_data.get(character_name, {})
    return character_data


# --- Loot System Logic ---

DATA_FILE_PATH = APP_WEB_DIR / "gamification_data.json"
file_lock = threading.Lock()

def claim_loot_for_character(character: str, activity_id: str, loot: dict):
    """
    Adds loot to a character's inventory and marks the activity as claimed.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load current data
        try:
            if DATA_FILE_PATH.exists() and DATA_FILE_PATH.stat().st_size > 0:
                with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        # 2. Get or create character data structure
        char_data = data.setdefault(character, {})
        
        # Ensure 'currencies' and 'claimed_loot' are correctly typed
        char_data.setdefault('currencies', {})
        char_data.setdefault('items', {})
        char_data.setdefault('claimed_loot', [])

        # 3. Update currencies and items from the structured loot object
        if 'currencies' in loot and isinstance(loot['currencies'], dict):
            for currency, amount in loot['currencies'].items():
                char_data['currencies'][currency] = char_data['currencies'].get(currency, 0) + amount
        
        if 'items' in loot and isinstance(loot['items'], dict):
            for item, amount in loot['items'].items():
                char_data['items'][item] = char_data['items'].get(item, 0) + amount

        # 4. Mark activity as claimed
        if activity_id not in char_data["claimed_loot"]:
            char_data["claimed_loot"].append(activity_id)

        # 5. Save data back to file
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return char_data

# --- Crafting System Logic ---

CRAFTING_RECIPES_PATH = APP_WEB_DIR / "crafting_recipes.json"

def craft_item(character_name: str, recipe_id: str):
    """
    Handles the logic for crafting an item. Checks materials, deducts them, and adds the result.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load data
        all_data = load_json_file(DATA_FILE_PATH, {})
        recipes = load_json_file(CRAFTING_RECIPES_PATH, [])

        char_data = all_data.get(character_name)
        if not char_data:
            raise ValueError("Personnage non trouvé.")

        recipe = next((r for r in recipes if r['id'] == recipe_id), None)
        if not recipe:
            raise ValueError("Recette non trouvée.")

        # Initialiser l'inventaire si nécessaire
        char_data.setdefault('currencies', {})
        char_data.setdefault('items', {})

        # 2. Check if the player has enough materials
        for material, required_amount in recipe['cost'].items():
            # Materials can be in 'currencies' or 'items'
            user_amount = char_data['currencies'].get(material, 0) + char_data['items'].get(material, 0)
            if user_amount < required_amount:
                raise ValueError("Matériaux insuffisants.")

        # 3. Deduct materials
        for material, required_amount in recipe['cost'].items():
            if material in char_data['currencies']:
                char_data['currencies'][material] -= required_amount
            elif material in char_data['items']:
                char_data['items'][material] -= required_amount

        # 4. Add the result
        result = recipe['result']
        message = ""
        if result['type'] == 'item':
            item_id = result['item_id']
            quantity = result['quantity']
            char_data['items'][item_id] = char_data['items'].get(item_id, 0) + quantity
            message = f"{quantity}x {recipe['name']} ajouté à l'inventaire."
        elif result['type'] == 'buff':
            # La logique pour les "buffs" sera à implémenter plus tard
            message = f"Vous avez obtenu le buff : {recipe['name']}."
        else:
            message = f"Fabrication de {recipe['name']} réussie."

        # Log crafting event for achievements
        char_data.setdefault('crafting_log', [])
        char_data['crafting_log'].append({
            "recipe_id": recipe_id,
            "date": datetime.now().isoformat()
        })
        # 5. Save data back to file
        all_data[character_name] = char_data
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        return message

# --- Merchant System Logic ---

ITEMS_DEFINITIONS_PATH = APP_WEB_DIR / "items_definitions.json"

def sell_item(character_name: str, item_id: str, quantity: int):
    """
    Handles the logic for selling an item. Checks inventory, removes item, and adds currency.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load data
        all_data = load_json_file(DATA_FILE_PATH, {})
        item_definitions = load_json_file(ITEMS_DEFINITIONS_PATH, {})

        char_data = all_data.get(character_name)
        if not char_data:
            raise ValueError("Personnage non trouvé.")

        item_def = item_definitions.get(item_id)
        if not item_def or 'sell_price' not in item_def:
            raise ValueError("Cet objet ne peut pas être vendu.")

        # 2. Check if the player has the item
        char_data.setdefault('items', {})
        if char_data['items'].get(item_id, 0) < quantity:
            raise ValueError("Quantité insuffisante de l'objet à vendre.")

        # 3. Perform the transaction
        # Remove item
        char_data['items'][item_id] -= quantity
        if char_data['items'][item_id] == 0:
            del char_data['items'][item_id]

        # Add currency (steel_shards by default)
        char_data.setdefault('currencies', {})
        gain = item_def['sell_price'] * quantity
        char_data['currencies']['steel_shards'] = char_data['currencies'].get('steel_shards', 0) + gain

        # 4. Save data
        all_data[character_name] = char_data
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        return f"Vente réussie de {quantity}x {item_def['name']} pour {gain} Éclats d'Acier."

MERCHANT_WARES_PATH = APP_WEB_DIR / "merchant_wares.json"

def buy_item(character_name: str, item_id: str, quantity: int):
    """
    Handles the logic for buying an item. Checks currency, removes it, and adds the item.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load data
        all_data = load_json_file(DATA_FILE_PATH, {})
        merchant_wares = load_json_file(MERCHANT_WARES_PATH, [])
        item_definitions = load_json_file(ITEMS_DEFINITIONS_PATH, {})

        char_data = all_data.get(character_name)
        if not char_data:
            raise ValueError("Personnage non trouvé.")

        ware = next((w for w in merchant_wares if w['item_id'] == item_id), None)
        if not ware:
            raise ValueError("Cet objet n'est pas vendu par le marchand.")

        # 2. Check if the player has enough currency
        char_data.setdefault('currencies', {})
        cost = ware['buy_price'] * quantity
        if char_data['currencies'].get('steel_shards', 0) < cost:
            raise ValueError("Fonds insuffisants (Éclats d'Acier).")

        # 3. Perform the transaction
        # Remove currency
        char_data['currencies']['steel_shards'] -= cost

        # Add item
        char_data.setdefault('items', {})
        char_data['items'][item_id] = char_data['items'].get(item_id, 0) + quantity

        # 4. Save data
        all_data[character_name] = char_data
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        item_name = item_definitions.get(item_id, {}).get('name', item_id)
        return f"Achat réussi de {quantity}x {item_name} pour {cost} Éclats d'Acier."

# --- Daily Quests System Logic ---

DAILY_QUESTS_PATH = APP_WEB_DIR / "daily_quests.json"
WEEKLY_QUESTS_PATH = APP_WEB_DIR / "weekly_quests.json"
ACTIVITIES_PATH = APP_WEB_DIR / "activities.json"

def get_all_quests_status(character_name: str):
    """
    Calculates the current progress for both daily and weekly quests.
    """
    daily_quests = load_json_file(DAILY_QUESTS_PATH, [])
    weekly_quests = load_json_file(WEEKLY_QUESTS_PATH, [])
    activities = load_json_file(ACTIVITIES_PATH, [])
    all_data = load_json_file(DATA_FILE_PATH, {})
    char_data = all_data.get(character_name, {})

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    # La semaine commence le lundi (weekday() == 0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week_str = start_of_week.strftime("%Y-%m-%d")
    week_identifier = start_of_week.strftime("%Y-W%W") # ex: 2023-W40
    
    # Get activities for today and this week
    today_activities = [act for act in activities if act.get('date') == today_str]
    week_activities = [act for act in activities if act.get('date') >= start_of_week_str]

    # Get claimed quests
    claimed_daily = char_data.get('claimed_quests', {}).get('daily', {}).get(today_str, [])
    claimed_weekly = char_data.get('claimed_quests', {}).get('weekly', {}).get(week_identifier, [])

    def calculate_status(quest_list, relevant_activities, claimed_list):
        status_dict = {}
        for quest in quest_list:
            progress = 0
            objective = quest['objective']

            # Filter activities relevant to the quest
            quest_activities = relevant_activities
            if objective['activity_type'] != 'any':
                quest_activities = [
                    act for act in relevant_activities 
                    if act.get('type', '').lower() == objective['activity_type'].lower()
                ]

            # Calculate progress based on objective type
            if objective['type'] == 'distance':
                progress = sum(float(act.get('distance', 0)) for act in quest_activities)
            elif objective['type'] == 'calories':
                progress = sum(int(act.get('calories', 0)) for act in quest_activities)
            elif objective['type'] == 'session_count':
                progress = len(quest_activities)

            is_completed = progress >= objective['target']
            is_claimed = quest['id'] in claimed_list

            status_dict[quest['id']] = {
                "progress": progress,
                "completed": is_completed,
                "claimed": is_claimed
            }
        return status_dict

    return {
        "daily": calculate_status(daily_quests, today_activities, claimed_daily),
        "weekly": calculate_status(weekly_quests, week_activities, claimed_weekly)
    }

def claim_quest_reward(character_name: str, quest_id: str):
    """
    Claims the reward for a completed daily or weekly quest.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load data
        all_data = load_json_file(DATA_FILE_PATH, {})
        daily_quests = load_json_file(DAILY_QUESTS_PATH, [])
        weekly_quests = load_json_file(WEEKLY_QUESTS_PATH, [])
        all_quests = daily_quests + weekly_quests

        char_data = all_data.get(character_name)
        if not char_data:
            raise ValueError("Personnage non trouvé.")

        quest = next((q for q in all_quests if q['id'] == quest_id), None)
        if not quest:
            raise ValueError("Quête non trouvée.")

        # 2. Verify quest status
        current_status = get_all_quests_status(character_name)
        is_daily = quest_id in current_status['daily']
        quest_status = current_status['daily'].get(quest_id) or current_status['weekly'].get(quest_id)

        if not quest_status:
            raise ValueError("Statut de la quête introuvable.")
        if quest_status['claimed']:
            raise ValueError("Récompense déjà réclamée.")
        if not quest_status['completed']:
            raise ValueError("Quête non complétée.")

        # 3. Add rewards
        reward = quest.get('reward', {})
        char_data.setdefault('currencies', {})
        char_data.setdefault('items', {})

        # Add XP (Note: XP is calculated dynamically, so we add it to a persistent store if needed,
        # or we can just return it in the message for now)
        xp_reward = reward.get('xp', 0)
        
        # Add currencies
        if 'currencies' in reward:
            for currency, amount in reward['currencies'].items():
                char_data['currencies'][currency] = char_data['currencies'].get(currency, 0) + amount
        
        # Add items
        if 'items' in reward:
            for item, amount in reward['items'].items():
                char_data['items'][item] = char_data['items'].get(item, 0) + amount

        # 4. Mark quest as claimed for today/this week
        char_data.setdefault('claimed_quests', {'daily': {}, 'weekly': {}})
        if is_daily:
            today_str = datetime.now().strftime("%Y-%m-%d")
            char_data['claimed_quests'].setdefault('daily', {}).setdefault(today_str, [])
            if quest_id not in char_data['claimed_quests']['daily'][today_str]:
                char_data['claimed_quests']['daily'][today_str].append(quest_id)
        else: # is weekly
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            week_identifier = start_of_week.strftime("%Y-W%W")
            char_data['claimed_quests'].setdefault('weekly', {}).setdefault(week_identifier, [])
            if quest_id not in char_data['claimed_quests']['weekly'][week_identifier]:
                char_data['claimed_quests']['weekly'][week_identifier].append(quest_id)

        # 5. Save data
        all_data[character_name] = char_data
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        return f"Récompense pour '{quest['title']}' réclamée !"

# --- Achievements System Logic ---

ACHIEVEMENTS_PATH = APP_WEB_DIR / "achievements_definitions.json"

def get_achievements_status(character_name: str):
    """
    Checks the status of all achievements for a given character.
    """
    definitions = load_json_file(ACHIEVEMENTS_PATH, [])
    all_data = load_json_file(DATA_FILE_PATH, {})
    char_data = all_data.get(character_name, {})
    activities = load_json_file(ACTIVITIES_PATH, [])
    
    # --- Pre-calculation of aggregates to avoid re-calculating for each achievement ---
    # Pre-calculate aggregates to avoid re-calculating for each achievement
    total_distance = sum(float(act.get('distance', 0)) for act in activities)
    
    craft_log = char_data.get('crafting_log', [])
    craft_count = len(craft_log)

    # Calculate total completed quests
    claimed_quests = char_data.get('claimed_quests', {})
    completed_quests_count = 0
    if 'daily' in claimed_quests:
        completed_quests_count += sum(len(quests) for quests in claimed_quests['daily'].values())
    if 'weekly' in claimed_quests:
        completed_quests_count += sum(len(quests) for quests in claimed_quests['weekly'].values())

    # Calculate count of specific crafted recipes
    from collections import Counter
    craft_counts_by_recipe = Counter(item['recipe_id'] for item in craft_log)
    
    try:
        # We need the profile to get the current level
        profile = get_player_profile(character_name)
        current_level = profile.get('level', 0)
    except ValueError:
        current_level = 0

    achievements_status = {}
    for ach in definitions:
        criteria = ach['criteria']
        unlocked = False

        # Check criteria
        if criteria['type'] == 'total_distance':
            if total_distance >= criteria['value']:
                unlocked = True
        elif criteria['type'] == 'craft_count':
            if craft_count >= criteria['value']:
                unlocked = True
        elif criteria['type'] == 'level_reached':
            if current_level >= criteria['value']:
                unlocked = True
        elif criteria['type'] == 'completed_quests_count':
            if completed_quests_count >= criteria['value']:
                unlocked = True
        elif criteria['type'] == 'craft_specific_recipe':
            if craft_counts_by_recipe.get(criteria['recipe_id'], 0) >= criteria['value']:
                unlocked = True
        
        claimed = ach['id'] in char_data.get('claimed_achievements', [])

        achievements_status[ach['id']] = {
            "unlocked": unlocked,
            "claimed": claimed
        }
    
    return achievements_status

def claim_achievement_reward(character_name: str, achievement_id: str):
    """
    Claims the reward for an unlocked achievement.
    This function is thread-safe.
    """
    with file_lock:
        # 1. Load data
        all_data = load_json_file(DATA_FILE_PATH, {})
        definitions = load_json_file(ACHIEVEMENTS_PATH, [])

        char_data = all_data.get(character_name)
        if not char_data:
            raise ValueError("Personnage non trouvé.")

        achievement = next((ach for ach in definitions if ach['id'] == achievement_id), None)
        if not achievement:
            raise ValueError("Haut fait non trouvé.")

        # 2. Verify status
        current_status = get_achievements_status(character_name)
        ach_status = current_status.get(achievement_id)

        if not ach_status or not ach_status['unlocked']:
            raise ValueError("Haut fait non débloqué.")
        if ach_status['claimed']:
            raise ValueError("Récompense déjà réclamée.")

        # 3. Add rewards
        reward = achievement.get('reward', {})
        if 'xp' in reward:
            # Note: XP is calculated dynamically. To add XP, we'd need a persistent XP store.
            # For now, we'll just mention it in the message.
            pass
        if 'currencies' in reward:
            for currency, amount in reward['currencies'].items():
                char_data.setdefault('currencies', {})[currency] = char_data['currencies'].get(currency, 0) + amount
        if 'items' in reward:
            for item, amount in reward['items'].items():
                char_data.setdefault('items', {})[item] = char_data['items'].get(item, 0) + amount

        # 4. Mark as claimed
        char_data.setdefault('claimed_achievements', []).append(achievement_id)

        # 5. Save data
        all_data[character_name] = char_data
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        return f"Récompense pour '{achievement['title']}' réclamée !"