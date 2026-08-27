"""
Marketplace URL configuration — Freelancer Portal routes at /freelancer/
"""
from django.urls import path
from . import views_freelancer, api_views_freelancer

app_name = 'freelancer'

urlpatterns = [
    # ── Freelancer Registration ─────────────────────────────
    path('register/', views_freelancer.freelancer_register, name='register'),

    # ── Freelancer Dashboard ────────────────────────────────
    path('dashboard/', views_freelancer.freelancer_dashboard, name='dashboard'),

    # ── Freelancer Profile ──────────────────────────────────
    path('profile/', views_freelancer.freelancer_profile_view, name='profile_view'),
    path('profile/edit/', views_freelancer.freelancer_profile_edit, name='profile_edit'),

    # ── Find & Browse Projects ──────────────────────────────
    path('find-projects/', views_freelancer.freelancer_find_projects, name='find_projects'),
    path('projects/', views_freelancer.freelancer_find_projects, name='projects_list'),
    path('projects/<uuid:pk>/', views_freelancer.freelancer_project_detail, name='project_detail'),
    path('projects/<uuid:pk>/apply/', views_freelancer.freelancer_project_apply, name='project_apply'),

    # ── My Applications ─────────────────────────────────────
    path('applications/', views_freelancer.freelancer_my_applications, name='my_applications'),
    path('applications/<uuid:app_pk>/withdraw/', views_freelancer.freelancer_application_withdraw, name='application_withdraw'),

    # ── My Active Projects & Workspace ──────────────────────
    path('my-projects/', views_freelancer.freelancer_my_projects, name='my_projects'),
    path('my-projects/<uuid:pk>/', views_freelancer.freelancer_workspace, name='workspace'),
    path('my-projects/<uuid:pk>/update-progress/', views_freelancer.freelancer_update_progress, name='update_progress'),

    # ── Payments ────────────────────────────────────────────
    path('payments/', views_freelancer.freelancer_payments, name='payments'),

    # ── Support / Reports ───────────────────────────────────
    path('support/', views_freelancer.freelancer_support_list, name='support_list'),
    path('support/create/', views_freelancer.freelancer_support_create, name='support_create'),

    # ── REST API v1 (Freelancer) ────────────────────────────
    path('api/v1/dashboard/stats/', api_views_freelancer.api_freelancer_dashboard_stats, name='api_dashboard_stats'),
    path('api/v1/profile/', api_views_freelancer.api_freelancer_profile, name='api_profile'),
    path('api/v1/projects/', api_views_freelancer.api_freelancer_find_projects, name='api_find_projects'),
    path('api/v1/projects/<uuid:pk>/', api_views_freelancer.api_freelancer_project_detail, name='api_project_detail'),
    path('api/v1/projects/<uuid:pk>/apply/', api_views_freelancer.api_freelancer_apply, name='api_apply'),
    path('api/v1/applications/', api_views_freelancer.api_freelancer_my_applications, name='api_my_applications'),
    path('api/v1/applications/<uuid:app_pk>/withdraw/', api_views_freelancer.api_freelancer_withdraw_application, name='api_withdraw_application'),
    path('api/v1/my-projects/', api_views_freelancer.api_freelancer_my_projects, name='api_my_projects'),
    path('api/v1/my-projects/<uuid:pk>/workspace/', api_views_freelancer.api_freelancer_workspace, name='api_workspace'),
    path('api/v1/my-projects/<uuid:pk>/progress/', api_views_freelancer.api_freelancer_update_progress, name='api_update_progress'),
    path('api/v1/payments/', api_views_freelancer.api_freelancer_payments, name='api_payments'),
    path('api/v1/reports/', api_views_freelancer.api_freelancer_reports, name='api_reports'),
]
