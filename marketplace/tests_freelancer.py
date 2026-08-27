"""
Comprehensive Unit & Integration Tests for Marketplace Stage 2 (Freelancer Side)
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from core.models import UserProfile
from marketplace.models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
)


class MarketplaceFreelancerStage2Tests(TestCase):
    def setUp(self):
        self.client = TestClient()

        # 1. Create Client User (Alice)
        self.client_user = User.objects.create_user(
            username='client_alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Smith'
        )
        self.client_user_profile = UserProfile.objects.create(
            user=self.client_user,
            role='client',
            is_verified=True
        )
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Alice Smith',
            company_name='Acme Global Corp',
            phone='+919876543210',
            location='Bengaluru, India',
            bio='Tech enterprise looking for high quality developers'
        )

        # 2. Create Freelancer User A (Dan)
        self.freelancer_user_a = User.objects.create_user(
            username='freelancer_dan',
            email='dan@example.com',
            password='Password123!',
            first_name='Dan',
            last_name='Developer'
        )
        self.freelancer_up_a = UserProfile.objects.create(
            user=self.freelancer_user_a,
            role='freelancer',
            is_verified=True,
            skills='Python, Django, React, PostgreSQL'
        )
        self.freelancer_profile_a = FreelancerProfile.objects.create(
            user=self.freelancer_user_a,
            full_name='Dan Developer',
            professional_title='Senior Python & Django Architect',
            phone='+919111222333',
            location='Pune, India',
            skills='Python, Django, React, PostgreSQL',
            experience='6 years of enterprise web dev',
            bio='Full-stack Python specialist building robust systems.',
            hourly_rate=Decimal('2000.00'),
            portfolio_website='https://dan-dev.io',
            github_url='https://github.com/dandev',
        )

        # 3. Create Freelancer User B (Eva - for isolation & competition tests)
        self.freelancer_user_b = User.objects.create_user(
            username='freelancer_eva',
            email='eva@example.com',
            password='Password123!',
            first_name='Eva',
            last_name='Engineer'
        )
        self.freelancer_up_b = UserProfile.objects.create(
            user=self.freelancer_user_b,
            role='freelancer',
            is_verified=True,
            skills='UI/UX, Figma, React, TailwindCSS'
        )
        self.freelancer_profile_b = FreelancerProfile.objects.create(
            user=self.freelancer_user_b,
            full_name='Eva Engineer',
            professional_title='UI/UX Designer & Frontend Dev',
            hourly_rate=Decimal('1800.00')
        )

        # 4. Create Open Marketplace Projects
        self.project_1 = MarketplaceProject.objects.create(
            client=self.client_profile,
            title='E-Commerce API & Backend Microservices',
            description='Build robust RESTful APIs in Django and PostgreSQL for a high-traffic retail store.',
            category='web_development',
            required_skills='Python, Django, PostgreSQL, Docker',
            budget=Decimal('45000.00'),
            budget_type='fixed',
            expected_duration='1_to_3_months',
            experience_level='expert',
            status='open'
        )
        self.payment_record_1 = ProjectPaymentRecord.objects.create(
            project=self.project_1,
            total_budget=Decimal('45000.00'),
            amount_paid=Decimal('0.00'),
            status='pending'
        )

        self.project_2 = MarketplaceProject.objects.create(
            client=self.client_profile,
            title='React Native Mobile App for Delivery Tracking',
            description='Cross-platform app for delivery drivers with real-time GPS updates.',
            category='mobile_development',
            required_skills='React Native, TypeScript, Firebase',
            budget=Decimal('30000.00'),
            budget_type='fixed',
            expected_duration='1_to_4_weeks',
            experience_level='intermediate',
            status='open'
        )
        self.payment_record_2 = ProjectPaymentRecord.objects.create(
            project=self.project_2,
            total_budget=Decimal('30000.00'),
            amount_paid=Decimal('0.00'),
            status='pending'
        )

    # -------------------------------------------------------------------------
    # 1. Registration Tests
    # -------------------------------------------------------------------------
    def test_freelancer_registration_success(self):
        """Test registering a new Freelancer account."""
        response = self.client.post(reverse('freelancer:register'), {
            'full_name': 'Frank Fullstack',
            'email': 'frank@example.com',
            'phone': '+919876500000',
            'professional_title': 'Full Stack Cloud Engineer',
            'skills': 'Python, AWS, React',
            'experience': '4 years in SaaS',
            'hourly_rate': '1500',
            'bio': 'Passionate about scalable cloud architectures.',
            'password1': 'SecretPass123!',
            'password2': 'SecretPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('freelancer:dashboard'))

        # Check DB records
        user = User.objects.get(email='frank@example.com')
        self.assertEqual(user.profile.role, 'freelancer')
        self.assertTrue(hasattr(user, 'freelancer_profile'))
        self.assertEqual(user.freelancer_profile.full_name, 'Frank Fullstack')
        self.assertEqual(user.freelancer_profile.hourly_rate, Decimal('1500.00'))

    def test_freelancer_registration_duplicate_email_rejected(self):
        """Prevent registering with an existing email."""
        response = self.client.post(reverse('freelancer:register'), {
            'full_name': 'Dan Duplicate',
            'email': 'dan@example.com',  # existing email
            'password1': 'SecretPass123!',
            'password2': 'SecretPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'An account with this email already exists.')

    # -------------------------------------------------------------------------
    # 2. Login & Role-Based Routing
    # -------------------------------------------------------------------------
    def test_freelancer_login_redirects_to_freelancer_dashboard(self):
        """Logging in as Freelancer routes to /freelancer/dashboard/."""
        response = self.client.post(reverse('core:login'), {
            'username': 'freelancer_dan',
            'password': 'Password123!',
            'login_type': 'user'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('freelancer:dashboard'))

    def test_home_redirects_freelancer_to_freelancer_dashboard(self):
        """Visiting landing page when logged in as freelancer routes to freelancer dashboard."""
        self.client.login(username='freelancer_dan', password='Password123!')
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('freelancer:dashboard'))

    # -------------------------------------------------------------------------
    # 3. Freelancer Dashboard & Profile
    # -------------------------------------------------------------------------
    def test_freelancer_dashboard_view(self):
        """Freelancer dashboard renders metrics and open projects."""
        self.client.login(username='freelancer_dan', password='Password123!')
        response = self.client.get(reverse('freelancer:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dan Developer')
        self.assertContains(response, 'Available Projects')

    def test_freelancer_profile_view_and_edit(self):
        """View and edit freelancer profile."""
        self.client.login(username='freelancer_dan', password='Password123!')

        # View profile
        res_view = self.client.get(reverse('freelancer:profile_view'))
        self.assertEqual(res_view.status_code, 200)
        self.assertContains(res_view, 'Senior Python & Django Architect')

        # Edit profile
        res_edit = self.client.post(reverse('freelancer:profile_edit'), {
            'full_name': 'Dan Developer Updated',
            'professional_title': 'Principal AI & Cloud Engineer',
            'email': 'dan_updated@example.com',
            'phone': '+919999888877',
            'location': 'Hyderabad, India',
            'hourly_rate': '2500.00',
            'skills': 'Python, Django, FastAPI, PyTorch',
            'experience': '8+ years',
            'bio': 'Updated professional summary.',
        })
        self.assertEqual(res_edit.status_code, 302)

        # Verify update
        self.freelancer_profile_a.refresh_from_db()
        self.assertEqual(self.freelancer_profile_a.full_name, 'Dan Developer Updated')
        self.assertEqual(self.freelancer_profile_a.hourly_rate, Decimal('2500.00'))

    # -------------------------------------------------------------------------
    # 4. Find & Browse Projects (Search & Filters)
    # -------------------------------------------------------------------------
    def test_find_projects_search_and_filters(self):
        """Test searching and filtering open projects."""
        self.client.login(username='freelancer_dan', password='Password123!')

        # All open projects
        res = self.client.get(reverse('freelancer:find_projects'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'E-Commerce API')
        self.assertContains(res, 'React Native Mobile App')

        # Search query matching project 1
        res_search = self.client.get(reverse('freelancer:find_projects') + '?q=Django')
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'E-Commerce API')
        self.assertNotContains(res_search, 'React Native Mobile App')

        # Filter by Category
        res_cat = self.client.get(reverse('freelancer:find_projects') + '?category=mobile_development')
        self.assertContains(res_cat, 'React Native Mobile App')
        self.assertNotContains(res_cat, 'E-Commerce API')

        # Filter by Minimum Budget
        res_budget = self.client.get(reverse('freelancer:find_projects') + '?budget_min=40000')
        self.assertContains(res_budget, 'E-Commerce API')
        self.assertNotContains(res_budget, 'React Native Mobile App')

    # -------------------------------------------------------------------------
    # 5. Project Details & Client Contact Privacy
    # -------------------------------------------------------------------------
    def test_project_detail_sanitizes_client_private_info(self):
        """Unassigned freelancer sees company & public bio, but NOT private client email/phone."""
        self.client.login(username='freelancer_dan', password='Password123!')
        res = self.client.get(reverse('freelancer:project_detail', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Acme Global Corp')
        self.assertContains(res, 'E-Commerce API')
        # Private contact info must NOT be in public detail page before assignment
        self.assertNotContains(res, '+919876543210')
        self.assertNotContains(res, 'mailto:alice@example.com')

    # -------------------------------------------------------------------------
    # 6. Apply to Project & Duplicate Prevention
    # -------------------------------------------------------------------------
    def test_apply_to_project_and_prevent_duplicates(self):
        """Freelancer submits proposal; duplicate applications are rejected."""
        self.client.login(username='freelancer_dan', password='Password123!')

        # 1. Submit proposal
        res_apply = self.client.post(reverse('freelancer:project_apply', kwargs={'pk': self.project_1.pk}), {
            'proposed_price': '40000.00',
            'estimated_duration': '3 weeks',
            'proposal': 'I have 6+ years experience with Django, PostgreSQL, and scalable microservices.',
        })
        self.assertEqual(res_apply.status_code, 302)
        self.assertRedirects(res_apply, reverse('freelancer:my_applications'))

        # Check DB application record
        app = ProjectApplication.objects.filter(project=self.project_1, freelancer=self.freelancer_user_a).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, 'pending')
        self.assertEqual(app.proposed_price, Decimal('40000.00'))

        # 2. Attempt duplicate application
        res_dup = self.client.post(reverse('freelancer:project_apply', kwargs={'pk': self.project_1.pk}), {
            'proposed_price': '38000.00',
            'estimated_duration': '2 weeks',
            'proposal': 'Second proposal attempt.',
        })
        self.assertEqual(res_dup.status_code, 302)
        self.assertRedirects(res_dup, reverse('freelancer:my_applications'))
        # Count should still be 1
        self.assertEqual(ProjectApplication.objects.filter(project=self.project_1, freelancer=self.freelancer_user_a).count(), 1)

    def test_freelancer_cannot_apply_to_closed_project(self):
        """Prevent applying to closed or completed projects."""
        self.project_1.status = 'closed'
        self.project_1.save()

        self.client.login(username='freelancer_dan', password='Password123!')
        res = self.client.post(reverse('freelancer:project_apply', kwargs={'pk': self.project_1.pk}), {
            'proposed_price': '40000.00',
            'estimated_duration': '3 weeks',
            'proposal': 'Applying to closed project.',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ProjectApplication.objects.filter(project=self.project_1).count(), 0)

    # -------------------------------------------------------------------------
    # 7. My Applications & Withdraw
    # -------------------------------------------------------------------------
    def test_my_applications_and_withdraw(self):
        """Freelancer views application ledger and can withdraw pending proposal."""
        app = ProjectApplication.objects.create(
            project=self.project_1,
            freelancer=self.freelancer_user_a,
            proposal='Test application',
            proposed_price=Decimal('42000.00'),
            estimated_duration='2 weeks',
            status='pending'
        )

        self.client.login(username='freelancer_dan', password='Password123!')
        res = self.client.get(reverse('freelancer:my_applications'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'E-Commerce API')

        # Withdraw application
        res_withdraw = self.client.post(reverse('freelancer:application_withdraw', kwargs={'app_pk': app.pk}))
        self.assertEqual(res_withdraw.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, 'withdrawn')

    # -------------------------------------------------------------------------
    # 8. Complete Client ↔ Freelancer End-to-End Lifecycle Flow
    # -------------------------------------------------------------------------
    def test_complete_client_freelancer_lifecycle(self):
        """
        Full lifecycle test:
        1. Freelancer A applies to Project 1.
        2. Freelancer B applies to Project 1.
        3. Client reviews applications and accepts Freelancer A.
        4. Project 1 status becomes 'assigned', assigned_freelancer becomes Freelancer A.
        5. Freelancer B's application automatically becomes 'rejected'.
        6. Freelancer A logs in, sees accepted project, and opens workspace.
        7. Freelancer A views unlocked Client contact info (email & phone).
        8. Freelancer A updates progress to 60% (status shifts to 'in_progress').
        9. Freelancer A checks payment breakdown.
        """
        # Step 1: Freelancer A applies
        self.client.login(username='freelancer_dan', password='Password123!')
        self.client.post(reverse('freelancer:project_apply', kwargs={'pk': self.project_1.pk}), {
            'proposed_price': '40000.00',
            'estimated_duration': '3 weeks',
            'proposal': 'Dan proposal for backend.',
        })
        self.client.logout()

        # Step 2: Freelancer B applies
        self.client.login(username='freelancer_eva', password='Password123!')
        self.client.post(reverse('freelancer:project_apply', kwargs={'pk': self.project_1.pk}), {
            'proposed_price': '45000.00',
            'estimated_duration': '4 weeks',
            'proposal': 'Eva proposal for backend.',
        })
        self.client.logout()

        app_dan = ProjectApplication.objects.get(project=self.project_1, freelancer=self.freelancer_user_a)
        app_eva = ProjectApplication.objects.get(project=self.project_1, freelancer=self.freelancer_user_b)

        # Step 3: Client logs in & accepts Dan
        self.client.login(username='client_alice', password='Password123!')
        res_accept = self.client.post(reverse('marketplace:application_accept', kwargs={'app_pk': app_dan.pk}))
        self.assertEqual(res_accept.status_code, 302)
        self.client.logout()

        # Step 4 & 5: Verify DB State
        self.project_1.refresh_from_db()
        app_dan.refresh_from_db()
        app_eva.refresh_from_db()

        self.assertEqual(self.project_1.status, 'assigned')
        self.assertEqual(self.project_1.assigned_freelancer, self.freelancer_user_a)
        self.assertEqual(app_dan.status, 'accepted')
        self.assertEqual(app_eva.status, 'rejected')

        # Step 6: Freelancer A logs in, visits dashboard and workspace
        self.client.login(username='freelancer_dan', password='Password123!')
        res_dash = self.client.get(reverse('freelancer:dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, 'Active Projects')

        # Step 7: Workspace shows unlocked client contact details
        res_ws = self.client.get(reverse('freelancer:workspace', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(res_ws.status_code, 200)
        self.assertContains(res_ws, 'alice@example.com')
        self.assertContains(res_ws, '+919876543210')

        # Step 8: Update progress to 60%
        res_prog = self.client.post(reverse('freelancer:update_progress', kwargs={'pk': self.project_1.pk}), {
            'progress': '60',
        })
        self.assertEqual(res_prog.status_code, 302)
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.progress, 60)
        self.assertEqual(self.project_1.status, 'in_progress')

        # Step 9: Check payments view
        res_pay = self.client.get(reverse('freelancer:payments'))
        self.assertEqual(res_pay.status_code, 200)
        self.assertContains(res_pay, 'E-Commerce API')

    # -------------------------------------------------------------------------
    # 9. Data Isolation Tests (Freelancer A vs Freelancer B)
    # -------------------------------------------------------------------------
    def test_freelancer_data_isolation(self):
        """Freelancer B cannot access Freelancer A's workspace, applications, or private data."""
        # Assign project 1 to Freelancer A
        self.project_1.assigned_freelancer = self.freelancer_user_a
        self.project_1.status = 'assigned'
        self.project_1.save()

        app_dan = ProjectApplication.objects.create(
            project=self.project_1,
            freelancer=self.freelancer_user_a,
            proposal='Private Dan proposal',
            status='accepted'
        )

        # Log in as Freelancer B
        self.client.login(username='freelancer_eva', password='Password123!')

        # 1. Freelancer B cannot open Freelancer A's assigned workspace (returns 404)
        res_ws = self.client.get(reverse('freelancer:workspace', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(res_ws.status_code, 404)

        # 2. Freelancer B cannot update progress of Freelancer A's project
        res_update = self.client.post(reverse('freelancer:update_progress', kwargs={'pk': self.project_1.pk}), {'progress': '90'})
        self.assertEqual(res_update.status_code, 404)

        # 3. Freelancer B cannot withdraw Freelancer A's application
        res_with = self.client.post(reverse('freelancer:application_withdraw', kwargs={'app_pk': app_dan.pk}))
        self.assertEqual(res_with.status_code, 404)

    # -------------------------------------------------------------------------
    # 10. Support & Reporting
    # -------------------------------------------------------------------------
    def test_freelancer_support_report_creation(self):
        """Freelancer submits a report against a client issue."""
        self.client.login(username='freelancer_dan', password='Password123!')

        res = self.client.post(reverse('freelancer:support_create'), {
            'project': str(self.project_1.pk),
            'reported_client': str(self.client_profile.pk),
            'reason': 'scam',
            'description': 'Client requested work off-platform without milestone creation.',
        })
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse('freelancer:support_list'))

        report = FreelancerReport.objects.filter(freelancer=self.freelancer_profile_a).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.reason, 'scam')
        self.assertEqual(report.status, 'open')

    # -------------------------------------------------------------------------
    # 11. REST API v1 Tests
    # -------------------------------------------------------------------------
    def test_freelancer_api_authorization_and_security(self):
        """Verify API authentication, role check, and no password leaks."""
        # Unauthenticated request rejected with 403
        res_unauth = self.client.get(reverse('freelancer:api_dashboard_stats'))
        self.assertEqual(res_unauth.status_code, 403)

        # Client role accessing freelancer API rejected with 403
        self.client.login(username='client_alice', password='Password123!')
        res_client = self.client.get(reverse('freelancer:api_dashboard_stats'))
        self.assertEqual(res_client.status_code, 403)
        self.client.logout()

        # Freelancer role succeeds
        self.client.login(username='freelancer_dan', password='Password123!')
        res_api = self.client.get(reverse('freelancer:api_dashboard_stats'))
        self.assertEqual(res_api.status_code, 200)

        # Profile API does not expose password or sensitive secrets
        res_prof = self.client.get(reverse('freelancer:api_profile'))
        self.assertEqual(res_prof.status_code, 200)
        data = res_prof.json()
        self.assertNotIn('password', data)
        self.assertNotIn('password_hash', data)
        self.assertNotIn('secret_key', data)
        self.assertEqual(data['full_name'], 'Dan Developer')
