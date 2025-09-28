import http.server
import socketserver
import threading
import os
from urllib.parse import urlparse

from config import PORT, DIRECTORY, SANTE_DIR, SCHEDULED_TASKS_DIR
from lore import load_coach_lore
from router import GET_ROUTES, POST_ROUTES
from utils import send_json_error

# S'assurer que les dossiers de base existent
SANTE_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

class AppContext:
    """Un objet simple pour contenir l'état partagé de l'application."""
    def __init__(self):
        self.coach_lore = {}
        self._loaded = False
        self._lock = threading.Lock()

    def load_data(self):
        """
        Charge les données nécessaires de manière "paresseuse" et thread-safe.
        Ne s'exécute qu'une seule fois.
        """
        with self._lock:
            if not self._loaded:
                print("--- INFO: Chargement du contexte de l'application (première requête)... ---")
                self.coach_lore = load_coach_lore()
                self._loaded = True
                print("--- INFO: Contexte chargé. ---")


# Créer une instance unique qui sera partagée
app_context = AppContext()

class CustomTCPServer(socketserver.TCPServer):
    """Un TCPServer personnalisé qui détient le contexte de l'application."""
    def __init__(self, server_address, RequestHandlerClass, app_context):
        self.app_context = app_context
        super().__init__(server_address, RequestHandlerClass)

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP qui désactive le cache et route les requêtes API."""
    def __init__(self, *args, **kwargs):
        # Appeler d'abord le constructeur parent pour qu'il initialise self.server
        super().__init__(*args, directory=DIRECTORY, **kwargs)

        # S'assurer que les données sont chargées avant de traiter la première requête
        if not self.server.app_context._loaded:
            self.server.app_context.load_data()

    def do_GET(self):
        """Gère les requêtes GET en les routant vers les handlers appropriés."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        
        # Chercher la route dans le dictionnaire des routes GET
        route_handler = GET_ROUTES.get(parsed_path.path)
        if route_handler:
            # Accéder au contexte via l'instance du serveur
            route_handler(self, self.server.app_context)
        else:
            # Si aucune route API ne correspond, servir un fichier statique
            super().do_GET()

    def do_POST(self):
        """Gère les requêtes POST en les routant vers les handlers appropriés."""
        # Chercher la route dans le dictionnaire des routes POST
        route_handler = POST_ROUTES.get(self.path)
        if route_handler:
            # Accéder au contexte via l'instance du serveur
            route_handler(self, self.server.app_context)
        else:
            send_json_error(self, 404, "Endpoint non trouvé.")

    def end_headers(self):
        # Ajoute des en-têtes pour désactiver le cache du navigateur
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def send_head(self):
        """
        Surcharge pour forcer la désactivation du cache en empêchant les réponses 304.
        Ceci résout le problème de F5 obligatoire dans Firefox pour les fichiers statiques.
        """
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            # La gestion des répertoires reste la même
            return super().send_head()
        
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        
        # On force une réponse 200 OK au lieu de laisser le parent gérer le 304
        self.send_response(200)
        
        # Amélioration : Spécifier l'encodage UTF-8 pour les fichiers texte
        if ctype.startswith('text/'):
            self.send_header("Content-type", f"{ctype}; charset=utf-8")
        else:
            self.send_header("Content-type", ctype)

        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f


# --- Démarrage du serveur ---
def run_server():
    """Initialise et lance le serveur HTTP."""
    # Charger les données AVANT de démarrer le serveur
    # app_context.load_data() # Le chargement est maintenant paresseux

    with CustomTCPServer(("", PORT), NoCacheHandler, app_context) as httpd:
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
