import re
from pathlib import Path
import sys
import os

# --- Configuration ---
# Le script s'attend à être exécuté depuis le dossier 'app web'

APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
LAUNCH_PATH = APP_WEB_DIR / "lancer_site.bat"

def toggle_windows_notifications(script_path: Path, action: str):
    """
    Commente ou décommente les lignes de notification Windows dans un script PowerShell.

    :param script_path: Chemin vers le fichier .ps1.
    :param action: 'activer' ou 'desactiver'.
    """
    # Cibles textuelles pour identifier les lignes, même si elles sont commentées
    target_logo = '$logoPath ='
    target_toast = 'New-BurntToastNotification'
    targets = [target_logo, target_toast]
    
    _toggle_notification_lines(script_path, action, targets, "Windows")

def toggle_windows_click_action(script_path: Path, action: str):
    """
    Ajoute ou retire l'action de clic (-Launch) sur les notifications Windows.

    :param script_path: Chemin vers le fichier .ps1.
    :param action: 'activer' ou 'desactiver'.
    """
    try:
        lines = script_path.read_text(encoding='utf-8-sig').splitlines()
        new_lines = []
        modified = False
        
        target_toast = 'New-BurntToastNotification'
        launch_param = f'-Launch "{str(LAUNCH_PATH)}"'

        for line in lines:
            stripped_line = line.strip()
            if target_toast in stripped_line:
                has_launch = launch_param in line
                
                if action == 'activer' and not has_launch:
                    # Ajoute le paramètre -Launch à la fin de la ligne
                    new_lines.append(line + f" {launch_param}")
                    modified = True
                elif action == 'desactiver' and has_launch:
                    # Retire le paramètre -Launch de la ligne
                    new_lines.append(line.replace(f" {launch_param}", ""))
                    modified = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if modified:
            script_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8-sig')
            print(f"✅ Action de clic {action}e pour les notifications Windows dans : {script_path.name}")
        else:
            print(f"ℹ️  Aucun changement nécessaire pour l'action de clic dans : {script_path.name}")

    except Exception as e:
        print(f"❌ Erreur lors de la modification de l'action de clic pour '{script_path.name}': {e}")

def toggle_ntfy_notifications(script_path: Path, action: str):
    """
    Commente ou décommente les lignes de notification ntfy.sh dans un script PowerShell.

    :param script_path: Chemin vers le fichier .ps1.
    :param action: 'activer' ou 'desactiver'.
    """
    # Cibles textuelles pour identifier les lignes du bloc ntfy
    target_headers_start = '$ntfyHeaders = @{'
    target_invoke = 'Invoke-RestMethod -Uri "https://ntfy.sh/'
    targets = [target_headers_start, target_invoke]
    
    _toggle_notification_block(script_path, action, targets, "ntfy.sh")

def _toggle_notification_lines(script_path: Path, action: str, targets: list, notif_name: str):
    """
    Logique générique pour (dé)commenter des lignes spécifiques.
    """
    try:
        # Lire le contenu avec l'encodage utf-8-sig pour préserver les caractères spéciaux
        # et éviter les problèmes de BOM (Byte Order Mark).
        lines = script_path.read_text(encoding='utf-8-sig').splitlines()
        
        new_lines = []
        modified = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Vérifie si la ligne contient l'une des cibles
            is_target_line = any(target in stripped_line for target in targets)
            if not is_target_line:
                new_lines.append(line)
                continue

            # Détermine si la ligne est actuellement commentée
            is_commented = stripped_line.startswith('#')
            
            if action == 'activer':
                if is_commented:
                    # Supprime le premier '#' et l'espace qui suit
                    new_lines.append(re.sub(r'#\s?', '', line, 1))
                    modified = True
                else:
                    new_lines.append(line) # Déjà activé, on ne change rien
            
            elif action == 'desactiver':
                if not is_commented:
                    # Ajoute un commentaire au début de la ligne
                    indentation = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indentation}# {stripped_line}")
                    modified = True
                else:
                    new_lines.append(line) # Déjà désactivé, on ne change rien

        if modified:
            script_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8-sig')
            print(f"✅ Notifications {notif_name} {action}es pour : {script_path.name}")
        else:
            print(f"ℹ️  Aucun changement nécessaire pour : {script_path.name}")

    except Exception as e:
        print(f"❌ Erreur lors du traitement de '{script_path.name}': {e}")

def _toggle_notification_block(script_path: Path, action: str, targets: list, notif_name: str):
    """
    Logique générique pour (dé)commenter un bloc de code entier.
    Le bloc est identifié par une ligne de début et une ligne de fin.
    """
    try:
        lines = script_path.read_text(encoding='utf-8-sig').splitlines()
        
        new_lines = []
        modified = False
        in_block = False
        
        for line in lines:
            stripped_line = line.strip()
            is_commented = stripped_line.startswith('#')
            
            # Détection du début et de la fin du bloc
            is_start_line = targets[0] in stripped_line
            is_end_line = targets[1] in stripped_line

            if is_start_line:
                in_block = True

            if in_block:
                if action == 'activer':
                    if is_commented:
                        new_lines.append(re.sub(r'#\s?', '', line, 1))
                        modified = True
                    else:
                        new_lines.append(line)
                elif action == 'desactiver':
                    if not is_commented:
                        indentation = line[:len(line) - len(line.lstrip())]
                        new_lines.append(f"{indentation}# {stripped_line}")
                        modified = True
                    else:
                        new_lines.append(line)
            else:
                new_lines.append(line)

            if is_end_line:
                in_block = False

        if modified:
            script_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8-sig')
            print(f"✅ Notifications {notif_name} {action}es pour : {script_path.name}")
        else:
            print(f"ℹ️  Aucun changement nécessaire pour : {script_path.name}")
    except Exception as e:
        print(f"❌ Erreur lors du traitement de '{script_path.name}': {e}")

def main():
    """Fonction principale pour lancer le processus."""
    while True:
        # Nettoie la console pour une meilleure lisibilité
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("====================================================")
        print("  Gestion des Notifications pour les Rappels")
        print("====================================================")
        print("\nCe script va modifier tous les fichiers de rappel (.ps1).")
        print("\nChoisissez une option :\n")
        print("  1. Activer les notifications Windows")
        print("  2. Désactiver les notifications Windows")
        print("  3. Activer les notifications ntfy.sh")
        print("  4. Désactiver les notifications ntfy.sh")
        print("  5. Activer le clic sur les notifications Windows (lancer l'app)")
        print("  6. Désactiver le clic sur les notifications Windows")
        print("\n  0. Quitter")
        print("----------------------------------------------------")
        
        choix = input("Votre choix : ")

        action = None
        target_function = None

        if choix == '1':
            action = 'activer'
            target_function = toggle_windows_notifications
        elif choix == '2':
            action = 'desactiver'
            target_function = toggle_windows_notifications
        elif choix == '3':
            action = 'activer'
            target_function = toggle_ntfy_notifications
        elif choix == '4':
            action = 'desactiver'
            target_function = toggle_ntfy_notifications
        elif choix == '5':
            action = 'activer'
            target_function = toggle_windows_click_action
        elif choix == '6':
            action = 'desactiver'
            target_function = toggle_windows_click_action
        elif choix == '0':
            print("\nAu revoir !")
            break
        else:
            input("\nChoix invalide. Appuyez sur Entrée pour réessayer...")
            continue

        # Extrait le nom de la notification du nom de la fonction pour l'affichage
        if 'click' in target_function.__name__:
            notif_type_name = "Clic Windows"
        else:
            notif_type_name = target_function.__name__.split('_')[1].replace('notifications', '').upper()
            if notif_type_name == "NTFY": notif_type_name = "ntfy.sh"
        
        
        print(f"\n--- Tentative de {action} les notifications {notif_type_name} pour tous les scripts ---")
        for ps_file in SCHEDULED_TASKS_DIR.glob("*.ps1"):
            target_function(ps_file, action)
        print("--- Opération terminée. ---")
        input("\nAppuyez sur Entrée pour retourner au menu...")

if __name__ == "__main__":
    main()
