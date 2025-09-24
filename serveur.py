"""
Serveur principal de l'application "Monde Vivant".

Ce script lance un serveur HTTP qui utilise une architecture modulaire pour gérer
les requêtes API et servir les fichiers statiques de l'application web.

L'architecture est la suivante :
- `serveur.py`: Point d'entrée, configure et lance le serveur.
- `site web/app web/config.py`: Centralise la configuration (ports, chemins, clés API).
- `site web/app web/router.py`: Associe les URL (endpoints) aux fonctions de traitement.
- `site web/app web/routes_*.py`: Modules contenant la logique métier pour chaque groupe de routes.
- `site web/app web/utils.py`: Fonctions utilitaires partagées.
- `site web/app web/lore.py`: Gère le chargement de la personnalité des coachs.
"""
import http.server
import socketserver
import sys
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

# Ajoute le répertoire de l'application au chemin de recherche de Python
# pour permettre les imports depuis les sous-dossiers.
APP_DIR = Path(__file__).resolve().parent / "site web" / "app web"
sys.path.insert(0, str(APP_DIR))

# Importe les modules de l'application après avoir modifié le chemin
from config import PORT, DIRECTORY, SANTE_DIR, SCHEDULED_TASKS_DIR
from lore import load_coach_lore
from router import GET_ROUTES, POST_ROUTES
from utils import send_json_error

# S'assure que les dossiers de base existent au démarrage
SANTE_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

class AppContext:
    """
    Un objet simple pour contenir l'état partagé de l'application.

    Cela évite d'utiliser des variables globales et permet de passer un contexte
    clair aux gestionnaires de requêtes.
    """
    def __init__(self):
        self.coach_lore = {}

    def load_data(self):
        """Charge toutes les données nécessaires au démarrage du serveur."""
        print("Chargement du contexte de l'application...")
        self.coach_lore = load_coach_lore()
        print("Contexte chargé.")

# Crée une instance unique du contexte qui sera partagée par toutes les requêtes
app_context = AppContext()

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """
    Gestionnaire de requêtes HTTP personnalisé.

    Hérite de SimpleHTTPRequestHandler mais ajoute :
    - La gestion des routes API via le routeur.
    - L'injection du contexte de l'application.
    - La désactivation du cache pour les réponses.
    """
    def __init__(self, *args, **kwargs):
        self.app_context = kwargs.pop('app_context')
        # Le répertoire de service est défini dans config.py
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        """Traite les requêtes GET."""
        parsed_path = urlparse(self.path)
        
        # Le favicon est souvent demandé par les navigateurs, on l'ignore poliment.
        if parsed_path.path == '/favicon.ico':
            self.send_response(204) # No Content
            self.end_headers()
            return
        
        # Cherche une correspondance dans les routes API définies
        route_handler = GET_ROUTES.get(parsed_path.path)
        if route_handler:
            route_handler(self, self.app_context)
        else:
            # Si aucune route API ne correspond, on suppose que c'est une requête
            # pour un fichier statique (ex: index.html, style.css).
            super().do_GET()

    def do_POST(self):
        """Traite les requêtes POST."""
        route_handler = POST_ROUTES.get(self.path)
        if route_handler:
            route_handler(self, self.app_context)
        else:
            send_json_error(self, 404, "Endpoint non trouvé.")

    def end_headers(self):
        """Ajoute des en-têtes pour désactiver le cache du navigateur."""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run_server():
    """Configure et lance le serveur HTTP."""
    # Charge les données (lore des coachs, etc.) AVANT de démarrer le serveur
    app_context.load_data()

    # Utilise functools.partial pour "pré-remplir" le constructeur du handler
    # avec notre contexte d'application.
    HandlerWithContext = partial(NoCacheHandler, app_context=app_context)

    with socketserver.TCPServer(("", PORT), HandlerWithContext) as httpd:
        print(f"Serveur démarré sur http://localhost:{PORT}")
        print(f"Les fichiers sont servis depuis le répertoire: {DIRECTORY}")
        print("Utilisez ce terminal pour voir les requêtes. Ctrl+C pour arrêter.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()