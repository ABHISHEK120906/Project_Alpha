from django.urls import path
from . import admin_views

urlpatterns = [
    # ── Master Dashboard ──────────────────────────────────
    path('', admin_views.admin_dashboard, name='admin_dashboard'),

    # ── User Management ──────────────────────────────────
    path('users/', admin_views.admin_users_list, name='admin_users_list'),
    path('users/create/', admin_views.admin_user_create, name='admin_user_create'),
    path('users/<int:user_id>/edit/', admin_views.admin_user_edit, name='admin_user_edit'),
    path('users/<int:user_id>/suspend/', admin_views.admin_user_suspend, name='admin_user_suspend'),
    path('users/<int:user_id>/activate/', admin_views.admin_user_activate, name='admin_user_activate'),
    path('users/<int:user_id>/verify/', admin_views.admin_user_verify_email, name='admin_user_verify_email'),
    path('users/<int:user_id>/reset-password/', admin_views.admin_user_reset_password, name='admin_user_reset_password'),
    path('users/<int:user_id>/force-logout/', admin_views.admin_user_force_logout, name='admin_user_force_logout'),
    path('users/<int:user_id>/delete/', admin_views.admin_user_delete, name='admin_user_delete'),
    path('users/<int:user_id>/restore/', admin_views.admin_user_restore, name='admin_user_restore'),
    path('users/<int:user_id>/history/', admin_views.admin_user_history, name='admin_user_history'),

    # ── Project Management ────────────────────────────────
    path('projects/', admin_views.admin_projects_list, name='admin_projects_list'),
    path('projects/create/', admin_views.admin_project_create, name='admin_project_create'),
    path('projects/<uuid:project_id>/edit/', admin_views.admin_project_edit, name='admin_project_edit'),
    path('projects/<uuid:project_id>/archive/', admin_views.admin_project_archive, name='admin_project_archive'),
    path('projects/<uuid:project_id>/duplicate/', admin_views.admin_project_duplicate, name='admin_project_duplicate'),
    path('projects/<uuid:project_id>/delete/', admin_views.admin_project_delete, name='admin_project_delete'),
    path('projects/bulk/', admin_views.admin_project_bulk_action, name='admin_project_bulk_action'),

    # ── Client Management ─────────────────────────────────
    path('clients/', admin_views.admin_clients_list, name='admin_clients_list'),
    path('clients/create/', admin_views.admin_client_create, name='admin_client_create'),
    path('clients/merge/', admin_views.admin_client_merge, name='admin_client_merge'),
    path('clients/<uuid:client_id>/delete/', admin_views.admin_client_delete, name='admin_client_delete'),

    # ── Financial Management ──────────────────────────────
    path('finances/', admin_views.admin_finances, name='admin_finances'),
    path('finances/refund/<uuid:refund_id>/', admin_views.admin_refund_action, name='admin_refund_action'),

    # ── Notification & Announcements ─────────────────────
    path('notifications/', admin_views.admin_notifications, name='admin_notifications'),
    path('notifications/<uuid:announcement_id>/delete/', admin_views.admin_announcement_delete, name='admin_announcement_delete'),

    # ── Activity Audit Logs ───────────────────────────────
    path('activities/', admin_views.admin_activity_logs, name='admin_activity_logs'),

    # ── Security Center ───────────────────────────────────
    path('security/', admin_security := admin_views.admin_security, name='admin_security'),
    path('security/unblock-ip/<uuid:ip_id>/', admin_views.admin_unblock_ip, name='admin_unblock_ip'),

    # ── System Settings ───────────────────────────────────
    path('settings/', admin_views.admin_settings, name='admin_settings'),

    # ── Database Management ───────────────────────────────
    path('database/', admin_views.admin_database, name='admin_database'),
    path('database/backup/', admin_views.admin_database_backup, name='admin_database_backup'),
    path('database/restore/', admin_views.admin_database_restore, name='admin_database_restore'),

    # ── Reports & Analytics Hub ───────────────────────────
    path('reports/', admin_views.admin_reports, name='admin_reports'),
    path('reports/export/<str:report_type>/<str:export_format>/', admin_views.admin_report_export, name='admin_report_export'),
]
