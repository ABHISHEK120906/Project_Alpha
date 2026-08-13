from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid
import os

ALLOWED_FILE_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.zip']
ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def validate_file_upload(file):
    if not file:
        return
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_FILE_EXTENSIONS)}")
    if getattr(file, 'size', 0) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds maximum limit of 10MB.")


def validate_image_upload(file):
    if not file:
        return
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Unsupported image extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    if getattr(file, 'size', 0) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"Image size exceeds maximum limit of 10MB.")


class Client(models.Model):
    """
    Client model for storing freelancer client information
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospective', 'Prospective'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=200)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return f"{self.name} ({self.company or 'Individual'})"
    
    def get_total_projects(self):
        return self.projects.filter(is_archived=False).count()
    
    def get_total_payments(self):
        return Payment.objects.filter(project__client=self).aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class Project(models.Model):
    """
    Project model for tracking freelancer projects
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.name} - {self.client.name}"
    
    def get_total_tasks(self):
        return self.tasks.filter(is_archived=False).count()
    
    def get_completed_tasks(self):
        return self.tasks.filter(status='completed', is_archived=False).count()
    
    def get_total_payments(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_pending_payments(self):
        return self.payments.filter(status='pending').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    def is_overdue(self):
        if self.deadline and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.deadline
        return False


class Payment(models.Model):
    """
    Payment model for tracking project payments
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    due_date = models.DateField(blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.project.name} - ${self.amount} ({self.status})"
    
    def is_overdue(self):
        if self.due_date and self.status == 'pending':
            return timezone.now().date() > self.due_date
        return False


class Task(models.Model):
    """
    Task model for tracking project tasks
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(blank=True, null=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False


class Note(models.Model):
    """
    Note model for project and client notes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_notes', 
                                 blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes', 
                               blank=True, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_related_object(self):
        """Return the related project or client"""
        if self.project:
            return self.project
        return self.client


class ActivityLog(models.Model):
    """
    Activity log model for tracking user actions
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
        ('status_change', 'Status Changed'),
        ('payment_received', 'Payment Received'),
        ('invoice_generated', 'Invoice Generated'),
        ('profile_updated', 'Profile Updated'),
        ('archive', 'Archived'),
        ('restore', 'Restored'),
    ]
    
    MODEL_CHOICES = [
        ('client', 'Client'),
        ('project', 'Project'),
        ('payment', 'Payment'),
        ('task', 'Task'),
        ('note', 'Note'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('invoice', 'Invoice'),
        ('file', 'File'),
        ('user', 'User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_type = models.CharField(max_length=20, choices=MODEL_CHOICES)
    model_id = models.UUIDField()
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} {self.model_type} ({self.timestamp})"


class UserProfile(models.Model):
    """
    Extended user profile for freelancers & super admins
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, validators=[validate_image_upload])
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated skills (e.g., Python, React, UI/UX)")
    experience = models.TextField(blank=True, null=True, help_text="Years or summary of experience")
    portfolio_website = models.URLField(blank=True, null=True)
    social_github = models.URLField(blank=True, null=True)
    social_linkedin = models.URLField(blank=True, null=True)
    social_twitter = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username} ({self.role})"


class ProjectFile(models.Model):
    """
    File Manager uploads for projects
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files', blank=True, null=True)
    file = models.FileField(upload_to='project_files/', validators=[validate_file_upload])
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0, help_text="Size in bytes")
    file_type = models.CharField(max_length=50, default='other')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.file_name


class ProjectComment(models.Model):
    """
    Internal notes/comments on a project
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_comments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.name}"


class Income(models.Model):
    """
    Income tracker for freelancer earnings
    """
    CATEGORY_CHOICES = [
        ('project', 'Project Work'),
        ('retainer', 'Monthly Retainer'),
        ('consulting', 'Consulting'),
        ('royalty', 'Royalties / Products'),
        ('other', 'Other Income'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    title = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, blank=True, null=True, related_name='incomes')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name='incomes')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='project')
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Income: {self.title} (${self.amount})"


class Expense(models.Model):
    """
    Expense tracker for business expenses
    """
    CATEGORY_CHOICES = [
        ('software', 'Software & SaaS'),
        ('hardware', 'Hardware & Equipment'),
        ('office', 'Office & Supplies'),
        ('subcontractor', 'Subcontractors / Freelancers'),
        ('marketing', 'Marketing & Ads'),
        ('travel', 'Travel & Meals'),
        ('tax', 'Taxes & Legal'),
        ('other', 'Other Expense'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='software')
    date = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True, validators=[validate_file_upload])
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Expense: {self.title} (${self.amount})"


class Invoice(models.Model):
    """
    Invoice management model
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name='invoices')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tax rate percentage (e.g. 10 for 10%)")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.name}"


class InvoiceItem(models.Model):
    """
    Line items for Invoices
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} (${self.amount})"


class CalendarEvent(models.Model):
    """
    Calendar deadlines, meetings, and personal reminders
    """
    EVENT_TYPE_CHOICES = [
        ('deadline', 'Project / Task Deadline'),
        ('meeting', 'Meeting'),
        ('payment', 'Payment Due Date'),
        ('reminder', 'Personal Reminder'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='reminder')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"


class Notification(models.Model):
    """
    User in-app notifications
    """
    TYPE_CHOICES = [
        ('deadline', 'Deadline Warning'),
        ('payment', 'Payment Reminder'),
        ('invoice', 'Invoice Notice'),
        ('task', 'Task Notice'),
        ('project', 'Project Update'),
        ('announcement', 'Announcement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='project')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class LoginHistory(models.Model):
    """
    Log of authentication attempts (successful & failed)
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='login_history')
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    device = models.CharField(max_length=50, default='Unknown')
    browser = models.CharField(max_length=50, default='Unknown')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Login History'
        verbose_name_plural = 'Login History Records'

    def __str__(self):
        return f"{self.username_attempted} - {self.status} ({self.timestamp})"


class BlockedIP(models.Model):
    """
    Blocked IP addresses list
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True, null=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Blocked IP: {self.ip_address}"


class SystemSetting(models.Model):
    """
    Dynamic system configuration settings managed by Super Admin
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"Setting: {self.key}"

    @classmethod
    def get_setting(cls, key, default=''):
        try:
            setting = cls.objects.get(key=key)
            return setting.value if setting.value is not None else default
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description=''):
        setting, created = cls.objects.get_or_create(key=key)
        setting.value = str(value)
        if description:
            setting.description = description
        setting.save()
        return setting


class RefundRequest(models.Model):
    """
    Refund requests for financial management
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refund_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund #{self.id} - ${self.amount} ({self.status})"


class Announcement(models.Model):
    """
    Super Admin announcements broadcast to platform users
    """
    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('selected', 'Selected Users'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_pinned = models.BooleanField(default=False)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    target_users = models.ManyToManyField(User, blank=True, related_name='user_announcements')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class EmailVerificationToken(models.Model):
    """
    Email verification token and OTP model for mandatory user account verification
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=100, unique=True, db_index=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Verification Token for {self.user.username} (Valid: {self.is_valid()})"


class ChatConversation(models.Model):
    """
    A single TrackBot chat session belonging to one user.
    Title is auto-generated from the first user message.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=200, default='New Conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Conversation'
        verbose_name_plural = 'Chat Conversations'

    def __str__(self):
        return f"{self.title} — {self.user.username}"


class ChatMessage(models.Model):
    """
    An individual message inside a ChatConversation.
    role is either 'user' or 'assistant'.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        ChatConversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
