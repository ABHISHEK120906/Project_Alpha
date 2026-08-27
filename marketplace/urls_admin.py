"""
Marketplace Admin URL Configuration (Stage 3) — /admin-dashboard/marketplace/
"""
from django.urls import path
from . import views_admin, api_views_admin

app_name = 'marketplace_admin'

urlpatterns = [
    # ── Platform Overview & Dashboard ───────────────────────
    path('', views_admin.admin_marketplace_dashboard, name='dashboard'),

    # ── User Management (Clients & Freelancers) ─────────────
    path('users/', views_admin.admin_users_list, name='users_list'),
    path('users/<int:user_id>/', views_admin.admin_user_detail, name='user_detail'),
    path('users/<int:user_id>/suspend/', views_admin.admin_user_toggle_suspend, name='user_toggle_suspend'),
    path('users/<int:user_id>/active/', views_admin.admin_user_toggle_active, name='user_toggle_active'),

    # ── Project Catalog & Moderation ────────────────────────
    path('projects/', views_admin.admin_projects_list, name='projects_list'),
    path('projects/<uuid:project_id>/', views_admin.admin_project_detail, name='project_detail'),

    # ── Application Monitoring ──────────────────────────────
    path('applications/', views_admin.admin_applications_list, name='applications_list'),

    # ── Report Management & Investigation ───────────────────
    path('reports/', views_admin.admin_reports_list, name='reports_list'),
    path('reports/<str:report_type>/<uuid:report_id>/', views_admin.admin_report_detail, name='report_detail'),

    # ── Dispute Management & Arbitration ────────────────────
    path('disputes/', views_admin.admin_disputes_list, name='disputes_list'),
    path('disputes/create/', views_admin.admin_dispute_create, name='dispute_create'),
    path('disputes/<uuid:dispute_id>/', views_admin.admin_dispute_detail, name='dispute_detail'),

    # ── Support Desk ────────────────────────────────────────
    path('support/', views_admin.admin_support_list, name='support_list'),
    path('support/<uuid:ticket_id>/', views_admin.admin_support_detail, name='support_detail'),

    # ── Platform Analytics ──────────────────────────────────
    path('analytics/', views_admin.admin_analytics_view, name='analytics'),

    # ── Administrative Reports & Multi-Format Exports ───────
    path('exports/', views_admin.admin_exports_hub, name='exports_hub'),
    path('exports/<str:export_type>/<str:export_format>/', views_admin.admin_export_data, name='export_data'),

    # ── REST API v1 (Admin) ─────────────────────────────────
    path('api/v1/dashboard/stats/', api_views_admin.api_admin_dashboard_stats, name='api_dashboard_stats'),
    path('api/v1/users/', api_views_admin.api_admin_users, name='api_users'),
    path('api/v1/users/<int:user_id>/suspend/', api_views_admin.api_admin_user_suspend, name='api_user_suspend'),
    path('api/v1/projects/', api_views_admin.api_admin_projects, name='api_projects'),
    path('api/v1/projects/<uuid:project_id>/moderate/', api_views_admin.api_admin_project_moderate, name='api_project_moderate'),
    path('api/v1/applications/', api_views_admin.api_admin_applications, name='api_applications'),
    path('api/v1/reports/', api_views_admin.api_admin_reports, name='api_reports'),
    path('api/v1/reports/<str:report_type>/<uuid:report_id>/resolve/', api_views_admin.api_admin_report_resolve, name='api_report_resolve'),
    path('api/v1/disputes/', api_views_admin.api_admin_disputes, name='api_disputes'),
    path('api/v1/disputes/<uuid:dispute_id>/resolve/', api_views_admin.api_admin_dispute_resolve, name='api_dispute_resolve'),
    path('api/v1/support/', api_views_admin.api_admin_support_tickets, name='api_support_tickets'),
    path('api/v1/support/<uuid:ticket_id>/respond/', api_views_admin.api_admin_support_respond, name='api_support_respond'),
]
