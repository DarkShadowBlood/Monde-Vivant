import json
import subprocess
import csv
import datetime
import re
import random

from config import SCHEDULED_TASKS_DIR, PORT, SCHEDULED_MESSAGES_PATH, APP_WEB_DIR
from lore import COACH_LORE
from utils import append_to_histoire_log, generate_llm_message, send_json_error

# Associer des icônes (tags ntfy) à chaque coach
coach_tags = {
    "Varkis": "boar",
    "Kara": "wolf",
    "Aegis": "robot_face",
    "KaraOmbre": "wolf",
    "KaraOmbreStable": "bell",
    "KaraOmbreChaos": "skull",
}

def handle_list_tasks(handler):
    try:
        # Exécute schtasks pour obtenir les tâches dans le dossier "Monde Vivant" au format CSV
        command = ['schtasks', '/query', '/tn', 'Monde Vivant\\', '/fo', 'CSV', '/v']
        result = subprocess.run(command, capture_output=True, text=True, encoding='latin-1', errors='ignore')

        # Gérer le cas où aucune tâche n'est trouvée (schtasks renvoie une erreur)
        if result.returncode != 0:
            stderr_lower = result.stderr.lower()
            # Si l'erreur indique que les tâches n'ont pas été trouvées, ce n'est pas une erreur fatale.
            if "ne trouve pas" in stderr_lower or "not found" in stderr_lower or "aucun" in stderr_lower:
                handler.send_response(200)
                handler.send_header('Content-type', 'application/json')
                handler.end_headers()
                handler.wfile.write(json.dumps({'success': True, 'tasks': []}).encode('utf-8'))
                return
            else:
                # Une autre erreur s'est produite
                raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
        
        # Le CSV peut commencer par un avertissement, on le nettoie
        csv_content = result.stdout
        if "AVERTISSEMENT:" in csv_content:
            csv_content = csv_content.split('\n', 1)[1]

        # Utiliser le module CSV pour parser la sortie
        reader = csv.reader(csv_content.splitlines())
        header = next(reader)
        
        tasks = []
        for row in reader:
            # Approche robuste basée sur la position des colonnes, insensible à la langue
            if not row or len(row) < 4: continue
            # On ne garde que le nom de la tâche, pas le chemin complet du dossier
            task_name_full = row[1] # TaskName est la 2ème colonne (index 1)
            task_name = task_name_full.split('\\')[-1] if '\\' in task_name_full else task_name_full
            tasks.append({
                'name': task_name,
                'next_run': row[2], # Next Run Time est la 3ème colonne (index 2)
                'status': row[3]   # Status est la 4ème colonne (index 3)
            })
        
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'tasks': tasks}).encode('utf-8'))
    except (subprocess.CalledProcessError, Exception) as e:
        send_json_error(handler, 500, f"Erreur lors de la récupération des tâches: {e}")

def handle_schedule_startup_notifications(handler):
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)
        enable = data.get('enable', False)

        task_name = "Monde Vivant\\NotificationGeneratorOnStartup"

        if enable:
            # Créer le script PowerShell qui appellera l'API de génération
            script_name = "run_notification_generator.ps1"
            script_path = SCHEDULED_TASKS_DIR / script_name
            
            # Ce script fait un simple appel web au serveur local
            ps_script_content = f\"\"\"
# Script pour déclencher la génération de notifications au démarrage
$ErrorActionPreference = "Stop"

try {{
    # Attendre quelques secondes pour que le serveur web ait le temps de démarrer
    Start-Sleep -Seconds 15

    # Envoyer une requête POST pour générer les notifications
    Invoke-RestMethod -Uri "http://localhost:{PORT}/api/notifications/generate" -Method Post -ContentType "application/json" -Body "{{}}"
    Write-Host "Requête de génération de notifications envoyée avec succès."

}} catch {{
    # En cas d'erreur, l'écrire dans un fichier log pour le débogage
    $logPath = "{str(SCHEDULED_TASKS_DIR / 'startup_error.log').replace('\\', '/')}"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorMessage = "$timestamp - Erreur dans le script de démarrage: $($_.Exception.Message)"
    Add-Content -Path $logPath -Value $errorMessage
}}
"""
            with open(script_path, 'w', encoding='utf-8-sig') as f:
                f.write(ps_script_content)

            # Créer la tâche planifiée pour s'exécuter à l'ouverture de session
            command = [
                'schtasks', '/create', '/tn', task_name,
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                '/sc', 'ONLOGON', '/f'
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            message = "La génération de notifications au démarrage est activée."
        else:
            # Supprimer la tâche planifiée
            command = ['schtasks', '/delete', '/tn', task_name, '/f']
            subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore') # Ignore les erreurs si la tâche n'existe pas
            message = "La génération de notifications au démarrage est désactivée."

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': message}).encode('utf-8'))
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur de schtasks: {e.stderr.strip()}"
        send_json_error(handler, 500, error_message)
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la planification de la tâche de démarrage : {e}")

def handle_preview_schedule(handler):
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
        all_coaches = list(COACH_LORE.keys())

        prompts_to_generate = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            chosen_coach = random.choice(all_coaches)
            prompts_to_generate[date_str] = {"coach": chosen_coach, "request": request_text}
            current_date += timedelta(days=1)

        system_prompt = f\"\"\"Tu es un générateur de messages de coach. Tu recevras un objet JSON où chaque clé est une date (YYYY-MM-DD) et la valeur contient le nom d'un coach et une requête.
Pour chaque date, tu dois générer un message de notification concis et percutant, en adoptant la personnalité du coach spécifié.
Le lore des coachs est le suivant: {json.dumps(COACH_LORE, indent=2)}

Ta réponse doit être UNIQUEMENT un objet JSON valide. Les clés de l'objet de sortie doivent être les mêmes dates que celles de l'entrée. La valeur pour chaque date doit être le message que tu as généré.

Exemple de réponse attendue:
{{ "2025-09-20": "Message généré pour le 20...", "2025-09-21": "Message généré pour le 21..." }}\"\"\"
        user_prompt = json.dumps(prompts_to_generate, indent=2)

        generated_messages_str, success = generate_llm_message("Aegis", user_prompt, system_prompt_override=system_prompt)
        if not success:
            raise Exception("Erreur lors de la génération des messages par l'API Mistral.")

        try:
            # La réponse de l'IA est un JSON contenant un JSON, nous devons parser deux fois.
            # C'est un contournement pour la sortie parfois incorrecte de l'IA.
            outer_json = json.loads(generated_messages_str)
            generated_messages = outer_json
        except json.JSONDecodeError:
            raise Exception(f"La réponse de l'IA n'était pas un JSON valide. Réponse: {generated_messages_str}")

        # Combiner les infos pour la réponse
        full_schedule = {}
        for date_str, message in generated_messages.items():
            full_schedule[date_str] = {
                "coach": prompts_to_generate[date_str]["coach"],
                "message": message
            }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'schedule': full_schedule}).encode('utf-8'))

    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la prévisualisation: {e}")

def handle_confirm_schedule(handler):
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        data = json.loads(post_data)

        task_name_prefix = data.get('taskName')
        time = data.get('time')
        trigger = data.get('trigger') # 'time' ou 'startup'
        schedule = data.get('schedule')

        if not all([task_name_prefix, time, schedule]):
            send_json_error(handler, 400, "Données de planification incomplètes (préfixe, heure, et planning requis).")
            return

        created_tasks_count = 0
        
        # Sauvegarder les messages planifiés pour référence dans tous les cas
        with open(SCHEDULED_MESSAGES_PATH, 'w', encoding='utf-8-sig') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)

        if trigger == 'startup':
            # --- Logique pour le déclenchement au démarrage ---
            task_name = f"{task_name_prefix}_OnStartup"
            safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
            script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

            # Le script PowerShell est maintenant plus complexe
            ps_script_content = f\"\"\"# Script de rappel au démarrage - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {{
    # --- Module BurntToast (pour notification Windows) ---
if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
    Write-Host "Module BurntToast non trouvé. Tentative d'installation..."
    Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
}}
Import-Module BurntToast

# 2. Logique pour exécution unique par jour
$lockFilePath = "{str(SCHEDULED_TASKS_DIR / (safe_filename + '_lock.txt')).replace('\\', '/')}"
$today = (Get-Date).ToString("yyyy-MM-dd")

if (Test-Path $lockFilePath) {{
    $lastRunDate = Get-Content $lockFilePath
    if ($lastRunDate -eq $today) {{
        Write-Host "Notification déjà envoyée aujourd'hui. Sortie."
        exit
    }}
}}

# 3. Lire le message du jour depuis le fichier JSON
$schedulePath = "{str(SCHEDULED_MESSAGES_PATH).replace('\\', '/')}"
$schedule = Get-Content -Raw -Path $schedulePath | ConvertFrom-Json
$messageData = $schedule.($today)

if ($null -ne $messageData) {{
    $coach = $messageData.coach
    $message = $messageData.message
    
    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{{
        "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
        "Title" = "Rappel de $coach";
        "Tags" = "{coach_tags.get('$coach', 'bell')}";
        "Click" = "http://localhost:8000/app%20web/index.html"
    }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

    # Mettre à jour le fichier de verrouillage
    Set-Content -Path $lockFilePath -Value $today
}}
}} catch {{
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    $_ | Format-List -Force
}} finally {{
    if ($Host.Name -eq "ConsoleHost") {{
        Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
    }}
}}
"""
            # Utiliser utf-8-sig pour que PowerShell lise correctement les accents
            with open(script_path, 'w', encoding='utf-8-sig') as f:
                f.write(ps_script_content)

            # Créer une seule tâche qui se lance à l'ouverture de session
            command = [
                'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}",
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script_path}"',
                '/sc', 'ONLOGON', '/f'
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            created_tasks_count = 1
            success_message = f"Tâche '{task_name}' planifiée pour s'exécuter au démarrage de l'ordinateur."

        else: # Logique existante pour le déclenchement à heure fixe
            for date_str, item in schedule.items():
                current_date = datetime.date.fromisoformat(date_str)
                coach_name = item['coach']
                message = item['message']

                # Log de la planification
                append_to_histoire_log(f"Planification - {task_name_prefix}", coach_name, message)

                # Créer le script PowerShell
                date_suffix = current_date.strftime('%Y-%m-%d')
                task_name = f"{task_name_prefix}_{date_suffix}"
                safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
                script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

                tag = coach_tags.get(coach_name, "bell")

                # Utilisation du modèle unifié et robuste
                ps_script_content = f\"\"\"# Script de rappel quotidien - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {{
    # --- Données du message ---
    $coach = '{coach_name.replace("'", "''")}'
    $message = @'
{message}
'@

    # --- Module BurntToast (pour notification Windows) ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }}
    Import-Module BurntToast

    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{{
    "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    "Title" = "Rappel de {coach_name}";
    "Tags" = "{tag}";
    "Click" = "http://localhost:8000/app%20web/index.html"
    }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "{str(APP_WEB_DIR / 'assets/logo.png').replace('\\', '/')}"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

}} catch {{
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    $_ | Format-List -Force
    Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
}}"""
                # Utiliser utf-8-sig pour que PowerShell lise correctement les accents
                with open(script_path, 'w', encoding='utf-8-sig') as f:
                    f.write(ps_script_content)

                # Créer la tâche planifiée
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
        error_message = f"Erreur lors de la création de la tâche: {e.stderr}"
        send_json_error(handler, 500, error_message)
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la confirmation de la planification: {e}")

def handle_confirm_schedule_old(handler):
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

            # Log de la planification
            append_to_histoire_log(f"Planification - {task_name_prefix}", coach_name, message)

            # Créer le script PowerShell
            date_suffix = current_date.strftime('%Y-%m-%d')
            task_name = f"{task_name_prefix}_{date_suffix}"
            safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
            script_path = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"

            ps_message = message.replace("'", "''").replace('"', '`"')
            tag = coach_tags.get(coach_name, "bell")

            ps_script_content = f\"\"\"# Script généré automatiquement
$message = @'
{ps_message}
'@
$headers = @{{
    "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    "Title" = "Rappel de {coach_name}";
    "Tags" = "{tag}";
    "Click" = "http://localhost:8000/app%20web/index.html"
}}
Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $headers"""
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(ps_script_content)

            # Créer la tâche planifiée
            command = [
                'schtasks', '/create', '/tn', f"Monde Vivant\\{task_name}", # Note: La date est en format US pour schtasks
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
        error_message = f"Erreur lors de la création de la tâche: {e.stderr}"
        send_json_error(handler, 500, error_message)
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la confirmation de la planification: {e}")

def handle_delete_task(handler):
    try:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        task_name = data.get('taskName')

        if not task_name:
            send_json_error(handler, 400, "Le nom de la tâche est requis.")
            return

        command = ['schtasks', '/delete', '/tn', f"Monde Vivant\\{task_name}", '/f']
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Supprimer également le fichier .ps1 associé
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", task_name).replace(" ", "_")
        script_path_to_delete = SCHEDULED_TASKS_DIR / f"{safe_filename}.ps1"
        if script_path_to_delete.exists():
            script_path_to_delete.unlink()

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({'success': True, 'message': f"Tâche '{task_name}' supprimée."}).encode('utf-8'))
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur lors de la suppression de la tâche planifiée: {e.stderr}"
        send_json_error(handler, 500, error_message)
    except Exception as e:
        send_json_error(handler, 500, f"Erreur lors de la suppression de la tâche: {e}")
