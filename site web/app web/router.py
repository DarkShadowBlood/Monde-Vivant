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

GET_ROUTES = {
    '/api/notifications': handle_get_notifications,
    '/api/notifications/config': handle_get_notifications_config,
    '/api/sante/files': handle_sante_files,
    '/api/sante/file': handle_sante_file,
    '/api/exercices': handle_exercices,
    '/api/request-templates': handle_get_request_templates,
    '/api/coaches': handle_get_coaches,
    '/api/histoire': handle_get_histoire,
    '/api/list-tasks': handle_list_tasks,
    '/api/aggregateData': handle_get_aggregate_data,
}

POST_ROUTES = {
    '/api/notifications/generate': handle_post_generate_notifications,
    '/api/notifications/config': handle_post_notifications_config,
    '/api/sante/save': handle_sante_save,
    '/api/generate-coach-message': handle_post_generate_coach_message,
    '/api/generate-motivation': handle_post_generate_motivation,
    '/api/schedule-startup-notifications': handle_schedule_startup_notifications,
    '/api/preview-schedule': handle_preview_schedule,
    '/api/confirm-schedule': handle_confirm_schedule,
    '/api/confirm-schedule-old': handle_confirm_schedule_old,
    '/api/delete-task': handle_delete_task,
    '/api/saveFile': handle_post_save_file,
    '/api/injectAnalysis': handle_post_inject_analysis,
    '/api/processAnalyses': handle_post_process_analyses,
}
