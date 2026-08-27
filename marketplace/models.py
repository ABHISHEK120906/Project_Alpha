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


def project_attachment_path(instance, filename):
    return f'project_attachments/{instance.id}/{filename}'


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
