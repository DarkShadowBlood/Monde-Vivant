import re
from pathlib import Path
import sys

# --- Configuration ---
# Le script s'attend à être exécuté depuis le dossier 'app web'
APP_WEB_DIR = Path(__file__).resolve().parent
SCHEDULED_TASKS_DIR = APP_WEB_DIR / "ntfy_sender" / "scheduled_tasks"
LOGO_PATH = APP_WEB_DIR / 'assets/logo.png'

# Associer des icônes (tags ntfy) à chaque coach
COACH_TAGS = {
    "Varkis": "boar",
    "Kara": "wolf",
    "Aegis": "robot_face",
    "KaraOmbre": "wolf",
    "KaraOmbreStable": "bell",
    "KaraOmbreChaos": "skull",
}

# --- Modèle PowerShell Fiable V2 ---
# Ce modèle inclut une gestion des erreurs pour un meilleur débogage.
POWERSHELL_TEMPLATE = """# Script de rappel quotidien - Généré et réparé (v2)
# On arrête le script à la première erreur pour un débogage clair
$ErrorActionPreference = "Stop"

try {{
    # --- Données du message ---
    $coach = '{coach}'
    $message = @'
{message}
'@

    # --- Module BurntToast (pour notification Windows) ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
        Write-Host "Module BurntToast non trouvé. Tentative d'installation..."
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }}
    Import-Module BurntToast

    # --- Envoi des notifications ---

    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{{
        "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
        "Title" = "Rappel de $coach";
        "Tags" = "{tag}";
        "Click" = "http://localhost:8000/app%20web/index.html"
    }}
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "{logo_path}"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

}} catch {{
    # --- En cas d'erreur, on affiche les détails ---
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    Write-Host "Ligne : $($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "Script : $($_.InvocationInfo.ScriptName)"
    Write-Host "Détails complets de l’erreur :"
    $_ | Format-List -Force
    Write-Host "----------------------------------------------------" -ForegroundColor Red
}} finally {{
    # --- Pause pour voir le résultat en cas d'exécution manuelle ---
    if ($Host.Name -eq "ConsoleHost") {{
        Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
    }}
}}
"""

def repair_script(script_path: Path):
    """
    Lit un script, en extrait le coach et le message, et le réécrit en utilisant le modèle fiable.
    """
    try:
        original_content = script_path.read_text(encoding='utf-8')

        # Regex pour extraire le coach et le message, même si le format est ancien ou nouveau
        coach_match = re.search(r"\$coach\s*=\s*'(.*?)'", original_content)
        message_match = re.search(r"\$message\s*=\s*@'\n(.*?)\n'@", original_content, re.DOTALL)

        if not coach_match or not message_match:
            print(f"⚠️  Impossible d'extraire les données de '{script_path.name}'. Format inattendu. Ignoré.")
            return

        coach = coach_match.group(1).strip()
        message = message_match.group(1).strip()
        
        tag = COACH_TAGS.get(coach, "bell")
        
        new_content = POWERSHELL_TEMPLATE.format(
            coach=coach.replace("'", "''"),
            message=message,
            tag=tag,
            logo_path=str(LOGO_PATH).replace('\\', '/')
        )

        script_path.write_text(new_content, encoding='utf-8-sig')
        print(f"✅  '{script_path.name}' a été réparé et standardisé avec le modèle v2.")

    except Exception as e:
        print(f"❌  Erreur lors du traitement de '{script_path.name}': {e}")

def main():
    """
    Fonction principale pour lancer le processus de réparation.
    """
    print("--- Début de la réparation (v2) des scripts de rappel PowerShell ---")
    
    if not SCHEDULED_TASKS_DIR.exists():
        print(f"❌ ERREUR: Le dossier des tâches '{SCHEDULED_TASKS_DIR}' est introuvable.", file=sys.stderr)
        return

    # Parcourir tous les fichiers de rappel quotidien
    repaired_count = 0
    for ps_file in SCHEDULED_TASKS_DIR.glob("Rappel_Quotidien_*.ps1"):
        repair_script(ps_file)
        repaired_count += 1
            
    print(f"\n--- Opération terminée. {repaired_count} scripts ont été traités. ---")

if __name__ == "__main__":
    main()
