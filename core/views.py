from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from .models import Client, Project, Payment, Task, Note, ActivityLog
from .forms import (ClientForm, ProjectForm, PaymentForm, TaskForm, 
                   NoteForm, SearchForm)


# Utility Functions
def log_activity(user, action, model_type, model_id, description, request=None):
    """Helper function to log user activities"""
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
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Authentication Views
def home(request):
    """Home page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            log_activity(user, 'create', 'user', user.id, 
                        f'User {username} registered', request)
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def custom_login(request):
    """Custom login view with activity logging"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            log_activity(user, 'login', 'user', user.id, 
                        f'User {username} logged in', request)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')


@login_required
def custom_logout(request):
    """Custom logout view with activity logging"""
    username = request.user.username
    log_activity(request.user, 'logout', 'user', request.user.id, 
                f'User {username} logged out', request)
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('core:login')


# Dashboard View
@login_required
def dashboard(request):
    """Main dashboard with statistics and overview"""
    user = request.user
    
    # Get statistics
    total_clients = Client.objects.filter(user=user).count()
    total_projects = Project.objects.filter(user=user).count()
    completed_projects = Project.objects.filter(user=user, status='completed').count()
    pending_projects = Project.objects.filter(user=user, status='pending').count()
    
    # Upcoming deadlines (next 7 days)
    upcoming_deadlines = Project.objects.filter(
        user=user,
        deadline__lte=timezone.now() + timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).order_by('deadline')[:5]
    
    # Total earnings (paid payments)
    total_earnings = Payment.objects.filter(
        user=user,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending payments
    pending_payments = Payment.objects.filter(
        user=user,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activities
    recent_activities = ActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:10]
    
    # Recent projects
    recent_projects = Project.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'pending_projects': pending_projects,
        'upcoming_deadlines': upcoming_deadlines,
        'total_earnings': total_earnings,
        'pending_payments': pending_payments,
        'recent_activities': recent_activities,
        'recent_projects': recent_projects,
    }
    
    return render(request, 'dashboard.html', context)
    """Main dashboard with statistics and overview"""
    user = request.user
    
    # Get statistics
    total_clients = Client.objects.filter(user=user).count()
    total_projects = Project.objects.filter(user=user).count()
    completed_projects = Project.objects.filter(user=user, status='completed').count()
    pending_projects = Project.objects.filter(user=user, status='pending').count()
    
    # Upcoming deadlines (next 7 days)
    upcoming_deadlines = Project.objects.filter(
        user=user,
        deadline__lte=timezone.now() + timezone.timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).order_by('deadline')[:5]
    
    # Total earnings (paid payments)
    total_earnings = Payment.objects.filter(
        user=user,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending payments
    pending_payments = Payment.objects.filter(
        user=user,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activities
    recent_activities = ActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:10]
    
    # Recent projects
    recent_projects = Project.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'pending_projects': pending_projects,
        'upcoming_deadlines': upcoming_deadlines,
        'total_earnings': total_earnings,
        'pending_payments': pending_payments,
        'recent_activities': recent_activities,
        'recent_projects': recent_projects,
    }
    
    return render(request, 'dashboard.html', context)


# Client Views
@login_required
def client_list(request):
    """List all clients with search and pagination"""
    user = request.user
    clients = Client.objects.filter(user=user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    if status_filter:
        clients = clients.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Client.STATUS_CHOICES,
    }
    
    return render(request, 'clients/client_list.html', context)


@login_required
def client_detail(request, pk):
    """View client details"""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    projects = client.projects.all()
    
    context = {
        'client': client,
        'projects': projects,
    }
    
    return render(request, 'clients/client_detail.html', context)


@login_required
def client_create(request):
    """Create a new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            log_activity(request.user, 'create', 'client', client.id, 
                        f'Created client: {client.name}', request)
            messages.success(request, 'Client created successfully!')
            return redirect('client_detail', pk=client.id)
    else:
        form = ClientForm()
    
    return render(request, 'clients/client_form.html', {'form': form, 'action': 'Create'})


@login_required
def client_update(request, pk):
    """Update an existing client"""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            updated_client = form.save()
            log_activity(request.user, 'update', 'client', client.id, 
                        f'Updated client: {updated_client.name}', request)
            messages.success(request, 'Client updated successfully!')
            return redirect('client_detail', pk=client.id)
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/client_form.html', {'form': form, 'action': 'Update', 'client': client})


@login_required
def client_delete(request, pk):
    """Delete a client"""
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        log_activity(request.user, 'delete', 'client', pk, 
                    f'Deleted client: {client_name}', request)
        messages.success(request, 'Client deleted successfully!')
        return redirect('client_list')
    
    return render(request, 'clients/client_confirm_delete.html', {'client': client})


# Project Views
@login_required
def project_list(request):
    """List all projects with search and pagination"""
    user = request.user
    projects = Project.objects.filter(user=user).select_related('client')
    
    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(client__name__icontains=search_query)
        )
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if priority_filter:
        projects = projects.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Project.STATUS_CHOICES,
        'priority_choices': Project.PRIORITY_CHOICES,
    }
    
    return render(request, 'projects/project_list.html', context)


@login_required
def project_detail(request, pk):
    """View project details"""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    tasks = project.tasks.all()
    payments = project.payments.all()
    notes = project.project_notes.all()
    
    context = {
        'project': project,
        'tasks': tasks,
        'payments': payments,
        'notes': notes,
    }
    
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_create(request):
    """Create a new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            log_activity(request.user, 'create', 'project', project.id, 
                        f'Created project: {project.name}', request)
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm()
        # Filter clients to show only user's clients
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})


@login_required
def project_update(request, pk):
    """Update an existing project"""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            updated_project = form.save()
            log_activity(request.user, 'update', 'project', project.id, 
                        f'Updated project: {updated_project.name}', request)
            messages.success(request, 'Project updated successfully!')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm(instance=project)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Update', 'project': project})


@login_required
def project_delete(request, pk):
    """Delete a project"""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        log_activity(request.user, 'delete', 'project', pk, 
                    f'Deleted project: {project_name}', request)
        messages.success(request, 'Project deleted successfully!')
        return redirect('project_list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})


# Payment Views
@login_required
def payment_list(request):
    """List all payments with search and pagination"""
    user = request.user
    payments = Payment.objects.filter(user=user).select_related('project', 'project__client')
    
    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        payments = payments.filter(
            Q(project__name__icontains=search_query) |
            Q(invoice_number__icontains=search_query)
        )
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Payment.STATUS_CHOICES,
    }
    
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_detail(request, pk):
    """View payment details"""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/payment_detail.html', context)


@login_required
def payment_create(request):
    """Create a new payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            log_activity(request.user, 'create', 'payment', payment.id, 
                        f'Created payment: ${payment.amount} for {payment.project.name}', request)
            messages.success(request, 'Payment created successfully!')
            return redirect('payment_detail', pk=payment.id)
    else:
        form = PaymentForm()
        # Filter projects to show only user's projects
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    
    return render(request, 'payments/payment_form.html', {'form': form, 'action': 'Create'})


@login_required
def payment_update(request, pk):
    """Update an existing payment"""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            updated_payment = form.save()
            # Log status change if status changed
            if payment.status != updated_payment.status:
                log_activity(request.user, 'status_change', 'payment', payment.id, 
                            f'Payment status changed from {payment.status} to {updated_payment.status}', request)
            
            log_activity(request.user, 'update', 'payment', payment.id, 
                        f'Updated payment: ${updated_payment.amount}', request)
            messages.success(request, 'Payment updated successfully!')
            return redirect('payment_detail', pk=payment.id)
    else:
        form = PaymentForm(instance=payment)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    
    return render(request, 'payments/payment_form.html', {'form': form, 'action': 'Update', 'payment': payment})


@login_required
def payment_delete(request, pk):
    """Delete a payment"""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    if request.method == 'POST':
        payment.delete()
        log_activity(request.user, 'delete', 'payment', pk, 
                    f'Deleted payment: ${payment.amount}', request)
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})


# Task Views
@login_required
def task_list(request):
    """List all tasks with search and pagination"""
    user = request.user
    tasks = Task.objects.filter(user=user).select_related('project', 'project__client')
    
    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(project__name__icontains=search_query)
        )
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }
    
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    """View task details"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    context = {
        'task': task,
    }
    
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create(request):
    """Create a new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            log_activity(request.user, 'create', 'task', task.id, 
                        f'Created task: {task.title}', request)
            messages.success(request, 'Task created successfully!')
            return redirect('task_detail', pk=task.id)
    else:
        form = TaskForm()
        # Filter projects to show only user's projects
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_update(request, pk):
    """Update an existing task"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            # Log status change if status changed
            if task.status != updated_task.status:
                log_activity(request.user, 'status_change', 'task', task.id, 
                            f'Task status changed from {task.status} to {updated_task.status}', request)
            
            log_activity(request.user, 'update', 'task', task.id, 
                        f'Updated task: {updated_task.title}', request)
            messages.success(request, 'Task updated successfully!')
            return redirect('task_detail', pk=task.id)
    else:
        form = TaskForm(instance=task)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Update', 'task': task})


@login_required
def task_delete(request, pk):
    """Delete a task"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        log_activity(request.user, 'delete', 'task', pk, 
                    f'Deleted task: {task_title}', request)
        messages.success(request, 'Task deleted successfully!')
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


# Note Views
@login_required
def note_list(request):
    """List all notes with search and pagination"""
    user = request.user
    notes = Note.objects.filter(user=user).select_related('project', 'client')
    
    # Search and filter
    search_query = request.GET.get('search', '')
    
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'notes/note_list.html', context)


@login_required
def note_detail(request, pk):
    """View note details"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    context = {
        'note': note,
    }
    
    return render(request, 'notes/note_detail.html', context)


@login_required
def note_create(request):
    """Create a new note"""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            log_activity(request.user, 'create', 'note', note.id, 
                        f'Created note: {note.title}', request)
            messages.success(request, 'Note created successfully!')
            return redirect('note_detail', pk=note.id)
    else:
        form = NoteForm()
        # Filter to show only user's projects and clients
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    
    return render(request, 'notes/note_form.html', {'form': form, 'action': 'Create'})


@login_required
def note_update(request, pk):
    """Update an existing note"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            updated_note = form.save()
            log_activity(request.user, 'update', 'note', note.id, 
                        f'Updated note: {updated_note.title}', request)
            messages.success(request, 'Note updated successfully!')
            return redirect('note_detail', pk=note.id)
    else:
        form = NoteForm(instance=note)
        form.fields['project'].queryset = Project.objects.filter(user=request.user)
        form.fields['client'].queryset = Client.objects.filter(user=request.user)
    
    return render(request, 'notes/note_form.html', {'form': form, 'action': 'Update', 'note': note})


@login_required
def note_delete(request, pk):
    """Delete a note"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note_title = note.title
        note.delete()
        log_activity(request.user, 'delete', 'note', pk, 
                    f'Deleted note: {note_title}', request)
        messages.success(request, 'Note deleted successfully!')
        return redirect('note_list')
    
    return render(request, 'notes/note_confirm_delete.html', {'note': note})


# Activity Log Views
@login_required
def activity_list(request):
    """List all user activities with pagination"""
    user = request.user
    activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'activities/activity_list.html', context)
