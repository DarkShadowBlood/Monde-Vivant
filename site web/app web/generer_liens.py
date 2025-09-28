from pathlib import Path
import os
import json

# --- Résolution des raccourcis Windows (.lnk)
try:
    import win32com.client

    def resolve_shortcut(path):
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(path))
        return Path(shortcut.Targetpath)
except ImportError:
    def resolve_shortcut(path):
        return None

# --- Configuration
TARGET_DIR = "../information" # Dossier contenant les données à analyser (relatif au script)
JSON_OUTPUT_FILE = "liens.json" # Fichier de données JSON généré

valid_extensions = [".html", ".md", ".jpg", ".jpeg", ".png", ".gif", ".webp"]

ICONS_BY_EXT = {
    ".html": "🌐",
    ".md": "📝",
    ".jpg": "🖼️",
    ".jpeg": "🖼️",
    ".png": "🖼️",
    ".gif": "🎞️",
    ".webp": "🖼️",
    ".json": "📄",
}

MD_TEMPLATE = """# Analyse de la séance du {date} à {time}

## 📝 Notes et Sensations

*   **Sensations générales :** (ex: En forme, fatigué, motivé...)
*   **Météo :** (ex: Ensoleillé, venteux, froid...)
*   **Objectif de la séance :** (ex: Endurance, vitesse, récupération...)
*   **Événements notables :** (ex: Crevaison, belle vue, difficulté dans une montée...)

---

## 📊 Données brutes (pour référence)

```json
{data}
```
"""

def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")) # Pas utilisé pour le moment, mais gardé pour l'avenir

def get_file_icon(file_path: Path) -> str:
    return ICONS_BY_EXT.get(file_path.suffix.lower(), "📄")

def build_file_tree(folder: Path, base_path: Path) -> list:
    """
    Construit une structure de données (liste de dictionnaires) représentant l'arborescence des fichiers.
    """
    items = []
    for file in sorted(folder.iterdir()):
        # Ignorer les fichiers et dossiers cachés ou système
        if file.name.startswith('.') or file.name == '__pycache__':
            continue

        if file.is_dir():
            # Récursion dans les sous-dossiers
            children = build_file_tree(file, base_path)
            # N'ajoute le dossier que s'il n'est pas vide
            if children:
                items.append({
                    "type": "folder",
                    "name": file.name,
                    "children": children
                })
        else:
            target = None
            display_path = None

            if file.suffix.lower() == ".lnk":
                resolved = resolve_shortcut(file)
                if resolved and resolved.exists() and resolved.suffix.lower() in valid_extensions: # type: ignore
                    target = resolved                    
                    display_path = os.path.relpath(resolved, base_path).replace("\\", "/") # type: ignore
            elif file.suffix.lower() in valid_extensions:
                target = file
                display_path = os.path.relpath(file, base_path).replace("\\", "/")

            if target and display_path:
                items.append({
                    "type": "file",
                    "name": target.stem.replace('_', ' ').replace(os.sep, ' '),
                    "icon": get_file_icon(target),
                    "path": "../information/" + display_path
                })
    return items

def gather_activities_data(base_path: Path) -> list:
    """
    Parcourt les dossiers pour trouver les fichiers JSON d'activité et en extraire les données.
    """
    activities = []
    for json_file in sorted(base_path.rglob("*_workout_log.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Cherche les données d'activité. D'abord dans une clé "apex", sinon à la racine.
            activity_data = None
            if 'apex' in data:
                activity_data = data['apex']
            elif 'activity' in data: # Si la clé 'apex' n'existe pas, on vérifie la présence de 'activity'
                activity_data = data
            else: # Sinon, on suppose que les données sont directement à la racine
                activity_data = data

            if activity_data:
                html_path = json_file.with_suffix(".html")
                if not html_path.exists():
                    print(f"[AVERTISSEMENT] Fichier HTML non trouvé pour {json_file.name}. L'activité ne sera pas ajoutée.")
                    continue

                # --- CRÉATION/MISE À JOUR DU FICHIER .MD D'ANALYSE ---
                md_path = json_file.with_name(f"{json_file.stem.replace('_workout_log', '')}_analyse_format.md")
                if not md_path.exists():
                    print(f"[INFO] Création du fichier d'analyse : {md_path.name}")
                    try:
                        template_content = MD_TEMPLATE.format(
                            date=activity_data.get("date", "N/A"),
                            time=activity_data.get("timeStart", "N/A"),
                            data=json.dumps(activity_data, indent=2, ensure_ascii=False)
                        )
                        with open(md_path, 'w', encoding='utf-8') as md_f:
                            md_f.write(template_content)
                    except Exception as e:
                        print(f"[ERREUR] Impossible de créer le fichier .md {md_path.name}: {e}")

                activities.append({
                    "type": activity_data.get("activity", activity_data.get("nom_exercice", "N/A")),
                    "date": activity_data.get("date", activity_data.get("date_activite", "N/A")),
                    "time": activity_data.get("timeStart", activity_data.get("heure_activite", "N/A")),
                    "duration": activity_data.get("apexDuration", activity_data.get("temps", "00:00")),
                    "calories": activity_data.get("calories", "0"),
                    "distance": activity_data.get("distance", "0"),
                    "avg_hr": activity_data.get("avgHR", activity_data.get("fc_moyenne", "0")),
                    "max_hr": activity_data.get("maxHR", activity_data.get("fc_max", "0")),
                    "html_file": "../information/" + os.path.relpath(html_path, base_path).replace("\\", "/"),
                    "location": activity_data.get("location", ""),
                    "weather": activity_data.get("weather", ""),
                    "serie": activity_data.get("serie", ""),
                    "notes": activity_data.get("notes", ""),
                    "heartRateZones": activity_data.get("heartRateZones", None) # Ajout des zones de FC
                })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[AVERTISSEMENT] Impossible de traiter {json_file}: {e}")
    return activities

def gather_goals_data(base_path: Path) -> list:
    """
    Parcourt les dossiers pour trouver les fichiers JSON d'objectifs et en extraire les données.
    """
    all_daily_goals = []
    # Cible spécifiquement le dossier des objectifs pour éviter de scanner des fichiers non désirés.
    goals_folder = base_path / "activité" / "Objectif"
    if not goals_folder.exists():
        return [] # Retourne une liste vide si le dossier n'existe pas
    for json_file in sorted(goals_folder.rglob("objectif_log_*.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Les données d'objectifs sont attendues dans une clé "apex" contenant une liste
            if 'apex' in data and isinstance(data['apex'], list):
                for entry in data['apex']:
                    all_daily_goals.append({
                        "date": entry.get("date_activite", "N/A"),
                        "calories": entry.get("calories", "0"),
                        "steps": entry.get("pas", "0"),
                        # Remplacer la virgule par un point pour le format numérique
                        "distance": entry.get("distance", "0.0").replace(',', '.')
                    })
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[AVERTISSEMNT] Impossible de traiter le fichier d'objectifs {json_file}: {e}")

    return all_daily_goals

def gather_analysis_data(activities: list, goals: list) -> list:
    """
    Combine les données d'activités avec les données d'objectifs correspondantes par date.
    """
    # Crée un dictionnaire de buts pour un accès rapide par date
    goals_by_date = {goal['date']: goal for goal in goals}
    
    analysis_data = []
    for activity in activities:
        # Copie l'activité pour ne pas modifier l'original
        activity_with_context = activity.copy()
        
        # Trouve l'objectif correspondant à la date de l'activité
        daily_goal = goals_by_date.get(activity['date'])
        
        # Ajoute les données de l'objectif à l'objet d'activité
        if daily_goal:
            activity_with_context['daily_goal'] = daily_goal
        else:
            activity_with_context['daily_goal'] = None
            
        analysis_data.append(activity_with_context)
        
    return analysis_data

def gather_sante_data(base_path: Path) -> list:
    """
    Parcourt le dossier 'santé' pour trouver les fichiers JSON et les compiler.
    """
    all_sante_entries = []
    sante_folder = base_path / "santé"
    if not sante_folder.exists():
        print("[INFO] Dossier 'santé' non trouvé, la génération de sante.json est ignorée.")
        return []

    for json_file in sorted(sante_folder.rglob("sante_log_*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_sante_entries.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[AVERTISSEMENT] Impossible de traiter {json_file}: {e}")
    
    return sorted(all_sante_entries, key=lambda x: x.get('date', ''))

# --- Point de départ ---
# Le dossier de sortie pour les fichiers JSON est le dossier où se trouve ce script.
OUTPUT_DIR = Path(__file__).parent

# --- Point de départ
base_path = Path(TARGET_DIR)
if not base_path.exists():
    print(f"[ERREUR] Le dossier '{TARGET_DIR}' est introuvable.")
    exit(1)

# --- 1. Générer le fichier de données `activities.json` ---
all_activities = gather_activities_data(base_path)
activities_json_path = OUTPUT_DIR / "activities.json"
with open(activities_json_path, "w", encoding="utf-8") as f_json:
    json.dump(all_activities, f_json, indent=2, ensure_ascii=False)
print(f"[OK] {len(all_activities)} activités trouvées et enregistrées dans {activities_json_path}.")

# --- 2. Générer le fichier de données `activities_enriched.json` ---
# Ce fichier est une copie de activities.json mais est destiné à évoluer
# avec plus de données pour la gamification. Pour l'instant, il est identique.
activities_enriched_json_path = OUTPUT_DIR / "activities_enriched.json"
with open(activities_enriched_json_path, "w", encoding="utf-8") as f_json:
    json.dump(all_activities, f_json, indent=2, ensure_ascii=False)
print(f"[OK] {len(all_activities)} activités enrichies enregistrées dans {activities_enriched_json_path}.")

# --- 3. Générer le fichier de données `objectifs.json` ---
all_goals = gather_goals_data(base_path)
goals_json_path = OUTPUT_DIR / "objectifs.json"
with open(goals_json_path, "w", encoding="utf-8") as f_json:
    json.dump(all_goals, f_json, indent=2, ensure_ascii=False)
print(f"[OK] {len(all_goals)} entrées d'objectifs trouvées et enregistrées dans {goals_json_path}.")

# --- 4. Générer le fichier de données `analysis_data.json` ---
analysis_data = gather_analysis_data(all_activities, all_goals)
analysis_json_path = OUTPUT_DIR / "analysis_data.json"
with open(analysis_json_path, "w", encoding="utf-8") as f_json:
    json.dump(analysis_data, f_json, indent=2, ensure_ascii=False)
print(f"[OK] {len(analysis_data)} activités enrichies enregistrées dans {analysis_json_path}.")

# --- 1.quater Générer le fichier de données `sante.json` ---
all_sante_data = gather_sante_data(base_path)
sante_json_path = Path(__file__).parent / "sante.json"
with open(sante_json_path, "w", encoding="utf-8") as f_json: # Correction: garder le chemin original pour sante.json
    json.dump(all_sante_data, f_json, indent=2, ensure_ascii=False)
print(f"[OK] {len(all_sante_data)} entrées de santé trouvées et enregistrées dans {sante_json_path}.")

# --- 5. Construire l'arborescence des fichiers ---
file_tree = build_file_tree(base_path, base_path)

# --- 6. Sauvegarder l'arborescence dans liens.json ---
json_output_path = OUTPUT_DIR / JSON_OUTPUT_FILE
with open(json_output_path, "w", encoding="utf-8") as f_json:
    json.dump(file_tree, f_json, indent=2, ensure_ascii=False)
print(f"[OK] Arborescence des fichiers enregistrée dans {json_output_path}.")

print("\n--- Opération terminée ---")
