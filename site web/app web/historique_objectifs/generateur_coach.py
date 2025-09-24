import os
import json
import re
import requests
import argparse
import webbrowser

# --- Configuration des chemins ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COACH_ENGINE_FILE_PATH = os.path.join(SCRIPT_DIR, 'coach_engine.json')
LORE_FILE_NAME = 'coach_engine_lore-chatgpt.md'
LORE_FILE_PATH = os.path.join(SCRIPT_DIR, LORE_FILE_NAME)

# --- Configuration des APIs ---
API_CONFIGS = {
    "mistral": {
        "url": 'https://api.mistral.ai/v1/chat/completions',
        "model": 'mistral-large-latest'
    }
}


def extract_personalities(filepath):
    """Extrait les fiches de personnalités du fichier lore."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Erreur : Le fichier {filepath} n'a pas été trouvé.")
        return None

    sections = re.split(r'\n## ', content)
    personalities = {}

    for section in sections:
        if 'Archétype' in section:
            title_line = section.split('\n')[0].strip()
            name = re.split(r'\s*–\s*', title_line)[0].strip()
            personalities[name] = "## " + section

    if not personalities:
        print("Aucune personnalité avec un 'Archétype' n'a été trouvée dans le fichier lore.")
        return None

    return personalities

def generate_prompt(personality_lore, json_structure_doc):
    """Construit le prompt pour l'API Mistral."""
    combination_instruction = ""
    if "Fiches des Personnalités à combiner" in personality_lore:
        combination_instruction = "Tu dois fusionner leurs tons, styles et vocabulaires de manière cohérente."

    prompt = f"""
Objectif : Tu es un générateur de base de données pour un coach sportif virtuel.
Ta tâche est de créer une configuration JSON complète pour une nouvelle personnalité de coach.
La réponse doit être UNIQUEMENT un bloc de code JSON valide, sans aucun texte ou explication avant ou après.
Le JSON doit contenir une clé racine 'personalities' qui contient les objets de chaque personnalité.

Voici la documentation de la structure JSON que tu dois impérativement respecter :
---
{json_structure_doc}
---

Maintenant, voici la ou les fiches de personnalité pour lesquelles tu dois générer la configuration.
{combination_instruction}
Tu dois t'imprégner de cette personnalité et créer des règles et des textes qui correspondent PARFAITEMENT à son ton, son style et son vocabulaire.

Fiche(s) de Personnalité :
---
{personality_lore}
---

Instructions de génération :
1.  Crée une clé principale pour la personnalité (en minuscules, ex: "varkis" ou "varkis_kara" pour une combinaison) à l'intérieur de l'objet 'personalities'.
2.  Le "name" doit être le nom complet (ex: "Varkis – Maraudeur Survivant" ou "Varkis + Kara" pour une combinaison).
3.  Crée au moins 8 règles ('rules') distinctes et pertinentes avec des priorités variées.
4.  Pour chaque règle, fournis au moins 5 à 10 options de texte ('texts') uniques et créatives.
5.  Inclus au moins 5 messages par défaut ('default').
6.  Assure-toi que le JSON final est valide et complet.

Commence la génération du JSON maintenant.
"""
    return prompt

def get_json_structure_documentation(filepath):
    """Extrait la partie documentation de la structure JSON du fichier lore."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return ""
    
    structure_doc = content.split("## Référentiel Lore")[0]
    return structure_doc.strip()

def load_main_coach_engine(llm_provider="mistral"):
    """Charge le fichier coach_engine.json principal ou en crée un vide."""
    if os.path.exists(COACH_ENGINE_FILE_PATH):
        try:
            with open(COACH_ENGINE_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Avertissement : Impossible de lire {COACH_ENGINE_FILE_PATH}. Un nouveau fichier sera créé. Erreur : {e}")
            return {"llm_source": llm_provider, "personalities": {}}
    else:
        print(f"Info : Le fichier {COACH_ENGINE_FILE_PATH} n'existe pas. Il va être créé.")
        # Structure par défaut si le fichier n'existe pas
        return {"llm_source": llm_provider, "personalities": {}}

def delete_personality_interactive():
    """Fonction interactive pour supprimer une personnalité de coach_engine.json."""
    main_coach_engine = load_main_coach_engine()
    personalities = main_coach_engine.get('personalities', {})

    if not personalities:
        print("\nAucune personnalité à supprimer dans coach_engine.json.")
        return

    print("\nQuelle personnalité souhaitez-vous supprimer ?")
    
    # Crée une liste des clés pour un accès par index
    p_keys = list(personalities.keys())
    for i, key in enumerate(p_keys, 1):
        name = personalities[key].get('name', key)
        print(f"  {i}. {name} (clé: {key})")
    
    print("  0. Annuler")

    try:
        choice_str = input("\nEntrez le numéro de la personnalité à supprimer : ")
        choice = int(choice_str)

        if choice == 0:
            print("Opération annulée.")
            return
        
        if 1 <= choice <= len(p_keys):
            key_to_delete = p_keys[choice - 1]
            name_to_delete = personalities[key_to_delete].get('name', key_to_delete)
            
            confirm = input(f"Êtes-vous sûr de vouloir supprimer définitivement '{name_to_delete}' ? [o/N] : ").lower().strip()
            
            if confirm == 'o':
                del main_coach_engine['personalities'][key_to_delete]
                with open(COACH_ENGINE_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(main_coach_engine, f, indent=2, ensure_ascii=False)
                print(f"\nSuccès ! La personnalité '{name_to_delete}' a été supprimée.")
            else:
                print("Suppression annulée.")
        else:
            print("Choix invalide.")
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro.")

def call_llm_api(provider, api_key, prompt):
    """Appelle l'API LLM spécifiée et retourne le JSON généré."""
    api_config = API_CONFIGS[provider]
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    data = {
        'model': api_config['model'],
        'messages': [{'role': 'user', 'content': prompt}],
        'response_format': {'type': 'json_object'}
    }

    print(f"Envoi de la requête à l'API {provider.capitalize()}...")
    try:
        response = requests.post(api_config['url'], headers=headers, json=data, timeout=180)
        response.raise_for_status()
        return json.loads(response.json()['choices'][0]['message']['content'])
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API {provider.capitalize()} : {e}")
    except json.JSONDecodeError:
        print(f"Erreur : La réponse de l'API {provider.capitalize()} n'était pas un JSON valide.")
    except (IndexError, KeyError):
        print(f"Erreur : Structure de réponse API inattendue de {provider.capitalize()}.")
    return None

def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(description="Générateur de coach JSON via l'API Mistral.")
    parser.add_argument('--api-key', type=str, help="Votre clé API Mistral.")
    parser.add_argument('--personality', type=str, help="Le nom de la personnalité à générer (ex: Varkis, \"Varkis + Kara\").")
    parser.add_argument('--delete', action='store_true', help="Lance le mode de suppression de personnalité.")
    args = parser.parse_args()

    llm_choice = "mistral"
    API_KEY = args.api_key or os.getenv('MISTRAL_API_KEY')

    if not API_KEY:
        print(f"Erreur : Clé API non fournie pour Mistral. Utilisez --api-key ou définissez la variable d'environnement MISTRAL_API_KEY.")
        return
        
    personalities = extract_personalities(LORE_FILE_PATH)
    if not personalities:
        return

    if args.delete:
        delete_personality_interactive()
        return

    selected_name = args.personality
    if not selected_name:
        print("Personnalités trouvées dans le fichier lore :")
        for i, name in enumerate(personalities.keys(), 1):
            print(f"  {i}. {name}")
        try:
            choice = int(input("\nPour quelle personnalité voulez-vous générer un coach ? (entrez le numéro) : "))
            selected_name = list(personalities.keys())[choice - 1]
        except (ValueError, IndexError):
            print("Sélection invalide.")
            return

    print(f"\nGénération du coach pour : {selected_name}")
    lore_to_use = get_lore_for_personality(selected_name, personalities)
    if not lore_to_use:
        return

    json_structure_doc = get_json_structure_documentation(LORE_FILE_PATH)
    if not json_structure_doc:
        print("Avertissement : Impossible de lire la documentation de la structure JSON.")

    prompt = generate_prompt(lore_to_use, json_structure_doc)

    generated_json = call_llm_api(llm_choice, API_KEY, prompt)

    if not generated_json:
        print("Abandon de la fusion en raison d'une erreur de l'API.")
        return

    # --- NOUVELLE LOGIQUE DE FUSION ---
    # 1. Charger le fichier coach_engine.json principal
    main_coach_engine = load_main_coach_engine(llm_choice)

    # 2. Extraire la nouvelle personnalité générée et définir la clé nous-mêmes
    # On ne fait plus confiance à l'IA pour la clé, on la crée à partir de la sélection.
    try:
        generated_personality_key = list(generated_json['personalities'].keys())[0]
        new_personality_data = generated_json['personalities'][generated_personality_key]
    except (KeyError, IndexError):
        print(f"Erreur: La structure JSON retournée par {llm_choice.capitalize()} est invalide.")
        print(json.dumps(generated_json, indent=2))
        return
        
    # Création d'une clé fiable et standardisée
    final_personality_key = selected_name.lower().replace(' ', '').replace('+', '_')

    print(f"\nFusion de la personnalité '{final_personality_key}' dans coach_engine.json...")

    # 3. Ajouter ou mettre à jour la personnalité dans le fichier principal
    main_coach_engine['personalities'][final_personality_key] = new_personality_data

    # Mettre à jour la source LLM globale pour refléter la dernière génération
    main_coach_engine['llm_source'] = llm_choice
        
    # 3.5 (AMÉLIORATION) : Ajouter la description du lore pour une utilisation future
    main_coach_engine['personalities'][final_personality_key]['description'] = lore_to_use

    # 4. Sauvegarder le fichier principal mis à jour
    with open(COACH_ENGINE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(main_coach_engine, f, indent=2, ensure_ascii=False)

    print(f"\nSuccès ! Le coach a été généré et fusionné dans : {COACH_ENGINE_FILE_PATH}")
    # --- FIN DE LA NOUVELLE LOGIQUE ---

def get_lore_for_personality(selected_name, personalities):
    """Récupère le texte de lore pour une ou plusieurs personnalités."""
    if '+' in selected_name:
        individual_names = [name.strip() for name in selected_name.split('+')]
        combined_lore_parts = []
        all_found = True
        for name in individual_names:
            found_lore = None
            for key, lore_text in personalities.items():
                if key.lower() == name.lower():
                    found_lore = lore_text
                    break
            if found_lore:
                combined_lore_parts.append(found_lore)
            else:
                print(f"Erreur: Personnalité individuelle ''{name}'' non trouvée.")
                all_found = False
                break
        if not all_found:
            return None
        lore_to_use = "\n\n---\n\n".join(combined_lore_parts)
        return "## Fiches des Personnalités à combiner:\n\n" + lore_to_use
    else:
        found = False
        for key, lore_text in personalities.items():
            if key.lower() == selected_name.lower():
                return lore_text
        if not found: # Should not happen if selected_name comes from the list
            print(f"Erreur : Personnalité ''{selected_name}'' non trouvée.")
            return None

if __name__ == '__main__':
    main()
