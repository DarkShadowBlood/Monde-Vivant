import sys
import re
import argparse
from pathlib import Path
import subprocess
from datetime import date, datetime
import logging
import time
import json

# --- Configuration ---
APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
LOG_FILE = APP_WEB_DIR / "win_notification_sender.log"
HISTORY_FILE = APP_WEB_DIR / "win_notifications_history.json"

# --- Configuration du logging ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

try:
    from win10toast_click import ToastNotifier

except ImportError:
    sys.exit(
        "ERREUR: Le package 'win10toast-click' est manquant. "
        "Veuillez l'installer avec la commande : pip install win10toast-click"
    )

def log_notification_to_history(title: str, message: str, notif_type: str):
    """Ajoute une notification à l'historique JSON."""
    try:
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = [] # Fichier corrompu, on repart de zéro
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": notif_type,
            "title": title,
            "message": message
        }
        history.insert(0, new_entry) # Ajoute au début

        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Impossible d'écrire dans l'historique des notifications : {e}")


def find_and_display_todays_notification():
    """
    Scanne le dossier des tâches, trouve le script du jour,
    extrait les informations et affiche la notification Windows.
    """
    today_str = date.today().strftime('%Y-%m-%d')
    logging.info(f"Recherche de scripts pour la date : {today_str}")

    # 1. Parcourir tous les scripts .ps1 dans le dossier des tâches
    for script_path in SCHEDULED_TASKS_DIR.glob("*.ps1"):
        # 2. Vérifier si la date du jour est dans le nom du fichier
        if today_str in script_path.name:
            found_script = True
            logging.info(f"Script du jour trouvé : {script_path.name}")
            
            try:
                # 3. Lire le contenu du script pour extraire le coach et le message
                content = script_path.read_text(encoding='utf-8-sig')
                coach_match = re.search(r"\$coach = '([^']*)'", content)
                message_match = re.search(r"\$message = @'\n(.*?)\n'@", content, re.DOTALL)
                
                if not coach_match or not message_match:
                    logging.error(f"Impossible d'extraire le coach ou le message de {script_path.name}.")
                    continue

                coach = coach_match.group(1)
                message = message_match.group(1).strip()
                title = f"Rappel de {coach}"

                # 4. Préparer les chemins pour l'icône et l'action de clic
                icon_path = str(APP_WEB_DIR / "assets/logo.ico")
                launch_path = str(APP_WEB_DIR / "lancer_site.bat")

                # 5. Afficher la notification
                log_notification_to_history(title, message, "Rappel Quotidien")
                show_windows_toast(title, message, icon_path, launch_path)
                logging.info(f"Notification pour '{title}' envoyée avec succès.")
                
            except Exception as e:
                logging.error(f"Problème lors du traitement du script {script_path.name}: {e}")
            
            # On a trouvé le script du jour, on peut arrêter la recherche
            break
    
    # Cette condition est maintenant gérée par le logging au début.
    # if not found_script:
    #     logging.info(f"Aucun script de notification trouvé pour aujourd'hui ({today_str}).")

def show_windows_toast(title: str, message: str, icon_path: str, launch_path: str):
    """
    Affiche une notification 'Toast' sur Windows avec un titre, un message et une icône.
    """
    # L'historique est déjà loggué par la fonction appelante
    # log_notification_to_history(title, message, "Test")

    # Initialiser le notificateur
    toaster = ToastNotifier()

    # Définir la fonction à exécuter au clic
    def launch_action():
        subprocess.Popen([launch_path], shell=True)

    # Afficher la notification
    toaster.show_toast(
        title,
        message,
        icon_path=icon_path,
        duration=10,  # La notification reste visible 10 secondes
        threaded=True,  # Ne bloque pas le script parent pendant l'affichage
        callback_on_click=launch_action # Action à exécuter au clic
    )
    
    # Attendre un peu plus longtemps que la durée de la notification pour s'assurer que
    # le thread de notification a terminé son travail proprement.
    # C'est la méthode la plus fiable pour éviter les erreurs "WNDPROC" lorsque le script
    # principal se termine trop tôt.
    time.sleep(12)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Affiche une notification Windows.")
    parser.add_argument("--test", action="store_true", help="Affiche une notification de test.")
    args = parser.parse_args()

    if args.test:
        logging.info("--- Lancement du mode test de notification ---")
        try:
            title = "Notification de Test"
            message = "Si vous voyez ceci, le système de notification Windows fonctionne correctement."
            icon_path = str(APP_WEB_DIR / "assets/logo.ico")
            launch_path = str(APP_WEB_DIR / "lancer_site.bat")
            log_notification_to_history(title, message, "Test")
            show_windows_toast(title, message, icon_path, launch_path)
            logging.info("Notification de test envoyée avec succès.")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de la notification de test : {e}")
    else:
        logging.info("--- Démarrage du Centre de Notifications Windows (mode normal) ---")
        find_and_display_todays_notification()
    
    logging.info("--- Fin de l'exécution du script de notification. ---")