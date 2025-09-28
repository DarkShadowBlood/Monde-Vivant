import json
from pathlib import Path
import re

def process_raw_data():
    """
    Lit tous les fichiers JSON bruts depuis le dossier d'export,
    les transforme, les regroupe par catégorie et les sauvegarde
    dans un unique fichier de base de données.
    """
    # Définition des chemins
    base_dir = Path(__file__).resolve().parent.parent
    source_dir = base_dir.parent / "information" / "JSON_Export_Par_Ligne"
    output_dir = base_dir / "gym"
    output_file = output_dir / "exercices_db.json"

    # S'assurer que le dossier de sortie existe
    output_dir.mkdir(exist_ok=True)

    if not source_dir.exists():
        print(f"❌ ERREUR: Le dossier source '{source_dir}' n'a pas été trouvé.")
        return

    print(f"🔍 Lecture des fichiers depuis : {source_dir}")

    all_exercises_by_category = {}
    files_processed = 0

    # Parcourir tous les fichiers JSON dans le dossier source
    for json_file in source_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Transformer les données brutes en une structure propre
            exercise = {
                "id": raw_data.get("Key", "").strip(),
                "nom": raw_data.get("Exercice", "Sans nom").strip(),
                "category": raw_data.get("Category", "Non classé").strip(),
                "focus": raw_data.get("Focus", "").strip(),
                
                # Convertir les chaînes de caractères en listes
                "materiel_requis": [item.strip() for item in raw_data.get("Equipement", "").split(',') if item.strip()],
                
                "description": raw_data.get("Description", "").strip(),
                
                # Convertir les blocs de texte en listes de lignes
                "instructions": [line.strip() for line in raw_data.get("Explication", "").split('\n') if line.strip()],
                "conseils": [line.strip() for line in raw_data.get("Conseils_Expert", "").split('\n') if line.strip()],
                
                "variantes": raw_data.get("Variantes", "").strip(),
                
                # Construire une URL d'image propre
                "image_url": f"assets/exercices/{raw_data.get('Image', '').strip()}" if raw_data.get('Image') else "",
                "video_url": raw_data.get("Video_URL", "").strip(),
                
                # Regrouper les notations
                "ratings": {
                    "difficulte": int(raw_data.get("Notation_Difficulte", 0) or 0),
                    "efficacite": int(raw_data.get("Notation_Efficacite", 0) or 0)
                },
                
                # Regrouper les éléments de gamification
                "gamification": {
                    "narration": raw_data.get("LitRPG_Narration", "").strip(),
                    "stats": {
                        "force": int(raw_data.get("Stat_Force", 0) or 0),
                        "endurance": int(raw_data.get("Stat_Endurance", 0) or 0),
                        "agilite": int(raw_data.get("Stat_Agilite", 0) or 0),
                        "vitalite": int(raw_data.get("Stat_Vitalite", 0) or 0),
                        "technique": int(raw_data.get("Stat_Technique", 0) or 0),
                    },
                    "xp_value": int(raw_data.get("XP_Value", 0) or 0)
                }
            }

            # Ajouter l'exercice à la bonne catégorie
            category = exercise["category"]
            if category not in all_exercises_by_category:
                all_exercises_by_category[category] = []
            
            all_exercises_by_category[category].append(exercise)
            files_processed += 1

        except Exception as e:
            print(f"⚠️ AVERTISSEMENT: Impossible de traiter le fichier '{json_file.name}'. Erreur: {e}")

    if files_processed > 0:
        # Trier les catégories par ordre alphabétique
        sorted_db = dict(sorted(all_exercises_by_category.items()))

        # Sauvegarder la base de données unifiée
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_db, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Succès ! {files_processed} exercices traités.")
            print(f"   Base de données sauvegardée dans : {output_file}")
        except Exception as e:
            print(f"❌ ERREUR: Impossible de sauvegarder le fichier de base de données. Erreur: {e}")
    else:
        print("\nℹ️ Aucun fichier n'a été traité. Vérifiez le contenu du dossier source.")


if __name__ == "__main__":
    print("==============================================")
    print("==   Raffinerie de Données d'Exercices Gym  ==")
    print("==============================================")
    process_raw_data()
    print("\nAppuyez sur Entrée pour fermer...")
    input()
