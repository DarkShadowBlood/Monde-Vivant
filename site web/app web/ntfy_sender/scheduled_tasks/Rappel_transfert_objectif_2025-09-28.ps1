# Script de rappel quotidien - Généré par serveur.py
$ErrorActionPreference = "Stop"

try {
    # --- Données du message ---
    $coach = 'KaraOmbreChaos'
    $message = @'
La lune veille sur tes conquêtes, mais se lasse d'attendre. Grave tes résultats avant que le vent ne les emporte.
'@

    # --- Module BurntToast (pour notification Windows) ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }
    Import-Module BurntToast

    # --- Envoi des notifications ---
    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{
    "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
    "Title" = "Rappel de KaraOmbreChaos";
    "Tags" = "skull";
    }
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "C:/important/ApexWear/app web pour apex/app web - Monde Vivant/site web/app web/assets/logo.png"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

} catch {
    # Gérer les erreurs silencieusement en production, mais les logger si possible.
}