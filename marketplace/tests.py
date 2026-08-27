"""
Comprehensive Unit Tests for Marketplace (Stage 1 — Client Side)
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from core.models import UserProfile
from marketplace.models import (
    ClientProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
)


class MarketplaceClientStage1Tests(TestCase):
    def setUp(self):
        self.client = TestClient()

        # Create Client User A
        self.user_a = User.objects.create_user(
            username='client_alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Smith'
        )
        self.profile_a = UserProfile.objects.create(
            user=self.user_a,
            role='client',
            is_verified=True
        )
        self.client_profile_a = ClientProfile.objects.create(
            user=self.user_a,
            full_name='Alice Smith',
            company_name='Acme Corp',
            phone='+919876543210',
            location='Bengaluru, India',
            bio='Founder of Acme Corp'
        )

        # Create Client User B (for Data Isolation tests)
        self.user_b = User.objects.create_user(
            username='client_bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Jones'
        )
        self.profile_b = UserProfile.objects.create(
            user=self.user_b,
            role='client',
            is_verified=True
        )
        self.client_profile_b = ClientProfile.objects.create(
            user=self.user_b,
            full_name='Bob Jones',
            company_name='Beta LLC'
        )

        # Create Freelancer User (for applications)
        self.freelancer_user = User.objects.create_user(
            username='freelancer_dan',
            email='dan@example.com',
            password='Password123!',
            first_name='Dan',
            last_name='Developer'
        )
        self.freelancer_profile = UserProfile.objects.create(
            user=self.freelancer_user,
            role='user',
            is_verified=True,
            skills='Python, Django, React'
        )

        # Create Freelancer User 2
        self.freelancer_user_2 = User.objects.create_user(
            username='freelancer_eva',
            email='eva@example.com',
            password='Password123!',
            first_name='Eva',
            last_name='Engineer'
        )
        self.freelancer_profile_2 = UserProfile.objects.create(
            user=self.freelancer_user_2,
            role='user',
            is_verified=True,
            skills='UI/UX, Figma'
        )

    # -------------------------------------------------------------------------
    # 1. Registration
    # -------------------------------------------------------------------------
    def test_client_registration(self):
        """Test registering a new Client account via the form."""
        response = self.client.post(reverse('marketplace:client_register'), {
            'full_name': 'Charlie Brown',
            'email': 'charlie@example.com',
            'phone': '+919998887776',
            'company_name': 'Charlie Tech',
            'password1': 'SecretPass123!',
            'password2': 'SecretPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('marketplace:client_dashboard'))

        # Check User & ClientProfile created
        user = User.objects.get(email='charlie@example.com')
        self.assertEqual(user.profile.role, 'client')
        self.assertTrue(hasattr(user, 'client_profile'))
        self.assertEqual(user.client_profile.company_name, 'Charlie Tech')

    # -------------------------------------------------------------------------
    # 2. Login & Routing
    # -------------------------------------------------------------------------
    def test_client_login_redirects_to_client_dashboard(self):
        """Test logging in as a Client redirects to marketplace:client_dashboard."""
        response = self.client.post(reverse('core:login'), {
            'username': 'client_alice',
            'password': 'Password123!',
            'login_type': 'user'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('marketplace:client_dashboard'))

    def test_home_redirects_client_to_client_dashboard(self):
        """When an authenticated client visits home page, redirect to client dashboard."""
        self.client.login(username='client_alice', password='Password123!')
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('marketplace:client_dashboard'))

    # -------------------------------------------------------------------------
    # 3. Client Dashboard
    # -------------------------------------------------------------------------
    def test_client_dashboard_view(self):
        """Test accessing the client dashboard."""
        self.client.login(username='client_alice', password='Password123!')
        response = self.client.get(reverse('marketplace:client_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Smith')
        self.assertContains(response, 'Dashboard')

    # -------------------------------------------------------------------------
    # 4. Client Profile
    # -------------------------------------------------------------------------
    def test_client_profile_view_and_edit(self):
        """Test viewing and updating client profile."""
        self.client.login(username='client_alice', password='Password123!')
        
        # View profile
        res_view = self.client.get(reverse('marketplace:client_profile_view'))
        self.assertEqual(res_view.status_code, 200)
        self.assertContains(res_view, 'Acme Corp')

        # Edit profile
        res_edit = self.client.post(reverse('marketplace:client_profile_edit'), {
            'full_name': 'Alice Wonderland',
            'email': 'alice_new@example.com',
            'phone': '+919876543210',
            'company_name': 'Acme Global',
            'company_description': 'Global solutions enterprise',
            'location': 'New Delhi, India',
            'bio': 'Updated executive bio',
        })
        self.assertEqual(res_edit.status_code, 302)
        self.assertRedirects(res_edit, reverse('marketplace:client_profile_view'))

        self.client_profile_a.refresh_from_db()
        self.assertEqual(self.client_profile_a.full_name, 'Alice Wonderland')
        self.assertEqual(self.client_profile_a.company_name, 'Acme Global')

    # -------------------------------------------------------------------------
    # 5. Project Management: Create, List, Detail, Edit, Close, Reopen
    # -------------------------------------------------------------------------
    def test_project_post_and_management(self):
        """Test full project lifecycle for client."""
        self.client.login(username='client_alice', password='Password123!')

        # 5. Create Project
        res_post = self.client.post(reverse('marketplace:project_post'), {
            'title': 'E-Commerce Website Development',
            'description': 'Need a responsive e-commerce web platform built with Django.',
            'category': 'web_development',
            'required_skills': 'HTML, CSS, JavaScript, Django',
            'budget': '40000.00',
            'budget_type': 'fixed',
            'expected_duration': '1_to_3_months',
            'deadline': '2026-12-31',
            'experience_level': 'intermediate',
            'status': 'open',
        })
        self.assertEqual(res_post.status_code, 302)
        project = MarketplaceProject.objects.get(title='E-Commerce Website Development')
        self.assertEqual(project.client, self.client_profile_a)
        self.assertEqual(project.budget, Decimal('40000.00'))
        self.assertEqual(project.status, 'open')

        # Verify Payment record initialized
        self.assertTrue(hasattr(project, 'payment_record'))
        self.assertEqual(project.payment_record.total_budget, Decimal('40000.00'))

        # 6. List Projects
        res_list = self.client.get(reverse('marketplace:project_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'E-Commerce Website Development')

        # 7. Project Detail
        res_detail = self.client.get(reverse('marketplace:project_detail', kwargs={'pk': project.pk}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'E-Commerce Website Development')
        self.assertContains(res_detail, '₹40000')

        # 8. Edit Project
        res_edit = self.client.post(reverse('marketplace:project_edit', kwargs={'pk': project.pk}), {
            'title': 'E-Commerce Website Development (Updated)',
            'description': 'Updated description with payment gateway integration.',
            'category': 'web_development',
            'required_skills': 'HTML, CSS, Django, Stripe',
            'budget': '45000.00',
            'budget_type': 'fixed',
            'expected_duration': '1_to_3_months',
            'deadline': '2026-12-31',
            'experience_level': 'expert',
            'status': 'open',
        })
        self.assertEqual(res_edit.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.title, 'E-Commerce Website Development (Updated)')
        self.assertEqual(project.budget, Decimal('45000.00'))

        # 9. Close Project
        res_close = self.client.post(reverse('marketplace:project_close', kwargs={'pk': project.pk}))
        self.assertEqual(res_close.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.status, 'closed')

        # 10. Reopen Project
        res_reopen = self.client.post(reverse('marketplace:project_reopen', kwargs={'pk': project.pk}))
        self.assertEqual(res_reopen.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.status, 'open')

    # -------------------------------------------------------------------------
    # 6. Data Isolation (Client A cannot access Client B's projects)
    # -------------------------------------------------------------------------
    def test_client_data_isolation(self):
        """Verify Client B cannot view or modify Client A's projects."""
        project_a = MarketplaceProject.objects.create(
            client=self.client_profile_a,
            title="Alice's Secret Project",
            description="Confidential project details",
            budget=50000,
            status='open'
        )

        # Login as Bob (Client B)
        self.client.login(username='client_bob', password='Password123!')

        # Bob views his project list — should NOT contain Alice's project
        res_list = self.client.get(reverse('marketplace:project_list'))
        self.assertNotContains(res_list, "Alice's Secret Project")

        # Bob attempts to open Alice's project detail directly -> 404
        res_detail = self.client.get(reverse('marketplace:project_detail', kwargs={'pk': project_a.pk}))
        self.assertEqual(res_detail.status_code, 404)

        # Bob attempts to edit Alice's project -> 404
        res_edit = self.client.post(reverse('marketplace:project_edit', kwargs={'pk': project_a.pk}), {
            'title': 'Hacked Title',
            'description': 'Hacked',
            'category': 'web_development',
            'budget': 100,
            'status': 'open'
        })
        self.assertEqual(res_edit.status_code, 404)

        # Bob attempts to close Alice's project -> 404
        res_close = self.client.post(reverse('marketplace:project_close', kwargs={'pk': project_a.pk}))
        self.assertEqual(res_close.status_code, 404)

    # -------------------------------------------------------------------------
    # 7. Application Review, Accept & Reject Workflows
    # -------------------------------------------------------------------------
    def test_application_accept_and_reject_workflows(self):
        """Test reviewing applications, accepting one freelancer, and rejecting others."""
        project = MarketplaceProject.objects.create(
            client=self.client_profile_a,
            title="Mobile App Development",
            description="Flutter or React Native app.",
            budget=60000,
            status='open'
        )

        # Create two applications (as if submitted in Stage 2)
        app1 = ProjectApplication.objects.create(
            project=project,
            freelancer=self.freelancer_user,
            proposal="I have 5 years experience in Flutter and backend APIs.",
            proposed_price=55000,
            estimated_duration="4 weeks",
            status='pending'
        )
        app2 = ProjectApplication.objects.create(
            project=project,
            freelancer=self.freelancer_user_2,
            proposal="I can build this in 6 weeks with premium UI.",
            proposed_price=60000,
            estimated_duration="6 weeks",
            status='pending'
        )

        self.client.login(username='client_alice', password='Password123!')

        # Review applications list
        res_apps = self.client.get(reverse('marketplace:project_applications', kwargs={'pk': project.pk}))
        self.assertEqual(res_apps.status_code, 200)
        self.assertContains(res_apps, "I have 5 years experience in Flutter")
        self.assertContains(res_apps, "₹55000")

        # Accept app1
        res_accept = self.client.post(reverse('marketplace:application_accept', kwargs={'app_pk': app1.pk}))
        self.assertEqual(res_accept.status_code, 302)
        self.assertRedirects(res_accept, reverse('marketplace:project_workspace', kwargs={'pk': project.pk}))

        # Verify application status changed
        app1.refresh_from_db()
        app2.refresh_from_db()
        project.refresh_from_db()

        self.assertEqual(app1.status, 'accepted')
        self.assertEqual(app2.status, 'rejected')  # Other pending applications auto-rejected
        self.assertEqual(project.assigned_freelancer, self.freelancer_user)
        self.assertEqual(project.status, 'assigned')

        # Verify Workspace displays assigned freelancer contact information
        res_ws = self.client.get(reverse('marketplace:project_workspace', kwargs={'pk': project.pk}))
        self.assertEqual(res_ws.status_code, 200)
        self.assertContains(res_ws, 'dan@example.com')
        self.assertContains(res_ws, 'Active Workspace')

    # -------------------------------------------------------------------------
    # 8. Support / Report Workflow
    # -------------------------------------------------------------------------
    def test_client_support_report_creation(self):
        """Test filing an incident report from client desk."""
        self.client.login(username='client_alice', password='Password123!')

        res_create = self.client.post(reverse('marketplace:client_support_create'), {
            'reason': 'scam',
            'description': 'Freelancer demanded advance payment off-platform.',
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertRedirects(res_create, reverse('marketplace:client_support_list'))

        report = ProjectReport.objects.filter(reporter=self.client_profile_a).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.reason, 'scam')
        self.assertEqual(report.status, 'open')

    # -------------------------------------------------------------------------
    # 9. API Authorization & Data Exposure Tests
    # -------------------------------------------------------------------------
    def test_api_requires_authentication_and_client_role(self):
        """Verify API endpoints reject unauthenticated and non-client users."""
        # Unauthenticated request
        res = self.client.get(reverse('marketplace:api_client_dashboard_stats'))
        self.assertEqual(res.status_code, 403)

        # Non-client user (Freelancer role)
        self.client.login(username='freelancer_dan', password='Password123!')
        res_freelancer = self.client.get(reverse('marketplace:api_client_dashboard_stats'))
        self.assertEqual(res_freelancer.status_code, 403)

    def test_api_never_exposes_passwords(self):
        """Verify profile API does not leak passwords, tokens, or private secrets."""
        self.client.login(username='client_alice', password='Password123!')
        res = self.client.get(reverse('marketplace:api_client_profile'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn('password', data)
        self.assertNotIn('password_hash', data)
        self.assertNotIn('secret_key', data)
        self.assertEqual(data['full_name'], 'Alice Smith')
