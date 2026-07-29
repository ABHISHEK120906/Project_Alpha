from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
import json
import re
from .models import Client, Project, Payment, Task, Note, ActivityLog
from .forms import (ClientForm, ProjectForm, PaymentForm, TaskForm,
                    NoteForm, SearchForm)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def log_activity(user, action, model_type, model_id, description, request=None):
    """Helper function to log user activities to the ActivityLog."""
    ip_address = None
    if request:
        ip_address = get_client_ip(request)

    ActivityLog.objects.create(
        user=user,
        action=action,
        model_type=model_type,
        model_id=model_id,
        description=description,
        ip_address=ip_address
    )


def get_client_ip(request):
    """Extract the real client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def home(request):
    """Landing page — redirects authenticated users to dashboard."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'home.html')


def register(request):
    """User registration with activity logging."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            log_activity(user, 'create', 'user', user.id,
                         f'User {username} registered', request)
            messages.success(request, f'Account created! Welcome, {username}. Please log in.')
            return redirect('core:login')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def custom_login(request):
    """Custom login view with activity logging."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_activity(user, 'login', 'user', user.id,
                         f'User {username} logged in', request)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'registration/login.html')


@require_http_methods(['GET', 'POST'])
def custom_logout(request):
    """Logout view — POST only to prevent CSRF-logout attacks."""
    # H-02: Only process logout on POST to prevent logout via embedded GET requests
    if request.method == 'POST' and request.user.is_authenticated:
        username = request.user.username
        log_activity(request.user, 'logout', 'user', request.user.id,
                     f'User logged out', request)
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    elif request.method == 'GET' and request.user.is_authenticated:
        # For GET requests, redirect to a confirmation page instead of logging out
        return redirect('core:dashboard')
    return redirect('core:login')


# ============================================================
# DASHBOARD VIEW
# ============================================================

@login_required
def dashboard(request):
    """Main dashboard with KPI cards, charts data, and recent records."""
    user = request.user

    # ── KPI Statistics ──────────────────────────────────────
    total_clients = Client.objects.filter(user=user).count()
    total_projects = Project.objects.filter(user=user).count()
    completed_projects = Project.objects.filter(user=user, status='completed').count()
    pending_projects = Project.objects.filter(user=user, status='pending').count()
    in_progress_projects = Project.objects.filter(user=user, status='in_progress').count()
    on_hold_projects = Project.objects.filter(user=user, status='on_hold').count()
    cancelled_projects = Project.objects.filter(user=user, status='cancelled').count()

    # ── Upcoming deadlines (next 7 days) ────────────────────
    upcoming_deadlines = Project.objects.filter(
        user=user,
        deadline__gte=timezone.now().date(),
        deadline__lte=timezone.now().date() + timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).select_related('client').order_by('deadline')[:5]

    # ── Financial Summary ───────────────────────────────────
    total_earnings = Payment.objects.filter(
        user=user, status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    pending_payments = Payment.objects.filter(
        user=user, status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ── Recent Activities ───────────────────────────────────
    recent_activities = ActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:10]

    # ── Recent Projects ─────────────────────────────────────
    recent_projects = Project.objects.filter(
        user=user
    ).select_related('client').order_by('-created_at')[:5]

    # ── Monthly Earnings (last 6 months for Line/Bar chart) ─
    monthly_earnings = []
    monthly_labels = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_total = Payment.objects.filter(
            user=user,
            status='paid',
            paid_date__year=month_date.year,
            paid_date__month=month_date.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_earnings.append(float(month_total))
        monthly_labels.append(month_date.strftime('%b %Y'))

    # ── Task completion stats ────────────────────────────────
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()

    context = {
        'total_clients': total_clients,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'pending_projects': pending_projects,
        'in_progress_projects': in_progress_projects,
        'on_hold_projects': on_hold_projects,
        'cancelled_projects': cancelled_projects,
        'upcoming_deadlines': upcoming_deadlines,
        'total_earnings': total_earnings,
        'pending_payments': pending_payments,
        'recent_activities': recent_activities,
        'recent_projects': recent_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
    }

    return render(request, 'dashboard.html', context)


# ============================================================
# CLIENT VIEWS
# ============================================================

@login_required
def client_list(request):
    """List all clients with search, status filter, and pagination."""
    user = request.user
    clients = Client.objects.filter(user=user)

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company__icontains=search_query)
        )

    if status_filter:
        clients = clients.filter(status=status_filter)

    # Sorting
    valid_sorts = ['name', '-name', 'created_at', '-created_at', 'company', '-company']
    if sort_by in valid_sorts:
        clients = clients.order_by(sort_by)

    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Client.STATUS_CHOICES,
        'total_count': clients.count(),
    }
    return render(request, 'clients/client_list.html', context)


@login_required
def client_detail(request, pk):
    """View client details with projects and financial summary."""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    projects = client.projects.all().order_by('-created_at')
    total_earned = Payment.objects.filter(
        project__client=client, status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'client': client,
        'projects': projects,
        'total_earned': total_earned,
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
def client_create(request):
    """Create a new client record."""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            log_activity(request.user, 'create', 'client', client.id,
                         f'Created client: {client.name}', request)
            messages.success(request, f'Client "{client.name}" created successfully!')
            return redirect('core:client_detail', pk=client.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {'form': form, 'action': 'Create'})


@login_required
def client_update(request, pk):
    """Update an existing client record."""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            updated_client = form.save()
            log_activity(request.user, 'update', 'client', client.id,
                         f'Updated client: {updated_client.name}', request)
            messages.success(request, f'Client "{updated_client.name}" updated successfully!')
            return redirect('core:client_detail', pk=client.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {
        'form': form, 'action': 'Update', 'client': client
    })


@login_required
def client_delete(request, pk):
    """Confirm and delete a client record."""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    if request.method == 'POST':
        client_name = client.name
        log_activity(request.user, 'delete', 'client', pk,
                     f'Deleted client: {client_name}', request)
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return redirect('core:client_list')
    return render(request, 'clients/client_confirm_delete.html', {'client': client})


# ============================================================
# PROJECT VIEWS
# ============================================================

@login_required
def project_list(request):
    """List all projects with search, filter, sorting, and pagination."""
    user = request.user
    projects = Project.objects.filter(user=user).select_related('client')

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if status_filter:
        projects = projects.filter(status=status_filter)

    if priority_filter:
        projects = projects.filter(priority=priority_filter)

    valid_sorts = ['name', '-name', 'deadline', '-deadline', 'created_at', '-created_at',
                   'budget', '-budget', 'progress', '-progress']
    if sort_by in valid_sorts:
        projects = projects.order_by(sort_by)

    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'sort_by': sort_by,
        'status_choices': Project.STATUS_CHOICES,
        'priority_choices': Project.PRIORITY_CHOICES,
        'total_count': projects.count(),
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_detail(request, pk):
    """View project details with tasks, payments, and notes."""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    tasks = project.tasks.all().order_by('status', '-created_at')
    payments = project.payments.all().order_by('-created_at')
    notes = project.project_notes.all().order_by('-created_at')

    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'project': project,
        'tasks': tasks,
        'payments': payments,
        'notes': notes,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'completed_tasks': tasks.filter(status='completed').count(),
        'total_tasks': tasks.count(),
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_create(request):
    """Create a new project."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            log_activity(request.user, 'create', 'project', project.id,
                         f'Created project: {project.name}', request)
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('core:project_detail', pk=project.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProjectForm()
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})


@login_required
def project_update(request, pk):
    """Update an existing project."""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
        if form.is_valid():
            old_status = project.status
            updated_project = form.save()
            if old_status != updated_project.status:
                log_activity(request.user, 'status_change', 'project', project.id,
                             f'Project status changed: {old_status} → {updated_project.status}', request)
            log_activity(request.user, 'update', 'project', project.id,
                         f'Updated project: {updated_project.name}', request)
            messages.success(request, f'Project "{updated_project.name}" updated successfully!')
            return redirect('core:project_detail', pk=project.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProjectForm(instance=project)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    return render(request, 'projects/project_form.html', {
        'form': form, 'action': 'Update', 'project': project
    })


@login_required
def project_delete(request, pk):
    """Confirm and delete a project."""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        project_name = project.name
        log_activity(request.user, 'delete', 'project', pk,
                     f'Deleted project: {project_name}', request)
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('core:project_list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})


# ============================================================
# PAYMENT VIEWS
# ============================================================

@login_required
def payment_list(request):
    """List all payments with search, filter, and pagination."""
    user = request.user
    payments = Payment.objects.filter(user=user).select_related('project', 'project__client')

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        payments = payments.filter(
            Q(project__name__icontains=search_query) |
            Q(invoice_number__icontains=search_query) |
            Q(project__client__name__icontains=search_query)
        )

    if status_filter:
        payments = payments.filter(status=status_filter)

    valid_sorts = ['amount', '-amount', 'due_date', '-due_date', 'created_at', '-created_at']
    if sort_by in valid_sorts:
        payments = payments.order_by(sort_by)

    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary stats
    total_paid = Payment.objects.filter(user=user, status='paid').aggregate(t=Sum('amount'))['t'] or 0
    total_pending = Payment.objects.filter(user=user, status='pending').aggregate(t=Sum('amount'))['t'] or 0

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Payment.STATUS_CHOICES,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_detail(request, pk):
    """View payment details."""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
def payment_create(request):
    """Create a new payment record."""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            log_activity(request.user, 'create', 'payment', payment.id,
                         f'Created payment: ${payment.amount} for {payment.project.name}', request)
            messages.success(request, 'Payment created successfully!')
            return redirect('core:payment_detail', pk=payment.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PaymentForm()
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    return render(request, 'payments/payment_form.html', {'form': form, 'action': 'Create'})


@login_required
def payment_update(request, pk):
    """Update an existing payment record."""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    old_status = payment.status
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        if form.is_valid():
            updated_payment = form.save()
            if old_status != updated_payment.status:
                log_activity(request.user, 'status_change', 'payment', payment.id,
                             f'Payment status: {old_status} → {updated_payment.status}', request)
            log_activity(request.user, 'update', 'payment', payment.id,
                         f'Updated payment: ${updated_payment.amount}', request)
            messages.success(request, 'Payment updated successfully!')
            return redirect('core:payment_detail', pk=payment.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PaymentForm(instance=payment)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    return render(request, 'payments/payment_form.html', {
        'form': form, 'action': 'Update', 'payment': payment
    })


@login_required
def payment_delete(request, pk):
    """Confirm and delete a payment record."""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    if request.method == 'POST':
        amount = payment.amount
        log_activity(request.user, 'delete', 'payment', pk,
                     f'Deleted payment: ${amount}', request)
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('core:payment_list')
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})


# ============================================================
# TASK VIEWS
# ============================================================

@login_required
def task_list(request):
    """List all tasks with search, filter, sorting, and pagination."""
    user = request.user
    tasks = Task.objects.filter(user=user).select_related('project', 'project__client')

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    project_filter = request.GET.get('project', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(project__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if project_filter:
        tasks = tasks.filter(project__id=project_filter)

    valid_sorts = ['title', '-title', 'due_date', '-due_date', 'created_at', '-created_at',
                   'priority', '-priority', 'status', '-status']
    if sort_by in valid_sorts:
        tasks = tasks.order_by(sort_by)

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Available projects for filter dropdown
    user_projects = Project.objects.filter(user=user).order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'sort_by': sort_by,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'user_projects': user_projects,
        'total_count': tasks.count(),
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    """View task details."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_create(request):
    """Create a new task."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            log_activity(request.user, 'create', 'task', task.id,
                         f'Created task: {task.title}', request)
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('core:task_detail', pk=task.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = TaskForm()
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_update(request, pk):
    """Update an existing task."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    old_status = task.status
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        if form.is_valid():
            updated_task = form.save()
            if old_status != updated_task.status:
                log_activity(request.user, 'status_change', 'task', task.id,
                             f'Task status: {old_status} → {updated_task.status}', request)
            log_activity(request.user, 'update', 'task', task.id,
                         f'Updated task: {updated_task.title}', request)
            messages.success(request, f'Task "{updated_task.title}" updated successfully!')
            return redirect('core:task_detail', pk=task.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = TaskForm(instance=task)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    return render(request, 'tasks/task_form.html', {
        'form': form, 'action': 'Update', 'task': task
    })


@login_required
def task_delete(request, pk):
    """Confirm and delete a task."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task_title = task.title
        log_activity(request.user, 'delete', 'task', pk,
                     f'Deleted task: {task_title}', request)
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('core:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


# ============================================================
# NOTE VIEWS
# ============================================================

@login_required
def note_list(request):
    """List all notes with search and pagination."""
    user = request.user
    notes = Note.objects.filter(user=user).select_related('project', 'client')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    paginator = Paginator(notes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'notes/note_list.html', context)


@login_required
def note_detail(request, pk):
    """View note details."""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    return render(request, 'notes/note_detail.html', {'note': note})


@login_required
def note_create(request):
    """Create a new note."""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            log_activity(request.user, 'create', 'note', note.id,
                         f'Created note: {note.title}', request)
            messages.success(request, 'Note created successfully!')
            return redirect('core:note_detail', pk=note.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = NoteForm()
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    return render(request, 'notes/note_form.html', {'form': form, 'action': 'Create'})


@login_required
def note_update(request, pk):
    """Update an existing note."""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
        if form.is_valid():
            updated_note = form.save()
            log_activity(request.user, 'update', 'note', note.id,
                         f'Updated note: {updated_note.title}', request)
            messages.success(request, 'Note updated successfully!')
            return redirect('core:note_detail', pk=note.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = NoteForm(instance=note)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    return render(request, 'notes/note_form.html', {
        'form': form, 'action': 'Update', 'note': note
    })


@login_required
def note_delete(request, pk):
    """Confirm and delete a note."""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note_title = note.title
        log_activity(request.user, 'delete', 'note', pk,
                     f'Deleted note: {note_title}', request)
        note.delete()
        messages.success(request, 'Note deleted successfully!')
        return redirect('core:note_list')
    return render(request, 'notes/note_confirm_delete.html', {'note': note})


# ============================================================
# ACTIVITY LOG VIEW
# ============================================================

@login_required
def activity_list(request):
    """List all user activities with pagination."""
    user = request.user
    activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')

    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'activities/activity_list.html', {'page_obj': page_obj})


# ============================================================
# REPORTS VIEW
# ============================================================

@login_required
def reports_dashboard(request):
    """Reports overview page with export options."""
    user = request.user

    # Payment report data
    total_paid = Payment.objects.filter(user=user, status='paid').aggregate(t=Sum('amount'))['t'] or 0
    total_pending = Payment.objects.filter(user=user, status='pending').aggregate(t=Sum('amount'))['t'] or 0
    total_overdue = Payment.objects.filter(user=user, status='overdue').aggregate(t=Sum('amount'))['t'] or 0

    # Project report data
    projects_by_status = {
        'completed': Project.objects.filter(user=user, status='completed').count(),
        'in_progress': Project.objects.filter(user=user, status='in_progress').count(),
        'pending': Project.objects.filter(user=user, status='pending').count(),
        'on_hold': Project.objects.filter(user=user, status='on_hold').count(),
        'cancelled': Project.objects.filter(user=user, status='cancelled').count(),
    }

    # Monthly report — last 12 months
    monthly_data = []
    today = timezone.now().date()
    for i in range(11, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i * 30))
        month_total = Payment.objects.filter(
            user=user, status='paid',
            paid_date__year=month_date.year,
            paid_date__month=month_date.month
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly_data.append({
            'month': month_date.strftime('%b %Y'),
            'total': float(month_total),
        })

    # Client report
    top_clients = Client.objects.filter(user=user).annotate(
        project_count=Count('projects')
    ).order_by('-project_count')[:10]

    context = {
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'projects_by_status': projects_by_status,
        'monthly_data': monthly_data,
        'top_clients': top_clients,
        'monthly_labels_json': json.dumps([d['month'] for d in monthly_data]),
        'monthly_values_json': json.dumps([d['total'] for d in monthly_data]),
    }
    return render(request, 'reports/reports.html', context)


_VALID_REPORT_TYPES = frozenset(['payment', 'project', 'client', 'monthly'])


@login_required
def export_pdf_report(request, report_type):
    """Generate and stream a PDF report using ReportLab."""
    if report_type not in _VALID_REPORT_TYPES:
        messages.error(request, 'Invalid report type requested.')
        return redirect('core:reports_dashboard')

    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
    except ImportError:
        messages.error(request, 'ReportLab is not installed. Cannot generate PDF.')
        return redirect('core:reports_dashboard')

    user = request.user
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=20, textColor=colors.HexColor('#4f46e5'),
                                  alignment=TA_CENTER, spaceAfter=12)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                    textColor=colors.HexColor('#1e1b4b'), spaceAfter=8)
    normal_style = styles['Normal']

    elements = []
    today = timezone.now().date()
    report_date = today.strftime('%B %d, %Y')

    # Report Title
    elements.append(Paragraph(f'Freelancer Project Tracker', title_style))
    elements.append(Paragraph(f'Report Type: {report_type.title().replace("_", " ")} — {report_date}', normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    header_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ])

    if report_type == 'payment':
        elements.append(Paragraph('Payment Report', heading_style))
        payments = Payment.objects.filter(user=user).select_related('project').order_by('-created_at')
        data = [['Invoice #', 'Project', 'Amount', 'Status', 'Due Date', 'Paid Date']]
        for p in payments:
            data.append([
                p.invoice_number or 'N/A',
                p.project.name[:30],
                f'${p.amount:,.2f}',
                p.get_status_display(),
                str(p.due_date or 'N/A'),
                str(p.paid_date or 'N/A'),
            ])
        if len(data) > 1:
            t = Table(data, colWidths=[1.2 * inch, 2 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch])
            t.setStyle(header_style)
            elements.append(t)
        else:
            elements.append(Paragraph('No payment records found.', normal_style))

    elif report_type == 'project':
        elements.append(Paragraph('Project Report', heading_style))
        projects = Project.objects.filter(user=user).select_related('client').order_by('-created_at')
        data = [['Project Name', 'Client', 'Status', 'Priority', 'Budget', 'Progress', 'Deadline']]
        for p in projects:
            data.append([
                p.name[:25],
                p.client.name[:20],
                p.get_status_display(),
                p.get_priority_display(),
                f'${p.budget:,.2f}' if p.budget else 'N/A',
                f'{p.progress}%',
                str(p.deadline or 'N/A'),
            ])
        if len(data) > 1:
            t = Table(data, colWidths=[1.5 * inch, 1.2 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, 0.6 * inch, 0.8 * inch])
            t.setStyle(header_style)
            elements.append(t)
        else:
            elements.append(Paragraph('No project records found.', normal_style))

    elif report_type == 'client':
        elements.append(Paragraph('Client Report', heading_style))
        clients = Client.objects.filter(user=user).annotate(proj_count=Count('projects')).order_by('-proj_count')
        data = [['Client Name', 'Company', 'Email', 'Status', 'Total Projects']]
        for c in clients:
            data.append([
                c.name[:25],
                (c.company or 'Individual')[:25],
                c.email[:30],
                c.get_status_display(),
                str(c.proj_count),
            ])
        if len(data) > 1:
            t = Table(data, colWidths=[1.5 * inch, 1.5 * inch, 2 * inch, 0.8 * inch, 0.8 * inch])
            t.setStyle(header_style)
            elements.append(t)
        else:
            elements.append(Paragraph('No client records found.', normal_style))

    elif report_type == 'monthly':
        elements.append(Paragraph('Monthly Earnings Report (Last 12 Months)', heading_style))
        today = timezone.now().date()
        data = [['Month', 'Total Earned', 'Number of Payments']]
        for i in range(11, -1, -1):
            month_date = (today.replace(day=1) - timedelta(days=i * 30))
            month_payments = Payment.objects.filter(
                user=user, status='paid',
                paid_date__year=month_date.year,
                paid_date__month=month_date.month
            )
            month_total = month_payments.aggregate(t=Sum('amount'))['t'] or 0
            data.append([
                month_date.strftime('%B %Y'),
                f'${month_total:,.2f}',
                str(month_payments.count()),
            ])
        t = Table(data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        t.setStyle(header_style)
        elements.append(t)

    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f'Generated by Freelancer Project Tracker on {report_date}', normal_style))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    safe_filename = f'{report_type}_report_{today.strftime("%Y-%m-%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
    return response


@login_required
def export_excel_report(request, report_type):
    """Generate and stream an Excel report using openpyxl."""
    if report_type not in _VALID_REPORT_TYPES:
        messages.error(request, 'Invalid report type requested.')
        return redirect('core:reports_dashboard')

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        import io
    except ImportError:
        messages.error(request, 'openpyxl is not installed. Cannot generate Excel.')
        return redirect('core:reports_dashboard')

    user = request.user
    wb = openpyxl.Workbook()
    ws = wb.active

    # Styling helpers
    header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='4F46E5', end_color='4F46E5', fill_type='solid')
    alt_fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    def style_header_row(ws, row_num, col_count):
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row_num, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = border

    def style_data_row(ws, row_num, col_count, alternate=False):
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row_num, column=col)
            if alternate:
                cell.fill = alt_fill
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            cell.border = border

    today = timezone.now().date()

    if report_type == 'payment':
        ws.title = 'Payment Report'
        headers = ['Invoice #', 'Project', 'Client', 'Amount', 'Status', 'Method', 'Due Date', 'Paid Date']
        ws.append(headers)
        style_header_row(ws, 1, len(headers))
        payments = Payment.objects.filter(user=user).select_related('project', 'project__client').order_by('-created_at')
        for i, p in enumerate(payments, 2):
            ws.append([
                p.invoice_number or 'N/A',
                p.project.name,
                p.project.client.name,
                float(p.amount),
                p.get_status_display(),
                p.get_payment_method_display(),
                str(p.due_date or ''),
                str(p.paid_date or ''),
            ])
            style_data_row(ws, i, len(headers), i % 2 == 0)
        col_widths = [15, 25, 20, 12, 12, 15, 12, 12]

    elif report_type == 'project':
        ws.title = 'Project Report'
        headers = ['Project Name', 'Client', 'Status', 'Priority', 'Budget', 'Progress %',
                   'Start Date', 'Deadline', 'Total Paid', 'Total Pending']
        ws.append(headers)
        style_header_row(ws, 1, len(headers))
        projects = Project.objects.filter(user=user).select_related('client').order_by('-created_at')
        for i, p in enumerate(projects, 2):
            total_paid = p.payments.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
            total_pending = p.payments.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0
            ws.append([
                p.name, p.client.name, p.get_status_display(), p.get_priority_display(),
                float(p.budget) if p.budget else 0,
                p.progress,
                str(p.start_date or ''), str(p.deadline or ''),
                float(total_paid), float(total_pending),
            ])
            style_data_row(ws, i, len(headers), i % 2 == 0)
        col_widths = [25, 20, 12, 12, 12, 12, 12, 12, 12, 12]

    elif report_type == 'client':
        ws.title = 'Client Report'
        headers = ['Client Name', 'Company', 'Email', 'Phone', 'Status',
                   'Total Projects', 'Total Earned']
        ws.append(headers)
        style_header_row(ws, 1, len(headers))
        clients = Client.objects.filter(user=user).annotate(proj_count=Count('projects')).order_by('-proj_count')
        for i, c in enumerate(clients, 2):
            total_earned = Payment.objects.filter(
                project__client=c, status='paid'
            ).aggregate(t=Sum('amount'))['t'] or 0
            ws.append([
                c.name, c.company or 'Individual', c.email,
                c.phone or '', c.get_status_display(),
                c.proj_count, float(total_earned),
            ])
            style_data_row(ws, i, len(headers), i % 2 == 0)
        col_widths = [20, 20, 25, 15, 12, 15, 15]

    elif report_type == 'monthly':
        ws.title = 'Monthly Report'
        headers = ['Month', 'Year', 'Total Earned ($)', 'No. of Payments',
                   'Pending Amount ($)', 'No. of Pending']
        ws.append(headers)
        style_header_row(ws, 1, len(headers))
        for i_m, i in enumerate(range(11, -1, -1), 2):
            month_date = (today.replace(day=1) - timedelta(days=i * 30))
            paid = Payment.objects.filter(
                user=user, status='paid',
                paid_date__year=month_date.year,
                paid_date__month=month_date.month
            )
            pending = Payment.objects.filter(
                user=user, status='pending',
                due_date__year=month_date.year,
                due_date__month=month_date.month
            )
            ws.append([
                month_date.strftime('%B'), month_date.year,
                float(paid.aggregate(t=Sum('amount'))['t'] or 0),
                paid.count(),
                float(pending.aggregate(t=Sum('amount'))['t'] or 0),
                pending.count(),
            ])
            style_data_row(ws, i_m, len(headers), i_m % 2 == 0)
        col_widths = [15, 8, 18, 15, 18, 15]

    else:
        messages.error(request, f'Unknown report type: {report_type}')
        return redirect('core:reports_dashboard')

    # Apply column widths
    for idx, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    # Freeze header row
    ws.freeze_panes = 'A2'

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    safe_filename = f'{report_type}_report_{today.strftime("%Y-%m-%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
    return response


# ============================================================
# SETTINGS VIEW
# ============================================================

_VALID_SETTINGS_ACTIONS = frozenset(['profile', 'password'])


@login_required
def user_settings(request):
    """User settings page — profile update and password change."""
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action not in _VALID_SETTINGS_ACTIONS:
            messages.error(request, 'Invalid settings action.')
            return redirect('core:settings')

        if action == 'profile':
            # Update basic profile fields
            user = request.user
            user.first_name = request.POST.get('first_name', '').strip()[:150]
            user.last_name = request.POST.get('last_name', '').strip()[:150]
            
            new_email = request.POST.get('email', '').strip()
            if new_email:
                try:
                    validate_email(new_email)
                    user.email = new_email
                except ValidationError:
                    messages.error(request, 'Please enter a valid email address.')
                    return render(request, 'settings.html', {'password_form': password_form})
            else:
                user.email = ''
                
            user.save()
            log_activity(request.user, 'update', 'user', request.user.id,
                         'Updated profile settings', request)
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:settings')

        elif action == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                log_activity(request.user, 'update', 'user', request.user.id,
                             'Changed account password', request)
                messages.success(request, 'Password changed successfully!')
                return redirect('core:settings')
            else:
                messages.error(request, 'Password change failed. Please check the errors below.')

    context = {
        'password_form': password_form,
    }
    return render(request, 'settings.html', context)
