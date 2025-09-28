from routes_gamification import (
    handle_get_gamification_profile,
    handle_post_claim_loot,
    handle_get_inventory,
    handle_craft_item,
    handle_sell_item,
    handle_buy_item,
    handle_get_quests,
    handle_claim_quest,
    handle_get_achievements,
    handle_claim_achievement
)
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
    handle_post_generate_motivation,
    handle_get_win_notification_status,
    handle_post_toggle_win_notification_task,
    handle_get_win_notification_history,
    handle_post_test_win_notification,
    handle_post_clear_win_notification_history
)
from routes_schedule import (
    handle_list_tasks,
    handle_schedule_startup_notifications,
    handle_preview_schedule,
    handle_confirm_schedule,
    handle_confirm_schedule_old,
    handle_delete_task,
    handle_update_task
)
from routes_misc import (
    handle_get_request_templates,
    handle_get_coaches,
    handle_get_histoire,
    handle_post_save_file,
    handle_post_inject_analysis,
    handle_post_process_analyses
)
from gym.routes_gym import (
    handle_get_muscle_groups,
    handle_get_exercises_by_group
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
    '/api/tasks/list': handle_list_tasks,
    '/api/gamification/profile': handle_get_gamification_profile,
    '/api/gamification/inventory': handle_get_inventory,
    '/api/gamification/quests': handle_get_quests,
    '/api/gamification/achievements': handle_get_achievements,
    '/api/win-notifications/status': handle_get_win_notification_status,
    '/api/win-notifications/history': handle_get_win_notification_history,
    '/api/gym/muscle-groups': handle_get_muscle_groups,
    '/api/gym/exercises': handle_get_exercises_by_group,
}

POST_ROUTES = {
    '/api/notifications/generate': handle_post_generate_notifications,
    '/api/notifications/config': handle_post_notifications_config,
    '/api/sante/save': handle_sante_save,
    '/api/generate-motivation': handle_post_generate_motivation,
    '/api/schedule-startup-notifications': handle_schedule_startup_notifications,
    '/api/preview-schedule': handle_preview_schedule,
    '/api/confirm-schedule': handle_confirm_schedule,
    '/api/confirm-schedule-old': handle_confirm_schedule_old,
    '/api/update-task': handle_update_task,
    '/api/delete-task': handle_delete_task,
    '/api/saveFile': handle_post_save_file,
    '/api/injectAnalysis': handle_post_inject_analysis,
    '/api/processAnalyses': handle_post_process_analyses,
    '/api/gamification/claim-loot': handle_post_claim_loot,
    '/api/gamification/craft': handle_craft_item,
    '/api/gamification/sell': handle_sell_item,
    '/api/gamification/buy': handle_buy_item,
    '/api/gamification/claim-quest': handle_claim_quest,
    '/api/gamification/claim-achievement': handle_claim_achievement,
    '/api/win-notifications/toggle': handle_post_toggle_win_notification_task,
    '/api/win-notifications/test': handle_post_test_win_notification,
    '/api/win-notifications/clear-history': handle_post_clear_win_notification_history,
}
