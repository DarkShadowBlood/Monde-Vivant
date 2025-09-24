"""
Ce module gère le "lore" des coachs, c'est-à-dire leur personnalité et leur histoire.

Il est responsable de :
- Charger les fiches de personnalité des coachs depuis un fichier Markdown.
- Stocker ces informations dans une variable globale `COACH_LORE` pour un accès
  facile depuis les autres parties de l'application.

Le fichier de lore est un simple fichier Markdown où chaque coach est défini
dans une section de niveau 2 (##).
"""
import re
from config import LORE_FILE_PATH

# --- Données des coachs ---

# Variable globale pour stocker les fiches de personnalité chargées.
# C'est un dictionnaire où la clé est le nom du coach et la valeur est sa fiche.
COACH_LORE = {}

# (Obsolète) Dictionnaire simple de styles, conservé pour rétrocompatibilité potentielle.
# Le lore complet est maintenant chargé depuis le fichier Markdown.
coach_styles = {
    "Varkis": "brutal, direct, comme un guerrier survivant",
    "Kara": "mystique, poétique, comme une rôdeuse de l'ombre",
    "Aegis": "rationnel, analytique, comme une IA bienveillante"
}

def load_coach_lore():
    """
    Charge les fiches de personnalité des coachs depuis le fichier de lore.

    Cette fonction lit le fichier Markdown spécifié dans `LORE_FILE_PATH`, le découpe
    en sections (une par coach), et peuple le dictionnaire global `COACH_LORE`.
    Elle est appelée au démarrage du serveur pour que les données soient prêtes.

    Returns:
        dict: Le dictionnaire `COACH_LORE` rempli avec les données des coachs.
              Retourne un dictionnaire vide en cas d'erreur ou si le fichier est introuvable.
    """
    global COACH_LORE
    if not LORE_FILE_PATH.exists():
        print(f"AVERTISSEMENT: Fichier de lore non trouvé à '{LORE_FILE_PATH}'. Aucun coach ne sera chargé.")
        COACH_LORE = {}
        return COACH_LORE

    try:
        with open(LORE_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sépare le contenu en sections basées sur les titres de niveau 2 (##)
        sections = re.split(r'\n## ', content)
        personalities = {}
        for section in sections:
            if 'Archétype' in section:
                # Extrait le nom du coach depuis la ligne de titre (ex: "Varkis – Le Survivant")
                title_line = section.split('\n')[0].strip()
                name = re.split(r'\s*–\s*', title_line)[0].strip()
                if name:
                    personalities[name] = "## " + section
        
        COACH_LORE = personalities
        if COACH_LORE:
            print(f"Succès : {len(COACH_LORE)} fiches de lore chargées pour les coachs : {', '.join(COACH_LORE.keys())}")
        else:
            print("AVERTISSEMENT: Le fichier de lore a été trouvé, mais aucun coach n'a pu être parsé.")
        return COACH_LORE
    except Exception as e:
        print(f"ERREUR critique lors du chargement du fichier de lore : {e}")
        COACH_LORE = {}
        return COACH_LORE