"""
Marketplace Admin Views — Platform Administration, Moderation, Dispute & Support Management (Stage 3)
"""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

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
from .forms_admin import (
    DisputeResolutionForm,
    DisputeCreateForm,
    ReportResolutionForm,
    SupportTicketResponseForm,
    UserModerationForm,
    ProjectModerationForm,
)
from .services_admin import AdminAnalyticsService, AdminExportService


# ---------------------------------------------------------------------------
# Authorization & Audit Logging Helpers
# ---------------------------------------------------------------------------

def is_admin_user(user):
    """Checks if user has Staff, Superuser, or explicit Admin role."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.role == 'admin')


def admin_required(view_func):
    """
    Decorator enforcing platform Admin authorization.
    Rejects Clients and Freelancers with 403 Forbidden.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not is_admin_user(request.user):
            messages.error(request, "403 Forbidden: Administrator access required.")
            return redirect('core:forbidden')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def log_admin_action(admin_user, action, model_type, model_id, description, request=None):
    """Records administrative actions to ActivityLog for compliance & audit."""
    ip_address = None
    user_agent = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    ActivityLog.objects.create(
        user=admin_user,
        action=action,
        model_type=model_type,
        model_id=model_id,
        description=f"[ADMIN ACTION] {description}",
        ip_address=ip_address,
        user_agent=user_agent
    )


# ---------------------------------------------------------------------------
# 1. Admin Master Dashboard
# ---------------------------------------------------------------------------

@admin_required
def admin_marketplace_dashboard(request):
    """Platform Master Dashboard showing comprehensive marketplace statistics and metrics."""
    kpi = AdminAnalyticsService.get_platform_kpis()
    trends = AdminAnalyticsService.get_monthly_trends()
    risk_analysis = AdminAnalyticsService.get_predictive_risk_analysis()

    recent_reports_client = ProjectReport.objects.select_related('reporter', 'reported_user', 'project')[:4]
    recent_reports_freelancer = FreelancerReport.objects.select_related('freelancer', 'reported_client', 'project')[:4]
    recent_disputes = MarketplaceDispute.objects.select_related('project', 'client', 'freelancer')[:5]
    recent_tickets = PlatformSupportTicket.objects.select_related('user')[:5]
    recent_projects = MarketplaceProject.objects.select_related('client', 'assigned_freelancer')[:5]
    recent_activities = ActivityLog.objects.select_related('user').filter(description__startswith='[ADMIN')[:8]

    context = {
        'kpi': kpi,
        'trends_json': json.dumps(trends),
        'risk_analysis': risk_analysis,
        'recent_reports_client': recent_reports_client,
        'recent_reports_freelancer': recent_reports_freelancer,
        'recent_disputes': recent_disputes,
        'recent_tickets': recent_tickets,
        'recent_projects': recent_projects,
        'recent_activities': recent_activities,
    }
    return render(request, 'admin_dashboard/marketplace/dashboard.html', context)


# ---------------------------------------------------------------------------
# 2. User Management (Clients & Freelancers)
# ---------------------------------------------------------------------------

@admin_required
def admin_users_list(request):
    """Browse and manage all registered platform users (Clients and Freelancers)."""
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    users_qs = User.objects.select_related('profile', 'client_profile', 'freelancer_profile').all().order_by('-date_joined')

    if role_filter == 'client':
        users_qs = users_qs.filter(profile__role='client')
    elif role_filter == 'freelancer':
        users_qs = users_qs.filter(profile__role='freelancer')
    elif role_filter == 'admin':
        users_qs = users_qs.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin'))

    if status_filter == 'active':
        users_qs = users_qs.filter(is_active=True, profile__is_suspended=False)
    elif status_filter == 'suspended':
        users_qs = users_qs.filter(profile__is_suspended=True)
    elif status_filter == 'inactive':
        users_qs = users_qs.filter(is_active=False)

    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(client_profile__full_name__icontains=search_query) |
            Q(client_profile__company_name__icontains=search_query) |
            Q(freelancer_profile__full_name__icontains=search_query)
        )

    context = {
        'users': users_qs,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': users_qs.count(),
    }
    return render(request, 'admin_dashboard/marketplace/users.html', context)


@admin_required
def admin_user_detail(request, user_id):
    """Detailed profile inspection, reports history, and moderation actions for a user."""
    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    client_p = getattr(target_user, 'client_profile', None)
    freelancer_p = getattr(target_user, 'freelancer_profile', None)

    # Activity history
    projects_posted = client_p.projects.all() if client_p else []
    projects_assigned = target_user.assigned_marketplace_projects.all()
    applications_submitted = target_user.project_applications.select_related('project')
    
    # Reports involving this user
    reports_filed = ProjectReport.objects.filter(reporter=client_p) if client_p else FreelancerReport.objects.filter(freelancer=freelancer_p) if freelancer_p else []
    reports_against = ProjectReport.objects.filter(reported_user=target_user) | (FreelancerReport.objects.filter(reported_client=client_p) if client_p else FreelancerReport.objects.none())

    context = {
        'target_user': target_user,
        'profile': profile,
        'client_profile': client_p,
        'freelancer_profile': freelancer_p,
        'projects_posted': projects_posted,
        'projects_assigned': projects_assigned,
        'applications_submitted': applications_submitted,
        'reports_filed': reports_filed,
        'reports_against': reports_against,
    }
    return render(request, 'admin_dashboard/marketplace/user_detail.html', context)


@admin_required
@require_POST
def admin_user_toggle_suspend(request, user_id):
    """Suspends or unsuspends a user account."""
    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    reason = request.POST.get('reason', '').strip() or "Administrative action"

    if profile.is_suspended:
        profile.is_suspended = False
        profile.save()
        log_admin_action(request.user, 'status_change', 'user', target_user.id, f"Unsuspended user {target_user.username}. Reason: {reason}", request)
        messages.success(request, f"User {target_user.username} has been unsuspended and reactivated.")
    else:
        profile.is_suspended = True
        profile.save()
        log_admin_action(request.user, 'status_change', 'user', target_user.id, f"Suspended user {target_user.username}. Reason: {reason}", request)
        messages.warning(request, f"User {target_user.username} has been SUSPENDED. Reason: {reason}")

    return redirect(request.META.get('HTTP_REFERER', 'marketplace_admin:users_list'))


@admin_required
@require_POST
def admin_user_toggle_active(request, user_id):
    """Enables or disables standard login active flag for a user."""
    target_user = get_object_or_404(User, id=user_id)
    reason = request.POST.get('reason', '').strip() or "Administrative action"

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "Activated" if target_user.is_active else "Deactivated"
    log_admin_action(request.user, 'status_change', 'user', target_user.id, f"{status_str} account {target_user.username}. Reason: {reason}", request)
    messages.success(request, f"Account {target_user.username} has been {status_str.lower()}.")

    return redirect(request.META.get('HTTP_REFERER', 'marketplace_admin:users_list'))


# ---------------------------------------------------------------------------
# 3. Project Management & Moderation
# ---------------------------------------------------------------------------

@admin_required
def admin_projects_list(request):
    """Platform project catalog with moderation tools and status filtering."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('q', '').strip()

    projects_qs = MarketplaceProject.objects.select_related('client', 'assigned_freelancer').prefetch_related('applications').order_by('-created_at')

    if status_filter != 'all':
        projects_qs = projects_qs.filter(status=status_filter)

    if category_filter != 'all':
        projects_qs = projects_qs.filter(category=category_filter)

    if search_query:
        projects_qs = projects_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__full_name__icontains=search_query) |
            Q(client__company_name__icontains=search_query) |
            Q(assigned_freelancer__username__icontains=search_query)
        )

    context = {
        'projects': projects_qs,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'total_count': projects_qs.count(),
        'categories': MarketplaceProject.CATEGORY_CHOICES,
        'statuses': MarketplaceProject.STATUS_CHOICES,
    }
    return render(request, 'admin_dashboard/marketplace/projects.html', context)


@admin_required
def admin_project_detail(request, project_id):
    """Full project inspection including applications, payment records, disputes, and moderation actions."""
    project = get_object_or_404(MarketplaceProject.objects.select_related('client', 'assigned_freelancer'), id=project_id)
    applications = project.applications.select_related('freelancer').order_by('-created_at')
    payment_record = getattr(project, 'payment_record', None)
    reports = project.reports.select_related('reporter', 'reported_user').all()
    freelancer_reports = project.freelancer_reports.select_related('freelancer', 'reported_client').all()
    disputes = project.disputes.select_related('opened_by', 'resolved_by').all()

    if request.method == 'POST':
        action = request.POST.get('moderation_action')
        new_status = request.POST.get('status')
        reason = request.POST.get('reason', '').strip() or "Administrative moderation"

        if action == 'close':
            project.status = 'closed'
            project.save()
            log_admin_action(request.user, 'status_change', 'project', project.id, f"Closed project '{project.title}'. Reason: {reason}", request)
            messages.warning(request, f"Project '{project.title}' has been closed by administrator.")
        elif action == 'reopen':
            project.status = 'open'
            project.save()
            log_admin_action(request.user, 'status_change', 'project', project.id, f"Reopened project '{project.title}'. Reason: {reason}", request)
            messages.success(request, f"Project '{project.title}' has been reopened.")
        elif new_status and new_status in dict(MarketplaceProject.STATUS_CHOICES):
            project.status = new_status
            project.save()
            log_admin_action(request.user, 'status_change', 'project', project.id, f"Updated project status to {new_status}. Reason: {reason}", request)
            messages.success(request, f"Project status updated to {project.get_status_display()}.")

        return redirect('marketplace_admin:project_detail', project_id=project.id)

    context = {
        'project': project,
        'applications': applications,
        'payment_record': payment_record,
        'reports': reports,
        'freelancer_reports': freelancer_reports,
        'disputes': disputes,
        'statuses': MarketplaceProject.STATUS_CHOICES,
    }
    return render(request, 'admin_dashboard/marketplace/project_detail.html', context)


# ---------------------------------------------------------------------------
# 4. Application Monitoring
# ---------------------------------------------------------------------------

@admin_required
def admin_applications_list(request):
    """Platform-wide proposal monitor to inspect bidding patterns and prevent spam."""
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    apps_qs = ProjectApplication.objects.select_related('project', 'project__client', 'freelancer').order_by('-created_at')

    if status_filter != 'all':
        apps_qs = apps_qs.filter(status=status_filter)

    if search_query:
        apps_qs = apps_qs.filter(
            Q(project__title__icontains=search_query) |
            Q(freelancer__username__icontains=search_query) |
            Q(freelancer__email__icontains=search_query) |
            Q(proposal__icontains=search_query)
        )

    context = {
        'applications': apps_qs,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': apps_qs.count(),
        'statuses': ProjectApplication.STATUS_CHOICES,
    }
    return render(request, 'admin_dashboard/marketplace/applications.html', context)


# ---------------------------------------------------------------------------
# 5. Report Management & Scam/Fraud Handling
# ---------------------------------------------------------------------------

@admin_required
def admin_reports_list(request):
    """Unified incident inbox for all Client and Freelancer reports."""
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')

    client_reports = ProjectReport.objects.select_related('reporter', 'reported_user', 'project').order_by('-created_at')
    freelancer_reports = FreelancerReport.objects.select_related('freelancer', 'reported_client', 'project').order_by('-created_at')

    if status_filter != 'all':
        client_reports = client_reports.filter(status=status_filter)
        freelancer_reports = freelancer_reports.filter(status=status_filter)

    context = {
        'client_reports': client_reports if type_filter in ['all', 'client'] else [],
        'freelancer_reports': freelancer_reports if type_filter in ['all', 'freelancer'] else [],
        'status_filter': status_filter,
        'type_filter': type_filter,
        'total_reports': (client_reports.count() if type_filter in ['all', 'client'] else 0) + (freelancer_reports.count() if type_filter in ['all', 'freelancer'] else 0),
    }
    return render(request, 'admin_dashboard/marketplace/reports.html', context)


@admin_required
def admin_report_detail(request, report_type, report_id):
    """Investigation console for a specific report (client or freelancer filed)."""
    if report_type == 'client':
        report = get_object_or_404(ProjectReport.objects.select_related('reporter', 'reported_user', 'project'), id=report_id)
        reported_user_obj = report.reported_user
    else:
        report = get_object_or_404(FreelancerReport.objects.select_related('freelancer', 'reported_client', 'project'), id=report_id)
        reported_user_obj = report.reported_client.user if report.reported_client else None

    if request.method == 'POST':
        action = request.POST.get('action_taken')
        new_status = request.POST.get('status', 'resolved')
        admin_notes = request.POST.get('admin_notes', '').strip()

        report.status = new_status
        report.admin_notes = admin_notes
        report.save()

        # Execute moderation consequences if selected
        if action == 'account_suspended' and reported_user_obj:
            p, _ = UserProfile.objects.get_or_create(user=reported_user_obj)
            p.is_suspended = True
            p.save()
            log_admin_action(request.user, 'status_change', 'user', reported_user_obj.id, f"Suspended account due to report #{str(report.id)[:8]}", request)
            messages.warning(request, f"Report resolved: Account for {reported_user_obj.username} has been SUSPENDED.")
        elif action == 'project_closed' and report.project:
            report.project.status = 'closed'
            report.project.save()
            log_admin_action(request.user, 'status_change', 'project', report.project.id, f"Closed project due to report #{str(report.id)[:8]}", request)
            messages.warning(request, f"Report resolved: Project '{report.project.title}' has been closed.")
        elif action == 'escalated_to_dispute' and report.project:
            # Create formal dispute
            client_p = report.project.client
            freelancer_p = getattr(report.project.assigned_freelancer, 'freelancer_profile', None) if report.project.assigned_freelancer else None
            dispute = MarketplaceDispute.objects.create(
                project=report.project,
                opened_by=request.user,
                client=client_p,
                freelancer=freelancer_p,
                category='scam' if 'scam' in report.reason else 'delivery',
                title=f"Dispute escalated from Report #{str(report.id)[:8]}",
                description=report.description,
                admin_notes=f"Escalated from {report_type} report. {admin_notes}",
                status='open'
            )
            log_admin_action(request.user, 'create', 'dispute', dispute.id, f"Created dispute #{str(dispute.id)[:8]} from report", request)
            messages.info(request, f"Report escalated to formal Dispute #{str(dispute.id)[:8]}.")
            return redirect('marketplace_admin:dispute_detail', dispute_id=dispute.id)
        else:
            messages.success(request, f"Report #{str(report.id)[:8]} status updated to {report.get_status_display()}.")

        log_admin_action(request.user, 'update', 'report', report.id, f"Resolved report #{str(report.id)[:8]} with status {new_status}. Action: {action}", request)
        return redirect('marketplace_admin:reports_list')

    context = {
        'report': report,
        'report_type': report_type,
        'reported_user_obj': reported_user_obj,
    }
    return render(request, 'admin_dashboard/marketplace/report_detail.html', context)


# ---------------------------------------------------------------------------
# 6. Dispute Resolution System
# ---------------------------------------------------------------------------

@admin_required
def admin_disputes_list(request):
    """Dedicated arbitration dashboard for active and closed disputes."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    disputes_qs = MarketplaceDispute.objects.select_related('project', 'client', 'freelancer', 'opened_by').order_by('-created_at')

    if status_filter != 'all':
        disputes_qs = disputes_qs.filter(status=status_filter)

    if category_filter != 'all':
        disputes_qs = disputes_qs.filter(category=category_filter)

    context = {
        'disputes': disputes_qs,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'total_count': disputes_qs.count(),
        'statuses': MarketplaceDispute.STATUS_CHOICES,
        'categories': MarketplaceDispute.CATEGORY_CHOICES,
    }
    return render(request, 'admin_dashboard/marketplace/disputes.html', context)


@admin_required
def admin_dispute_detail(request, dispute_id):
    """Full arbitration console to review evidence, payment status, and submit a binding decision."""
    dispute = get_object_or_404(MarketplaceDispute.objects.select_related('project', 'client', 'freelancer', 'opened_by', 'resolved_by'), id=dispute_id)
    payment_record = getattr(dispute.project, 'payment_record', None)

    if request.method == 'POST':
        form = DisputeResolutionForm(request.POST, instance=dispute)
        if form.is_valid():
            resolved_dispute = form.save(commit=False)
            resolved_dispute.resolved_by = request.user
            resolved_dispute.save()

            log_admin_action(
                request.user, 'update', 'dispute', resolved_dispute.id,
                f"Resolved dispute #{str(resolved_dispute.id)[:8]} as {resolved_dispute.get_resolution_type_display()}",
                request
            )
            messages.success(request, f"Dispute #{str(resolved_dispute.id)[:8]} decision recorded successfully.")
            return redirect('marketplace_admin:disputes_list')
    else:
        form = DisputeResolutionForm(instance=dispute)

    context = {
        'dispute': dispute,
        'payment_record': payment_record,
        'form': form,
    }
    return render(request, 'admin_dashboard/marketplace/dispute_detail.html', context)


@admin_required
def admin_dispute_create(request):
    """Admin tool to open a formal dispute for any project."""
    if request.method == 'POST':
        form = DisputeCreateForm(request.POST)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.opened_by = request.user
            dispute.client = dispute.project.client
            dispute.freelancer = getattr(dispute.project.assigned_freelancer, 'freelancer_profile', None) if dispute.project.assigned_freelancer else None
            dispute.save()

            log_admin_action(request.user, 'create', 'dispute', dispute.id, f"Opened dispute #{str(dispute.id)[:8]} for project '{dispute.project.title}'", request)
            messages.success(request, f"Dispute #{str(dispute.id)[:8]} created.")
            return redirect('marketplace_admin:dispute_detail', dispute_id=dispute.id)
    else:
        form = DisputeCreateForm()

    return render(request, 'admin_dashboard/marketplace/dispute_form.html', {'form': form})


# ---------------------------------------------------------------------------
# 7. Support Ticket Desk
# ---------------------------------------------------------------------------

@admin_required
def admin_support_list(request):
    """Platform support desk queue for user tickets."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    tickets_qs = PlatformSupportTicket.objects.select_related('user', 'assigned_admin').order_by('-created_at')

    if status_filter != 'all':
        tickets_qs = tickets_qs.filter(status=status_filter)

    if category_filter != 'all':
        tickets_qs = tickets_qs.filter(category=category_filter)

    context = {
        'tickets': tickets_qs,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'total_count': tickets_qs.count(),
        'statuses': PlatformSupportTicket.STATUS_CHOICES,
        'categories': PlatformSupportTicket.CATEGORY_CHOICES,
    }
    return render(request, 'admin_dashboard/marketplace/support.html', context)


@admin_required
def admin_support_detail(request, ticket_id):
    """View and respond to a support ticket."""
    ticket = get_object_or_404(PlatformSupportTicket.objects.select_related('user', 'assigned_admin'), id=ticket_id)

    if request.method == 'POST':
        form = SupportTicketResponseForm(request.POST, instance=ticket)
        if form.is_valid():
            updated_ticket = form.save(commit=False)
            updated_ticket.assigned_admin = request.user
            updated_ticket.save()

            log_admin_action(request.user, 'update', 'support_ticket', updated_ticket.id, f"Updated support ticket #{str(updated_ticket.id)[:8]} ({updated_ticket.status})", request)
            messages.success(request, f"Response saved for Support Ticket #{str(updated_ticket.id)[:8]}.")
            return redirect('marketplace_admin:support_list')
    else:
        form = SupportTicketResponseForm(instance=ticket)

    context = {
        'ticket': ticket,
        'form': form,
    }
    return render(request, 'admin_dashboard/marketplace/support_detail.html', context)


# ---------------------------------------------------------------------------
# 8. Platform Analytics & Risk Insights
# ---------------------------------------------------------------------------

@admin_required
def admin_analytics_view(request):
    """Deep platform business intelligence and predictive project risk engine."""
    kpi = AdminAnalyticsService.get_platform_kpis()
    trends = AdminAnalyticsService.get_monthly_trends()
    risk_analysis = AdminAnalyticsService.get_predictive_risk_analysis()

    # Category breakdown
    categories_qs = MarketplaceProject.objects.values('category').annotate(count=Count('id'), total_budget=Sum('budget')).order_by('-count')
    category_labels = [dict(MarketplaceProject.CATEGORY_CHOICES).get(c['category'], c['category']) for c in categories_qs]
    category_counts = [c['count'] for c in categories_qs]

    # Status distribution
    status_counts = [
        MarketplaceProject.objects.filter(status='open').count(),
        MarketplaceProject.objects.filter(status='applications_received').count(),
        MarketplaceProject.objects.filter(status='assigned').count(),
        MarketplaceProject.objects.filter(status='in_progress').count(),
        MarketplaceProject.objects.filter(status='completed').count(),
        MarketplaceProject.objects.filter(status='closed').count(),
    ]

    context = {
        'kpi': kpi,
        'trends_json': json.dumps(trends),
        'risk_analysis': risk_analysis,
        'category_labels_json': json.dumps(category_labels),
        'category_counts_json': json.dumps(category_counts),
        'status_counts_json': json.dumps(status_counts),
        'categories_summary': categories_qs,
    }
    return render(request, 'admin_dashboard/marketplace/analytics.html', context)


# ---------------------------------------------------------------------------
# 9. Multi-Format Administrative Reports & Exports
# ---------------------------------------------------------------------------

@admin_required
def admin_exports_hub(request):
    """Download hub for PDF, Excel, and CSV platform reports."""
    return render(request, 'admin_dashboard/marketplace/exports.html')


@admin_required
def admin_export_data(request, export_type, export_format):
    """
    Exports platform datasets in PDF, XLSX, or CSV.
    export_type: 'summary' | 'projects' | 'users' | 'applications' | 'disputes'
    export_format: 'pdf' | 'xlsx' | 'csv'
    """
    timestamp = timezone.now().strftime('%Y%m%d_%H%M')
    filename = f"marketplace_{export_type}_{timestamp}"

    if export_type == 'projects':
        headers = ['Project ID', 'Title', 'Category', 'Client', 'Assigned Freelancer', 'Budget ($)', 'Status', 'Progress (%)', 'Created Date']
        projects = MarketplaceProject.objects.select_related('client', 'assigned_freelancer').all()
        rows = [
            [
                str(p.id)[:8],
                p.title,
                p.get_category_display(),
                p.client.display_name,
                p.assigned_freelancer.username if p.assigned_freelancer else 'None',
                float(p.budget or 0),
                p.get_status_display(),
                p.progress,
                p.created_at.strftime('%Y-%m-%d')
            ]
            for p in projects
        ]
        title = "Platform Marketplace Projects Report"

    elif export_type == 'users':
        headers = ['User ID', 'Username', 'Email', 'Role', 'Status', 'Projects / Apps', 'Joined Date']
        users = User.objects.select_related('profile', 'client_profile', 'freelancer_profile').all().order_by('-date_joined')
        rows = []
        for u in users:
            p = getattr(u, 'profile', None)
            role = p.role if p else 'user'
            status_str = "Suspended" if (p and p.is_suspended) else ("Active" if u.is_active else "Inactive")
            activity_count = u.client_profile.projects.count() if hasattr(u, 'client_profile') else u.project_applications.count()
            rows.append([u.id, u.username, u.email, role.upper(), status_str, activity_count, u.date_joined.strftime('%Y-%m-%d')])
        title = "Platform Users & Account Status Report"

    elif export_type == 'applications':
        headers = ['App ID', 'Project Title', 'Client', 'Freelancer', 'Proposed Price ($)', 'Status', 'Submitted Date']
        apps = ProjectApplication.objects.select_related('project', 'project__client', 'freelancer').all()
        rows = [
            [
                str(a.id)[:8],
                a.project.title,
                a.project.client.display_name,
                a.freelancer.username,
                float(a.proposed_price or 0),
                a.get_status_display(),
                a.created_at.strftime('%Y-%m-%d')
            ]
            for a in apps
        ]
        title = "Platform Proposals & Applications Report"

    elif export_type == 'disputes':
        headers = ['Dispute ID', 'Project', 'Client', 'Freelancer', 'Category', 'Status', 'Resolution Type', 'Opened Date']
        disputes = MarketplaceDispute.objects.select_related('project', 'client', 'freelancer').all()
        rows = [
            [
                str(d.id)[:8],
                d.project.title,
                d.client.display_name,
                d.freelancer.display_name if d.freelancer else 'Unassigned',
                d.get_category_display(),
                d.get_status_display(),
                d.get_resolution_type_display(),
                d.created_at.strftime('%Y-%m-%d')
            ]
            for d in disputes
        ]
        title = "Platform Disputes & Arbitration Summary"

    else:  # summary
        kpi = AdminAnalyticsService.get_platform_kpis()
        headers = ['Platform Metric', 'Metric Value']
        rows = [
            ['Total Registered Clients', kpi['total_clients']],
            ['Total Registered Freelancers', kpi['total_freelancers']],
            ['Total Marketplace Projects', kpi['total_projects']],
            ['Open Projects Seeking Freelancers', kpi['open_projects']],
            ['Active Projects In Progress', kpi['active_projects']],
            ['Completed Projects', kpi['completed_projects']],
            ['Total Submitted Applications', kpi['total_applications']],
            ['Application to Hire Conversion', f"{kpi['hire_conversion_rate']}%"],
            ['Total Project Budget Volume', f"${kpi['total_budget_volume']:,.2f}"],
            ['Total Paid Milestones', f"${kpi['total_paid_volume']:,.2f}"],
            ['Pending Milestone Payments', f"${kpi['total_pending_payment']:,.2f}"],
            ['Open Support & Reports', kpi['open_reports']],
            ['Active Disputes', kpi['open_disputes']],
            ['Suspended Users', kpi['suspended_users']],
        ]
        title = "Marketplace Executive Platform Summary"

    if export_format == 'csv':
        return AdminExportService.export_csv(filename, headers, rows)
    elif export_format == 'xlsx':
        return AdminExportService.export_excel(filename, export_type.title(), headers, rows)
    else:  # pdf
        return AdminExportService.export_pdf(filename, title, headers, rows)
