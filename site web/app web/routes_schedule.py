"""
Ce module gère les routes liées à la planification et à la gestion des tâches.

Il permet de :
- Lister les tâches planifiées existantes (via schtasks).
- Activer/désactiver une tâche qui génère des notifications au démarrage.
- Prévisualiser un planning de notifications généré par l'IA.
- Confirmer et créer des tâches planifiées pour un planning de notifications.
- Supprimer des tâches planifiées.
"""
import json
import subprocess
import csv
import datetime
import re
import random

from config import SCHEDULED_TASKS_DIR, PORT, SCHEDULED_MESSAGES_PATH, APP_WEB_DIR
from utils import append_to_histoire_log, generate_llm_message, send_json_error
import lore

# Associe une icône (tag ntfy.sh) à chaque coach pour des notifications visuelles
coach_tags = {
    "Varkis": "boar",
    "Kara": "wolf",
    "Aegis": "robot_face",
    "KaraOmbre": "wolf",
    "KaraOmbreStable": "bell",
    "KaraOmbreChaos": "skull",
}

def handle_list_tasks(handler, context):
    """
    (GET /api/list-tasks)
    Récupère et liste les tâches planifiées dans le dossier "Monde Vivant".

    Utilise la commande `schtasks` de Windows pour interroger le système.
    Parse la sortie CSV pour renvoyer une liste JSON claire au client.
    """
    try:
        # Exécute schtasks pour obtenir les tâches au format CSV avec détails
        command = ['schtasks', '/query', '/tn', 'Monde Vivant\\', '/fo', 'CSV', '/v']
        result = subprocess.run(command, capture_output=True, text=True, encoding='latin-1', errors='ignore')

        # Gère le cas où le dossier de tâches n'existe pas ou est vide
        if result.returncode != 0:
            stderr_lower = result.stderr.lower()
            if "ne trouve pas" in stderr_lower or "not found" in stderr_lower or "aucun" in stderr_lower:
                handler.send_response(200)
                handler.send_header('Content-type', 'application/json')
                handler.end_headers()
                handler.wfile.write(json.dumps({'success': True, 'tasks': []}).encode('utf-8'))
                return
            else:
                raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
        
        # Nettoie la sortie de schtasks qui peut contenir des avertissements
        csv_content = result.stdout.split('"\n"AVERTISSEMENT:')[0] if "AVERTISSEMENT:" in result.stdout else result.stdout

        reader = csv.reader(csv_content.splitlines())
        header = next(reader)
        
        tasks = []
        for row in reader:
            # Approche robuste pour extraire les colonnes nécessaires
            if not row or len(row) < 4: continue
            task_name_full = row[1]
            task_name = task_name_full.split('\\')[-1]
            tasks.append({
                'name': task_name,
                'next_run': row[2],
                'status': row[3]
            })
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'tasks': tasks}).encode('utf-8'))
    except (subprocess.CalledProcessError, Exception) as e:
        send_json_error(handler, 500, f"Erreur lors de la récupération des tâches: {e}")

def handle_schedule_startup_notifications(handler, context):
    """
    (POST /api/schedule-startup-notifications)
    Active ou désactive la tâche qui génère les notifications au démarrage.

    Attend un JSON avec {'enable': true/false}.
    Crée ou supprime une tâche planifiée qui se déclenche à l'ouverture de session.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)
        enable = data.get('enable', False)

        task_name = "Monde Vivant\\NotificationGeneratorOnStartup"

        if enable:
            # Crée un script PowerShell qui appelle l'API de génération locale
            script_name = "run_notification_generator.ps1"
            script_path = SCHEDULED_TASKS_DIR / script_name
            
            ps_script_content = rf"""
# Ce script déclenche la génération de notifications au démarrage de la session.
$ErrorActionPreference = "Stop"
try {{
    Start-Sleep -Seconds 15 # Laisse le temps au serveur web de démarrer
    Invoke-RestMethod -Uri "http://localhost:{PORT}/api/notifications/generate" -Method Post -ContentType "application/json" -Body "{{}}"
}} catch {{
    # Log les erreurs pour faciliter le débogage
    $logPath = "{str(SCHEDULED_TASKS_DIR / 'startup_error.log').replace('\\', '/')}"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logPath -Value "$timestamp - Erreur: $($_.Exception.Message)"
}}
"""
            with open(script_path, 'w', encoding='utf-8-sig') as f:
                f.write(ps_script_content)

            # Crée la tâche planifiée via schtasks
            command = [
                'schtasks', '/create', '/tn', task_name,
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                '/sc', 'ONLOGON', '/f'
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            message = "Génération de notifications au démarrage activée."
        else:
            # Supprime la tâche planifiée
            command = ['schtasks', '/delete', '/tn', task_name, '/f']
            subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore')
            message = "Génération de notifications au démarrage désactivée."

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': message}).encode('utf-8'))
    except subprocess.CalledProcessError as e:
        send_json_error(handler, 500, f"Erreur schtasks: {e.stderr.strip()}")
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la planification de la tâche: {e}")

def handle_preview_schedule(handler, context):
    """
    (POST /api/preview-schedule)
    Génère un aperçu d'un planning de notifications sans le créer.

    Attend un JSON avec 'request' et 'endDate'.
    Utilise l'IA pour générer un message pour chaque jour jusqu'à la date de fin.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        request_text = data.get('request')
        end_date_str = data.get('endDate')

        if not request_text or not end_date_str:
            send_json_error(handler, 400, "La requête et la date de fin sont requises.")
            return

        from datetime import date, timedelta
        start_date = date.today()
        end_date = date.fromisoformat(end_date_str)
        all_coaches = list(lore.COACH_LORE.keys())

        # Prépare un prompt pour chaque jour du planning
        prompts_to_generate = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            chosen_coach = random.choice(all_coaches)
            prompts_to_generate[date_str] = {"coach": chosen_coach, "request": request_text}
            current_date += timedelta(days=1)

        system_prompt = rf"""Tu es un générateur de messages. Tu recevras un JSON où chaque clé est une date et la valeur contient un coach et une requête.
Pour chaque date, génère un message de notification percutant, en adoptant la personnalité du coach spécifié.
Le lore des coachs est : {json.dumps(lore.COACH_LORE, indent=2)}
Ta réponse doit être UNIQUEMENT un objet JSON valide, avec les mêmes dates comme clés.
"""
        user_prompt = json.dumps(prompts_to_generate, indent=2)

        generated_messages_str, success = generate_llm_message("Aegis", user_prompt, system_prompt_override=system_prompt)
        if not success:
            raise Exception("Erreur lors de la génération des messages par l'API.")

        generated_messages = json.loads(generated_messages_str)

        # Combine les messages générés avec les coachs choisis pour la réponse finale
        full_schedule = {
            date_str: {
                "coach": prompts_to_generate[date_str]["coach"],
                "message": message
            } for date_str, message in generated_messages.items()
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'schedule': full_schedule}).encode('utf-8'))

    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la prévisualisation du planning: {e}")

def handle_confirm_schedule(handler, context):
    """
    (POST /api/confirm-schedule)
    Crée les tâches planifiées à partir d'un planning de notifications.

    Attend un JSON avec 'taskName', 'time', 'trigger' ('time' ou 'startup'), et 'schedule'.
    Génère des scripts PowerShell pour chaque notification et les planifie via schtasks.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        task_name_prefix = data.get('taskName')
        time = data.get('time')
        trigger = data.get('trigger')
        schedule = data.get('schedule')

        if not all([task_name_prefix, schedule, trigger]) or (trigger == 'time' and not time):
            send_json_error(handler, 400, "Données de planification incomplètes.")
            return

        # Sauvegarde le planning complet pour une utilisation future (ex: par le script de démarrage)
        with open(SCHEDULED_MESSAGES_PATH, 'w', encoding='utf-8-sig') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)

        if trigger == 'startup':
            # --- Logique pour le déclenchement au démarrage ---
            task_name = f"{task_name_prefix}_OnStartup"
            safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
            script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

            # Ce script PowerShell complexe gère la notification unique par jour
            ps_script_content = rf"""# Script de rappel au démarrage.
$ErrorActionPreference = "Stop"
try {{
    # Installe le module de notification Windows si nécessaire
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }}
    Import-Module BurntToast

    # Vérifie si la notification a déjà été envoyée aujourd'hui
    $lockFilePath = "{str(SCHEDULED_TASKS_DIR / (safe_filename + '_lock.txt')).replace('\\', '/')}"
    $today = (Get-Date).ToString("yyyy-MM-dd")
    if (Test-Path $lockFilePath -and (Get-Content $lockFilePath) -eq $today) {{ exit }}

    # Lit le message du jour depuis le planning JSON
    $schedule = Get-Content -Raw -Path "{str(SCHEDULED_MESSAGES_PATH).replace('\\', '/')}" | ConvertFrom-Json
    $messageData = $schedule.($today)

    if ($null -ne $messageData) {{
        $coach = $messageData.coach
        $message = $messageData.message

        # Envoie les notifications (ntfy.sh et native Windows)
        $ntfyHeaders = @{{ "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34"; "Title" = "Rappel de $coach"; "Tags" = "{coach_tags.get('$coach', 'bell')}"; "Click" = "http://localhost:8000/app%20web/index.html" }}
        Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"
        New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"

        # Met à jour le fichier de verrouillage
        Set-Content -Path $lockFilePath -Value $today
    }}
}} catch {{
    Write-Host "Erreur dans le script de rappel: $($_.Exception.Message)"
}}
"""
            with open(script_path, 'w', encoding='utf-8-sig') as f:
                f.write(ps_script_content)

            # Crée une seule tâche qui se lance à l'ouverture de session
            command = [
                'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                '/sc', 'ONLOGON', '/f'
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            success_message = f"Tâche '{task_name}' planifiée pour s'exécuter au démarrage."

        else: # --- Logique pour le déclenchement à heure fixe ---
            created_tasks_count = 0
            for date_str, item in schedule.items():
                current_date = datetime.date.fromisoformat(date_str)
                coach_name = item['coach']
                message = item['message']

                append_to_histoire_log(f"Planification - {task_name_prefix}", coach_name, message)

                # Crée un script PowerShell pour chaque jour
                task_name = f"{task_name_prefix}_{current_date.strftime('%Y-%m-%d')}"
                safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"
                tag = coach_tags.get(coach_name, "bell")

                ps_script_content = rf"""# Script de rappel quotidien.
$ErrorActionPreference = "Stop"
try {{
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {{ Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck }}
    Import-Module BurntToast

    $coach = '{coach_name.replace("'", "''")}'
    $message = @'
{message}
'@

    $ntfyHeaders = @{{ "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34"; "Title" = "Rappel de {coach_name}"; "Tags" = "{tag}"; "Click" = "http://localhost:8000/app%20web/index.html" }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"
}} catch {{
    Write-Host "Erreur dans le script de rappel: $($_.Exception.Message)"
}}"""
                with open(script_path, 'w', encoding='utf-8-sig') as f:
                    f.write(ps_script_content)

                # Crée la tâche planifiée pour ce jour
                command = [
                    'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                    '/tr', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                    '/sc', 'ONCE', '/sd', current_date.strftime('%d/%m/%Y'), '/st', time, '/f'
                ]
                subprocess.run(command, check=True, capture_output=True, text=True)
                created_tasks_count += 1
            success_message = f"{created_tasks_count} tâches ont été planifiées avec succès."

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': success_message}).encode('utf-8'))

    except subprocess.CalledProcessError as e:
        send_json_error(handler, 500, f"Erreur schtasks: {e.stderr}")
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la confirmation de la planification: {e}")

def handle_confirm_schedule_old(handler, context):
    """
    (POST /api/confirm-schedule-old)
    Ancienne version de la confirmation de planning, conservée pour rétrocompatibilité.

    Cette version est moins robuste et ne gère pas les notifications Windows natives.
    Elle devrait être considérée comme obsolète.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        task_name_prefix = data.get('taskName')
        time = data.get('time')
        schedule = data.get('schedule')

        if not all([task_name_prefix, time, schedule]):
            send_json_error(handler, 400, "Données de planification incomplètes.")
            return

        created_tasks_count = 0
        for date_str, item in schedule.items():
            current_date = datetime.date.fromisoformat(date_str)
            coach_name = item['coach']
            message = item['message']

            append_to_histoire_log(f"Planification (Ancienne) - {task_name_prefix}", coach_name, message)

            task_name = f"{task_name_prefix}_{current_date.strftime('%Y-%m-%d')}"
            safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
            script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

            ps_message = message.replace("'", "''").replace('"', '`"')
            tag = coach_tags.get(coach_name, "bell")

            ps_script_content = rf"""# Script généré (ancienne méthode)
$message = @'
{ps_message}
'@
$headers = @{{ "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34"; "Title" = "Rappel de {coach_name}"; "Tags" = "{tag}"; "Click" = "http://localhost:8000/app%20web/index.html" }}
Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $headers"""
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(ps_script_content)

            command = [
                'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                '/sc', 'ONCE', '/sd', current_date.strftime('%d/%m/%Y'), '/st', time, '/f'
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            created_tasks_count += 1

        success_message = f"{created_tasks_count} tâches (ancienne méthode) ont été planifiées."
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': success_message}).encode('utf-8'))

    except subprocess.CalledProcessError as e:
        send_json_error(handler, 500, f"Erreur schtasks (ancienne méthode): {e.stderr}")
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la confirmation (ancienne méthode): {e}")

def handle_delete_task(handler, context):
    """
    (POST /api/delete-task)
    Supprime une tâche planifiée spécifique.

    Attend un JSON avec {'taskName': '...'}.
    Supprime la tâche via schtasks et nettoie le script PowerShell associé.
    """
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        task_name = data.get('taskName')

        if not task_name:
            send_json_error(handler, 400, "Le nom de la tâche est requis.")
            return

        # Supprime la tâche du planificateur Windows
        command = ['schtasks', '/delete', '/tn', f"Monde Vivant\\{task_name}", '/f']
        subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore')

        # Supprime le script .ps1 correspondant pour garder le dossier propre
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
        script_path_to_delete = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"
        if script_path_to_delete.exists():
            script_path_to_delete.unlink()

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': f"Tâche '{task_name}' supprimée."}).encode('utf-8'))
    except subprocess.CalledProcessError as e:
        send_json_error(handler, 500, f"Erreur lors de la suppression de la tâche: {e.stderr}")
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la suppression de la tâche: {e}")