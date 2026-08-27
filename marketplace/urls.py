"""
Marketplace URL configuration — all client-facing routes at /client/
"""
from django.urls import path
from . import views, api_views

app_name = 'marketplace'

urlpatterns = [
    # ── Client Registration ────────────────────────────────
    path('register/', views.client_register, name='client_register'),

    # ── Client Dashboard ───────────────────────────────────
    path('dashboard/', views.client_dashboard, name='client_dashboard'),

    # ── Client Profile ─────────────────────────────────────
    path('profile/', views.client_profile_view, name='client_profile_view'),
    path('profile/edit/', views.client_profile_edit, name='client_profile_edit'),

    # ── Projects ───────────────────────────────────────────
    path('projects/', views.project_list, name='project_list'),
    path('projects/post/', views.project_post, name='project_post'),
    path('projects/<uuid:pk>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<uuid:pk>/close/', views.project_close, name='project_close'),
    path('projects/<uuid:pk>/reopen/', views.project_reopen, name='project_reopen'),

    # ── Applications ───────────────────────────────────────
    path('projects/<uuid:pk>/applications/', views.project_applications, name='project_applications'),
    path('applications/<uuid:app_pk>/accept/', views.application_accept, name='application_accept'),
    path('applications/<uuid:app_pk>/reject/', views.application_reject, name='application_reject'),

    # ── Active Project Workspace ───────────────────────────
    path('projects/<uuid:pk>/workspace/', views.project_workspace, name='project_workspace'),
    path('projects/<uuid:pk>/mark-in-progress/', views.project_mark_in_progress, name='project_mark_in_progress'),
    path('projects/<uuid:pk>/mark-completed/', views.project_mark_completed, name='project_mark_completed'),

    # ── Payments ───────────────────────────────────────────
    path('payments/', views.client_payments, name='client_payments'),

    # ── Support / Reports ──────────────────────────────────
    path('support/', views.client_support_list, name='client_support_list'),
    path('support/create/', views.client_support_create, name='client_support_create'),

    # ── API v1 (Client) ────────────────────────────────────
    path('api/v1/client/dashboard/stats/', api_views.api_client_dashboard_stats, name='api_client_dashboard_stats'),
    path('api/v1/client/profile/', api_views.api_client_profile, name='api_client_profile'),
    path('api/v1/client/projects/', api_views.api_client_projects, name='api_client_projects'),
    path('api/v1/client/projects/<uuid:pk>/', api_views.api_client_project_detail, name='api_client_project_detail'),
    path('api/v1/client/projects/<uuid:pk>/applications/', api_views.api_project_applications, name='api_project_applications'),
    path('api/v1/client/applications/<uuid:app_pk>/accept/', api_views.api_accept_application, name='api_accept_application'),
    path('api/v1/client/applications/<uuid:app_pk>/reject/', api_views.api_reject_application, name='api_reject_application'),
    path('api/v1/client/payments/', api_views.api_client_payments, name='api_client_payments'),
    path('api/v1/client/reports/', api_views.api_client_reports, name='api_client_reports'),
]
