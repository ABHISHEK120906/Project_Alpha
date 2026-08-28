"""
Comprehensive Unit & Integration Tests for Freelancer Verification Module
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from core.models import UserProfile
from marketplace.models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    FreelancerVerification,
    is_freelancer_verified,
)
from marketplace.services_admin import AdminVerificationService


class FreelancerVerificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='freelancer_bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Builder'
        )
        self.up = UserProfile.objects.create(
            user=self.user,
            role='freelancer',
            is_verified=True
        )
        self.fp = FreelancerProfile.objects.create(
            user=self.user,
            full_name='Bob Builder',
            professional_title='Full-Stack Django Architect',
            skills='Python, Django, React, PostgreSQL',
            experience='5 years building scalable web applications',
            bio='Specialist in backend architecture and secure systems.',
            portfolio_website='https://bob-builds.dev',
        )

    def test_initial_verification_state(self):
        ver, created = FreelancerVerification.objects.get_or_create(freelancer_profile=self.fp)
        self.assertTrue(created)
        self.assertFalse(ver.is_fully_verified)
        self.assertEqual(ver.final_verification_status, 'not_verified')
        self.assertFalse(is_freelancer_verified(self.user))

    def test_profile_completion_calculation(self):
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=self.fp)
        score, missing = ver.calculate_profile_completion()
        # All 6 fields populated -> 100%
        self.assertEqual(score, 100)
        self.assertEqual(len(missing), 0)
        self.assertEqual(ver.profile_status, 'complete')

        # Incomplete profile test
        self.fp.portfolio_website = ''
        self.fp.bio = ''
        self.fp.save()
        score2, missing2 = ver.calculate_profile_completion()
        self.assertEqual(score2, 65)
        self.assertIn('Portfolio Website', missing2)
        self.assertIn('Professional Bio', missing2)
        self.assertEqual(ver.profile_status, 'incomplete')

    def test_full_verification_workflow_lifecycle(self):
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=self.fp)
        ver.calculate_profile_completion()
        self.assertEqual(ver.profile_status, 'complete')

        # 1. Email
        ver.email_verified = True
        ver.email_verified_at = timezone.now()

        # 2. Phone
        ver.phone_verified = True
        ver.phone_number = '+91 98765 43210'
        ver.phone_verified_at = timezone.now()

        # 3. Identity
        ver.identity_status = 'verified'
        ver.identity_type = 'Aadhaar / National ID'
        ver.identity_holder_name = 'Bob Builder'
        ver.identity_reference_id = 'ID-SEC-1234ABCD'
        ver.identity_verified_at = timezone.now()

        # 4. PAN (masked)
        ver.pan_status = 'verified'
        ver.pan_masked = 'XXXXXX1234'
        ver.pan_verified_at = timezone.now()

        # 5. Payment
        ver.payment_status = 'verified'
        ver.payment_account_type = 'Razorpay Verified'
        ver.payment_account_reference = 'acc_rzp_mock_1122'
        ver.payment_verified_at = timezone.now()

        # Status before admin review
        ver.update_verification_status()
        self.assertEqual(ver.final_verification_status, 'pending_admin_review')
        self.assertFalse(ver.is_fully_verified)
        self.assertFalse(is_freelancer_verified(self.user))

        # 6. Admin Approval via AdminVerificationService
        AdminVerificationService.approve_verification(ver, admin_user=None, notes="All credentials verified.")
        self.assertEqual(ver.admin_review_status, 'approved')
        self.assertEqual(ver.final_verification_status, 'verified')
        self.assertTrue(ver.is_fully_verified)
        self.assertTrue(is_freelancer_verified(self.user))

    def test_safe_summary_privacy_guarantee(self):
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=self.fp)
        ver.email_verified = True
        ver.phone_verified = True
        ver.identity_status = 'verified'
        ver.identity_type = 'Passport'
        ver.identity_reference_id = 'SECRET_PASSPORT_9988'
        ver.pan_status = 'verified'
        ver.pan_masked = 'XXXXXX5678'
        ver.payment_status = 'verified'
        ver.payment_account_reference = 'SECRET_BANK_ACC_00112233'
        ver.calculate_profile_completion()
        ver.admin_review_status = 'approved'
        ver.update_verification_status()
        ver.save()

        summary = ver.get_safe_summary()
        self.assertTrue(summary['is_verified'])
        self.assertEqual(summary['badge_text'], 'Verified Freelancer')
        self.assertTrue(summary['email_verified'])
        self.assertTrue(summary['identity_verified'])
        self.assertTrue(summary['payment_verified'])

        # Guarantee zero sensitive data in safe summary
        summary_str = str(summary)
        self.assertNotIn('SECRET_PASSPORT', summary_str)
        self.assertNotIn('SECRET_BANK_ACC', summary_str)
        self.assertNotIn('5678', summary_str)


class FreelancerVerificationViewsAndGatingTests(TestCase):
    def setUp(self):
        self.client = TestClient()

        # 1. Client User & Profile
        self.client_user = User.objects.create_user(
            username='client_carol',
            email='carol@enterprise.com',
            password='Password123!',
            first_name='Carol'
        )
        self.client_up = UserProfile.objects.create(
            user=self.client_user,
            role='client',
            is_verified=True
        )
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Carol Enterprise',
            company_name='Enterprise Global Corp'
        )

        # 2. Marketplace Project
        self.project = MarketplaceProject.objects.create(
            client=self.client_profile,
            title='Full-Stack Microservices Architecture',
            description='Design and implement distributed Django backend microservices.',
            budget=Decimal('50000.00'),
            status='open'
        )

        # 3. Freelancer User & Profile (Unverified initially)
        self.freelancer_user = User.objects.create_user(
            username='freelancer_dave',
            email='dave@code.dev',
            password='Password123!',
            first_name='Dave'
        )
        self.freelancer_up = UserProfile.objects.create(
            user=self.freelancer_user,
            role='freelancer',
            is_verified=True
        )
        self.freelancer_profile = FreelancerProfile.objects.create(
            user=self.freelancer_user,
            full_name='Dave Developer',
            professional_title='Backend Django Engineer',
            skills='Python, Django, PostgreSQL, Redis',
            experience='4 years',
            bio='Full-stack Python specialist',
            portfolio_website='https://dave-dev.io'
        )

    def test_unverified_freelancer_blocked_from_applying(self):
        """Unverified freelancer must be strictly blocked from submitting project proposals."""
        self.client.login(username='freelancer_dave', password='Password123!')
        
        # Verify not verified
        self.assertFalse(is_freelancer_verified(self.freelancer_user))

        # Attempt to apply to project
        apply_url = reverse('freelancer:project_apply', kwargs={'pk': self.project.pk})
        response = self.client.post(apply_url, {
            'proposed_price': '45000.00',
            'estimated_duration': '3 weeks',
            'proposal': 'I am highly experienced with Django microservices and would love to build this.'
        }, follow=True)

        # Must redirect to verification center
        self.assertRedirects(response, reverse('freelancer:verification_center'))
        # Must show blocking warning message
        self.assertContains(response, "You must complete Freelancer verification before applying to projects")
        # Ensure application was NOT created
        self.assertEqual(ProjectApplication.objects.filter(project=self.project, freelancer=self.freelancer_user).count(), 0)

    def test_complete_verification_workflow_and_apply_success(self):
        """Test step-by-step verification center completion and subsequent successful project application."""
        self.client.login(username='freelancer_dave', password='Password123!')

        # 1. Verification center loads
        center_url = reverse('freelancer:verification_center')
        res = self.client.get(center_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Freelancer Verification Center")

        # 2. Verify Email
        res_email = self.client.post(reverse('freelancer:verify_email'), {'otp_code': '123456'})
        self.assertEqual(res_email.status_code, 302)

        # 3. Verify Phone
        res_phone = self.client.post(reverse('freelancer:verify_phone'), {
            'phone_number': '+91 98765 43210',
            'otp_code': '654321'
        })
        self.assertEqual(res_phone.status_code, 302)

        # 4. Verify Identity
        res_id = self.client.post(reverse('freelancer:verify_identity'), {
            'identity_type': 'Aadhaar / National ID',
            'legal_name': 'Dave Developer',
            'id_number': '1234 5678 9012'
        })
        self.assertEqual(res_id.status_code, 302)

        # 5. Verify PAN
        res_pan = self.client.post(reverse('freelancer:verify_pan'), {
            'pan_number': 'ABCDE1234F'
        })
        self.assertEqual(res_pan.status_code, 302)

        # 6. Verify Payment Account
        res_pay = self.client.post(reverse('freelancer:verify_payment'), {
            'account_provider': 'razorpay',
            'account_holder_name': 'Dave Developer',
            'account_identifier': 'dave@okhdfcbank'
        })
        self.assertEqual(res_pay.status_code, 302)

        # 7. Submit for Admin Review
        res_sub = self.client.post(reverse('freelancer:verify_submit_admin'))
        self.assertEqual(res_sub.status_code, 302)

        # Verify state is pending_admin_review
        ver = FreelancerVerification.objects.get(freelancer_profile=self.freelancer_profile)
        self.assertEqual(ver.final_verification_status, 'pending_admin_review')

        # 8. Simulate Admin Approval
        res_app = self.client.post(reverse('freelancer:verify_simulate_approve'))
        self.assertEqual(res_app.status_code, 302)

        ver.refresh_from_db()
        self.assertTrue(ver.is_fully_verified)
        self.assertTrue(is_freelancer_verified(self.freelancer_user))

        # 9. Now apply to project — MUST SUCCEED
        apply_url = reverse('freelancer:project_apply', kwargs={'pk': self.project.pk})
        response = self.client.post(apply_url, {
            'proposed_price': '48000.00',
            'estimated_duration': '4 weeks',
            'proposal': 'Now fully verified! Here is my detailed architecture blueprint.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your application for")
        self.assertEqual(ProjectApplication.objects.filter(project=self.project, freelancer=self.freelancer_user).count(), 1)

    def test_client_application_view_displays_verified_status_without_sensitive_leak(self):
        """Client reviewing applications must see verification badge and safe checklist with zero sensitive leaks."""
        # 1. Verify freelancer
        ver, _ = FreelancerVerification.objects.get_or_create(freelancer_profile=self.freelancer_profile)
        ver.email_verified = True
        ver.phone_verified = True
        ver.phone_number = '+919988776655'
        ver.identity_status = 'verified'
        ver.identity_type = 'Aadhaar / National ID'
        ver.identity_reference_id = 'SECRET_AADHAAR_9999_8888'
        ver.pan_status = 'verified'
        ver.pan_masked = 'XXXXXX1234'
        ver.payment_status = 'verified'
        ver.payment_account_reference = 'SECRET_BANK_ACCOUNT_NUM_12345'
        ver.calculate_profile_completion()
        ver.admin_review_status = 'approved'
        ver.update_verification_status()
        ver.save()

        # 2. Create application
        app = ProjectApplication.objects.create(
            project=self.project,
            freelancer=self.freelancer_user,
            proposal='Proposal with high confidence and verified credentials.',
            proposed_price=Decimal('50000.00'),
            estimated_duration='3 weeks',
            status='pending'
        )

        # 3. Log in as Client
        self.client.login(username='client_carol', password='Password123!')
        app_list_url = reverse('marketplace:project_applications', kwargs={'pk': self.project.pk})
        response = self.client.get(app_list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Freelancer")
        self.assertContains(response, "View Verification")

        # Zero private leak checks
        content = response.content.decode('utf-8')
        self.assertNotIn('SECRET_AADHAAR', content)
        self.assertNotIn('SECRET_BANK_ACCOUNT_NUM', content)
        self.assertNotIn('9988776655', content)  # Raw unmasked phone

    def test_rest_api_verification_status_and_gating(self):
        """Test REST API verification status and gating enforcement."""
        self.client.login(username='freelancer_dave', password='Password123!')

        # 1. API Status check
        status_url = reverse('freelancer:api_verification_status')
        res = self.client.get(status_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('is_verified', res.data)
        self.assertFalse(res.data['is_verified'])

        # 2. API Apply when unverified -> 403 Forbidden
        apply_url = reverse('freelancer:api_apply', kwargs={'pk': self.project.pk})
        res_apply_blocked = self.client.post(apply_url, {
            'proposal': 'REST proposal attempt',
            'proposed_price': '40000.00'
        }, format='json')
        self.assertEqual(res_apply_blocked.status_code, 403)
        self.assertTrue(res_apply_blocked.data.get('verification_required'))

        # 3. API Step verification (e.g. Email)
        step_url = reverse('freelancer:api_verification_verify_step')
        res_step = self.client.post(step_url, {'step': 'email', 'otp': '123456'}, format='json')
        self.assertEqual(res_step.status_code, 200)
        self.assertIn('Email verified successfully', res_step.data.get('message', ''))
