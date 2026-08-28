"""
Marketplace models — Stage 1: Client Side

These models are ADDITIVE. No existing core models are modified or dropped.

Architecture:
  - ClientProfile    → extends User for marketplace Client role
  - MarketplaceProject → project posted by a Client seeking a Freelancer
  - ProjectApplication → Stage-2 ready stub for Freelancer applications
  - ProjectReport    → Client support/report records
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid
import os


def client_avatar_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'client_avatars/{instance.user.id}{ext}'


def freelancer_avatar_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'freelancer_avatars/{instance.user.id}{ext}'


def project_attachment_path(instance, filename):
    return f'project_attachments/{instance.id}/{filename}'


def project_message_attachment_path(instance, filename):
    return f'project_messages/{instance.project.id}/{filename}'


# ---------------------------------------------------------------------------
# ClientProfile
# ---------------------------------------------------------------------------

class ClientProfile(models.Model):
    """
    Marketplace Client account profile.
    One-to-one with Django's built-in User.
    Created automatically when a user registers as a Client.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    # Basic info
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    # Company / business info
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    # Location
    location = models.CharField(max_length=200, blank=True, null=True)
    # Personal description
    bio = models.TextField(blank=True, null=True)
    # Avatar
    avatar = models.ImageField(
        upload_to=client_avatar_path,
        blank=True,
        null=True,
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Profile'
        verbose_name_plural = 'Client Profiles'

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    @property
    def display_name(self):
        return self.full_name or self.user.username

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


# ---------------------------------------------------------------------------
# FreelancerProfile (Stage 2)
# ---------------------------------------------------------------------------

class FreelancerProfile(models.Model):
    """
    Marketplace Freelancer account profile.
    One-to-one with Django's built-in User.
    Created when a user registers as a Freelancer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='freelancer_profile'
    )
    # Basic info
    full_name = models.CharField(max_length=200)
    professional_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="e.g. Full-Stack Developer | Python & AI Specialist"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    # Professional skills & background
    skills = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated list of skills (e.g., Python, Django, React, PostgreSQL)"
    )
    experience = models.TextField(
        blank=True,
        null=True,
        help_text="Years of experience or background summary"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed summary of professional strengths and services"
    )
    # Portfolio & links
    portfolio_website = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    # Avatar
    avatar = models.ImageField(
        upload_to=freelancer_avatar_path,
        blank=True,
        null=True,
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Freelancer Profile'
        verbose_name_plural = 'Freelancer Profiles'

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    @property
    def display_name(self):
        return self.full_name or self.user.username

    @property
    def skills_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


# ---------------------------------------------------------------------------
# MarketplaceProject
# ---------------------------------------------------------------------------

class MarketplaceProject(models.Model):
    """
    A project posted by a Client to hire a Freelancer.
    Different from core.Project (which is the freelancer's own project tracker).
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('applications_received', 'Applications Received'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    BUDGET_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ]

    DURATION_CHOICES = [
        ('less_than_1_week', 'Less than 1 week'),
        ('1_to_4_weeks', '1 to 4 weeks'),
        ('1_to_3_months', '1 to 3 months'),
        ('3_to_6_months', '3 to 6 months'),
        ('more_than_6_months', 'More than 6 months'),
    ]

    CATEGORY_CHOICES = [
        ('web_development', 'Web Development'),
        ('mobile_development', 'Mobile Development'),
        ('ui_ux_design', 'UI/UX Design'),
        ('graphic_design', 'Graphic Design'),
        ('data_science', 'Data Science & Analytics'),
        ('machine_learning', 'Machine Learning / AI'),
        ('content_writing', 'Content Writing'),
        ('digital_marketing', 'Digital Marketing'),
        ('seo', 'SEO / SEM'),
        ('video_editing', 'Video Editing'),
        ('animation', 'Animation'),
        ('photography', 'Photography'),
        ('accounting', 'Accounting & Finance'),
        ('legal', 'Legal Services'),
        ('translation', 'Translation'),
        ('customer_support', 'Customer Support'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Owner
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    # Project info
    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='web_development'
    )
    required_skills = models.TextField(
        help_text="Comma-separated list of required skills",
        blank=True,
        null=True
    )

    # Budget
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    budget_type = models.CharField(
        max_length=20,
        choices=BUDGET_TYPE_CHOICES,
        default='fixed'
    )

    # Timeline
    expected_duration = models.CharField(
        max_length=30,
        choices=DURATION_CHOICES,
        blank=True,
        null=True
    )
    deadline = models.DateField(blank=True, null=True)

    # Experience
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        default='intermediate'
    )

    # Status & assignment
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='open'
    )

    # Assigned freelancer (set in Stage 2 when Client accepts)
    # FK to User — the freelancer's User account
    assigned_freelancer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_marketplace_projects'
    )

    # Progress (0–100)
    progress = models.IntegerField(default=0)

    # Attachments
    attachment = models.FileField(
        upload_to=project_attachment_path,
        blank=True,
        null=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Marketplace Project'
        verbose_name_plural = 'Marketplace Projects'

    def __str__(self):
        return f"{self.title} — {self.client.display_name}"

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def pending_application_count(self):
        return self.applications.filter(status='pending').count()

    @property
    def skills_list(self):
        if self.required_skills:
            return [s.strip() for s in self.required_skills.split(',') if s.strip()]
        return []

    def is_overdue(self):
        if self.deadline and self.status not in ['completed', 'closed']:
            return timezone.now().date() > self.deadline
        return False


# ---------------------------------------------------------------------------
# ProjectApplication  (Stage-2 ready stub)
# ---------------------------------------------------------------------------

class ProjectApplication(models.Model):
    """
    A Freelancer's application to a MarketplaceProject.
    The Freelancer UI is built in Stage 2, but this model is defined here
    so the Client can already read / accept / reject applications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        MarketplaceProject,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    # Freelancer's User account (Stage 2 will have a FreelancerProfile)
    freelancer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_applications'
    )

    # Application details
    proposal = models.TextField(help_text="Cover letter / proposal from freelancer")
    proposed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    estimated_duration = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Client notes (internal, not shown to freelancer)
    client_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('project', 'freelancer')]  # one application per project
        verbose_name = 'Project Application'
        verbose_name_plural = 'Project Applications'

    def __str__(self):
        return f"{self.freelancer.username} → {self.project.title} ({self.status})"


# ---------------------------------------------------------------------------
# ProjectPaymentRecord
# ---------------------------------------------------------------------------

class ProjectPaymentRecord(models.Model):
    """
    Tracks payment milestones for a marketplace project.
    Not a real payment gateway — records payment status for dashboard display.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        MarketplaceProject,
        on_delete=models.CASCADE,
        related_name='payment_record'
    )
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project Payment Record'
        verbose_name_plural = 'Project Payment Records'

    def __str__(self):
        return f"Payment for {self.project.title} — {self.status}"

    @property
    def amount_pending(self):
        return self.total_budget - self.amount_paid


# ---------------------------------------------------------------------------
# ProjectReport (Support)
# ---------------------------------------------------------------------------

class ProjectReport(models.Model):
    """
    Client support / report ticket.
    Client can report a freelancer or a general issue.
    Admin handling implemented in Stage 3.
    """
    REASON_CHOICES = [
        ('scam', 'Freelancer Scam'),
        ('non_performance', 'Non-Performance / Abandonment'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('abuse', 'Abuse / Harassment'),
        ('payment_issue', 'Payment Issue'),
        ('quality_issue', 'Quality / Deliverable Issue'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='reports_filed'
    )
    # The reported freelancer (nullable — might be a platform issue, not freelancer)
    reported_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_against'
    )
    project = models.ForeignKey(
        MarketplaceProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports'
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_notes = models.TextField(blank=True, null=True)  # Stage 3
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project Report'
        verbose_name_plural = 'Project Reports'

    def __str__(self):
        return f"Report #{str(self.id)[:8]} — {self.reason} ({self.status})"


# ---------------------------------------------------------------------------
# FreelancerReport (Freelancer Support)
# ---------------------------------------------------------------------------

class FreelancerReport(models.Model):
    """
    Freelancer support / report ticket.
    Freelancer can report a client scam, non-payment, misleading project, abuse, or general issue.
    Admin handling implemented in Stage 3.
    """
    REASON_CHOICES = [
        ('scam', 'Client Scam'),
        ('non_payment', 'Non-Payment / Milestone Issue'),
        ('misleading_project', 'Misleading Project / Scope Creep'),
        ('abuse', 'Abuse / Harassment'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('other', 'Other Issue'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='reports_filed'
    )
    reported_client = models.ForeignKey(
        ClientProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_received'
    )
    project = models.ForeignKey(
        MarketplaceProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='freelancer_reports'
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Freelancer Report'
        verbose_name_plural = 'Freelancer Reports'

    def __str__(self):
        return f"Freelancer Report #{str(self.id)[:8]} — {self.reason} ({self.status})"


# ---------------------------------------------------------------------------
# MarketplaceDispute (Stage 3: Dispute Management)
# ---------------------------------------------------------------------------

class MarketplaceDispute(models.Model):
    """
    Dedicated Dispute model for arbitration between Clients and Freelancers.
    Admin investigates project status, payments, messages, evidence, and records resolution.
    """
    CATEGORY_CHOICES = [
        ('payment', 'Payment & Milestones'),
        ('delivery', 'Non-Performance & Delivery Failure'),
        ('quality', 'Scope & Quality Discrepancy'),
        ('communication', 'Unresponsive / Abandonment'),
        ('terms_breach', 'Terms & Policy Breach'),
        ('scam', 'Suspected Fraud / Scam'),
        ('other', 'Other Dispute'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_investigation', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    RESOLUTION_CHOICES = [
        ('pending', 'Pending Resolution'),
        ('favor_client', 'Resolved in Favor of Client (Refund Recommended)'),
        ('favor_freelancer', 'Resolved in Favor of Freelancer (Payment Release)'),
        ('mutual_settlement', 'Mutual Settlement / Partial Split'),
        ('dismissed', 'Dismissed / No Action Required'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        MarketplaceProject,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    opened_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='marketplace_disputes_opened'
    )
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputes'
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='delivery')
    title = models.CharField(max_length=255)
    description = models.TextField()
    evidence = models.TextField(blank=True, null=True, help_text="Links, logs, or detailed evidence statements")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    resolution_type = models.CharField(max_length=30, choices=RESOLUTION_CHOICES, default='pending')
    resolution = models.TextField(blank=True, null=True, help_text="Final verdict and resolution rationale")
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_marketplace_disputes'
    )
    admin_notes = models.TextField(blank=True, null=True, help_text="Confidential administrative notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Marketplace Dispute'
        verbose_name_plural = 'Marketplace Disputes'

    def __str__(self):
        return f"Dispute #{str(self.id)[:8]} — {self.title} ({self.status})"


# ---------------------------------------------------------------------------
# PlatformSupportTicket (Stage 3: Support Desk)
# ---------------------------------------------------------------------------

class PlatformSupportTicket(models.Model):
    """
    General platform support ticket submitted by Clients or Freelancers.
    """
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('freelancer', 'Freelancer'),
        ('other', 'Other / General User'),
    ]

    CATEGORY_CHOICES = [
        ('account_problem', 'Account & Authentication Problem'),
        ('project_problem', 'Project & Workspace Issue'),
        ('payment_problem', 'Payment & Milestone Issue'),
        ('scam_report', 'Scam / Security Alert'),
        ('technical_issue', 'Technical Issue / Bug'),
        ('other', 'Other Support Request'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='marketplace_support_tickets'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_response = models.TextField(blank=True, null=True)
    assigned_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_support_tickets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Platform Support Ticket'
        verbose_name_plural = 'Platform Support Tickets'

    def __str__(self):
        return f"Support Ticket #{str(self.id)[:8]} — {self.subject} ({self.status})"


# ---------------------------------------------------------------------------
# FreelancerVerification (Freelancer Verification Module)
# ---------------------------------------------------------------------------

class FreelancerVerification(models.Model):
    """
    Tracks multi-step security and professional verification for a Freelancer.
    Required steps before applying to projects:
      1. Email Verification
      2. Phone / Mobile Verification
      3. Identity Verification
      4. PAN Verification
      5. Payment Account Verification (Razorpay / Bank KYC signal)
      6. Professional Profile Verification (completion >= 80% & all core fields)
      7. Admin Review & Approval
    """
    IDENTITY_STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    PAN_STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    PROFILE_STATUS_CHOICES = [
        ('incomplete', 'Incomplete'),
        ('complete', 'Complete'),
    ]

    ADMIN_REVIEW_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    FINAL_STATUS_CHOICES = [
        ('not_verified', 'Not Verified'),
        ('pending_admin_review', 'Pending Admin Review'),
        ('verified', 'Verified Freelancer'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.OneToOneField(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    # 1. Email Verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # 2. Phone Verification
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # 3. Identity Verification
    identity_status = models.CharField(
        max_length=20,
        choices=IDENTITY_STATUS_CHOICES,
        default='not_submitted'
    )
    identity_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. Aadhaar / National ID, Passport, Voter ID, Driver License"
    )
    identity_holder_name = models.CharField(max_length=200, blank=True, null=True)
    identity_reference_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Secure simulation/reference token (no raw IDs stored publicly)"
    )
    identity_verified_at = models.DateTimeField(null=True, blank=True)

    # 4. PAN Verification
    pan_status = models.CharField(
        max_length=20,
        choices=PAN_STATUS_CHOICES,
        default='not_submitted'
    )
    pan_masked = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Masked PAN e.g. XXXXXX1234 (never full PAN publicly)"
    )
    pan_verified_at = models.DateTimeField(null=True, blank=True)

    # 5. Payment Account Verification (Razorpay / Bank KYC simulation)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_submitted'
    )
    payment_account_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. Razorpay Route Verified, UPI KYC Linked, Bank Account Verified"
    )
    payment_account_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Safe masked reference token"
    )
    payment_verified_at = models.DateTimeField(null=True, blank=True)

    # 6. Professional Profile Verification
    profile_completion_percentage = models.IntegerField(default=0)
    profile_status = models.CharField(
        max_length=20,
        choices=PROFILE_STATUS_CHOICES,
        default='incomplete'
    )

    # 7. Admin Review & Approval
    admin_review_status = models.CharField(
        max_length=20,
        choices=ADMIN_REVIEW_CHOICES,
        default='pending'
    )
    admin_review_notes = models.TextField(blank=True, null=True)
    admin_reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_freelancer_verifications'
    )

    # Final Overall Verification Status
    final_verification_status = models.CharField(
        max_length=30,
        choices=FINAL_STATUS_CHOICES,
        default='not_verified'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Freelancer Verification'
        verbose_name_plural = 'Freelancer Verifications'

    def __str__(self):
        return f"{self.freelancer_profile.full_name} — {self.get_final_verification_status_display()}"

    def calculate_profile_completion(self):
        """
        Calculates profile completion percentage and checks if required profile fields are present.
        Required:
          - full_name (15%)
          - professional_title (15%)
          - skills (20%)
          - experience (15%)
          - bio (20%)
          - portfolio_website (15%)
        """
        fp = self.freelancer_profile
        score = 0
        missing = []

        if fp.full_name and fp.full_name.strip():
            score += 15
        else:
            missing.append('Full Legal / Professional Name')

        if fp.professional_title and fp.professional_title.strip():
            score += 15
        else:
            missing.append('Professional Title')

        if fp.skills and fp.skills.strip():
            score += 20
        else:
            missing.append('Skills List')

        if fp.experience and fp.experience.strip():
            score += 15
        else:
            missing.append('Experience / Background')

        if fp.bio and fp.bio.strip():
            score += 20
        else:
            missing.append('Professional Bio')

        if fp.portfolio_website and fp.portfolio_website.strip():
            score += 15
        else:
            missing.append('Portfolio Website')

        self.profile_completion_percentage = min(100, score)
        self.profile_status = 'complete' if (score >= 80 and len(missing) == 0) else 'incomplete'
        return score, missing

    def update_verification_status(self):
        """
        Evaluates the status across all 6 prerequisites and admin approval:
        1. Email
        2. Phone
        3. Identity
        4. PAN
        5. Payment
        6. Profile
        7. Admin Approval
        """
        self.calculate_profile_completion()

        prereqs_met = (
            self.email_verified and
            self.phone_verified and
            self.identity_status == 'verified' and
            self.pan_status == 'verified' and
            self.payment_status == 'verified' and
            self.profile_status == 'complete'
        )

        if self.admin_review_status == 'suspended':
            self.final_verification_status = 'suspended'
        elif self.admin_review_status == 'rejected' or self.identity_status == 'rejected' or self.pan_status == 'rejected' or self.payment_status == 'rejected':
            self.final_verification_status = 'rejected'
        elif prereqs_met and self.admin_review_status == 'approved':
            self.final_verification_status = 'verified'
            if not self.verified_at:
                self.verified_at = timezone.now()
        elif prereqs_met:
            self.final_verification_status = 'pending_admin_review'
        else:
            self.final_verification_status = 'not_verified'

        return self.final_verification_status

    @property
    def is_fully_verified(self):
        return (
            self.final_verification_status == 'verified' and
            self.admin_review_status == 'approved' and
            self.email_verified and
            self.phone_verified and
            self.identity_status == 'verified' and
            self.pan_status == 'verified' and
            self.payment_status == 'verified' and
            self.profile_status == 'complete'
        )

    def get_completed_steps_count(self):
        count = 0
        if self.email_verified: count += 1
        if self.phone_verified: count += 1
        if self.identity_status == 'verified': count += 1
        if self.pan_status == 'verified': count += 1
        if self.payment_status == 'verified': count += 1
        if self.profile_status == 'complete': count += 1
        if self.admin_review_status == 'approved': count += 1
        return count

    def get_safe_summary(self):
        """
        Returns client-safe summary dictionary with NO sensitive information.
        Excludes PAN, Aadhaar/ID refs, payment credentials, etc.
        """
        return {
            'is_verified': self.is_fully_verified,
            'status': self.final_verification_status,
            'status_display': self.get_final_verification_status_display(),
            'badge_text': 'Verified Freelancer' if self.is_fully_verified else (
                'Verification Pending' if self.final_verification_status == 'pending_admin_review' else 'Not Verified'
            ),
            'email_verified': bool(self.email_verified),
            'phone_verified': bool(self.phone_verified),
            'identity_verified': self.identity_status == 'verified',
            'pan_verified': self.pan_status == 'verified',
            'payment_verified': self.payment_status == 'verified',
            'profile_verified': self.profile_status == 'complete',
            'admin_approved': self.admin_review_status == 'approved',
            'verified_at': self.verified_at.strftime('%d/%m/%Y') if self.verified_at else None,
            'steps_completed': self.get_completed_steps_count(),
            'total_steps': 7,
        }


def is_freelancer_verified(user):
    """
    Central backend check: returns True if user is a verified Freelancer eligible to apply to projects.
    """
    if not user or not user.is_authenticated:
        return False
    try:
        fp = user.freelancer_profile
    except Exception:
        return False
    try:
        ver = fp.verification
        return ver.is_fully_verified
    except FreelancerVerification.DoesNotExist:
        return False



