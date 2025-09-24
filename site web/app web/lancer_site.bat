@echo off
REM Titre de la fenêtre de console
title Serveur Monde Vivant

echo =================================================
echo  Lancement de l'application Monde Vivant
echo =================================================
echo.

REM 1. Générer les fichiers de données et de navigation à jour
echo [ETAPE 1/3] Generation des liens et des donnees d'activites...
python generer_liens.py
if %errorlevel% neq 0 (echo. & echo ERREUR: Le script generer_liens.py a echoue. & cmd /k)
echo.

REM 2. Lance le navigateur sur la bonne page avec un paramètre pour forcer le rafraîchissement
echo [ETAPE 2/3] Lancement du navigateur...
REM L'ajout de "?v=%RANDOM%" force le navigateur à recharger les fichiers au lieu d'utiliser le cache.
start http://localhost:8000/app%%20web/index.html?v=%RANDOM%
echo.

REM Lance le serveur Python. La console restera ouverte.
echo [ETAPE 3/3] Le serveur est en cours d'execution.
echo Pour arreter, fermez cette fenetre ou faites Ctrl+C.
echo.
python serveur.py

echo.
echo Le serveur s'est arrete. La fenetre reste ouverte pour la copie.
echo Vous pouvez la fermer manuellement.
cmd /k
