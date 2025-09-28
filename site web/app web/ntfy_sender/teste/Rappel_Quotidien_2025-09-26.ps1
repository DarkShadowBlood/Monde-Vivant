# Script de rappel quotidien - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {
    # --- Données du message ---
    $coach = 'Aegis'
    $message = @'
Analyse des données en attente. Transfère les résultats pour une efficacité optimale.
'@

    # --- Module BurntToast (pour notification Windows) ---
    # On s'assure d'avoir une version de BurntToast qui supporte le paramètre -Launch.
    try {
        # Étape 1: On retire de force toute version du module déjà chargée en mémoire.
        # L'option -ErrorAction SilentlyContinue ignore l'erreur si le module n'était pas chargé.
        Remove-Module -Name BurntToast -Force -ErrorAction SilentlyContinue

        # Étape 2: On force l'importation de la version la plus récente disponible sur le disque.
        Import-Module BurntToast -Force
    }
    catch {
        # Étape 3: Si l'importation échoue (car le module est manquant), on l'installe.
        Write-Host "Module BurntToast non trouvé ou corrompu. Installation de la dernière version..."
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
        
        # Étape 4: On ré-importe le module fraîchement installé.
        Import-Module BurntToast
    }

    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    # $ntfyHeaders = @{
    # "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    # "Title" = "Rappel de Aegis";
    # "Tags" = "robot_face";
    # "Click" = "http://localhost:8000/app%20web/index.html"
    # }
    # Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "C:/important/ApexWear/app web pour apex/app web - Monde Vivant/site web/app web/assets/logo.png"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath -Launch "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\lancer_site.bat"

} catch {
    # --- En cas d'erreur, on affiche les détails ---
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    Write-Host "Ligne : $($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "Script : $($_.InvocationInfo.ScriptName)"
    Write-Host "Détails complets de l’erreur :"
    $_ | Format-List -Force
    Write-Host "----------------------------------------------------" -ForegroundColor Red
    if ($Host.Name -eq "ConsoleHost") {
        Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
    }
}
