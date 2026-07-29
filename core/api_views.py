"""
FreelanceTrack — Internal API Views (/api/v1/)
Strictly authenticated, session-protected JSON endpoints for frontend interactions.
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Client, Project, Payment, Task, Note, ActivityLog
from .serializers import (
    ClientSerializer, ProjectSerializer, PaymentSerializer,
    TaskSerializer, ActivityLogSerializer
)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_health(request):
    """Minimal system health check endpoint."""
    return Response({"status": "ok", "service": "FreelanceTrack API Proxy", "version": "v1.0"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_dashboard_stats(request):
    """
    Returns aggregated dashboard stats and chart metrics for the current user.
    All data is scoped strictly to request.user and filtered via DRF serializers.
    """
    user = request.user
    today = timezone.now().date()

    # Base Querysets
    user_projects = Project.objects.filter(user=user)
    user_payments = Payment.objects.filter(user=user)
    user_clients = Client.objects.filter(user=user)
    user_tasks = Task.objects.filter(user=user)

    # Core Aggregations
    total_revenue = user_payments.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
    pending_amount = user_payments.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0
    active_projects_count = user_projects.filter(status='in_progress').count()
    total_clients_count = user_clients.filter(status='active').count()
    pending_tasks_count = user_tasks.filter(Q(status='pending') | Q(status='in_progress')).count()

    # Monthly Earnings (Last 6 Months)
    months_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i * 30))
        m_total = user_payments.filter(
            status='paid',
            paid_date__year=month_date.year,
            paid_date__month=month_date.month
        ).aggregate(t=Sum('amount'))['t'] or 0
        months_labels.append(month_date.strftime('%b'))
        monthly_data.append(float(m_total))

    # Project Status Breakdown
    status_counts = user_projects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    status_distribution = {
        'in_progress': status_dict.get('in_progress', 0),
        'completed': status_dict.get('completed', 0),
        'on_hold': status_dict.get('on_hold', 0),
        'planning': status_dict.get('planning', 0),
    }

    # Recent Projects (Serialized)
    recent_projects_qs = user_projects.select_related('client').order_by('-created_at')[:5]
    recent_projects_serialized = ProjectSerializer(recent_projects_qs, many=True).data

    payload = {
        "total_revenue": float(total_revenue),
        "pending_amount": float(pending_amount),
        "active_projects_count": active_projects_count,
        "total_clients_count": total_clients_count,
        "pending_tasks_count": pending_tasks_count,
        "monthly_chart": {
            "labels": months_labels,
            "data": monthly_data
        },
        "status_chart": status_distribution,
        "recent_projects": recent_projects_serialized
    }

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_activity_log(request):
    """
    Returns recent activity log entries for request.user.
    Strips IP addresses and sensitive metadata.
    """
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    serializer = ActivityLogSerializer(activities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_toggle_task(request, pk):
    """
    Safely toggle task completion status for request.user.
    Input validated and output serialized.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if task.status == 'completed':
        task.status = 'pending'
    else:
        task.status = 'completed'

    task.save()
    serializer = TaskSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_update_project_status(request, pk):
    """
    Validates and updates project status.
    Prevents unauthorized state transitions.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    new_status = request.data.get('status', '').strip()

    valid_statuses = [choice[0] for choice in Project.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return Response(
            {"error": "Invalid status value", "allowed": valid_statuses},
            status=status.HTTP_400_BAD_REQUEST
        )

    project.status = new_status
    if new_status == 'completed':
        project.progress = 100
    project.save()

    serializer = ProjectSerializer(project)
    return Response(serializer.data, status=status.HTTP_200_OK)
