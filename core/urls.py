from django.urls import path, include
from . import views, api_views

app_name = 'core'

urlpatterns = [
    # ── Home ──────────────────────────────────────────────
    path('', views.home, name='home'),

    # ── Authentication ────────────────────────────────────
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # ── Super Admin Dashboard Module ─────────────────────
    path('admin-dashboard/', include('core.admin_urls')),

    # ── Dashboard & Sample Data ───────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),
    path('seed-sample-data/', views.load_sample_data, name='load_sample_data'),

    # ── Clients ───────────────────────────────────────────
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<uuid:pk>/', views.client_detail, name='client_detail'),
    path('clients/<uuid:pk>/update/', views.client_update, name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete, name='client_delete'),

    # ── Projects ──────────────────────────────────────────
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<uuid:pk>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:pk>/update/', views.project_update, name='project_update'),
    path('projects/<uuid:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<uuid:pk>/archive/', views.project_archive, name='project_archive'),
    path('projects/<uuid:pk>/restore/', views.project_restore, name='project_restore'),
    path('projects/<uuid:pk>/duplicate/', views.project_duplicate, name='project_duplicate'),
    path('projects/<uuid:pk>/comment/', views.project_add_comment, name='project_add_comment'),
    path('projects/<uuid:pk>/upload/', views.project_upload_file, name='project_upload_file'),

    # ── Clients ───────────────────────────────────────────
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<uuid:pk>/', views.client_detail, name='client_detail'),
    path('clients/<uuid:pk>/update/', views.client_update, name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/<uuid:pk>/archive/', views.client_archive, name='client_archive'),
    path('clients/<uuid:pk>/restore/', views.client_restore, name='client_restore'),

    # ── Payments ──────────────────────────────────────────
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<uuid:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<uuid:pk>/update/', views.payment_update, name='payment_update'),
    path('payments/<uuid:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('payments/<uuid:pk>/receipt/', views.payment_receipt, name='payment_receipt'),

    # ── Tasks ─────────────────────────────────────────────
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:pk>/update/', views.task_update, name='task_update'),
    path('tasks/<uuid:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<uuid:pk>/archive/', views.task_archive, name='task_archive'),
    path('tasks/<uuid:pk>/restore/', views.task_restore, name='task_restore'),

    # ── Profile ───────────────────────────────────────────
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.profile_change_password, name='profile_change_password'),
    path('profile/remove-picture/', views.profile_remove_picture, name='profile_remove_picture'),

    # ── Income & Expense Tracker ──────────────────────────
    path('finances/', views.income_expense_tracker, name='income_expense_tracker'),
    path('incomes/create/', views.income_create, name='income_create'),
    path('incomes/<uuid:pk>/delete/', views.income_delete, name='income_delete'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<uuid:pk>/delete/', views.expense_delete, name='expense_delete'),

    # ── Invoices ──────────────────────────────────────────
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<uuid:pk>/email/', views.invoice_email, name='invoice_email'),
    path('invoices/<uuid:pk>/delete/', views.invoice_delete, name='invoice_delete'),

    # ── Calendar & Deadlines ──────────────────────────────
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('calendar/events/create/', views.calendar_event_create, name='calendar_event_create'),
    path('calendar/events/<uuid:pk>/delete/', views.calendar_event_delete, name='calendar_event_delete'),

    # ── File Manager ──────────────────────────────────────
    path('files/', views.file_manager, name='file_manager'),
    path('files/upload/', views.file_upload, name='file_upload'),
    path('files/<uuid:pk>/delete/', views.file_delete, name='file_delete'),

    # ── Notifications ─────────────────────────────────────
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<uuid:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notification_read_all, name='notification_read_all'),
    path('notifications/<uuid:pk>/delete/', views.notification_delete, name='notification_delete'),

    # ── Search & Access Restrictions ──────────────────────
    path('search/', views.global_search, name='global_search'),
    path('forbidden/', views.forbidden_view, name='forbidden'),

    # ── Notes ─────────────────────────────────────────────
    path('notes/', views.note_list, name='note_list'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<uuid:pk>/', views.note_detail, name='note_detail'),
    path('notes/<uuid:pk>/update/', views.note_update, name='note_update'),
    path('notes/<uuid:pk>/delete/', views.note_delete, name='note_delete'),

    # ── Activity Log ──────────────────────────────────────
    path('activities/', views.activity_list, name='activity_list'),

    # ── Reports ───────────────────────────────────────────
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/export/pdf/<str:report_type>/', views.export_pdf_report, name='export_pdf_report'),
    path('reports/export/excel/<str:report_type>/', views.export_excel_report, name='export_excel_report'),

    # ── Settings ──────────────────────────────────────────
    path('settings/', views.user_settings, name='settings'),

    # ── Backend Proxy API Endpoints (/api/v1/) ───────────
    path('api/v1/health/', api_views.api_health, name='api_health'),
    path('api/v1/dashboard/stats/', api_views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/v1/dashboard/analytics/', api_views.api_dashboard_analytics, name='api_dashboard_analytics'),
    path('api/v1/dashboard/activity/', api_views.api_activity_log, name='api_activity_log'),
    path('api/v1/tasks/<uuid:pk>/toggle/', api_views.api_toggle_task, name='api_toggle_task'),
    path('api/v1/projects/<uuid:pk>/quick-status/', api_views.api_update_project_status, name='api_update_project_status'),
    path('api/v1/notifications/unread-count/', api_views.api_unread_notification_count, name='api_unread_notification_count'),
]