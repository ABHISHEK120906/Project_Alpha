"""
social_auth/models.py

Three new models — purely additive, no changes to any existing table.

SocialAccount    — links a Django User to an OAuth provider identity
OAuthState       — short-lived CSRF state tokens for OAuth flows (auto-expired)
OAuthLoginHistory — audit log for every social-login attempt
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


PROVIDER_CHOICES = [
    ('google',    'Google'),
    ('github',    'GitHub'),
    ('linkedin',  'LinkedIn'),
    ('microsoft', 'Microsoft'),
    ('facebook',  'Facebook'),
    ('twitter',   'X (Twitter)'),
    # Future providers — add here without schema changes
    ('apple',     'Apple'),
    ('discord',   'Discord'),
    ('slack',     'Slack'),
    ('reddit',    'Reddit'),
    ('gitlab',    'GitLab'),
]


class SocialAccount(models.Model):
    """
    A record linking a Django User to a specific OAuth provider identity.
    One user can have many SocialAccount rows (one per provider).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_accounts',
    )
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(
        max_length=255,
        help_text='Unique user identifier returned by the OAuth provider',
    )

    # Profile data imported from provider
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    profile_photo_url = models.URLField(max_length=1024, blank=True, null=True)

    # Tokens (store as text; rotate on each login refresh)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)

    # Verification & status
    is_verified = models.BooleanField(
        default=False,
        help_text='True if provider confirmed this email as verified',
    )
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [('provider', 'provider_user_id')]
        ordering = ['-created_at']
        verbose_name = 'Social Account'
        verbose_name_plural = 'Social Accounts'

    def __str__(self):
        return f'{self.user.username} via {self.get_provider_display()}'

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])


class OAuthState(models.Model):
    """
    Short-lived record storing the random `state` parameter for CSRF protection
    and the PKCE `code_verifier` for providers that support it.
    Rows are cleaned up on callback or expiry (max 10 minutes).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    state = models.CharField(max_length=128, unique=True, db_index=True)
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)

    # PKCE support (RFC 7636)
    code_verifier = models.CharField(max_length=128, blank=True, null=True)

    # Where to redirect after successful OAuth
    next_url = models.CharField(max_length=512, default='/dashboard/')

    # Track session to prevent state theft across sessions
    session_key = models.CharField(max_length=40, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OAuth State Token'
        verbose_name_plural = 'OAuth State Tokens'

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f'OAuthState:{self.provider}:{self.state[:12]}…'


class OAuthLoginHistory(models.Model):
    """
    Audit log for every social-login attempt — success, failure, or cancellation.
    Linked to the LoginHistory model's pattern already used by core.
    """
    STATUS_CHOICES = [
        ('success',   'Success'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled (user denied)'),
        ('error',     'Provider Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='oauth_login_history',
    )
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')

    # Network details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)

    # Error tracking
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    # Was this a new account creation?
    is_new_account = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'OAuth Login History'
        verbose_name_plural = 'OAuth Login History Records'

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f'{user_str} — {self.get_provider_display()} ({self.status}) @ {self.timestamp:%Y-%m-%d %H:%M}'
