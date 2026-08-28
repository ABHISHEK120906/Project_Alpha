"""
Marketplace views — Stage 2: Freelancer Side

All views enforce:
  1. Authentication (login_required)
  2. Freelancer role check (must be role='freelancer')
  3. Object ownership & Data Isolation (freelancers only see their own applications, assigned projects, payments, and reports)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, Http404
from decimal import Decimal

from core.models import UserProfile
from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
    FreelancerVerification,
    is_freelancer_verified,
)
from .forms import (
    FreelancerRegistrationForm,
    FreelancerProfileForm,
    FreelancerEmailForm,
    ProjectApplicationForm,
    ProjectProgressUpdateForm,
    FreelancerReportForm,
    FreelancerEmailVerifyForm,
    FreelancerPhoneVerifyForm,
    FreelancerIdentityVerifyForm,
    FreelancerPANVerifyForm,
    FreelancerPaymentVerifyForm,
)



# ---------------------------------------------------------------------------
# Role Helpers & Decorator
# ---------------------------------------------------------------------------

def _get_freelancer_profile_or_403(request):
    """
    Returns the FreelancerProfile for the authenticated user,
    or redirects to forbidden if not a freelancer role.
    Returns (freelancer_profile, redirect_response_or_None).
    """
    try:
        up = request.user.profile
    except Exception:
        up, _ = UserProfile.objects.get_or_create(user=request.user)

    if up.role not in ('freelancer', 'user'):
        # Client or Admin trying to access Freelancer pages
        return None, redirect('core:forbidden')

    try:
        fp = request.user.freelancer_profile
    except FreelancerProfile.DoesNotExist:
        # Auto-create a minimal FreelancerProfile if not existing
        fp = FreelancerProfile.objects.create(
            user=request.user,
            full_name=request.user.get_full_name() or request.user.username,
            skills=up.skills or '',
            experience=up.experience or '',
            bio=up.bio or '',
            portfolio_website=up.portfolio_website or None,
            github_url=up.social_github or None,
            linkedin_url=up.social_linkedin or None,
        )
    return fp, None


def _require_freelancer(view_func):
    """Decorator: login_required + freelancer role check."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        freelancer_profile, err = _get_freelancer_profile_or_403(request)
        if err:
            return err
        return view_func(request, *args, freelancer_profile=freelancer_profile, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def freelancer_register(request):
    """Freelancer-specific registration page."""
    if request.user.is_authenticated:
        try:
            if request.user.profile.role == 'freelancer':
                return redirect('freelancer:dashboard')
            elif request.user.profile.role == 'client':
                return redirect('marketplace:client_dashboard')
        except Exception:
            pass
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = FreelancerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user, freelancer_profile = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to FreelanceHub, {freelancer_profile.full_name}! "
                "Your freelancer profile is ready."
            )
            return redirect('freelancer:dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = FreelancerRegistrationForm()

    return render(request, 'marketplace/freelancer/auth/freelancer_register.html', {'form': form})


# ---------------------------------------------------------------------------
# Freelancer Dashboard
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_dashboard(request, freelancer_profile=None):
    """Freelancer marketplace dashboard."""
    user = request.user

    # Stats
    open_projects_count = MarketplaceProject.objects.filter(
        status__in=['open', 'applications_received']
    ).count()

    my_applications = ProjectApplication.objects.filter(freelancer=user)
    total_applications = my_applications.count()
    pending_applications = my_applications.filter(status='pending').count()
    accepted_applications = my_applications.filter(status='accepted').count()
    rejected_applications = my_applications.filter(status='rejected').count()

    # Assigned projects
    assigned_projects = MarketplaceProject.objects.filter(assigned_freelancer=user)
    active_projects_count = assigned_projects.filter(status__in=['assigned', 'in_progress']).count()
    completed_projects_count = assigned_projects.filter(status='completed').count()

    # Payment summary from assigned projects
    payment_records = ProjectPaymentRecord.objects.filter(project__assigned_freelancer=user)
    total_earned = payment_records.filter(status='paid').aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending_payment = payment_records.exclude(status='paid').aggregate(
        t=Sum('total_budget') - Sum('amount_paid')
    )['t'] or 0

    # Recent applications (last 5)
    recent_applications = my_applications.select_related('project', 'project__client').order_by('-created_at')[:5]

    # Active projects (last 5)
    recent_active_projects = assigned_projects.filter(
        status__in=['assigned', 'in_progress']
    ).select_related('client').order_by('-updated_at')[:5]

    # Recommended / Featured Open Projects (last 4)
    recommended_projects = MarketplaceProject.objects.filter(
        status__in=['open', 'applications_received']
    ).exclude(
        applications__freelancer=user
    ).select_related('client').order_by('-created_at')[:4]

    # Freelancer Verification Status
    verification, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    profile_completion, missing_fields = verification.calculate_profile_completion()
    verification.update_verification_status()
    verification.save()

    context = {
        'freelancer_profile': freelancer_profile,
        'verification': verification,
        'profile_completion': profile_completion,
        'missing_fields': missing_fields,
        'is_verified': verification.is_fully_verified,
        'open_projects_count': open_projects_count,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'active_projects_count': active_projects_count,
        'completed_projects_count': completed_projects_count,
        'total_earned': total_earned,
        'total_pending_payment': max(0, total_pending_payment),
        'recent_applications': recent_applications,
        'recent_active_projects': recent_active_projects,
        'recommended_projects': recommended_projects,
    }
    return render(request, 'marketplace/freelancer/dashboard.html', context)



# ---------------------------------------------------------------------------
# Freelancer Profile
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_profile_view(request, freelancer_profile=None):
    """View freelancer profile."""
    # Applications & Completed projects counts
    applications_count = ProjectApplication.objects.filter(freelancer=request.user).count()
    completed_projects = MarketplaceProject.objects.filter(
        assigned_freelancer=request.user,
        status='completed'
    ).count()

    context = {
        'freelancer_profile': freelancer_profile,
        'user': request.user,
        'applications_count': applications_count,
        'completed_projects_count': completed_projects,
    }
    return render(request, 'marketplace/freelancer/profile/view.html', context)


@_require_freelancer
def freelancer_profile_edit(request, freelancer_profile=None):
    """Edit freelancer profile."""
    if request.method == 'POST':
        profile_form = FreelancerProfileForm(
            request.POST, request.FILES, instance=freelancer_profile
        )
        email_form = FreelancerEmailForm(request.POST, instance=request.user)

        if profile_form.is_valid() and email_form.is_valid():
            fp = profile_form.save()
            email_form.save()

            # Sync with UserProfile
            try:
                up = request.user.profile
                up.skills = fp.skills
                up.experience = fp.experience
                up.bio = fp.bio
                up.phone_number = fp.phone
                up.portfolio_website = fp.portfolio_website
                up.social_github = fp.github_url
                up.social_linkedin = fp.linkedin_url
                up.save()
            except Exception:
                pass

            messages.success(request, "Your freelancer profile has been updated.")
            return redirect('freelancer:profile_view')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        profile_form = FreelancerProfileForm(instance=freelancer_profile)
        email_form = FreelancerEmailForm(instance=request.user)

    context = {
        'freelancer_profile': freelancer_profile,
        'profile_form': profile_form,
        'email_form': email_form,
    }
    return render(request, 'marketplace/freelancer/profile/edit.html', context)


# ---------------------------------------------------------------------------
# Find Projects (Browse Open Projects)
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_find_projects(request, freelancer_profile=None):
    """Browse OPEN projects with search, category, skill, budget, duration, and sort filters."""
    projects = MarketplaceProject.objects.filter(
        status__in=['open', 'applications_received']
    ).select_related('client')

    search_q = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    skill_filter = request.GET.get('skill', '').strip()
    budget_min = request.GET.get('budget_min', '').strip()
    budget_max = request.GET.get('budget_max', '').strip()
    duration_filter = request.GET.get('duration', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    if search_q:
        projects = projects.filter(
            Q(title__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(required_skills__icontains=search_q) |
            Q(client__company_name__icontains=search_q)
        )

    if category_filter:
        projects = projects.filter(category=category_filter)

    if skill_filter:
        projects = projects.filter(required_skills__icontains=skill_filter)

    if budget_min:
        try:
            projects = projects.filter(budget__gte=Decimal(budget_min))
        except Exception:
            pass

    if budget_max:
        try:
            projects = projects.filter(budget__lte=Decimal(budget_max))
        except Exception:
            pass

    if duration_filter:
        projects = projects.filter(expected_duration=duration_filter)

    if sort_by == 'oldest':
        projects = projects.order_by('created_at')
    elif sort_by == 'budget_high':
        projects = projects.order_by('-budget')
    elif sort_by == 'budget_low':
        projects = projects.order_by('budget')
    elif sort_by == 'deadline':
        projects = projects.order_by('deadline')
    else:  # 'newest' default
        projects = projects.order_by('-created_at')

    # Get set of project IDs the current user has already applied to
    applied_project_ids = set(
        ProjectApplication.objects.filter(freelancer=request.user).values_list('project_id', flat=True)
    )

    context = {
        'freelancer_profile': freelancer_profile,
        'projects': projects,
        'applied_project_ids': applied_project_ids,
        'search_q': search_q,
        'category_filter': category_filter,
        'skill_filter': skill_filter,
        'budget_min': budget_min,
        'budget_max': budget_max,
        'duration_filter': duration_filter,
        'sort_by': sort_by,
        'category_choices': MarketplaceProject.CATEGORY_CHOICES,
        'duration_choices': MarketplaceProject.DURATION_CHOICES,
        'total_found': projects.count(),
    }
    return render(request, 'marketplace/freelancer/projects/find.html', context)


# ---------------------------------------------------------------------------
# Project Details (Public / Freelancer View)
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_project_detail(request, pk, freelancer_profile=None):
    """View project details — sanitized client public info only."""
    project = get_object_or_404(MarketplaceProject, pk=pk)

    # Check verification status
    is_verified = is_freelancer_verified(request.user)

    # Check if user has applied
    user_application = ProjectApplication.objects.filter(
        project=project,
        freelancer=request.user
    ).first()

    # Check if this freelancer is assigned to this project
    is_assigned = (project.assigned_freelancer == request.user)

    # Cannot apply if closed/assigned to someone else, or already applied
    can_apply = (
        project.status in ('open', 'applications_received') and
        user_application is None and
        project.assigned_freelancer is None
    )

    context = {
        'freelancer_profile': freelancer_profile,
        'project': project,
        'user_application': user_application,
        'is_assigned': is_assigned,
        'can_apply': can_apply,
        'is_verified': is_verified,
    }
    return render(request, 'marketplace/freelancer/projects/detail.html', context)


# ---------------------------------------------------------------------------
# Apply to Project
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_project_apply(request, pk, freelancer_profile=None):
    """Submit proposal / application to an open project."""
    project = get_object_or_404(MarketplaceProject, pk=pk)

    # 0. Enforce Freelancer Verification Check
    if not is_freelancer_verified(request.user):
        messages.error(
            request,
            "You must complete Freelancer verification before applying to projects. "
            "Please complete your verification in the Verification Center."
        )
        return redirect('freelancer:verification_center')

    # 1. Prevent applying to closed or completed projects
    if project.status not in ('open', 'applications_received'):
        messages.error(request, "This project is not currently accepting applications.")
        return redirect('freelancer:project_detail', pk=pk)

    # 2. Prevent applying if already assigned
    if project.assigned_freelancer is not None:
        messages.error(request, "A freelancer has already been assigned to this project.")
        return redirect('freelancer:project_detail', pk=pk)

    # 3. Prevent duplicate applications
    existing_app = ProjectApplication.objects.filter(
        project=project,
        freelancer=request.user
    ).first()
    if existing_app:
        messages.info(request, f"You have already submitted an application (Status: {existing_app.get_status_display()}).")
        return redirect('freelancer:my_applications')

    # 4. Prevent applying to own client project if user owns the client profile
    if hasattr(request.user, 'client_profile') and project.client == request.user.client_profile:
        messages.error(request, "You cannot apply to a project you posted as a client.")
        return redirect('freelancer:project_detail', pk=pk)


    if request.method == 'POST':
        form = ProjectApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.project = project
            application.freelancer = request.user
            application.status = 'pending'
            application.save()

            # Update project status to 'applications_received' if it was 'open'
            if project.status == 'open':
                project.status = 'applications_received'
                project.save()

            messages.success(
                request,
                f"Your application for \"{project.title}\" has been submitted successfully!"
            )
            return redirect('freelancer:my_applications')
        else:
            messages.error(request, "Please review the application form errors.")
    else:
        # Pre-fill proposed price with project budget if available
        initial = {}
        if project.budget:
            initial['proposed_price'] = project.budget
        form = ProjectApplicationForm(initial=initial)

    context = {
        'freelancer_profile': freelancer_profile,
        'project': project,
        'form': form,
    }
    return render(request, 'marketplace/freelancer/projects/apply.html', context)


# ---------------------------------------------------------------------------
# My Applications
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_my_applications(request, freelancer_profile=None):
    """List all applications submitted by this freelancer."""
    status_filter = request.GET.get('status', '').strip()

    applications = ProjectApplication.objects.filter(
        freelancer=request.user
    ).select_related('project', 'project__client')

    if status_filter:
        applications = applications.filter(status=status_filter)

    applications = applications.order_by('-created_at')

    context = {
        'freelancer_profile': freelancer_profile,
        'applications': applications,
        'status_filter': status_filter,
        'status_choices': ProjectApplication.STATUS_CHOICES,
    }
    return render(request, 'marketplace/freelancer/applications/list.html', context)


@_require_freelancer
@require_POST
def freelancer_application_withdraw(request, app_pk, freelancer_profile=None):
    """Withdraw a pending application."""
    application = get_object_or_404(
        ProjectApplication,
        pk=app_pk,
        freelancer=request.user
    )

    if application.status == 'pending':
        application.status = 'withdrawn'
        application.save()
        messages.success(request, f"Application for \"{application.project.title}\" has been withdrawn.")
    else:
        messages.warning(request, f"Cannot withdraw an application that is {application.status}.")

    return redirect('freelancer:my_applications')


# ---------------------------------------------------------------------------
# My Active Projects
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_my_projects(request, freelancer_profile=None):
    """List all projects assigned to this freelancer."""
    status_filter = request.GET.get('status', '').strip()

    projects = MarketplaceProject.objects.filter(
        assigned_freelancer=request.user
    ).select_related('client', 'payment_record')

    if status_filter == 'active':
        projects = projects.filter(status__in=['assigned', 'in_progress'])
    elif status_filter == 'completed':
        projects = projects.filter(status='completed')
    elif status_filter:
        projects = projects.filter(status=status_filter)

    projects = projects.order_by('-updated_at')

    context = {
        'freelancer_profile': freelancer_profile,
        'projects': projects,
        'status_filter': status_filter,
    }
    return render(request, 'marketplace/freelancer/projects/my_projects.html', context)


# ---------------------------------------------------------------------------
# Project Workspace & Progress Update (Assigned Project)
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_workspace(request, pk, freelancer_profile=None):
    """Project Workspace for assigned freelancer — includes allowed Client contact details."""
    project = get_object_or_404(
        MarketplaceProject,
        pk=pk,
        assigned_freelancer=request.user
    )

    # Get the accepted application
    accepted_application = ProjectApplication.objects.filter(
        project=project,
        freelancer=request.user,
        status='accepted'
    ).first()

    # Payment record
    payment_record = getattr(project, 'payment_record', None)

    # Progress form
    progress_form = ProjectProgressUpdateForm(initial={'progress': project.progress})

    # Allowed Client Contact details
    client = project.client

    context = {
        'freelancer_profile': freelancer_profile,
        'project': project,
        'accepted_application': accepted_application,
        'payment_record': payment_record,
        'client': client,
        'progress_form': progress_form,
    }
    return render(request, 'marketplace/freelancer/projects/workspace.html', context)


@_require_freelancer
@require_POST
def freelancer_update_progress(request, pk, freelancer_profile=None):
    """Freelancer updates project progress percentage."""
    project = get_object_or_404(
        MarketplaceProject,
        pk=pk,
        assigned_freelancer=request.user
    )

    if project.status == 'completed':
        messages.info(request, "This project is marked as Completed and cannot be updated.")
        return redirect('freelancer:workspace', pk=pk)

    form = ProjectProgressUpdateForm(request.POST)
    if form.is_valid():
        new_progress = form.cleaned_data['progress']
        project.progress = new_progress

        # Auto-shift from 'assigned' to 'in_progress' if progress > 0
        if project.status == 'assigned' and new_progress > 0:
            project.status = 'in_progress'

        project.save()
        messages.success(request, f"Project progress updated to {new_progress}%.")
    else:
        messages.error(request, "Please provide a valid progress value between 0 and 100.")

    return redirect('freelancer:workspace', pk=pk)


# ---------------------------------------------------------------------------
# Payments (Freelancer View)
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_payments(request, freelancer_profile=None):
    """Payment ledger for projects assigned to this freelancer."""
    payment_records = ProjectPaymentRecord.objects.filter(
        project__assigned_freelancer=request.user
    ).select_related('project', 'project__client').order_by('-created_at')

    total_budget = payment_records.aggregate(t=Sum('total_budget'))['t'] or 0
    total_paid = payment_records.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending = float(total_budget) - float(total_paid)

    context = {
        'freelancer_profile': freelancer_profile,
        'payment_records': payment_records,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_pending': max(0, total_pending),
    }
    return render(request, 'marketplace/freelancer/payments/list.html', context)


# ---------------------------------------------------------------------------
# Support / Reports (Freelancer Side)
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_support_list(request, freelancer_profile=None):
    """List support reports filed by this freelancer."""
    reports = FreelancerReport.objects.filter(
        freelancer=freelancer_profile
    ).select_related('project', 'reported_client').order_by('-created_at')

    context = {
        'freelancer_profile': freelancer_profile,
        'reports': reports,
    }
    return render(request, 'marketplace/freelancer/support/list.html', context)


@_require_freelancer
def freelancer_support_create(request, freelancer_profile=None):
    """Create a new support report against a client or project."""
    if request.method == 'POST':
        form = FreelancerReportForm(request.POST, freelancer_profile=freelancer_profile)
        if form.is_valid():
            report = form.save(commit=False)
            report.freelancer = freelancer_profile
            report.save()
            messages.success(
                request,
                "Your support report has been submitted. Our team will investigate shortly."
            )
            return redirect('freelancer:support_list')
        else:
            messages.error(request, "Please fix the errors in the report form.")
    else:
        form = FreelancerReportForm(freelancer_profile=freelancer_profile)

    context = {
        'freelancer_profile': freelancer_profile,
        'form': form,
    }
    return render(request, 'marketplace/freelancer/support/create.html', context)


# ---------------------------------------------------------------------------
# Freelancer Verification Center & Multi-Step Verification Handlers
# ---------------------------------------------------------------------------

@_require_freelancer
def freelancer_verification_center(request, freelancer_profile=None):
    """
    Dedicated Verification Center dashboard.
    Displays cards for:
      1. Email Verification
      2. Mobile / Phone Verification
      3. Identity Verification
      4. PAN Verification
      5. Payment Account Verification (Razorpay / Bank KYC simulation)
      6. Professional Profile Verification
      7. Admin Review & Approval
    """
    import uuid as py_uuid
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    ver.update_verification_status()
    ver.save()

    score, missing_fields = ver.calculate_profile_completion()

    email_form = FreelancerEmailVerifyForm()
    phone_form = FreelancerPhoneVerifyForm(initial={'phone_number': freelancer_profile.phone or request.user.profile.phone_number or ''})
    identity_form = FreelancerIdentityVerifyForm(initial={'legal_name': freelancer_profile.full_name})
    pan_form = FreelancerPANVerifyForm()
    payment_form = FreelancerPaymentVerifyForm(initial={'account_holder_name': freelancer_profile.full_name})

    context = {
        'freelancer_profile': freelancer_profile,
        'verification': ver,
        'profile_completion': score,
        'missing_fields': missing_fields,
        'is_verified': ver.is_fully_verified,
        'email_form': email_form,
        'phone_form': phone_form,
        'identity_form': identity_form,
        'pan_form': pan_form,
        'payment_form': payment_form,
    }
    return render(request, 'marketplace/freelancer/verification/center.html', context)


@_require_freelancer
@require_POST
def freelancer_verify_email(request, freelancer_profile=None):
    """Verify email via OTP code submission."""
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    form = FreelancerEmailVerifyForm(request.POST)
    if form.is_valid():
        ver.email_verified = True
        ver.email_verified_at = timezone.now()
        ver.update_verification_status()
        ver.save()
        messages.success(request, "Email verified successfully! ✓")
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_verify_phone(request, freelancer_profile=None):
    """Verify mobile phone number via SMS OTP simulation."""
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    form = FreelancerPhoneVerifyForm(request.POST)
    if form.is_valid():
        phone = form.cleaned_data['phone_number']
        ver.phone_verified = True
        ver.phone_number = phone
        ver.phone_verified_at = timezone.now()
        if not freelancer_profile.phone:
            freelancer_profile.phone = phone
            freelancer_profile.save(update_fields=['phone'])
        ver.update_verification_status()
        ver.save()
        messages.success(request, "Mobile phone number verified successfully! ✓")
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_verify_identity(request, freelancer_profile=None):
    """Submit identity document for verification (secure simulation)."""
    import uuid as py_uuid
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    form = FreelancerIdentityVerifyForm(request.POST)
    if form.is_valid():
        id_type = form.cleaned_data['identity_type']
        legal_name = form.cleaned_data['legal_name']
        ver.identity_type = id_type
        ver.identity_holder_name = legal_name
        ver.identity_reference_id = f"ID-SEC-{py_uuid.uuid4().hex[:8].upper()}"
        ver.identity_status = 'verified'
        ver.identity_verified_at = timezone.now()
        ver.update_verification_status()
        ver.save()
        messages.success(request, f"Identity verification ({id_type}) completed and verified! ✓")
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_verify_pan(request, freelancer_profile=None):
    """Submit and verify PAN number (stored only in masked format XXXXXX1234)."""
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    form = FreelancerPANVerifyForm(request.POST)
    if form.is_valid():
        pan = form.cleaned_data['pan_number']
        masked_pan = f"XXXXXX{pan[-4:]}"
        ver.pan_masked = masked_pan
        ver.pan_status = 'verified'
        ver.pan_verified_at = timezone.now()
        ver.update_verification_status()
        ver.save()
        messages.success(request, f"PAN {masked_pan} verified successfully! ✓")
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_verify_payment(request, freelancer_profile=None):
    """Submit payment account / Razorpay payout onboarding KYC verification simulation."""
    import uuid as py_uuid
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    form = FreelancerPaymentVerifyForm(request.POST)
    if form.is_valid():
        provider = form.cleaned_data['account_provider']
        provider_name = dict(FreelancerPaymentVerifyForm.PROVIDER_CHOICES).get(provider, 'Razorpay Verified')
        ver.payment_account_type = provider_name
        ver.payment_account_reference = f"acc_rzp_mock_{py_uuid.uuid4().hex[:6]}"
        ver.payment_status = 'verified'
        ver.payment_verified_at = timezone.now()
        ver.update_verification_status()
        ver.save()
        messages.success(request, f"Payment account ({provider_name}) linked and verified! ✓")
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_submit_for_admin_review(request, freelancer_profile=None):
    """Submit completed verification package for admin review & approval."""
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    ver.update_verification_status()

    if (
        ver.email_verified and
        ver.phone_verified and
        ver.identity_status == 'verified' and
        ver.pan_status == 'verified' and
        ver.payment_status == 'verified' and
        ver.profile_status == 'complete'
    ):
        ver.admin_review_status = 'pending'
        ver.final_verification_status = 'pending_admin_review'
        ver.save()
        messages.success(
            request,
            "Your verification has been submitted for review. An administrator will examine your credentials."
        )
    else:
        messages.warning(
            request,
            "Your verification requires attention. Please complete all missing verification steps before submitting."
        )
    return redirect('freelancer:verification_center')


@_require_freelancer
@require_POST
def freelancer_simulate_admin_approval(request, freelancer_profile=None):
    """
    Simulation helper to approve pending verification in development/testing.
    Enforces that all 6 prerequisites are met before granting approved status.
    """
    ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=freelancer_profile)
    ver.update_verification_status()

    if (
        ver.email_verified and
        ver.phone_verified and
        ver.identity_status == 'verified' and
        ver.pan_status == 'verified' and
        ver.payment_status == 'verified' and
        ver.profile_status == 'complete'
    ):
        ver.admin_review_status = 'approved'
        ver.admin_reviewed_at = timezone.now()
        ver.final_verification_status = 'verified'
        ver.verified_at = timezone.now()
        ver.save()
        messages.success(
            request,
            "Your Freelancer account has been verified. You can now apply for projects."
        )
    else:
        messages.error(
            request,
            "Cannot approve verification: required verification steps are still incomplete."
        )
    return redirect('freelancer:verification_center')

