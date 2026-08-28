"""
Marketplace views — Stage 1: Client Side

All views enforce:
  1. Authentication (login_required)
  2. Client role check (must be role='client')
  3. Object ownership (client can only access their own data)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import UserProfile
from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,

    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerVerification,
)

from .forms import (
    ClientRegistrationForm,
    ClientProfileForm,
    ClientEmailForm,
    MarketplaceProjectForm,
    ProjectReportForm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_profile_or_403(request):
    """
    Returns the ClientProfile for the authenticated user,
    or redirects to forbidden if not a client role.
    Returns (client_profile, redirect_response_or_None).
    """
    try:
        up = request.user.profile
    except Exception:
        up, _ = UserProfile.objects.get_or_create(user=request.user)

    if up.role != 'client':
        return None, redirect('core:forbidden')

    try:
        cp = request.user.client_profile
    except ClientProfile.DoesNotExist:
        # Edge case: UserProfile says client but no ClientProfile exists
        # Auto-create a minimal one
        cp = ClientProfile.objects.create(
            user=request.user,
            full_name=request.user.get_full_name() or request.user.username,
        )
    return cp, None


def _require_client(view_func):
    """Decorator: login_required + client role check."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        client_profile, err = _get_client_profile_or_403(request)
        if err:
            return err
        return view_func(request, *args, client_profile=client_profile, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def client_register(request):
    """Client-specific registration page."""
    if request.user.is_authenticated:
        try:
            if request.user.profile.role == 'client':
                return redirect('marketplace:client_dashboard')
        except Exception:
            pass
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user, client_profile = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to the marketplace, {client_profile.full_name}! "
                "Your client account is ready."
            )
            return redirect('marketplace:client_dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ClientRegistrationForm()

    return render(request, 'marketplace/auth/client_register.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@_require_client
def client_dashboard(request, client_profile=None):
    """Client marketplace dashboard."""
    projects = MarketplaceProject.objects.filter(client=client_profile)

    # Stats
    total_projects = projects.count()
    open_projects = projects.filter(status='open').count()
    projects_with_applications = projects.filter(
        applications__isnull=False
    ).distinct().count()
    active_projects = projects.filter(status__in=['assigned', 'in_progress']).count()
    completed_projects = projects.filter(status='completed').count()
    pending_applications = ProjectApplication.objects.filter(
        project__client=client_profile,
        status='pending'
    ).count()

    # Payment summary
    payment_records = ProjectPaymentRecord.objects.filter(
        project__client=client_profile
    )
    total_budget = payment_records.aggregate(t=Sum('total_budget'))['t'] or 0
    total_paid = payment_records.aggregate(t=Sum('amount_paid'))['t'] or 0

    # Recent projects (last 5)
    recent_projects = projects.annotate(
        app_count=Count('applications')
    ).order_by('-created_at')[:5]

    # Recent applications
    recent_applications = ProjectApplication.objects.filter(
        project__client=client_profile,
        status='pending'
    ).select_related('project', 'freelancer').order_by('-created_at')[:5]

    context = {
        'client_profile': client_profile,
        'total_projects': total_projects,
        'open_projects': open_projects,
        'projects_with_applications': projects_with_applications,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'pending_applications': pending_applications,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_pending': float(total_budget) - float(total_paid),
        'recent_projects': recent_projects,
        'recent_applications': recent_applications,
    }
    return render(request, 'marketplace/dashboard.html', context)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@_require_client
def client_profile_view(request, client_profile=None):
    """View client profile."""
    context = {
        'client_profile': client_profile,
        'user': request.user,
    }
    return render(request, 'marketplace/profile/view.html', context)


@_require_client
def client_profile_edit(request, client_profile=None):
    """Edit client profile."""
    if request.method == 'POST':
        profile_form = ClientProfileForm(
            request.POST, request.FILES, instance=client_profile
        )
        email_form = ClientEmailForm(request.POST, instance=request.user)

        if profile_form.is_valid() and email_form.is_valid():
            profile_form.save()
            email_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('marketplace:client_profile_view')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        profile_form = ClientProfileForm(instance=client_profile)
        email_form = ClientEmailForm(instance=request.user)

    context = {
        'client_profile': client_profile,
        'profile_form': profile_form,
        'email_form': email_form,
    }
    return render(request, 'marketplace/profile/edit.html', context)


# ---------------------------------------------------------------------------
# Projects — Post / List / Detail / Edit / Close
# ---------------------------------------------------------------------------

@_require_client
def project_post(request, client_profile=None):
    """Client posts a new project."""
    if request.method == 'POST':
        form = MarketplaceProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = client_profile
            project.save()
            # Create payment record linked to project
            ProjectPaymentRecord.objects.create(
                project=project,
                total_budget=project.budget or 0,
                amount_paid=0,
                status='pending',
            )
            messages.success(
                request,
                f"Project \"{project.title}\" posted successfully!"
            )
            return redirect('marketplace:project_detail', pk=project.pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MarketplaceProjectForm()

    context = {
        'client_profile': client_profile,
        'form': form,
        'page_title': 'Post a New Project',
    }
    return render(request, 'marketplace/projects/post.html', context)


@_require_client
def project_list(request, client_profile=None):
    """List all projects posted by this client."""
    status_filter = request.GET.get('status', '')
    search_q = request.GET.get('q', '').strip()

    projects = MarketplaceProject.objects.filter(
        client=client_profile
    ).annotate(app_count=Count('applications'))

    if status_filter:
        projects = projects.filter(status=status_filter)
    if search_q:
        projects = projects.filter(
            Q(title__icontains=search_q) | Q(description__icontains=search_q)
        )

    projects = projects.order_by('-created_at')

    context = {
        'client_profile': client_profile,
        'projects': projects,
        'status_filter': status_filter,
        'search_q': search_q,
        'status_choices': MarketplaceProject.STATUS_CHOICES,
    }
    return render(request, 'marketplace/projects/list.html', context)


@_require_client
def project_detail(request, pk, client_profile=None):
    """Detail view of a single project — ownership enforced."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)

    applications = ProjectApplication.objects.filter(
        project=project
    ).select_related('freelancer').order_by('-created_at')

    # Payment record
    payment_record = getattr(project, 'payment_record', None)

    context = {
        'client_profile': client_profile,
        'project': project,
        'applications': applications,
        'payment_record': payment_record,
    }
    return render(request, 'marketplace/projects/detail.html', context)


@_require_client
def project_edit(request, pk, client_profile=None):
    """Edit an existing project."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)

    # Cannot edit an assigned/completed project's core fields
    if project.status in ('completed', 'closed'):
        messages.warning(
            request,
            f"Project \"{project.title}\" is {project.status} and cannot be edited."
        )
        return redirect('marketplace:project_detail', pk=pk)

    if request.method == 'POST':
        form = MarketplaceProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            updated = form.save()
            # Sync payment record budget
            try:
                pr = updated.payment_record
                pr.total_budget = updated.budget or 0
                pr.save()
            except ProjectPaymentRecord.DoesNotExist:
                ProjectPaymentRecord.objects.create(
                    project=updated,
                    total_budget=updated.budget or 0,
                )
            messages.success(request, f"Project \"{updated.title}\" updated.")
            return redirect('marketplace:project_detail', pk=pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MarketplaceProjectForm(instance=project)

    context = {
        'client_profile': client_profile,
        'project': project,
        'form': form,
        'page_title': 'Edit Project',
    }
    return render(request, 'marketplace/projects/edit.html', context)


@_require_client
@require_POST
def project_close(request, pk, client_profile=None):
    """Close a project (sets status to 'closed')."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)
    if project.status not in ('completed', 'closed'):
        project.status = 'closed'
        project.save()
        messages.success(request, f"Project \"{project.title}\" has been closed.")
    else:
        messages.info(request, f"Project is already {project.status}.")
    return redirect('marketplace:project_detail', pk=pk)


@_require_client
@require_POST
def project_reopen(request, pk, client_profile=None):
    """Reopen a closed project back to 'open'."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)
    if project.status == 'closed':
        project.status = 'open'
        project.save()
        messages.success(request, f"Project \"{project.title}\" is now open again.")
    else:
        messages.info(request, "Only closed projects can be reopened.")
    return redirect('marketplace:project_detail', pk=pk)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@_require_client
def project_applications(request, pk, client_profile=None):
    """View all applications for a project with client-safe verification badges and profiles."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)

    status_filter = request.GET.get('status', '')
    applications = ProjectApplication.objects.filter(
        project=project
    ).select_related('freelancer')

    if status_filter:
        applications = applications.filter(status=status_filter)

    applications = applications.order_by('-created_at')

    # Attach safe verification summaries and profile details for client review
    for app in applications:
        try:
            fp = app.freelancer.freelancer_profile
            app.freelancer_profile_obj = fp
            ver = getattr(fp, 'verification', None)
            if ver:
                app.verification_summary = ver.get_safe_summary()
            else:
                app.verification_summary = {
                    'is_verified': False,
                    'badge_text': 'Not Verified',
                    'status': 'not_verified',
                    'status_display': 'Not Verified',
                    'email_verified': False,
                    'phone_verified': False,
                    'identity_verified': False,
                    'pan_verified': False,
                    'payment_verified': False,
                    'profile_verified': False,
                    'admin_approved': False,
                    'verified_at': None,
                    'steps_completed': 0,
                    'total_steps': 7,
                }
        except Exception:
            app.freelancer_profile_obj = None
            app.verification_summary = {
                'is_verified': False,
                'badge_text': 'Not Verified',
                'status': 'not_verified',
                'status_display': 'Not Verified',
                'email_verified': False,
                'phone_verified': False,
                'identity_verified': False,
                'pan_verified': False,
                'payment_verified': False,
                'profile_verified': False,
                'admin_approved': False,
                'verified_at': None,
                'steps_completed': 0,
                'total_steps': 7,
            }

    context = {
        'client_profile': client_profile,
        'project': project,
        'applications': applications,
        'status_filter': status_filter,
        'status_choices': ProjectApplication.STATUS_CHOICES,
    }
    return render(request, 'marketplace/projects/applications.html', context)


@_require_client
def client_freelancer_verification_safe_api(request, freelancer_id, client_profile=None):
    """
    Client-safe API returning verification status of a freelancer.
    Guarantees that private KYC, full PAN, or financial credentials are never leaked.
    """
    freelancer_user = get_object_or_404(User, pk=freelancer_id)
    try:
        fp = freelancer_user.freelancer_profile
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=fp)
        ver.update_verification_status()
        summary = ver.get_safe_summary()
    except Exception:
        summary = {
            'is_verified': False,
            'badge_text': 'Not Verified',
            'status': 'not_verified',
            'status_display': 'Not Verified',
            'email_verified': False,
            'phone_verified': False,
            'identity_verified': False,
            'pan_verified': False,
            'payment_verified': False,
            'profile_verified': False,
            'admin_approved': False,
            'verified_at': None,
            'steps_completed': 0,
            'total_steps': 7,
        }
    return JsonResponse(summary)



@_require_client
@require_POST
def application_accept(request, app_pk, client_profile=None):
    """
    Accept a freelancer application:
    1. Verify client owns the project.
    2. Change application status → accepted.
    3. Reject all other pending applications for the same project.
    4. Assign freelancer to the project.
    5. Update project status to 'assigned'.
    """
    application = get_object_or_404(
        ProjectApplication,
        pk=app_pk,
        project__client=client_profile
    )
    project = application.project

    if project.assigned_freelancer is not None:
        messages.warning(
            request,
            "A freelancer is already assigned to this project."
        )
        return redirect('marketplace:project_applications', pk=project.pk)

    if application.status != 'pending':
        messages.warning(request, f"This application is already {application.status}.")
        return redirect('marketplace:project_applications', pk=project.pk)

    # Accept this application
    application.status = 'accepted'
    application.save()

    # Reject all other pending applications
    ProjectApplication.objects.filter(
        project=project,
        status='pending'
    ).exclude(pk=app_pk).update(status='rejected')

    # Assign freelancer & update project status
    project.assigned_freelancer = application.freelancer
    project.status = 'assigned'
    project.save()

    messages.success(
        request,
        f"You have accepted {application.freelancer.get_full_name() or application.freelancer.username} "
        f"for \"{project.title}\". The project is now Assigned."
    )
    return redirect('marketplace:project_workspace', pk=project.pk)


@_require_client
@require_POST
def application_reject(request, app_pk, client_profile=None):
    """Reject a freelancer application."""
    application = get_object_or_404(
        ProjectApplication,
        pk=app_pk,
        project__client=client_profile
    )

    if application.status == 'pending':
        application.status = 'rejected'
        application.save()
        messages.success(
            request,
            f"Application from {application.freelancer.username} has been rejected."
        )
    else:
        messages.info(request, f"Application is already {application.status}.")

    return redirect('marketplace:project_applications', pk=application.project.pk)


# ---------------------------------------------------------------------------
# Active Project Workspace
# ---------------------------------------------------------------------------

@_require_client
def project_workspace(request, pk, client_profile=None):
    """Active project workspace — shown after freelancer is assigned."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)

    if project.status not in ('assigned', 'in_progress', 'completed'):
        messages.info(
            request,
            "The project workspace is only available once a freelancer has been assigned."
        )
        return redirect('marketplace:project_detail', pk=pk)

    # Get the accepted application
    accepted_application = ProjectApplication.objects.filter(
        project=project,
        status='accepted'
    ).select_related('freelancer').first()

    # Payment record
    payment_record = getattr(project, 'payment_record', None)

    # Freelancer profile info (Stage 2 will add FreelancerProfile)
    freelancer = project.assigned_freelancer
    freelancer_profile = None
    if freelancer:
        try:
            freelancer_profile = freelancer.freelancer_profile
        except Exception:
            pass

    context = {
        'client_profile': client_profile,
        'project': project,
        'accepted_application': accepted_application,
        'freelancer': freelancer,
        'freelancer_profile': freelancer_profile,
        'payment_record': payment_record,
    }
    return render(request, 'marketplace/projects/workspace.html', context)


@_require_client
@require_POST
def project_mark_in_progress(request, pk, client_profile=None):
    """Move assigned project to in_progress."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)
    if project.status == 'assigned':
        project.status = 'in_progress'
        project.save()
        messages.success(request, "Project marked as In Progress.")
    return redirect('marketplace:project_workspace', pk=pk)


@_require_client
@require_POST
def project_mark_completed(request, pk, client_profile=None):
    """Mark project as completed."""
    project = get_object_or_404(MarketplaceProject, pk=pk, client=client_profile)
    if project.status in ('assigned', 'in_progress'):
        project.status = 'completed'
        project.progress = 100
        project.save()
        # Update payment record
        try:
            pr = project.payment_record
            pr.status = 'paid'
            pr.amount_paid = pr.total_budget
            pr.save()
        except ProjectPaymentRecord.DoesNotExist:
            pass
        messages.success(request, "Project marked as Completed. Great work!")
    return redirect('marketplace:project_workspace', pk=pk)


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@_require_client
def client_payments(request, client_profile=None):
    """Payment overview for all of the client's projects."""
    payment_records = ProjectPaymentRecord.objects.filter(
        project__client=client_profile
    ).select_related('project').order_by('-created_at')

    total_budget = payment_records.aggregate(t=Sum('total_budget'))['t'] or 0
    total_paid = payment_records.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending = float(total_budget) - float(total_paid)

    context = {
        'client_profile': client_profile,
        'payment_records': payment_records,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    return render(request, 'marketplace/payments/list.html', context)


# ---------------------------------------------------------------------------
# Support / Reports
# ---------------------------------------------------------------------------

@_require_client
def client_support_list(request, client_profile=None):
    """List all support reports filed by this client."""
    reports = ProjectReport.objects.filter(
        reporter=client_profile
    ).order_by('-created_at')

    context = {
        'client_profile': client_profile,
        'reports': reports,
    }
    return render(request, 'marketplace/support/list.html', context)


@_require_client
def client_support_create(request, client_profile=None):
    """Create a new support report."""
    if request.method == 'POST':
        form = ProjectReportForm(request.POST, client_profile=client_profile)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = client_profile
            report.save()
            messages.success(
                request,
                "Your report has been submitted. Our team will review it shortly."
            )
            return redirect('marketplace:client_support_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProjectReportForm(client_profile=client_profile)

    context = {
        'client_profile': client_profile,
        'form': form,
    }
    return render(request, 'marketplace/support/create.html', context)
