
# Script pour déclencher la génération de notifications au démarrage
$ErrorActionPreference = "Stop"

try {
    # Attendre quelques secondes pour que le serveur web ait le temps de démarrer
    Start-Sleep -Seconds 15

    # Envoyer une requête POST pour générer les notifications
    Invoke-RestMethod -Uri "http://localhost:8000/api/notifications/generate" -Method Post -ContentType "application/json" -Body "{}"
    Write-Host "Requête de génération de notifications envoyée avec succès."

} catch {
    # En cas d'erreur, l'écrire dans un fichier log pour le débogage
    $logPath = "C:/important/ApexWear/app web pour apex/app web - Monde Vivant/site web/app web/ntfy_sender/scheduled_tasks/startup_error.log"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorMessage = "$timestamp - Erreur dans le script de démarrage: $($_.Exception.Message)"
    Add-Content -Path $logPath -Value $errorMessage
}
