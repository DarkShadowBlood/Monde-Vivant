@echo off
setlocal

:: ===================================================================
:: CONFIGURATION
:: Collez votre clé API Mistral ici, entre les guillemets.
:: ===================================================================
set "API_KEY=czBBdZtL4WA8DF5FmkD3SUVDZrPBNM0u"


:: Ne pas modifier en dessous de cette ligne
:: ===================================================================

:menu
cls
echo ======================================================
echo      Generateur de Coachs - Monde Vivant
echo ======================================================
echo.
echo Personnalites disponibles :
echo ------------------------------------------------------
echo   [ Individuelles ]
echo   1. Varkis
echo   2. KaraOmbre
echo   3. Aegis
echo   4. KaraOmbreStable
echo   5. KaraOmbreChaos
echo ------------------------------------------------------
echo   [ Combinaisons ]
echo   6. Varkis + KaraOmbre
echo   7. KaraOmbre + Aegis
echo   8. Varkis + Aegis
echo   9. Varkis + KaraOmbre + Aegis
echo ------------------------------------------------------
echo   [ Actions ]
echo   S. Supprimer une personnalite
echo   0. Quitter
echo.
echo ======================================================
echo.

set "choice="
set /p choice="Votre choix (ex: 1 pour generer, s pour supprimer) : "

if not defined choice goto menu

:: --- Logique de gestion des choix (v3) ---
set "action="
set "num_choice=%choice%"

:: 1. Detecter si une action est demandee (c ou s a la fin)
echo "%choice%" | findstr /r /i "[s]$" > nul
if %errorlevel% equ 0 (
    set "action=%choice:~-1%"
    set "num_choice=%choice:~0,-1%"
)

:: 2. Gerer les actions simples (sans numero)
if /i "%choice%"=="S" goto delete_personality
if "%choice%"=="0" goto :eof

:: 3. Associer le numero a la personnalite
if "%num_choice%"=="1" set "PERSONALITY=Varkis"
if "%num_choice%"=="2" set "PERSONALITY=KaraOmbre"
if "%num_choice%"=="3" set "PERSONALITY=Aegis"
if "%num_choice%"=="4" set "PERSONALITY=KaraOmbreStable"
if "%num_choice%"=="5" set "PERSONALITY=KaraOmbreChaos"
if "%num_choice%"=="6" set "PERSONALITY=Varkis + KaraOmbre"
if "%num_choice%"=="7" set "PERSONALITY=KaraOmbre + Aegis"
if "%num_choice%"=="8" set "PERSONALITY=Varkis + Aegis"
if "%num_choice%"=="9" set "PERSONALITY=Varkis + KaraOmbre + Aegis"

:: 4. Valider le choix et executer l'action
if not defined PERSONALITY (
    echo.
    echo Choix invalide. Veuillez reessayer.
    pause
    goto menu
)

:: --- Fin de la logique de gestion ---
cls
echo Lancement de la generation pour "%PERSONALITY%" avec Mistral...
echo Cela peut prendre une ou deux minutes...
echo.

:: Verifier si Python est installe
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python ou ajouter son chemin au PATH.
    pause
    exit /b
)

:: Execute le script Python en passant les arguments
:: Correction de l'appel a Python
python "%~dp0generateur_coach.py" --api-key "%API_KEY%" --personality "%PERSONALITY%"

echo.
echo ======================================================
echo. 
echo Operation terminee.
echo.
pause
goto menu

:delete_personality
cls
echo ======================================================
echo      Suppression d'une personnalite
echo ======================================================
echo.
python "%~dp0generateur_coach.py" --delete
echo.
pause
goto menu