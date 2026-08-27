"""
Marketplace Admin REST API Views (Stage 3) — /api/v1/admin/
============================================================
Protected endpoints for Platform Administrators.
Enforces SessionAuthentication and IsMarketplaceAdmin permission.
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import BasePermission
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q

from core.models import UserProfile, ActivityLog
from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
    MarketplaceDispute,
    PlatformSupportTicket,
)
from .serializers_admin import (
    AdminUserSerializer,
    AdminMarketplaceProjectSerializer,
    AdminProjectApplicationSerializer,
    AdminProjectReportSerializer,
    AdminFreelancerReportSerializer,
    AdminMarketplaceDisputeSerializer,
    AdminPlatformSupportTicketSerializer,
)
from .services_admin import AdminAnalyticsService


class IsMarketplaceAdmin(BasePermission):
    """Allows access only to authenticated Superusers, Staff, or role='admin'."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == 'admin')


# ---------------------------------------------------------------------------
# 1. Admin Dashboard Stats API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_dashboard_stats(request):
    """Returns platform KPI metrics and monthly trend distributions."""
    kpi = AdminAnalyticsService.get_platform_kpis()
    trends = AdminAnalyticsService.get_monthly_trends()
    risk = AdminAnalyticsService.get_predictive_risk_analysis()

    return Response({
        'kpis': kpi,
        'trends': trends,
        'risk_analysis': risk,
    })


# ---------------------------------------------------------------------------
# 2. User Management APIs
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_users(request):
    """List all users with filtering by role and status."""
    role = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('q', '').strip()

    users = User.objects.select_related('profile', 'client_profile', 'freelancer_profile').all().order_by('-date_joined')

    if role == 'client':
        users = users.filter(profile__role='client')
    elif role == 'freelancer':
        users = users.filter(profile__role='freelancer')

    if status_filter == 'active':
        users = users.filter(is_active=True, profile__is_suspended=False)
    elif status_filter == 'suspended':
        users = users.filter(profile__is_suspended=True)

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    serializer = AdminUserSerializer(users, many=True)
    return Response({'count': users.count(), 'results': serializer.data})


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_user_suspend(request, user_id):
    """Toggle suspension status for a user."""
    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    reason = request.data.get('reason', 'Administrative decision')

    profile.is_suspended = not profile.is_suspended
    profile.save()

    ActivityLog.objects.create(
        user=request.user,
        action='status_change',
        model_type='user',
        model_id=target_user.id,
        description=f"[ADMIN API] User {target_user.username} suspension set to {profile.is_suspended}. Reason: {reason}"
    )

    return Response({
        'message': f"User {target_user.username} suspension set to {profile.is_suspended}.",
        'is_suspended': profile.is_suspended,
    })


# ---------------------------------------------------------------------------
# 3. Project Management APIs
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_projects(request):
    """List all projects with status and category filtering."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    projects = MarketplaceProject.objects.select_related('client', 'assigned_freelancer').all().order_by('-created_at')

    if status_filter != 'all':
        projects = projects.filter(status=status_filter)
    if category_filter != 'all':
        projects = projects.filter(category=category_filter)

    serializer = AdminMarketplaceProjectSerializer(projects, many=True)
    return Response({'count': projects.count(), 'results': serializer.data})


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_project_moderate(request, project_id):
    """Moderate or update a project status."""
    project = get_object_or_404(MarketplaceProject, id=project_id)
    new_status = request.data.get('status')
    reason = request.data.get('reason', 'Administrative moderation')

    if new_status and new_status in dict(MarketplaceProject.STATUS_CHOICES):
        project.status = new_status
        project.save()

        ActivityLog.objects.create(
            user=request.user,
            action='status_change',
            model_type='project',
            model_id=project.id,
            description=f"[ADMIN API] Project '{project.title}' status set to {new_status}. Reason: {reason}"
        )
        return Response({
            'message': f"Project status updated to {new_status}.",
            'project': AdminMarketplaceProjectSerializer(project).data
        })

    return Response({'error': 'Invalid status choice.'}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# 4. Application Monitoring APIs
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_applications(request):
    """List all platform applications."""
    status_filter = request.GET.get('status', 'all')
    apps = ProjectApplication.objects.select_related('project', 'freelancer', 'project__client').all().order_by('-created_at')

    if status_filter != 'all':
        apps = apps.filter(status=status_filter)

    serializer = AdminProjectApplicationSerializer(apps, many=True)
    return Response({'count': apps.count(), 'results': serializer.data})


# ---------------------------------------------------------------------------
# 5. Report & Moderation APIs
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_reports(request):
    """List all filed reports from clients and freelancers."""
    status_filter = request.GET.get('status', 'all')
    c_reports = ProjectReport.objects.select_related('reporter', 'reported_user', 'project').all().order_by('-created_at')
    f_reports = FreelancerReport.objects.select_related('freelancer', 'reported_client', 'project').all().order_by('-created_at')

    if status_filter != 'all':
        c_reports = c_reports.filter(status=status_filter)
        f_reports = f_reports.filter(status=status_filter)

    return Response({
        'client_reports': AdminProjectReportSerializer(c_reports, many=True).data,
        'freelancer_reports': AdminFreelancerReportSerializer(f_reports, many=True).data,
        'total_count': c_reports.count() + f_reports.count(),
    })


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_report_resolve(request, report_type, report_id):
    """Update report status and optionally apply account suspension or project closure."""
    if report_type == 'client':
        report = get_object_or_404(ProjectReport, id=report_id)
        reported_user_obj = report.reported_user
    else:
        report = get_object_or_404(FreelancerReport, id=report_id)
        reported_user_obj = report.reported_client.user if report.reported_client else None

    new_status = request.data.get('status', 'resolved')
    action = request.data.get('action', 'no_action')
    admin_notes = request.data.get('admin_notes', '')

    report.status = new_status
    report.admin_notes = admin_notes
    report.save()

    if action == 'account_suspended' and reported_user_obj:
        p, _ = UserProfile.objects.get_or_create(user=reported_user_obj)
        p.is_suspended = True
        p.save()
    elif action == 'project_closed' and report.project:
        report.project.status = 'closed'
        report.project.save()

    ActivityLog.objects.create(
        user=request.user,
        action='update',
        model_type='report',
        model_id=report.id,
        description=f"[ADMIN API] Resolved {report_type} report #{str(report.id)[:8]} with status {new_status}. Action: {action}"
    )

    return Response({
        'message': f"Report #{str(report.id)[:8]} resolved successfully.",
        'status': report.status,
    })


# ---------------------------------------------------------------------------
# 6. Dispute Resolution APIs
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_disputes(request):
    """List all disputes or open a new formal dispute."""
    if request.method == 'GET':
        status_filter = request.GET.get('status', 'all')
        disputes = MarketplaceDispute.objects.select_related('project', 'client', 'freelancer', 'opened_by').all().order_by('-created_at')

        if status_filter != 'all':
            disputes = disputes.filter(status=status_filter)

        serializer = AdminMarketplaceDisputeSerializer(disputes, many=True)
        return Response({'count': disputes.count(), 'results': serializer.data})

    elif request.method == 'POST':
        project_id = request.data.get('project_id')
        project = get_object_or_404(MarketplaceProject, id=project_id)
        freelancer_p = getattr(project.assigned_freelancer, 'freelancer_profile', None) if project.assigned_freelancer else None

        dispute = MarketplaceDispute.objects.create(
            project=project,
            opened_by=request.user,
            client=project.client,
            freelancer=freelancer_p,
            category=request.data.get('category', 'other'),
            title=request.data.get('title', f"Dispute on {project.title}"),
            description=request.data.get('description', ''),
            evidence=request.data.get('evidence', ''),
            admin_notes=request.data.get('admin_notes', ''),
            status='open'
        )

        return Response(AdminMarketplaceDisputeSerializer(dispute).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_dispute_resolve(request, dispute_id):
    """Resolve an open dispute with a decision and rationale."""
    dispute = get_object_or_404(MarketplaceDispute, id=dispute_id)
    
    dispute.status = request.data.get('status', 'resolved')
    dispute.resolution_type = request.data.get('resolution_type', 'mutual_settlement')
    dispute.resolution = request.data.get('resolution', '')
    dispute.admin_notes = request.data.get('admin_notes', dispute.admin_notes)
    dispute.resolved_by = request.user
    dispute.save()

    ActivityLog.objects.create(
        user=request.user,
        action='update',
        model_type='dispute',
        model_id=dispute.id,
        description=f"[ADMIN API] Resolved dispute #{str(dispute.id)[:8]} ({dispute.resolution_type})"
    )

    return Response({
        'message': f"Dispute #{str(dispute.id)[:8]} resolved successfully.",
        'dispute': AdminMarketplaceDisputeSerializer(dispute).data
    })


# ---------------------------------------------------------------------------
# 7. Support Desk APIs
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_support_tickets(request):
    """List or filter support tickets."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    tickets = PlatformSupportTicket.objects.select_related('user', 'assigned_admin').all().order_by('-created_at')

    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    if category_filter != 'all':
        tickets = tickets.filter(category=category_filter)

    serializer = AdminPlatformSupportTicketSerializer(tickets, many=True)
    return Response({'count': tickets.count(), 'results': serializer.data})


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsMarketplaceAdmin])
def api_admin_support_respond(request, ticket_id):
    """Update support ticket status and add official response."""
    ticket = get_object_or_404(PlatformSupportTicket, id=ticket_id)

    ticket.status = request.data.get('status', 'resolved')
    ticket.admin_response = request.data.get('admin_response', '')
    ticket.assigned_admin = request.user
    ticket.save()

    ActivityLog.objects.create(
        user=request.user,
        action='update',
        model_type='support_ticket',
        model_id=ticket.id,
        description=f"[ADMIN API] Responded to support ticket #{str(ticket.id)[:8]} ({ticket.status})"
    )

    return Response({
        'message': f"Support ticket #{str(ticket.id)[:8]} updated.",
        'ticket': AdminPlatformSupportTicketSerializer(ticket).data
    })
