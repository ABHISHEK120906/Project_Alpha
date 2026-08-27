"""
Marketplace API views — /api/v1/client/

All endpoints require:
  - SessionAuthentication
  - IsAuthenticated
  - Client role (profile.role == 'client')
  - Object-level ownership enforcement
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum

from core.models import UserProfile
from .models import (
    ClientProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
)
from .serializers import (
    ClientProfileSerializer,
    MarketplaceProjectSerializer,
    ProjectApplicationSerializer,
    ProjectPaymentRecordSerializer,
    ProjectReportSerializer,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_client_profile(request):
    """
    Returns ClientProfile or None.
    Also returns an error Response if user is not a client.
    """
    try:
        up = request.user.profile
    except Exception:
        up, _ = UserProfile.objects.get_or_create(user=request.user)

    if up.role != 'client':
        return None, Response(
            {'error': 'Forbidden: Client role required.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        cp = request.user.client_profile
    except ClientProfile.DoesNotExist:
        return None, Response(
            {'error': 'Client profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    return cp, None


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_dashboard_stats(request):
    """Returns dashboard statistics for the logged-in Client."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    projects = MarketplaceProject.objects.filter(client=cp)
    payment_records = ProjectPaymentRecord.objects.filter(project__client=cp)

    data = {
        'total_projects': projects.count(),
        'open_projects': projects.filter(status='open').count(),
        'projects_with_applications': projects.filter(
            applications__isnull=False
        ).distinct().count(),
        'active_projects': projects.filter(status__in=['assigned', 'in_progress']).count(),
        'completed_projects': projects.filter(status='completed').count(),
        'pending_applications': ProjectApplication.objects.filter(
            project__client=cp, status='pending'
        ).count(),
        'total_budget': float(
            payment_records.aggregate(t=Sum('total_budget'))['t'] or 0
        ),
        'total_paid': float(
            payment_records.aggregate(t=Sum('amount_paid'))['t'] or 0
        ),
    }
    return Response(data)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_profile(request):
    """GET or update the Client's own profile."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    if request.method == 'GET':
        serializer = ClientProfileSerializer(cp, context={'request': request})
        return Response(serializer.data)

    partial = request.method == 'PATCH'
    serializer = ClientProfileSerializer(
        cp, data=request.data, partial=partial, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_projects(request):
    """GET: list client's projects. POST: create new project."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    if request.method == 'GET':
        status_filter = request.query_params.get('status', '')
        projects = MarketplaceProject.objects.filter(client=cp)
        if status_filter:
            projects = projects.filter(status=status_filter)
        projects = projects.order_by('-created_at')
        serializer = MarketplaceProjectSerializer(projects, many=True)
        return Response(serializer.data)

    # POST — create project
    serializer = MarketplaceProjectSerializer(data=request.data)
    if serializer.is_valid():
        project = serializer.save(client=cp)
        ProjectPaymentRecord.objects.create(
            project=project,
            total_budget=project.budget or 0,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_project_detail(request, pk):
    """GET/PUT/PATCH/DELETE for a single client project."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    project = get_object_or_404(MarketplaceProject, pk=pk, client=cp)

    if request.method == 'GET':
        serializer = MarketplaceProjectSerializer(project)
        return Response(serializer.data)

    if request.method == 'DELETE':
        # Soft-close instead of hard delete if project has applications
        if project.applications.exists():
            project.status = 'closed'
            project.save()
            return Response({'status': 'closed'})
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == 'PATCH'
    serializer = MarketplaceProjectSerializer(project, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_project_applications(request, pk):
    """List applications for a client-owned project."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    project = get_object_or_404(MarketplaceProject, pk=pk, client=cp)
    applications = ProjectApplication.objects.filter(
        project=project
    ).select_related('freelancer').order_by('-created_at')

    serializer = ProjectApplicationSerializer(applications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_accept_application(request, app_pk):
    """Accept a freelancer application."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    application = get_object_or_404(
        ProjectApplication, pk=app_pk, project__client=cp
    )
    project = application.project

    if project.assigned_freelancer:
        return Response(
            {'error': 'A freelancer is already assigned.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if application.status != 'pending':
        return Response(
            {'error': f'Application is already {application.status}.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    application.status = 'accepted'
    application.save()

    ProjectApplication.objects.filter(
        project=project, status='pending'
    ).exclude(pk=app_pk).update(status='rejected')

    project.assigned_freelancer = application.freelancer
    project.status = 'assigned'
    project.save()

    return Response({'status': 'accepted', 'project_status': project.status})


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_reject_application(request, app_pk):
    """Reject a freelancer application."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    application = get_object_or_404(
        ProjectApplication, pk=app_pk, project__client=cp
    )

    if application.status == 'pending':
        application.status = 'rejected'
        application.save()
        return Response({'status': 'rejected'})

    return Response(
        {'error': f'Application is already {application.status}.'},
        status=status.HTTP_400_BAD_REQUEST
    )


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_payments(request):
    """Get all payment records for the client."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    records = ProjectPaymentRecord.objects.filter(
        project__client=cp
    ).select_related('project').order_by('-created_at')

    serializer = ProjectPaymentRecordSerializer(records, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_client_reports(request):
    """List or create support reports."""
    cp, err = _get_client_profile(request)
    if err:
        return err

    if request.method == 'GET':
        reports = ProjectReport.objects.filter(
            reporter=cp
        ).order_by('-created_at')
        serializer = ProjectReportSerializer(reports, many=True)
        return Response(serializer.data)

    serializer = ProjectReportSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(reporter=cp)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
