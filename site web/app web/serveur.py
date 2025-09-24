import http.server
import socketserver
from functools import partial
from urllib.parse import urlparse

from config import PORT, DIRECTORY, SANTE_DIR, SCHEDULED_TASKS_DIR
from lore import load_coach_lore as load_lore_data # Renommer pour éviter confusion
from router import GET_ROUTES, POST_ROUTES
from utils import send_json_error

# S'assurer que les dossiers de base existent
SANTE_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

class AppContext:
    """Un objet simple pour contenir l'état partagé de l'application."""
    def __init__(self):
        self.coach_lore = {}
        # On pourrait ajouter ici d'autres choses : config, connexion db, etc.

    def load_data(self):
        """Charge toutes les données nécessaires au démarrage."""
        print("Chargement du contexte de l'application...")
        self.coach_lore = load_lore_data()
        print("Contexte chargé.")

# Créer une instance unique qui sera partagée
app_context = AppContext()

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Le contexte est passé via le constructeur
        self.app_context = kwargs.pop('app_context')
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        
        # Chercher la route dans le dictionnaire des routes GET
        route_handler = GET_ROUTES.get(parsed_path.path)
        if route_handler:
            route_handler(self, self.app_context) # On passe le contexte au handler
        else:
            # Si aucune route API ne correspond, servir un fichier statique
            super().do_GET()

    def do_POST(self):
        # Chercher la route dans le dictionnaire des routes POST
        route_handler = POST_ROUTES.get(self.path)
        if route_handler:
            route_handler(self, self.app_context) # On passe le contexte au handler
        else:
            send_json_error(self, 404, "Endpoint non trouvé.")

    def end_headers(self):
        # Ajoute des en-têtes pour désactiver le cache du navigateur
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


# --- Démarrage du serveur ---
def run_server():
    # Charger les données AVANT de démarrer le serveur
    app_context.load_data()

    # Utiliser functools.partial pour "pré-remplir" le handler avec notre contexte
    HandlerWithContext = partial(NoCacheHandler, app_context=app_context)

    with socketserver.TCPServer(("", PORT), HandlerWithContext) as httpd:
        print(f"Serveur démarré sur http://localhost:{PORT}")
        print("Servez-vous de ce terminal pour voir les requêtes.")
        print("Faites Ctrl+C pour arrêter le serveur.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()
