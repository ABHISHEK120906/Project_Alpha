from django.urls import path
from . import views, api_views

app_name = 'core'

urlpatterns = [
    # ── Home ──────────────────────────────────────────────
    path('', views.home, name='home'),

    # ── Authentication ────────────────────────────────────
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # ── Dashboard ─────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

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

    # ── Payments ──────────────────────────────────────────
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<uuid:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<uuid:pk>/update/', views.payment_update, name='payment_update'),
    path('payments/<uuid:pk>/delete/', views.payment_delete, name='payment_delete'),

    # ── Tasks ─────────────────────────────────────────────
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:pk>/update/', views.task_update, name='task_update'),
    path('tasks/<uuid:pk>/delete/', views.task_delete, name='task_delete'),

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
    path('api/v1/dashboard/activity/', api_views.api_activity_log, name='api_activity_log'),
    path('api/v1/tasks/<uuid:pk>/toggle/', api_views.api_toggle_task, name='api_toggle_task'),
    path('api/v1/projects/<uuid:pk>/quick-status/', api_views.api_update_project_status, name='api_update_project_status'),
]