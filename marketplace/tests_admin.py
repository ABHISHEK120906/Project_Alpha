"""
Comprehensive Unit, Security & Integration Tests for Marketplace Stage 3 (Admin Portal)
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json

from django.utils import timezone
from core.models import UserProfile, ActivityLog
from marketplace.models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
    MarketplaceDispute,
    PlatformSupportTicket,
    FreelancerVerification,
)


class MarketplaceAdminStage3Tests(TestCase):
    def setUp(self):
        self.client = TestClient()

        # 1. Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_super',
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin',
            is_verified=True
        )

        # 2. Staff / Regular Admin Role User
        self.staff_user = User.objects.create_user(
            username='admin_staff',
            email='staff@example.com',
            password='StaffPassword123!'
        )
        self.staff_profile = UserProfile.objects.create(
            user=self.staff_user,
            role='admin',
            is_verified=True
        )

        # 3. Client User (Alice)
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
            company_name='Acme Global',
            phone='+1234567890'
        )

        # 4. Freelancer User (Bob)
        self.freelancer_user = User.objects.create_user(
            username='freelancer_bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Builder'
        )
        self.freelancer_user_profile = UserProfile.objects.create(
            user=self.freelancer_user,
            role='freelancer',
            is_verified=True
        )
        self.freelancer_profile = FreelancerProfile.objects.create(
            user=self.freelancer_user,
            full_name='Bob Builder',
            professional_title='Senior Full-Stack Engineer',
            hourly_rate=Decimal('50.00'),
            skills='Python, Django, React, PostgreSQL',
            experience='5 years building scalable web systems',
            bio='Full-stack engineer specializing in web platforms.',
            portfolio_website='https://bob-builds.dev'
        )
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=self.freelancer_profile)
        ver.email_verified = True
        ver.phone_verified = True
        ver.identity_status = 'verified'
        ver.pan_status = 'verified'
        ver.pan_masked = 'XXXXXX1234'
        ver.payment_status = 'verified'
        ver.profile_status = 'complete'
        ver.admin_review_status = 'approved'
        ver.final_verification_status = 'verified'
        ver.verified_at = timezone.now()
        ver.save()

        # 5. Sample Project
        self.project = MarketplaceProject.objects.create(
            client=self.client_profile,
            title='E-Commerce Marketplace Build',
            description='Build a modern scalable web platform.',
            category='web_development',
            budget=Decimal('2500.00'),
            budget_type='fixed',
            status='open',
            progress=0
        )

        # 6. Sample Application
        self.application = ProjectApplication.objects.create(
            project=self.project,
            freelancer=self.freelancer_user,
            proposal='I have built dozens of Django marketplaces.',
            proposed_price=Decimal('2400.00'),
            status='pending'
        )

    # --------------------------------------------------------------------------
    # 1. Security & Role Boundary Enforcement Tests
    # --------------------------------------------------------------------------

    def test_admin_dashboard_accessible_by_admin(self):
        """Super Admin can access the admin dashboard."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Platform Administration")

    def test_admin_dashboard_accessible_by_admin_role(self):
        """User with profile role='admin' can access admin dashboard."""
        self.client.login(username='admin_staff', password='StaffPassword123!')
        response = self.client.get(reverse('marketplace_admin:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_access_admin_dashboard(self):
        """Client role is strictly rejected from accessing Admin Dashboard."""
        self.client.login(username='client_alice', password='Password123!')
        response = self.client.get(reverse('marketplace_admin:dashboard'))
        # Should redirect to forbidden or return 403
        self.assertEqual(response.status_code, 302)
        self.assertIn('/forbidden/', response.url)

    def test_freelancer_cannot_access_admin_dashboard(self):
        """Freelancer role is strictly rejected from accessing Admin Dashboard."""
        self.client.login(username='freelancer_bob', password='Password123!')
        response = self.client.get(reverse('marketplace_admin:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/forbidden/', response.url)

    def test_unauthenticated_user_redirected_to_login(self):
        """Anonymous user is redirected to login page."""
        response = self.client.get(reverse('marketplace_admin:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    # --------------------------------------------------------------------------
    # 2. User Management Tests
    # --------------------------------------------------------------------------

    def test_admin_users_list_and_filters(self):
        """Admin can list and filter users by role and status."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "client_alice")
        self.assertContains(response, "freelancer_bob")

        # Filter clients only
        response_client = self.client.get(reverse('marketplace_admin:users_list') + '?role=client')
        self.assertContains(response_client, "client_alice")

        # Filter freelancers only
        response_free = self.client.get(reverse('marketplace_admin:users_list') + '?role=freelancer')
        self.assertContains(response_free, "freelancer_bob")

    def test_admin_user_detail_inspection(self):
        """Admin can view detailed profile and history of a user."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:user_detail', kwargs={'user_id': self.freelancer_user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob Builder")
        self.assertContains(response, "Senior Full-Stack Engineer")

    def test_admin_toggle_user_suspension(self):
        """Admin can suspend and unsuspend a user account with audit logging."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        
        # Suspend user
        response = self.client.post(
            reverse('marketplace_admin:user_toggle_suspend', kwargs={'user_id': self.freelancer_user.id}),
            {'reason': 'Suspicious bidding pattern'}
        )
        self.assertEqual(response.status_code, 302)
        self.freelancer_user_profile.refresh_from_db()
        self.assertTrue(self.freelancer_user_profile.is_suspended)

        # Verify audit log
        log_entry = ActivityLog.objects.filter(model_type='user', model_id=self.freelancer_user.id).first()
        self.assertIsNotNone(log_entry)
        self.assertIn("Suspended user", log_entry.description)

        # Unsuspend user
        self.client.post(
            reverse('marketplace_admin:user_toggle_suspend', kwargs={'user_id': self.freelancer_user.id}),
            {'reason': 'Issue resolved with verification'}
        )
        self.freelancer_user_profile.refresh_from_db()
        self.assertFalse(self.freelancer_user_profile.is_suspended)

    # --------------------------------------------------------------------------
    # 3. Project Management & Moderation Tests
    # --------------------------------------------------------------------------

    def test_admin_projects_list_and_detail(self):
        """Admin can view all projects and inspect details."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:projects_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)

        detail_resp = self.client.get(reverse('marketplace_admin:project_detail', kwargs={'project_id': self.project.id}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "Moderate Project")

    def test_admin_moderate_and_close_project(self):
        """Admin can moderate and close an inappropriate project."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.post(
            reverse('marketplace_admin:project_detail', kwargs={'project_id': self.project.id}),
            {'moderation_action': 'close', 'reason': 'Terms of Service violation'}
        )
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    # --------------------------------------------------------------------------
    # 4. Application Monitoring Tests
    # --------------------------------------------------------------------------

    def test_admin_applications_list(self):
        """Admin can monitor all applications across projects."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:applications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "freelancer_bob")
        self.assertContains(response, "$2400.00")

    # --------------------------------------------------------------------------
    # 5. Report Management & Scam/Fraud Investigation Tests
    # --------------------------------------------------------------------------

    def test_admin_investigate_and_resolve_client_report(self):
        """Admin can review a client report and suspend the reported scam user."""
        report = ProjectReport.objects.create(
            reporter=self.client_profile,
            reported_user=self.freelancer_user,
            project=self.project,
            reason='scam',
            description='Freelancer requested payment outside platform.'
        )

        self.client.login(username='admin_super', password='AdminPassword123!')
        # View report list
        list_resp = self.client.get(reverse('marketplace_admin:reports_list'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Freelancer Scam")

        # Investigate detail
        detail_resp = self.client.get(reverse('marketplace_admin:report_detail', kwargs={'report_type': 'client', 'report_id': report.id}))
        self.assertEqual(detail_resp.status_code, 200)

        # Resolve with account suspension
        resolve_resp = self.client.post(
            reverse('marketplace_admin:report_detail', kwargs={'report_type': 'client', 'report_id': report.id}),
            {
                'status': 'resolved',
                'action_taken': 'account_suspended',
                'admin_notes': 'Confirmed off-platform solicitation violation.'
            }
        )
        self.assertEqual(resolve_resp.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, 'resolved')
        self.freelancer_user_profile.refresh_from_db()
        self.assertTrue(self.freelancer_user_profile.is_suspended)

    def test_admin_investigate_freelancer_report(self):
        """Admin can review a freelancer report against a client."""
        report = FreelancerReport.objects.create(
            freelancer=self.freelancer_profile,
            reported_client=self.client_profile,
            project=self.project,
            reason='non_payment',
            description='Client refusing to fund completed milestone.'
        )

        self.client.login(username='admin_super', password='AdminPassword123!')
        detail_resp = self.client.get(reverse('marketplace_admin:report_detail', kwargs={'report_type': 'freelancer', 'report_id': report.id}))
        self.assertEqual(detail_resp.status_code, 200)

        self.client.post(
            reverse('marketplace_admin:report_detail', kwargs={'report_type': 'freelancer', 'report_id': report.id}),
            {
                'status': 'resolved',
                'action_taken': 'no_action',
                'admin_notes': 'Mediated with client to release milestone.'
            }
        )
        report.refresh_from_db()
        self.assertEqual(report.status, 'resolved')

    # --------------------------------------------------------------------------
    # 6. Dispute Management Tests
    # --------------------------------------------------------------------------

    def test_admin_dispute_creation_and_resolution(self):
        """Admin can open, inspect, and arbitrate a dispute with a binding ruling."""
        self.client.login(username='admin_super', password='AdminPassword123!')

        # Open dispute
        create_resp = self.client.post(
            reverse('marketplace_admin:dispute_create'),
            {
                'project': str(self.project.id),
                'category': 'delivery',
                'title': 'Milestone 2 Deliverable Discrepancy',
                'description': 'Disagreement on acceptance criteria.',
                'evidence': 'GitHub commits and scope document.',
                'admin_notes': 'Reviewing submitted pull requests.'
            }
        )
        self.assertEqual(create_resp.status_code, 302)
        dispute = MarketplaceDispute.objects.filter(title='Milestone 2 Deliverable Discrepancy').first()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute.client, self.client_profile)

        # Inspect dispute
        detail_resp = self.client.get(reverse('marketplace_admin:dispute_detail', kwargs={'dispute_id': dispute.id}))
        self.assertEqual(detail_resp.status_code, 200)

        # Resolve dispute in favor of client
        resolve_resp = self.client.post(
            reverse('marketplace_admin:dispute_detail', kwargs={'dispute_id': dispute.id}),
            {
                'status': 'resolved',
                'resolution_type': 'favor_client',
                'resolution': 'Deliverables failed automated test suite; refund issued.',
                'admin_notes': 'Settled in client favor after technical review.'
            }
        )
        self.assertEqual(resolve_resp.status_code, 302)

        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'resolved')
        self.assertEqual(dispute.resolution_type, 'favor_client')
        self.assertEqual(dispute.resolved_by, self.admin_user)

    # --------------------------------------------------------------------------
    # 7. Support Desk Tests
    # --------------------------------------------------------------------------

    def test_admin_support_ticket_response(self):
        """Admin can view and respond to support tickets."""
        ticket = PlatformSupportTicket.objects.create(
            user=self.client_user,
            role='client',
            category='account_problem',
            subject='Unable to update company tax ID',
            message='I receive an error when submitting the form.'
        )

        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:support_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to update company tax ID")

        # Respond to ticket
        respond_resp = self.client.post(
            reverse('marketplace_admin:support_detail', kwargs={'ticket_id': ticket.id}),
            {
                'status': 'resolved',
                'admin_response': 'We have refreshed your account tax permissions. You can now update your ID.'
            }
        )
        self.assertEqual(respond_resp.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')
        self.assertEqual(ticket.assigned_admin, self.admin_user)

    # --------------------------------------------------------------------------
    # 8. Platform Analytics & Predictive Tests
    # --------------------------------------------------------------------------

    def test_admin_analytics_view(self):
        """Admin analytics view computes KPIs, category distributions, and risk insights."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Platform Analytics")
        self.assertIn('kpi', response.context)
        self.assertIn('risk_analysis', response.context)

    # --------------------------------------------------------------------------
    # 9. Multi-Format Exports Tests
    # --------------------------------------------------------------------------

    def test_admin_exports_csv_excel_pdf(self):
        """Admin can export platform summaries and entity reports in CSV, XLSX, and PDF."""
        self.client.login(username='admin_super', password='AdminPassword123!')

        # Summary Exports
        csv_resp = self.client.get(reverse('marketplace_admin:export_data', kwargs={'export_type': 'summary', 'export_format': 'csv'}))
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp['Content-Type'], 'text/csv')

        xlsx_resp = self.client.get(reverse('marketplace_admin:export_data', kwargs={'export_type': 'projects', 'export_format': 'xlsx'}))
        self.assertEqual(xlsx_resp.status_code, 200)
        self.assertIn('spreadsheetml', xlsx_resp['Content-Type'])

        pdf_resp = self.client.get(reverse('marketplace_admin:export_data', kwargs={'export_type': 'users', 'export_format': 'pdf'}))
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')

    # --------------------------------------------------------------------------
    # 10. REST API v1 (Admin) Tests
    # --------------------------------------------------------------------------

    def test_api_admin_dashboard_stats(self):
        """Admin REST API returns stats, and non-admins get 403."""
        self.client.login(username='admin_super', password='AdminPassword123!')
        response = self.client.get(reverse('marketplace_admin:api_dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('kpis', data)
        self.assertIn('trends', data)

        # Test unauthorized client call
        self.client.login(username='client_alice', password='Password123!')
        forbidden_resp = self.client.get(reverse('marketplace_admin:api_dashboard_stats'))
        self.assertEqual(forbidden_resp.status_code, 403)

    def test_api_admin_user_suspend_and_project_moderate(self):
        """Admin REST APIs support user suspension and project moderation."""
        self.client.login(username='admin_super', password='AdminPassword123!')

        # Suspend via API
        suspend_resp = self.client.post(
            reverse('marketplace_admin:api_user_suspend', kwargs={'user_id': self.freelancer_user.id}),
            json.dumps({'reason': 'Security violation'}),
            content_type='application/json'
        )
        self.assertEqual(suspend_resp.status_code, 200)
        self.freelancer_user_profile.refresh_from_db()
        self.assertTrue(self.freelancer_user_profile.is_suspended)

        # Moderate Project via API
        mod_resp = self.client.post(
            reverse('marketplace_admin:api_project_moderate', kwargs={'project_id': self.project.id}),
            json.dumps({'status': 'closed', 'reason': 'Moderator action'}),
            content_type='application/json'
        )
        self.assertEqual(mod_resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    # --------------------------------------------------------------------------
    # 11. Complete 3-Role End-to-End Integration Flow
    # --------------------------------------------------------------------------

    def test_complete_platform_3_role_workflow(self):
        """
        Comprehensive End-to-End Test across all 3 roles:
        1. Client posts project.
        2. Freelancer applies to project.
        3. Client accepts freelancer.
        4. Freelancer updates progress.
        5. Client reports issue.
        6. Admin reviews report, escalates to dispute, and resolves arbitration.
        """
        # Step 1: Client posts project
        self.client.login(username='client_alice', password='Password123!')
        post_resp = self.client.post(
            reverse('marketplace:project_post'),
            {
                'title': 'AI Automated Chatbot Build',
                'description': 'Develop an enterprise AI assistant.',
                'category': 'machine_learning',
                'budget': '5000.00',
                'budget_type': 'fixed',
                'experience_level': 'expert',
                'status': 'open',
            }
        )
        self.assertEqual(post_resp.status_code, 302)
        new_project = MarketplaceProject.objects.get(title='AI Automated Chatbot Build')
        self.assertEqual(new_project.status, 'open')

        # Step 2: Freelancer applies
        self.client.login(username='freelancer_bob', password='Password123!')
        apply_resp = self.client.post(
            reverse('freelancer:project_apply', kwargs={'pk': new_project.id}),
            {
                'proposal': 'Experienced AI developer ready to build.',
                'proposed_price': '4800.00',
                'estimated_duration': '2_to_4_weeks',
            }
        )
        self.assertEqual(apply_resp.status_code, 302)
        app = ProjectApplication.objects.get(project=new_project, freelancer=self.freelancer_user)
        self.assertEqual(app.status, 'pending')

        # Step 3: Client accepts freelancer
        self.client.login(username='client_alice', password='Password123!')
        accept_resp = self.client.post(reverse('marketplace:application_accept', kwargs={'app_pk': app.id}))
        self.assertEqual(accept_resp.status_code, 302)
        new_project.refresh_from_db()
        app.refresh_from_db()
        self.assertEqual(new_project.status, 'assigned')
        self.assertEqual(new_project.assigned_freelancer, self.freelancer_user)
        self.assertEqual(app.status, 'accepted')

        # Step 4: Freelancer updates progress
        self.client.login(username='freelancer_bob', password='Password123!')
        prog_resp = self.client.post(
            reverse('freelancer:update_progress', kwargs={'pk': new_project.id}),
            {'progress': 45}
        )
        self.assertEqual(prog_resp.status_code, 302)
        new_project.refresh_from_db()
        self.assertEqual(new_project.progress, 45)

        # Step 5: Client files report on non-performance
        self.client.login(username='client_alice', password='Password123!')
        report_resp = self.client.post(
            reverse('marketplace:client_support_create'),
            {
                'reported_user': str(self.freelancer_user.id),
                'project': str(new_project.id),
                'reason': 'non_performance',
                'description': 'Deliverable milestone is stuck at 45% with no communication.'
            }
        )
        self.assertEqual(report_resp.status_code, 302)
        report = ProjectReport.objects.filter(project=new_project).first()
        self.assertIsNotNone(report)

        # Step 6: Admin investigates, escalates to dispute and resolves
        self.client.login(username='admin_super', password='AdminPassword123!')
        
        # Escalate to dispute
        esc_resp = self.client.post(
            reverse('marketplace_admin:report_detail', kwargs={'report_type': 'client', 'report_id': report.id}),
            {
                'status': 'resolved',
                'action_taken': 'escalated_to_dispute',
                'admin_notes': 'Opening arbitration between Alice and Bob.'
            }
        )
        self.assertEqual(esc_resp.status_code, 302)
        
        dispute = MarketplaceDispute.objects.filter(project=new_project).first()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute.client, self.client_profile)
        self.assertEqual(dispute.freelancer, self.freelancer_profile)

        # Admin resolves dispute with settlement
        resolve_resp = self.client.post(
            reverse('marketplace_admin:dispute_detail', kwargs={'dispute_id': dispute.id}),
            {
                'status': 'resolved',
                'resolution_type': 'mutual_settlement',
                'resolution': 'Client agrees to release 45% partial milestone ($2,160) for completed work; remaining contract terminated cleanly.',
                'admin_notes': 'Both parties agreed to mutual split.'
            }
        )
        self.assertEqual(resolve_resp.status_code, 302)
        
        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'resolved')
        self.assertEqual(dispute.resolution_type, 'mutual_settlement')
        self.assertEqual(dispute.resolved_by, self.admin_user)
