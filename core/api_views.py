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
    return Response({"status": "ok", "service": "FreelanceTrack API Proxy", "version": "v1.0"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_dashboard_stats(request):
    user = request.user
    today = timezone.now().date()

    user_projects = Project.objects.filter(user=user)
    user_payments = Payment.objects.filter(user=user)
    user_clients = Client.objects.filter(user=user)
    user_tasks = Task.objects.filter(user=user)

    total_revenue = user_payments.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
    pending_amount = user_payments.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0
    active_projects_count = user_projects.filter(status='in_progress').count()
    total_clients_count = user_clients.filter(status='active').count()
    pending_tasks_count = user_tasks.filter(Q(status='pending') | Q(status='in_progress')).count()

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

    status_counts = user_projects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    status_distribution = {
        'in_progress': status_dict.get('in_progress', 0),
        'completed': status_dict.get('completed', 0),
        'on_hold': status_dict.get('on_hold', 0),
        'planning': status_dict.get('planning', 0),
    }

    scatter_data = []
    for p in user_projects.select_related('client')[:15]:
        p_paid = user_payments.filter(project=p, status='paid').aggregate(t=Sum('amount'))['t'] or 0
        scatter_data.append({
            'x': float(p.budget or 0),
            'y': float(p_paid),
            'name': p.name,
            'client': p.client.name if p.client else 'N/A',
            'progress': p.progress
        })

    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    heatmap_matrix = []
    for w in range(3, -1, -1):
        week_row = []
        for d in range(7):
            day_target = today - timedelta(days=(w * 7 + (today.weekday() - d) % 7))
            day_payments = user_payments.filter(paid_date=day_target, status='paid').aggregate(t=Sum('amount'))['t'] or 0
            intensity = min(100, int((float(day_payments) / 500.0) * 100)) if day_payments else (15 if d < 5 else 5)
            week_row.append({
                'date': day_target.strftime('%b %d'),
                'val': float(day_payments),
                'intensity': intensity
            })
        heatmap_matrix.append(week_row)


    # Client Revenue Breakdown (Top Clients)
    client_labels = []
    client_revenues = []
    for client in user_clients[:6]:
        c_rev = user_payments.filter(project__client=client, status='paid').aggregate(t=Sum('amount'))['t'] or 0
        client_labels.append(client.name)
        client_revenues.append(float(c_rev))

    # Recent Projects (Serialized)
    recent_projects_qs = user_projects.select_related('client').order_by('-created_at')[:5]
    recent_projects_serialized = ProjectSerializer(recent_projects_qs, many=True).data

    payload = {
        "total_revenue": float(total_revenue),
        "pending_amount": float(pending_amount),
        "active_projects_count": active_projects_count,
        "total_projects_count": user_projects.count(),
        "total_clients_count": total_clients_count,
        "pending_tasks_count": pending_tasks_count,
        "monthly_chart": {
            "labels": months_labels,
            "data": monthly_data
        },
        "status_chart": status_distribution,
        "scatter_chart": scatter_data,
        "heatmap_chart": {
            "days": days_of_week,
            "matrix": heatmap_matrix
        },
        "client_chart": {
            "labels": client_labels,
            "data": client_revenues
        },
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


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_dashboard_analytics(request):
    """
    Advanced interactive analytics engine for Feature 17.
    Supports filtering by date range, client, project, status, priority.
    """
    user = request.user
    today = timezone.now().date()

    # Query params
    date_range = request.GET.get('range', '30d')
    client_id = request.GET.get('client', '')
    project_id = request.GET.get('project', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')

    projects = Project.objects.filter(user=user, is_archived=False)
    payments = Payment.objects.filter(user=user)
    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)
    tasks = Task.objects.filter(user=user, is_archived=False)

    if client_id:
        projects = projects.filter(client_id=client_id)
        payments = payments.filter(project__client_id=client_id)
        incomes = incomes.filter(client_id=client_id)
    if project_id:
        projects = projects.filter(id=project_id)
        payments = payments.filter(project_id=project_id)
        incomes = incomes.filter(project_id=project_id)
        expenses = expenses.filter(project_id=project_id)
        tasks = tasks.filter(project_id=project_id)
    if status_filter:
        projects = projects.filter(status=status_filter)
    if priority_filter:
        projects = projects.filter(priority=priority_filter)

    # Filter by date range
    start_date = None
    if date_range == '7d':
        start_date = today - timedelta(days=7)
    elif date_range == '30d':
        start_date = today - timedelta(days=30)
    elif date_range == '90d':
        start_date = today - timedelta(days=90)
    elif date_range == 'month':
        start_date = today.replace(day=1)
    elif date_range == 'year':
        start_date = today.replace(month=1, day=1)

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)
        incomes = incomes.filter(date__gte=start_date)
        expenses = expenses.filter(date__gte=start_date)

    # 1. Project Status Distribution
    status_counts = projects.values('status').annotate(count=Count('id'))
    status_dist = {item['status']: item['count'] for item in status_counts}

    # 2. Priority Distribution
    priority_counts = projects.values('priority').annotate(count=Count('id'))
    priority_dist = {item['priority']: item['count'] for item in priority_counts}

    # 3. Monthly Income vs Expenses Trend (last 6 months)
    monthly_labels = []
    income_trend = []
    expense_trend = []
    profit_trend = []

    for i in range(5, -1, -1):
        m_date = (today.replace(day=1) - timedelta(days=i * 30))
        m_income = (incomes.filter(date__year=m_date.year, date__month=m_date.month).aggregate(t=Sum('amount'))['t'] or 0) + \
                   (payments.filter(status='paid', paid_date__year=m_date.year, paid_date__month=m_date.month).aggregate(t=Sum('amount'))['t'] or 0)
        m_expense = expenses.filter(date__year=m_date.year, date__month=m_date.month).aggregate(t=Sum('amount'))['t'] or 0
        
        monthly_labels.append(m_date.strftime('%b %Y'))
        income_trend.append(float(m_income))
        expense_trend.append(float(m_expense))
        profit_trend.append(float(m_income) - float(m_expense))

    # 4. Client Revenue Distribution
    client_rev_labels = []
    client_rev_data = []
    for client in Client.objects.filter(user=user, is_archived=False)[:7]:
        c_pay = payments.filter(project__client=client, status='paid').aggregate(t=Sum('amount'))['t'] or 0
        c_inc = incomes.filter(client=client).aggregate(t=Sum('amount'))['t'] or 0
        tot = float(c_pay) + float(c_inc)
        if tot > 0:
            client_rev_labels.append(client.name)
            client_rev_data.append(tot)

    # 5. Productivity Stats
    tasks_completed = tasks.filter(status='completed').count()
    tasks_pending = tasks.filter(status__in=['todo', 'in_progress']).count()
    tasks_overdue = tasks.filter(due_date__lt=today, status__in=['todo', 'in_progress']).count()

    total_projs = projects.count()
    completed_projs = projects.filter(status='completed').count()
    completion_rate = round((completed_projs / total_projs * 100), 1) if total_projs > 0 else 0

    payload = {
        "status_distribution": status_dist,
        "priority_distribution": priority_dist,
        "financial_trend": {
            "labels": monthly_labels,
            "income": income_trend,
            "expenses": expense_trend,
            "profit": profit_trend,
        },
        "client_revenue": {
            "labels": client_rev_labels,
            "data": client_rev_data,
        },
        "productivity": {
            "completed": tasks_completed,
            "pending": tasks_pending,
            "overdue": tasks_overdue,
            "completion_rate": completion_rate,
        }
    }
    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_unread_notification_count(request):
    from .models import Notification
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({"unread_count": count}, status=status.HTTP_200_OK)

