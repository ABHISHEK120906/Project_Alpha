"""
Freelancer REST API views — /freelancer/api/v1/

All endpoints require:
  - IsAuthenticated
  - Freelancer role (role in ['freelancer', 'user'] and not 'client')
  - Strict data isolation (freelancer can only access their own data)
  - No exposure of sensitive credentials
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q
from decimal import Decimal

from core.models import UserProfile
from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    FreelancerReport,
)
from .serializers import (
    FreelancerProfileSerializer,
    FreelancerProjectPublicSerializer,
    FreelancerProjectWorkspaceSerializer,
    FreelancerApplicationSerializer,
    FreelancerPaymentSerializer,
    FreelancerReportSerializer,
)


def _get_freelancer_profile(request):
    """Returns (freelancer_profile, error_response_or_None)."""
    try:
        up = request.user.profile
    except Exception:
        up, _ = UserProfile.objects.get_or_create(user=request.user)

    if up.role == 'client':
        return None, Response(
            {'error': 'Forbidden: Freelancer role required.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        fp = request.user.freelancer_profile
    except FreelancerProfile.DoesNotExist:
        fp = FreelancerProfile.objects.create(
            user=request.user,
            full_name=request.user.get_full_name() or request.user.username,
            skills=up.skills or '',
            experience=up.experience or '',
            bio=up.bio or '',
        )
    return fp, None


# ---------------------------------------------------------------------------
# Dashboard Stats API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_dashboard_stats(request):
    """GET summary metrics for the freelancer dashboard."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    user = request.user
    open_projects = MarketplaceProject.objects.filter(status__in=['open', 'applications_received']).count()
    my_applications = ProjectApplication.objects.filter(freelancer=user)
    total_apps = my_applications.count()
    pending_apps = my_applications.filter(status='pending').count()
    accepted_apps = my_applications.filter(status='accepted').count()

    assigned_projects = MarketplaceProject.objects.filter(assigned_freelancer=user)
    active_projects = assigned_projects.filter(status__in=['assigned', 'in_progress']).count()
    completed_projects = assigned_projects.filter(status='completed').count()

    payment_records = ProjectPaymentRecord.objects.filter(project__assigned_freelancer=user)
    total_earned = payment_records.filter(status='paid').aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending_pay = payment_records.exclude(status='paid').aggregate(
        t=Sum('total_budget') - Sum('amount_paid')
    )['t'] or 0

    return Response({
        'open_projects_count': open_projects,
        'total_applications': total_apps,
        'pending_applications': pending_apps,
        'accepted_applications': accepted_apps,
        'active_projects_count': active_projects,
        'completed_projects_count': completed_projects,
        'total_earned': str(total_earned),
        'total_pending_payment': str(max(0, total_pending_pay)),
    })


# ---------------------------------------------------------------------------
# Profile API
# ---------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_profile(request):
    """GET or update current freelancer profile."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    if request.method == 'GET':
        serializer = FreelancerProfileSerializer(fp, context={'request': request})
        return Response(serializer.data)

    partial = (request.method == 'PATCH')
    serializer = FreelancerProfileSerializer(
        fp, data=request.data, partial=partial, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Find Projects API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_find_projects(request):
    """Browse open projects with search, filter, and sorting."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    projects = MarketplaceProject.objects.filter(
        status__in=['open', 'applications_received']
    ).select_related('client')

    search_q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    skill = request.GET.get('skill', '').strip()
    budget_min = request.GET.get('budget_min', '').strip()
    budget_max = request.GET.get('budget_max', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    if search_q:
        projects = projects.filter(
            Q(title__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(required_skills__icontains=search_q)
        )
    if category:
        projects = projects.filter(category=category)
    if skill:
        projects = projects.filter(required_skills__icontains=skill)
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

    if sort_by == 'oldest':
        projects = projects.order_by('created_at')
    elif sort_by == 'budget_high':
        projects = projects.order_by('-budget')
    elif sort_by == 'budget_low':
        projects = projects.order_by('budget')
    elif sort_by == 'deadline':
        projects = projects.order_by('deadline')
    else:
        projects = projects.order_by('-created_at')

    serializer = FreelancerProjectPublicSerializer(
        projects, many=True, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_project_detail(request, pk):
    """View details of an open project."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    project = get_object_or_404(MarketplaceProject, pk=pk)
    serializer = FreelancerProjectPublicSerializer(project, context={'request': request})
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Apply to Project API
# ---------------------------------------------------------------------------

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_apply(request, pk):
    """Submit proposal to an open project."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    project = get_object_or_404(MarketplaceProject, pk=pk)

    if project.status not in ('open', 'applications_received'):
        return Response(
            {'error': 'This project is not accepting applications.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if project.assigned_freelancer is not None:
        return Response(
            {'error': 'A freelancer is already assigned to this project.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ProjectApplication.objects.filter(project=project, freelancer=request.user).exists():
        return Response(
            {'error': 'You have already applied to this project.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    proposal = request.data.get('proposal', '').strip()
    if not proposal:
        return Response({'error': 'Proposal text is required.'}, status=status.HTTP_400_BAD_REQUEST)

    proposed_price = request.data.get('proposed_price')
    estimated_duration = request.data.get('estimated_duration', '')

    app = ProjectApplication.objects.create(
        project=project,
        freelancer=request.user,
        proposal=proposal,
        proposed_price=proposed_price or project.budget,
        estimated_duration=estimated_duration,
        status='pending',
    )

    if project.status == 'open':
        project.status = 'applications_received'
        project.save()

    serializer = FreelancerApplicationSerializer(app, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Applications API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_my_applications(request):
    """List current freelancer's applications."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    applications = ProjectApplication.objects.filter(
        freelancer=request.user
    ).select_related('project', 'project__client').order_by('-created_at')

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        applications = applications.filter(status=status_filter)

    serializer = FreelancerApplicationSerializer(
        applications, many=True, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_withdraw_application(request, app_pk):
    """Withdraw a pending application."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    app = get_object_or_404(ProjectApplication, pk=app_pk, freelancer=request.user)
    if app.status != 'pending':
        return Response(
            {'error': f'Cannot withdraw application in {app.status} state.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    app.status = 'withdrawn'
    app.save()
    return Response({'message': 'Application withdrawn successfully.'})


# ---------------------------------------------------------------------------
# Assigned Projects & Workspace API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_my_projects(request):
    """List assigned active & completed projects."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    projects = MarketplaceProject.objects.filter(
        assigned_freelancer=request.user
    ).select_related('client', 'payment_record').order_by('-updated_at')

    serializer = FreelancerProjectWorkspaceSerializer(
        projects, many=True, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_workspace(request, pk):
    """GET workspace details for an assigned project (includes allowed client contact info)."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    project = get_object_or_404(
        MarketplaceProject, pk=pk, assigned_freelancer=request.user
    )
    serializer = FreelancerProjectWorkspaceSerializer(project, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_update_progress(request, pk):
    """Update progress percentage for assigned project."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    project = get_object_or_404(
        MarketplaceProject, pk=pk, assigned_freelancer=request.user
    )

    if project.status == 'completed':
        return Response(
            {'error': 'Completed projects cannot be modified.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        progress_val = int(request.data.get('progress', 0))
    except (ValueError, TypeError):
        return Response(
            {'error': 'Progress must be an integer between 0 and 100.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (0 <= progress_val <= 100):
        return Response(
            {'error': 'Progress must be between 0 and 100.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    project.progress = progress_val
    if project.status == 'assigned' and progress_val > 0:
        project.status = 'in_progress'
    project.save()

    return Response({
        'message': f'Progress updated to {progress_val}%.',
        'progress': project.progress,
        'status': project.status,
    })


# ---------------------------------------------------------------------------
# Payments API
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_payments(request):
    """GET payment records for assigned projects."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    records = ProjectPaymentRecord.objects.filter(
        project__assigned_freelancer=request.user
    ).select_related('project', 'project__client').order_by('-created_at')

    serializer = FreelancerPaymentSerializer(records, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Support / Reports API
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_freelancer_reports(request):
    """GET or POST support tickets for the freelancer."""
    fp, err = _get_freelancer_profile(request)
    if err:
        return err

    if request.method == 'GET':
        reports = FreelancerReport.objects.filter(freelancer=fp).order_by('-created_at')
        serializer = FreelancerReportSerializer(reports, many=True)
        return Response(serializer.data)

    serializer = FreelancerReportSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(freelancer=fp)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
