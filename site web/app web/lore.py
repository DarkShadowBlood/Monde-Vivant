import re
from config import LORE_FILE_PATH

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
