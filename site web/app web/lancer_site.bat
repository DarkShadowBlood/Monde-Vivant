@echo off
:: =============================================================================
:: ==         LANCEUR D'APPLICATION AVEC DEMANDE D'ADMINISTRATEUR             ==
:: =============================================================================
:: Ce script vérifie s'il est exécuté avec les droits d'administrateur.
:: Si ce n'est pas le cas, il se relance avec les privilèges élevés via une
:: fenêtre de confirmation Windows (UAC).
:: Une fois les privilèges obtenus, il exécute la séquence de lancement complète.

title Serveur Monde Vivant

:: --- Vérification des privilèges administrateur ---
net session >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Privileges administrateur detectes. Lancement de l'application complete...
) else (
    echo [INFO] Privileges administrateur requis. Demande d'elevation...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: --- Séquence de lancement (exécutée en tant qu'administrateur) ---
:: On se place dans le répertoire du script pour que les commandes python trouvent les fichiers.
:: C'est crucial car l'élévation de privilèges change le répertoire de travail.
cd /d "%~dp0"

echo.
echo =================================================
echo  Lancement de l'application Monde Vivant
echo =================================================
echo.

echo [ETAPE 1/3] Generation des liens et des donnees d'activites...
python generer_liens.py
if %errorlevel% neq 0 (echo. & echo ERREUR: Le script generer_liens.py a echoue. & pause & exit /b)
echo.

echo [ETAPE 2/3] Lancement du navigateur...
start http://localhost:8000/app%%20web/index.html?v=%RANDOM%
echo.

echo [ETAPE 3/3] Le serveur est en cours d'execution.
echo Pour arreter, fermez cette fenetre ou faites Ctrl+C.
echo.
python serveur.py

echo.
echo Le serveur s'est arrete. Appuyez sur une touche pour fermer.
pause
