# Script de rappel quotidien - Généré et réparé (v2)
# On arrête le script à la première erreur pour un débogage clair
$ErrorActionPreference = "Stop"

try {
    # --- Données du message ---
    $coach = 'KaraOmbreChaos'
    $message = @'
Les ombres grondent, transfère tes résultats avant qu''''''''elles ne les dévorent.
'@

    # --- Module BurntToast (pour notification Windows) ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {
        Write-Host "Module BurntToast non trouvé. Tentative d'installation..."
        Install-Module -Name BurntToast -Scope CurrentUser -Force -SkipPublisherCheck
    }
    Import-Module BurntToast

    # --- Envoi des notifications ---

    # 1. Notification ntfy.sh (Format Riche)
    $ntfyHeaders = @{
        "Authorization" = "Bearer tk_7jtopqibezu9c8yz76gzacx8nvz34";
        "Title" = "Rappel de $coach";
        "Tags" = "skull";
        "Click" = "http://localhost:8000/app%20web/index.html"
    }
    Invoke-RestMethod -Uri "https://ntfy.sh/monde-vivant-note" -Method Post -Body $message -Headers $ntfyHeaders -ContentType "text/plain; charset=utf-8"

    # 2. Notification native Windows
    $logoPath = "C:/important/ApexWear/app web pour apex/app web - Monde Vivant/site web/app web/assets/logo.png"
    New-BurntToastNotification -Text "Rappel de $coach", $message -AppLogo $logoPath

} catch {
    # --- En cas d'erreur, on affiche les détails ---
    Write-Host "--- UNE ERREUR EST SURVENUE DANS LE SCRIPT DE RAPPEL ---" -ForegroundColor Red
    Write-Host "Message d’erreur : $($_.Exception.Message)"
    Write-Host "Ligne : $($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "Script : $($_.InvocationInfo.ScriptName)"
    Write-Host "Détails complets de l’erreur :"
    $_ | Format-List -Force
    Write-Host "----------------------------------------------------" -ForegroundColor Red
} finally {
    # --- Pause pour voir le résultat en cas d'exécution manuelle ---
    if ($Host.Name -eq "ConsoleHost") {
        Read-Host -Prompt "Appuyez sur Entrée pour fermer..."
    }
}
