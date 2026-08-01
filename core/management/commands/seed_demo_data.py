from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Client, Project, Payment, Task, Note, ActivityLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds realistic sample clients, projects, tasks, payments, and notes for users.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='', help='Specific username to seed data for (defaults to all users)')

    def handle(self, *args, **options):
        target_username = options.get('username')
        if target_username:
            users = User.objects.filter(username=target_username)
        else:
            users = User.objects.all()

        if not users.exists():
            user = User.objects.create_user(username="sirji", email="sirji@example.com", password="password123")
            users = [user]

        for u in users:
            seed_user_data(u)
            self.stdout.write(self.style.SUCCESS(f"Successfully loaded realistic demo data for '{u.username}'!"))


def seed_user_data(user):
    today = timezone.now().date()

    clients_data = [
        {'name': 'Acme Global Corp', 'email': 'contact@acmeglobal.com', 'phone': '+1 (555) 234-5678', 'company': 'Acme Corp', 'notes': 'Enterprise client. High priority.'},
        {'name': 'Apex Digital Studios', 'email': 'hello@apexdigital.io', 'phone': '+1 (555) 876-5432', 'company': 'Apex Media', 'notes': 'UI/UX redesign & branding.'},
        {'name': 'Nova BioLabs', 'email': 'support@novabiolabs.org', 'phone': '+1 (555) 432-1098', 'company': 'Nova Science', 'notes': 'Web portal & data visualization.'},
        {'name': 'Quantum Tech', 'email': 'billing@quantumtech.com', 'phone': '+1 (555) 987-6543', 'company': 'Quantum Soft', 'notes': 'Mobile API & Cloud DevOps.'},
        {'name': 'Starlight Interactive', 'email': 'info@starlight.dev', 'phone': '+1 (555) 654-3210', 'company': 'Starlight Media', 'notes': 'Full stack SaaS & AI integration.'},
    ]

    clients = {}
    for c_data in clients_data:
        client_obj, _ = Client.objects.get_or_create(
            user=user, name=c_data['name'],
            defaults={
                'email': c_data['email'],
                'phone': c_data['phone'],
                'company': c_data['company'],
                'notes': c_data['notes'],
                'status': 'active'
            }
        )
        clients[c_data['name']] = client_obj

    projects_data = [
        {
            'name': 'E-Commerce Platform Redesign',
            'client': clients['Acme Global Corp'],
            'description': 'Full redesign of client e-commerce store with Stripe payment integration and modern React design.',
            'status': 'in_progress',
            'priority': 'high',
            'budget': Decimal('8500.00'),
            'progress': 75,
            'start_date': today - timedelta(days=25),
            'deadline': today + timedelta(days=5),
        },
        {
            'name': 'Mobile App REST API Backend',
            'client': clients['Quantum Tech'],
            'description': 'High-performance Django REST framework API backend with JWT authentication and PostgreSQL.',
            'status': 'in_progress',
            'priority': 'urgent',
            'budget': Decimal('6200.00'),
            'progress': 45,
            'start_date': today - timedelta(days=15),
            'deadline': today + timedelta(days=12),
        },
        {
            'name': 'Brand Identity & Landing Page',
            'client': clients['Apex Digital Studios'],
            'description': 'Custom UI design, color palette system, responsive landing page, and SEO optimization.',
            'status': 'completed',
            'priority': 'medium',
            'budget': Decimal('3400.00'),
            'progress': 100,
            'start_date': today - timedelta(days=50),
            'deadline': today - timedelta(days=10),
        },
        {
            'name': 'Data Visualization Dashboard',
            'client': clients['Nova BioLabs'],
            'description': 'Interactive analytics dashboard using Chart.js, responsive grid layout, and PDF export reporting.',
            'status': 'in_progress',
            'priority': 'high',
            'budget': Decimal('4800.00'),
            'progress': 60,
            'start_date': today - timedelta(days=12),
            'deadline': today + timedelta(days=18),
        },
        {
            'name': 'AI Copilot Integration Portal',
            'client': clients['Starlight Interactive'],
            'description': 'LLM assistant integration with streaming WebSocket responses and user access controls.',
            'status': 'completed',
            'priority': 'urgent',
            'budget': Decimal('9200.00'),
            'progress': 100,
            'start_date': today - timedelta(days=80),
            'deadline': today - timedelta(days=20),
        },
    ]

    projects = {}
    for p_data in projects_data:
        proj_obj, _ = Project.objects.get_or_create(
            user=user, name=p_data['name'],
            defaults=p_data
        )
        projects[p_data['name']] = proj_obj

    tasks_data = [
        {'title': 'Complete Checkout Flow Wireframes', 'project': projects['E-Commerce Platform Redesign'], 'status': 'completed', 'priority': 'high', 'due_date': today - timedelta(days=3)},
        {'title': 'Integrate Stripe Payment Gateway', 'project': projects['E-Commerce Platform Redesign'], 'status': 'in_progress', 'priority': 'high', 'due_date': today + timedelta(days=2)},
        {'title': 'Configure JWT Authentication Endpoints', 'project': projects['Mobile App REST API Backend'], 'status': 'in_progress', 'priority': 'urgent', 'due_date': today + timedelta(days=4)},
        {'title': 'Write Comprehensive API Unit Tests', 'project': projects['Mobile App REST API Backend'], 'status': 'pending', 'priority': 'medium', 'due_date': today + timedelta(days=8)},
        {'title': 'Export High-Res SVG Logo Assets', 'project': projects['Brand Identity & Landing Page'], 'status': 'completed', 'priority': 'low', 'due_date': today - timedelta(days=12)},
        {'title': 'Build Heatmap Matrix & Scatter Plot View', 'project': projects['Data Visualization Dashboard'], 'status': 'in_progress', 'priority': 'high', 'due_date': today + timedelta(days=5)},
        {'title': 'Optimize Streaming Token Throughput', 'project': projects['AI Copilot Integration Portal'], 'status': 'completed', 'priority': 'urgent', 'due_date': today - timedelta(days=22)},
    ]

    for t_data in tasks_data:
        Task.objects.get_or_create(
            user=user, title=t_data['title'], project=t_data['project'],
            defaults={'status': t_data['status'], 'priority': t_data['priority'], 'due_date': t_data['due_date']}
        )

    payments_data = [
        {'project': projects['AI Copilot Integration Portal'], 'amount': Decimal('4600.00'), 'status': 'paid', 'payment_method': 'bank_transfer', 'due_date': today - timedelta(days=70), 'paid_date': today - timedelta(days=68), 'invoice_number': 'INV-2026-101'},
        {'project': projects['AI Copilot Integration Portal'], 'amount': Decimal('4600.00'), 'status': 'paid', 'payment_method': 'bank_transfer', 'due_date': today - timedelta(days=25), 'paid_date': today - timedelta(days=22), 'invoice_number': 'INV-2026-102'},
        {'project': projects['Brand Identity & Landing Page'], 'amount': Decimal('3400.00'), 'status': 'paid', 'payment_method': 'bank_transfer', 'due_date': today - timedelta(days=15), 'paid_date': me_date(today, 12), 'invoice_number': 'INV-2026-103'},
        {'project': projects['E-Commerce Platform Redesign'], 'amount': Decimal('4250.00'), 'status': 'paid', 'payment_method': 'stripe', 'due_date': today - timedelta(days=10), 'paid_date': today - timedelta(days=8), 'invoice_number': 'INV-2026-104'},
        {'project': projects['E-Commerce Platform Redesign'], 'amount': Decimal('4250.00'), 'status': 'pending', 'payment_method': 'stripe', 'due_date': today + timedelta(days=5), 'paid_date': None, 'invoice_number': 'INV-2026-105'},
        {'project': projects['Mobile App REST API Backend'], 'amount': Decimal('3100.00'), 'status': 'paid', 'payment_method': 'paypal', 'due_date': today - timedelta(days=5), 'paid_date': today - timedelta(days=4), 'invoice_number': 'INV-2026-106'},
        {'project': projects['Mobile App REST API Backend'], 'amount': Decimal('3100.00'), 'status': 'pending', 'payment_method': 'bank_transfer', 'due_date': today + timedelta(days=12), 'paid_date': None, 'invoice_number': 'INV-2026-107'},
        {'project': projects['Data Visualization Dashboard'], 'amount': Decimal('2400.00'), 'status': 'paid', 'payment_method': 'stripe', 'due_date': today - timedelta(days=2), 'paid_date': today - timedelta(days=1), 'invoice_number': 'INV-2026-108'},
    ]

    for pm_data in payments_data:
        Payment.objects.get_or_create(
            user=user, invoice_number=pm_data['invoice_number'],
            defaults=pm_data
        )

    # Seed UserProfile
    from core.models import UserProfile, Income, Expense, Invoice, InvoiceItem, Notification, CalendarEvent
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': '+1 (555) 987-6543',
            'address': '742 Evergreen Terrace, Tech Hub, CA 90210',
            'bio': 'Senior Full-Stack Freelance Developer specializing in Python, Django, React, and Enterprise Web Analytics.',
            'skills': 'Python, Django, JavaScript, React, PostgreSQL, TailwindCSS, AWS, UI/UX',
            'experience': '6+ years full-stack web application development',
            'portfolio_website': 'https://freelancer-portfolio.example.com',
            'social_github': 'https://github.com/freelancer',
            'social_linkedin': 'https://linkedin.com/in/freelancer'
        }
    )

    # Seed Incomes & Expenses
    incomes_data = [
        {'title': 'Retainer Fee - Acme Global', 'client': clients['Acme Global Corp'], 'project': projects['E-Commerce Platform Redesign'], 'amount': Decimal('3500.00'), 'category': 'retainer', 'date': today - timedelta(days=14)},
        {'title': 'Consulting Milestone - Quantum', 'client': clients['Quantum Tech'], 'project': projects['Mobile App REST API Backend'], 'amount': Decimal('2800.00'), 'category': 'consulting', 'date': today - timedelta(days=5)},
    ]
    for inc_d in incomes_data:
        Income.objects.get_or_create(user=user, title=inc_d['title'], defaults=inc_d)

    expenses_data = [
        {'title': 'JetBrains PyCharm Professional License', 'amount': Decimal('249.00'), 'category': 'software', 'date': today - timedelta(days=30)},
        {'title': 'AWS Cloud Hosting Server', 'amount': Decimal('180.50'), 'category': 'software', 'date': today - timedelta(days=15)},
        {'title': 'Figma Organization Plan', 'amount': Decimal('45.00'), 'category': 'software', 'date': today - timedelta(days=10)},
    ]
    for exp_d in expenses_data:
        Expense.objects.get_or_create(user=user, title=exp_d['title'], defaults=exp_d)

    # Seed Invoice
    inv, created = Invoice.objects.get_or_create(
        user=user, invoice_number='INV-2026-001',
        defaults={
            'client': clients['Acme Global Corp'],
            'project': projects['E-Commerce Platform Redesign'],
            'issue_date': today - timedelta(days=10),
            'due_date': today + timedelta(days=4),
            'status': 'sent',
            'subtotal': Decimal('5000.00'),
            'tax_rate': Decimal('10.00'),
            'tax_amount': Decimal('500.00'),
            'discount_amount': Decimal('0.00'),
            'total': Decimal('5500.00'),
            'notes': 'Payment due within 14 days of issue via Bank Transfer.'
        }
    )
    if created:
        InvoiceItem.objects.create(invoice=inv, description='E-Commerce Frontend UI Implementation', quantity=Decimal('1'), unit_price=Decimal('3000.00'), amount=Decimal('3000.00'))
        InvoiceItem.objects.create(invoice=inv, description='Stripe Gateway & Cart Integration', quantity=Decimal('1'), unit_price=Decimal('2000.00'), amount=Decimal('2000.00'))

    # Seed Notifications
    notifs_data = [
        {'title': 'E-Commerce Project Deadline Approaching', 'message': 'Project deadline is in 5 days on ' + (today + timedelta(days=5)).strftime('%b %d'), 'notification_type': 'deadline'},
        {'title': 'Payment Received from Quantum Tech', 'message': 'Payment of $3,100.00 confirmed for REST API Backend', 'notification_type': 'payment'},
        {'title': 'Invoice INV-2026-001 Sent', 'message': 'Invoice emailed to Acme Global Corp', 'notification_type': 'invoice'},
    ]
    for ntf_d in notifs_data:
        if not Notification.objects.filter(user=user, title=ntf_d['title']).exists():
            Notification.objects.create(user=user, title=ntf_d['title'], message=ntf_d['message'], notification_type=ntf_d['notification_type'])

    # Seed Calendar Event
    if not CalendarEvent.objects.filter(user=user, title='Client Review Meeting - Acme Corp').exists():
        CalendarEvent.objects.create(
            user=user, title='Client Review Meeting - Acme Corp',
            event_type='meeting',
            start_time=timezone.now() + timedelta(days=2),
            project=projects['E-Commerce Platform Redesign'],
            description='Sprint 3 demo and progress review meeting.'
        )

    notes_data = [
        {'title': 'Client Kickoff Meeting Notes', 'content': 'Acme Corp team prefers clean purple/indigo color schemes with responsive drawer sidebar layout.'},
        {'title': 'API Rate Limits & Authentication', 'content': 'Enforce sliding window rate limit of 100 calls/min on /api/v1/ endpoints.'},
        {'title': 'Deployment Credentials', 'content': 'Production environment deployed via Vercel Serverless with WhiteNoise compressed static assets.'},
        {'title': 'Visualization Studio Specifications', 'content': 'Support Bar, Line, Area, Doughnut, Scatter plot, and Workload Heatmap grid rendering.'},
    ]

    for n_data in notes_data:
        note_obj = Note.objects.filter(user=user, title=n_data['title']).first()
        if not note_obj:
            Note.objects.create(user=user, title=n_data['title'], content=n_data['content'])

    import uuid
    logs_data = [
        ('login', 'user', uuid.uuid4(), f"User {user.username} logged into FreelanceTrack"),
        ('create', 'project', projects['E-Commerce Platform Redesign'].id, f"Created project '{projects['E-Commerce Platform Redesign'].name}'"),
        ('create', 'payment', uuid.uuid4(), "Recorded payment of $4,250.00 for E-Commerce Platform"),
        ('update', 'task', uuid.uuid4(), "Completed task 'Checkout Flow Wireframes'"),
        ('create', 'project', projects['AI Copilot Integration Portal'].id, f"Created project '{projects['AI Copilot Integration Portal'].name}'"),
    ]

    for action, m_type, m_id, desc in logs_data:
        ActivityLog.objects.create(
            user=user, action=action, model_type=m_type, model_id=m_id, description=desc
        )


def me_date(today, days_back):
    return today - timedelta(days=days_back)
