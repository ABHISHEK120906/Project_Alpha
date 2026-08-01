"""
Comprehensive unit tests for Freelancer Project Tracker.
Tests cover models, views, authentication, security, and forms.

Run with: python manage.py test core
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import Client, Project, Payment, Task, Note, ActivityLog


# ============================================================
# MODEL TESTS
# ============================================================

class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client_obj = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='test@example.com',
            company='Test Corp',
            status='active'
        )

    def test_client_str(self):
        self.assertIn('Test Client', str(self.client_obj))

    def test_client_default_status(self):
        self.assertEqual(self.client_obj.status, 'active')

    def test_client_total_projects(self):
        self.assertEqual(self.client_obj.get_total_projects(), 0)

    def test_client_uuid_pk(self):
        import uuid
        self.assertIsInstance(self.client_obj.id, uuid.UUID)


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='testpass123')
        self.client_obj = Client.objects.create(
            user=self.user, name='Client A', email='a@test.com'
        )
        self.project = Project.objects.create(
            user=self.user,
            client=self.client_obj,
            name='Test Project',
            status='in_progress',
            priority='high',
            progress=50,
        )

    def test_project_str(self):
        self.assertIn('Test Project', str(self.project))

    def test_project_not_overdue_without_deadline(self):
        self.assertFalse(self.project.is_overdue())

    def test_project_overdue_with_past_deadline(self):
        self.project.deadline = timezone.now().date() - timedelta(days=1)
        self.project.save()
        self.assertTrue(self.project.is_overdue())

    def test_project_not_overdue_when_completed(self):
        self.project.deadline = timezone.now().date() - timedelta(days=1)
        self.project.status = 'completed'
        self.project.save()
        self.assertFalse(self.project.is_overdue())

    def test_project_default_progress(self):
        proj = Project.objects.create(
            user=self.user, client=self.client_obj, name='P2'
        )
        self.assertEqual(proj.progress, 0)


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser3', password='testpass123')
        self.client_obj = Client.objects.create(user=self.user, name='C', email='c@test.com')
        self.project = Project.objects.create(user=self.user, client=self.client_obj, name='Proj')
        self.payment = Payment.objects.create(
            user=self.user,
            project=self.project,
            amount=Decimal('1500.00'),
            status='pending',
        )

    def test_payment_str(self):
        self.assertIn('1500', str(self.payment))

    def test_payment_not_overdue_without_due_date(self):
        self.assertFalse(self.payment.is_overdue())

    def test_payment_overdue(self):
        self.payment.due_date = timezone.now().date() - timedelta(days=1)
        self.payment.save()
        self.assertTrue(self.payment.is_overdue())


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser4', password='testpass123')
        self.client_obj = Client.objects.create(user=self.user, name='C', email='d@test.com')
        self.project = Project.objects.create(user=self.user, client=self.client_obj, name='Proj')
        self.task = Task.objects.create(
            user=self.user, project=self.project, title='Test Task', status='todo'
        )

    def test_task_str(self):
        self.assertIn('Test Task', str(self.task))

    def test_task_overdue(self):
        self.task.due_date = timezone.now().date() - timedelta(days=2)
        self.task.save()
        self.assertTrue(self.task.is_overdue())


# ============================================================
# VIEW TESTS — Authentication
# ============================================================

class AuthViewTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='viewuser', password='viewpass123')

    def test_home_redirects_authenticated(self):
        self.client.login(username='viewuser', password='viewpass123')
        resp = self.client.get(reverse('core:home'))
        self.assertRedirects(resp, reverse('core:dashboard'))

    def test_login_page_renders(self):
        resp = self.client.get(reverse('core:login'))
        self.assertEqual(resp.status_code, 200)

    def test_register_page_renders(self):
        resp = self.client.get(reverse('core:register'))
        self.assertEqual(resp.status_code, 200)

    def test_login_with_valid_credentials(self):
        resp = self.client.post(reverse('core:login'), {
            'username': 'viewuser', 'password': 'viewpass123'
        })
        self.assertRedirects(resp, reverse('core:dashboard'))

    def test_login_with_invalid_credentials(self):
        resp = self.client.post(reverse('core:login'), {
            'username': 'viewuser', 'password': 'wrongpassword'
        })
        self.assertEqual(resp.status_code, 200)

    def test_logout_redirects(self):
        self.client.login(username='viewuser', password='viewpass123')
        # POST request executes logout securely
        resp = self.client.post(reverse('core:logout'))
        self.assertRedirects(resp, reverse('core:login'))


# ============================================================
# VIEW TESTS — Login Required
# ============================================================

class LoginRequiredTest(TestCase):
    def setUp(self):
        self.client = TestClient()

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(resp, f"{reverse('core:login')}?next={reverse('core:dashboard')}")

    def test_client_list_requires_login(self):
        resp = self.client.get(reverse('core:client_list'))
        self.assertEqual(resp.status_code, 302)

    def test_project_list_requires_login(self):
        resp = self.client.get(reverse('core:project_list'))
        self.assertEqual(resp.status_code, 302)

    def test_payment_list_requires_login(self):
        resp = self.client.get(reverse('core:payment_list'))
        self.assertEqual(resp.status_code, 302)

    def test_task_list_requires_login(self):
        resp = self.client.get(reverse('core:task_list'))
        self.assertEqual(resp.status_code, 302)


# ============================================================
# VIEW TESTS — CRUD Operations
# ============================================================

class ClientCRUDTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='cruduser', password='crudpass123')
        self.client.login(username='cruduser', password='crudpass123')
        self.client_obj = Client.objects.create(
            user=self.user, name='CRUD Client', email='crud@test.com', status='active'
        )

    def test_client_list_view(self):
        resp = self.client.get(reverse('core:client_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'CRUD Client')

    def test_client_detail_view(self):
        resp = self.client.get(reverse('core:client_detail', args=[self.client_obj.id]))
        self.assertEqual(resp.status_code, 200)

    def test_client_create_view_get(self):
        resp = self.client.get(reverse('core:client_create'))
        self.assertEqual(resp.status_code, 200)

    def test_client_create_post(self):
        resp = self.client.post(reverse('core:client_create'), {
            'name': 'New Client',
            'email': 'new@test.com',
            'status': 'active',
        })
        self.assertEqual(Client.objects.filter(user=self.user).count(), 2)

    def test_client_update_post(self):
        resp = self.client.post(
            reverse('core:client_update', args=[self.client_obj.id]),
            {'name': 'Updated Client', 'email': 'updated@test.com', 'status': 'inactive'}
        )
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, 'Updated Client')

    def test_client_delete(self):
        resp = self.client.post(reverse('core:client_delete', args=[self.client_obj.id]))
        self.assertEqual(Client.objects.filter(user=self.user).count(), 0)

    def test_user_cannot_view_other_users_client(self):
        other_user = User.objects.create_user(username='otheruser', password='otherpass123')
        other_client = Client.objects.create(
            user=other_user, name='Other Client', email='other@test.com'
        )
        resp = self.client.get(reverse('core:client_detail', args=[other_client.id]))
        self.assertEqual(resp.status_code, 404)


class ProjectCRUDTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='projuser', password='projpass123')
        self.client.login(username='projuser', password='projpass123')
        self.client_obj = Client.objects.create(
            user=self.user, name='P Client', email='p@test.com'
        )
        self.project = Project.objects.create(
            user=self.user, client=self.client_obj,
            name='Test Project', status='pending'
        )

    def test_project_list(self):
        resp = self.client.get(reverse('core:project_list'))
        self.assertEqual(resp.status_code, 200)

    def test_project_detail(self):
        resp = self.client.get(reverse('core:project_detail', args=[self.project.id]))
        self.assertEqual(resp.status_code, 200)

    def test_project_search(self):
        resp = self.client.get(reverse('core:project_list'), {'search': 'Test Project'})
        self.assertContains(resp, 'Test Project')

    def test_project_filter_by_status(self):
        resp = self.client.get(reverse('core:project_list'), {'status': 'pending'})
        self.assertContains(resp, 'Test Project')


# ============================================================
# DASHBOARD VIEW TEST
# ============================================================

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='dashuser', password='dashpass123')
        self.client.login(username='dashuser', password='dashpass123')

    def test_dashboard_loads(self):
        resp = self.client.get(reverse('core:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_context_keys(self):
        resp = self.client.get(reverse('core:dashboard'))
        self.assertIn('total_clients', resp.context)
        self.assertIn('total_projects', resp.context)
        self.assertIn('total_earnings', resp.context)
        self.assertIn('pending_payments', resp.context)

    def test_dashboard_shows_correct_counts(self):
        client_obj = Client.objects.create(user=self.user, name='Dash Client', email='d@test.com')
        Project.objects.create(user=self.user, client=client_obj, name='Dash Project')
        resp = self.client.get(reverse('core:dashboard'))
        self.assertEqual(resp.context['total_clients'], 1)
        self.assertEqual(resp.context['total_projects'], 1)


# ============================================================
# REPORTS VIEW TEST
# ============================================================

class ReportsViewTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='reportuser', password='reportpass123')
        self.client.login(username='reportuser', password='reportpass123')

    def test_reports_page_loads(self):
        resp = self.client.get(reverse('core:reports_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_pdf_monthly_report(self):
        resp = self.client.get(reverse('core:export_pdf_report', args=['monthly']))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/pdf', resp['Content-Type'])

    def test_excel_monthly_report(self):
        resp = self.client.get(reverse('core:export_excel_report', args=['monthly']))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('spreadsheetml', resp['Content-Type'])

    def test_pdf_payment_report(self):
        resp = self.client.get(reverse('core:export_pdf_report', args=['payment']))
        self.assertEqual(resp.status_code, 200)

    def test_excel_client_report(self):
        resp = self.client.get(reverse('core:export_excel_report', args=['client']))
        self.assertEqual(resp.status_code, 200)


# ============================================================
# SETTINGS VIEW TEST
# ============================================================

class SettingsViewTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(
            username='settingsuser', password='settingspass123', email='settings@test.com'
        )
        self.client.login(username='settingsuser', password='settingspass123')

    def test_settings_page_loads(self):
        resp = self.client.get(reverse('core:settings'))
        self.assertEqual(resp.status_code, 200)

    def test_profile_update(self):
        resp = self.client.post(reverse('core:settings'), {
            'action': 'profile',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')

    def test_settings_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('core:settings'))
        self.assertEqual(resp.status_code, 302)


# ============================================================
# ACTIVITY LOG TEST
# ============================================================

class ActivityLogTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='actuser', password='actpass123')
        self.client.login(username='actuser', password='actpass123')

    def test_activity_created_on_client_create(self):
        self.client.post(reverse('core:client_create'), {
            'name': 'Activity Client', 'email': 'act@test.com', 'status': 'active'
        })
        activities = ActivityLog.objects.filter(user=self.user, action='create', model_type='client')
        self.assertGreater(activities.count(), 0)

    def test_activity_list_loads(self):
        resp = self.client.get(reverse('core:activity_list'))
        self.assertEqual(resp.status_code, 200)


# ============================================================
# API PROXY ENDPOINTS TEST (/api/v1/)
# ============================================================

class APIProxyEndpointTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='apiuser', password='apipassword123')
        self.client.login(username='apiuser', password='apipassword123')

    def test_api_health(self):
        resp = self.client.get(reverse('core:api_health'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'ok')

    def test_api_dashboard_stats_authenticated(self):
        resp = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('total_revenue', data)
        self.assertIn('monthly_chart', data)
        self.assertIn('status_chart', data)

    def test_api_dashboard_stats_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertIn(resp.status_code, [302, 401, 403])


class SuperAdminModuleTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.admin_user = User.objects.create_superuser(
            username='admin_test', email='abhishekmutthalkar121@gmail.com', password='pagal@123'
        )
        self.admin_profile, _ = UserProfile.objects.get_or_create(user=self.admin_user)
        self.admin_profile.role = 'admin'
        self.admin_profile.save()

        self.normal_user = User.objects.create_user(
            username='normal_user', email='normal@test.com', password='userpass123'
        )
        self.normal_profile, _ = UserProfile.objects.get_or_create(user=self.normal_user)
        self.normal_profile.role = 'user'
        self.normal_profile.save()

    def test_role_based_login_admin(self):
        resp = self.client.post(reverse('core:login'), {
            'username': 'admin_test',
            'password': 'pagal@123',
            'login_type': 'admin'
        })
        self.assertRedirects(resp, reverse('core:admin_dashboard'))

    def test_role_based_login_user(self):
        resp = self.client.post(reverse('core:login'), {
            'username': 'normal_user',
            'password': 'userpass123',
            'login_type': 'user'
        })
        self.assertRedirects(resp, reverse('core:dashboard'))

    def test_non_admin_cannot_access_admin_dashboard(self):
        self.client.login(username='normal_user', password='userpass123')
        resp = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username='admin_test', password='pagal@123')
        resp = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_user_management(self):
        self.client.login(username='admin_test', password='pagal@123')
        resp = self.client.get(reverse('core:admin_users_list'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_security_center(self):
        self.client.login(username='admin_test', password='pagal@123')
        resp = self.client.get(reverse('core:admin_security'))
        self.assertEqual(resp.status_code, 200)


