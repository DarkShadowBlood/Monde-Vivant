# Script de rappel quotidien avec compte à rebours - Généré pour PowerShell 7.5.3 et BurntToast 1.1.0
$ErrorActionPreference = "Stop"

try {
    # --- Données du message ---
    $coach = 'Aegis'
    $baseMessage = "Le serveur Monde Vivant démarrera dans {0} secondes. Cliquez sur Annuler pour arrêter."
    $totalTime = 300  # Durée totale en secondes
    $updateInterval = 5  # Intervalle de mise à jour de la notification en secondes
    $notificationId = "MondeVivantReminder"  # Identifiant unique pour remplacer les notifications

    # --- Installation et importation de BurntToast ---
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {
        Write-Host "Installation de BurntToast pour PowerShell 7..."
        Install-Module -Name BurntToast -Force -Scope CurrentUser -SkipPublisherCheck
    }
    Import-Module BurntToast -Force

    # --- Vérification des fichiers ---
    $logoPath = "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\assets\logo.png"
    $ps1Path = "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\launch_batch.ps1"
    $cancelPath = "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\cancel_action.ps1"
    $flagPath = "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\cancel_flag.txt"
    
    if (-not (Test-Path $logoPath)) { throw "Le fichier logo.png est introuvable à : $logoPath" }
    if (-not (Test-Path $ps1Path)) { throw "Le fichier launch_batch.ps1 est introuvable à : $ps1Path" }
    if (-not (Test-Path $cancelPath)) { throw "Le fichier cancel_action.ps1 est introuvable à : $cancelPath" }

    # --- Supprimer tout fichier d'annulation existant ---
    if (Test-Path $flagPath) { Remove-Item $flagPath -Force }

    # --- Création du bouton Annuler ---
    $button = New-BTButton -Content "Annuler (Rappel de $coach)" -Arguments "powershell.exe -NoProfile -File `"$cancelPath`""
    $action = New-BTAction -Buttons $button
    $logo = New-BTImage -Source $logoPath -AppLogoOverride -Crop None

    # --- Boucle pour le compte à rebours ---
    $remainingTime = $totalTime
    while ($remainingTime -gt 0) {
        # Créer le message avec le temps restant
        $message = $baseMessage -f $remainingTime
        $text = New-BTText -Content $message
        $binding = New-BTBinding -Children $text -AppLogoOverride $logo
        $visual = New-BTVisual -BindingGeneric $binding
        $content = New-BTContent -Visual $visual -Actions $action

        # Envoyer la notification avec un identifiant unique
        Submit-BTNotification -Content $content -UniqueIdentifier $notificationId

        Write-Host "Notification mise à jour : $message"

        # Attendre l'intervalle, mais vérifier l'annulation toutes les secondes
        for ($i = 0; $i -lt $updateInterval; $i++) {
            Start-Sleep -Seconds 1
            if (Test-Path $flagPath) {
                Write-Host "Lancement annulé par l'utilisateur."
                break
            }
        }

        # Si annulé, sortir de la boucle principale
        if (Test-Path $flagPath) { break }

        # Réduire le temps restant
        $remainingTime -= $updateInterval
    }

    # --- Vérifier si le lancement doit se faire ---
    if (-not (Test-Path $flagPath)) {
        Write-Host "Délai écoulé. Lancement de launch_batch.ps1..."
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -File `"$ps1Path`"" -Verb RunAs
    }

    # --- Nettoyage du fichier d'annulation ---
    if (Test-Path $flagPath) { Remove-Item $flagPath -Force }

    Write-Host "Script terminé avec succès !"

} catch {
    # --- Gestion d'erreur ---
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