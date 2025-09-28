import subprocess
from pathlib import Path
import sys

# --- Configuration ---
APP_WEB_DIR = Path(__file__).resolve().parent
PYTHON_EXE = Path(sys.executable) # Utilise le même interpréteur Python que celui qui exécute le serveur.
NOTIFICATION_SCRIPT = APP_WEB_DIR / "win_notification_sender.py"
TASK_NAME = "Monde Vivant\\CentreNotifications"

def check_task_status():
    """
    Vérifie si la tâche planifiée existe et est activée.
    Retourne un dictionnaire avec 'exists', 'enabled', et 'status'.
    """
    try:
        command = ['schtasks', '/query', '/tn', TASK_NAME]
        result = subprocess.run(command, capture_output=True, text=True, encoding='latin-1', errors='ignore')

        if result.returncode != 0:
            return {"exists": False, "enabled": False, "status": "N'existe pas"}

        output = result.stdout
        is_disabled = "Désactivé" in output or "Disabled" in output
        
        if is_disabled:
            return {"exists": True, "enabled": False, "status": "Existe mais est désactivée"}
        else:
            return {"exists": True, "enabled": True, "status": "Activée et prête"}

    except FileNotFoundError:
        return {"exists": False, "enabled": False, "status": "Erreur: 'schtasks' non trouvé."}
    except Exception as e:
        return {"exists": False, "enabled": False, "status": f"Erreur inconnue: {e}"}

def toggle_startup_task():
    """
    Crée ou supprime la tâche planifiée qui lance le centre de notifications au démarrage.
    """
    status = check_task_status()

    if status["exists"]:
        # La tâche existe, on la supprime
        try:
            command = ['schtasks', '/delete', '/tn', TASK_NAME, '/f']
            subprocess.run(command, check=True, capture_output=True)
            return {"success": True, "message": "Tâche de notification au démarrage désactivée."}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Erreur lors de la suppression de la tâche: {e.stderr}"}
    else:
        # La tâche n'existe pas, on la crée
        if not PYTHON_EXE.exists():
            return {"success": False, "message": f"Erreur: L'exécutable Python n'a pas été trouvé à {PYTHON_EXE}"}
        if not NOTIFICATION_SCRIPT.exists():
            return {"success": False, "message": f"Erreur: Le script de notification n'a pas été trouvé à {NOTIFICATION_SCRIPT}"}
            
        try:
            # Le /it force la tâche à s'exécuter même si l'utilisateur n'est pas connecté sur batterie
            command = [
                'schtasks', '/create', '/tn', TASK_NAME,
                '/tr', f'"{PYTHON_EXE}" "{NOTIFICATION_SCRIPT}"',
                '/sc', 'ONLOGON',
                '/it', # Exécuter même si l'utilisateur n'est pas connecté
                '/f'  # Forcer la création si elle existe déjà dans un état corrompu
            ]
            subprocess.run(command, check=True, capture_output=True)
            return {"success": True, "message": "Tâche de notification au démarrage activée."}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Erreur lors de la création de la tâche: {e.stderr}"}