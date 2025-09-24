"""
Ce module définit le système de routage de l'application.

Il centralise l'association entre les chemins d'API (endpoints) et les fonctions
gestionnaires (handlers) qui traitent les requêtes.

- `GET_ROUTES`: Dictionnaire pour les requêtes de type GET.
- `POST_ROUTES`: Dictionnaire pour les requêtes de type POST.

Cette approche permet de découpler la logique du serveur principal de la logique
spécifique à chaque route, rendant le code plus modulaire et facile à maintenir.
Les fonctions de gestion sont importées depuis les modules `routes_*` dédiés.
"""
from routes_sante import (
    handle_sante_files,
    handle_sante_file,
    handle_sante_save,
    handle_exercices
)
from routes_notifications import (
    handle_get_notifications,
    handle_get_notifications_config,
    handle_post_generate_notifications,
    handle_post_notifications_config,
    handle_post_generate_coach_message,
    handle_post_generate_motivation
)
from routes_schedule import (
    handle_list_tasks,
    handle_schedule_startup_notifications,
    handle_preview_schedule,
    handle_confirm_schedule,
    handle_confirm_schedule_old,
    handle_delete_task
)
from routes_misc import (
    handle_get_request_templates,
    handle_get_coaches,
    handle_get_histoire,
    handle_get_aggregate_data,
    handle_post_save_file,
    handle_post_inject_analysis,
    handle_post_process_analyses
)

# Définit les routes pour les requêtes GET
GET_ROUTES = {
    # Notifications
    '/api/notifications': handle_get_notifications,
    '/api/notifications/config': handle_get_notifications_config,
    # Santé
    '/api/sante/files': handle_sante_files,
    '/api/sante/file': handle_sante_file,
    '/api/exercices': handle_exercices,
    # Planification
    '/api/list-tasks': handle_list_tasks,
    # Divers
    '/api/request-templates': handle_get_request_templates,
    '/api/coaches': handle_get_coaches,
    '/api/histoire': handle_get_histoire,
    '/api/aggregateData': handle_get_aggregate_data,
}

# Définit les routes pour les requêtes POST
POST_ROUTES = {
    # Notifications
    '/api/notifications/generate': handle_post_generate_notifications,
    '/api/notifications/config': handle_post_notifications_config,
    '/api/generate-coach-message': handle_post_generate_coach_message,
    '/api/generate-motivation': handle_post_generate_motivation,
    # Santé
    '/api/sante/save': handle_sante_save,
    # Planification
    '/api/schedule-startup-notifications': handle_schedule_startup_notifications,
    '/api/preview-schedule': handle_preview_schedule,
    '/api/confirm-schedule': handle_confirm_schedule,
    '/api/confirm-schedule-old': handle_confirm_schedule_old, # Route obsolète
    '/api/delete-task': handle_delete_task,
    # Divers
    '/api/saveFile': handle_post_save_file,
    '/api/injectAnalysis': handle_post_inject_analysis,
    '/api/processAnalyses': handle_post_process_analyses,
}