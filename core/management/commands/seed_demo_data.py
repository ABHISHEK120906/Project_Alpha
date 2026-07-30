from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Client, Project, Payment, Task, Note, ActivityLog

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds realistic sample clients, projects, tasks, payments, and notes for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Username to seed data for')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, email=f"{username}@example.com", password="password123")
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}'"))

        seed_user_data(user)
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded sample data for '{user.username}'!"))


def seed_user_data(user):
    """Utility function to populate realistic demo data for a user."""
    today = timezone.now().date()

    # 1. Clients
    clients_data = [
        {'name': 'Acme Global Corp', 'email': 'contact@acmeglobal.com', 'phone': '+1 (555) 234-5678', 'company': 'Acme Corp', 'notes': 'Enterprise client. High priority.'},
        {'name': 'Apex Digital Studios', 'email': 'hello@apexdigital.io', 'phone': '+1 (555) 876-5432', 'company': 'Apex Media', 'notes': 'UI/UX redesign & branding.'},
        {'name': 'Nova BioLabs', 'email': 'support@novabiolabs.org', 'phone': '+1 (555) 432-1098', 'company': 'Nova Science', 'notes': 'Web portal & data visualization.'},
        {'name': 'Quantum Tech', 'email': 'billing@quantumtech.com', 'phone': '+1 (555) 987-6543', 'company': 'Quantum Soft', 'notes': 'Mobile API & Cloud DevOps.'},
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

    # 2. Projects
    projects_data = [
        {
            'name': 'E-Commerce Platform Redesign',
            'client': clients['Acme Global Corp'],
            'description': 'Full redesign of client e-commerce store with Stripe payment integration and modern React design.',
            'status': 'in_progress',
            'priority': 'high',
            'budget': Decimal('8500.00'),
            'progress': 75,
            'start_date': today - timedelta(days=20),
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
            'start_date': today - timedelta(days=10),
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
            'start_date': today - timedelta(days=40),
            'deadline': today - timedelta(days=5),
        },
        {
            'name': 'Data Visualization Dashboard',
            'client': clients['Nova BioLabs'],
            'description': 'Interactive analytics dashboard using Chart.js, responsive grid layout, and PDF export reporting.',
            'status': 'planning',
            'priority': 'medium',
            'budget': Decimal('4800.00'),
            'progress': 15,
            'start_date': today - timedelta(days=2),
            'deadline': today + timedelta(days=25),
        },
    ]

    projects = {}
    for p_data in projects_data:
        proj_obj, _ = Project.objects.get_or_create(
            user=user, name=p_data['name'],
            defaults=p_data
        )
        projects[p_data['name']] = proj_obj

    # 3. Tasks
    tasks_data = [
        {'title': 'Complete Checkout Flow Wireframes', 'project': projects['E-Commerce Platform Redesign'], 'status': 'completed', 'priority': 'high', 'due_date': today - timedelta(days=3)},
        {'title': 'Integrate Stripe Payment Gateway', 'project': projects['E-Commerce Platform Redesign'], 'status': 'in_progress', 'priority': 'high', 'due_date': today + timedelta(days=2)},
        {'title': 'Configure JWT Authentication Endpoints', 'project': projects['Mobile App REST API Backend'], 'status': 'in_progress', 'priority': 'urgent', 'due_date': today + timedelta(days=4)},
        {'title': 'Write Comprehensive API Unit Tests', 'project': projects['Mobile App REST API Backend'], 'status': 'pending', 'priority': 'medium', 'due_date': today + timedelta(days=8)},
        {'title': 'Export High-Res SVG Logo Assets', 'project': projects['Brand Identity & Landing Page'], 'status': 'completed', 'priority': 'low', 'due_date': today - timedelta(days=8)},
        {'title': 'Draft Analytics Dashboard Wireframe Layout', 'project': projects['Data Visualization Dashboard'], 'status': 'in_progress', 'priority': 'medium', 'due_date': today + timedelta(days=6)},
    ]

    for t_data in tasks_data:
        Task.objects.get_or_create(
            user=user, title=t_data['title'], project=t_data['project'],
            defaults={'status': t_data['status'], 'priority': t_data['priority'], 'due_date': t_data['due_date']}
        )

    # 4. Payments
    payments_data = [
        {'project': projects['Brand Identity & Landing Page'], 'amount': Decimal('3400.00'), 'status': 'paid', 'payment_method': 'bank_transfer', 'due_date': today - timedelta(days=10), 'paid_date': today - timedelta(days=6), 'invoice_number': 'INV-2026-001'},
        {'project': projects['E-Commerce Platform Redesign'], 'amount': Decimal('4250.00'), 'status': 'paid', 'payment_method': 'stripe', 'due_date': today - timedelta(days=15), 'paid_date': today - timedelta(days=14), 'invoice_number': 'INV-2026-002'},
        {'project': projects['E-Commerce Platform Redesign'], 'amount': Decimal('4250.00'), 'status': 'pending', 'payment_method': 'stripe', 'due_date': today + timedelta(days=5), 'paid_date': None, 'invoice_number': 'INV-2026-003'},
        {'project': projects['Mobile App REST API Backend'], 'amount': Decimal('3100.00'), 'status': 'paid', 'payment_method': 'paypal', 'due_date': today - timedelta(days=5), 'paid_date': today - timedelta(days=4), 'invoice_number': 'INV-2026-004'},
        {'project': projects['Mobile App REST API Backend'], 'amount': Decimal('3100.00'), 'status': 'pending', 'payment_method': 'bank_transfer', 'due_date': today + timedelta(days=12), 'paid_date': None, 'invoice_number': 'INV-2026-005'},
    ]

    for pm_data in payments_data:
        Payment.objects.get_or_create(
            user=user, invoice_number=pm_data['invoice_number'],
            defaults=pm_data
        )

    # 5. Notes
    notes_data = [
        {'title': 'Client Kickoff Meeting Notes', 'content': 'Acme Corp team prefers clean purple/indigo color schemes with responsive drawer sidebar layout.'},
        {'title': 'API Rate Limits & Authentication', 'content': 'Enforce sliding window rate limit of 100 calls/min on /api/v1/ endpoints.'},
        {'title': 'Deployment Credentials', 'content': 'Production environment deployed via Vercel Serverless with WhiteNoise compressed static assets.'},
    ]

    for n_data in notes_data:
        Note.objects.get_or_create(
            user=user, title=n_data['title'],
            defaults={'content': n_data['content']}
        )

    import uuid
    # 6. Activity Logs
    logs_data = [
        ('login', 'user', uuid.uuid4(), f"User {user.username} logged into FreelanceTrack"),
        ('create', 'project', projects['E-Commerce Platform Redesign'].id, f"Created project '{projects['E-Commerce Platform Redesign'].name}'"),
        ('create', 'payment', uuid.uuid4(), "Recorded payment of $3,400.00 for Brand Identity"),
        ('update', 'task', uuid.uuid4(), "Completed task 'Checkout Flow Wireframes'"),
    ]

    for action, m_type, m_id, desc in logs_data:
        ActivityLog.objects.create(
            user=user, action=action, model_type=m_type, model_id=m_id, description=desc
        )
