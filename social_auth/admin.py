"""
social_auth/admin.py

Django admin registration for social auth models.
Provides provider breakdown stats, login history, and error tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from .models import SocialAccount, OAuthState, OAuthLoginHistory


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'provider_badge', 'email', 'full_name',
        'is_verified', 'is_active', 'last_login', 'created_at',
    ]
    list_filter = ['provider', 'is_verified', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'email', 'full_name', 'provider_user_id']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_login',
        'avatar_preview',
    ]
    raw_id_fields = ['user']
    ordering = ['-created_at']

    fieldsets = (
        ('User & Provider', {
            'fields': ('user', 'provider', 'provider_user_id', 'is_active')
        }),
        ('Profile Data', {
            'fields': ('full_name', 'email', 'profile_photo_url', 'avatar_preview', 'is_verified')
        }),
        ('Tokens', {
            'fields': ('access_token', 'refresh_token', 'token_expires_at'),
            'classes': ('collapse',),
            'description': '⚠ Tokens are sensitive — handle with care.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def provider_badge(self, obj):
        colors = {
            'google': '#4285F4',
            'github': '#24292f',
            'linkedin': '#0a66c2',
            'microsoft': '#0078d4',
            'facebook': '#1877f2',
            'twitter': '#000000',
        }
        color = colors.get(obj.provider, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_provider_display(),
        )
    provider_badge.short_description = 'Provider'

    def avatar_preview(self, obj):
        if obj.profile_photo_url:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;" />',
                obj.profile_photo_url,
            )
        return '—'
    avatar_preview.short_description = 'Avatar'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def has_add_permission(self, request):
        return False  # Social accounts are created programmatically only


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ['state_short', 'provider', 'created_at', 'expires_at', 'is_valid_display']
    list_filter = ['provider', 'created_at']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    def state_short(self, obj):
        return obj.state[:16] + '…'
    state_short.short_description = 'State Token'

    def is_valid_display(self, obj):
        valid = obj.is_valid()
        icon = '✅' if valid else '❌'
        return format_html('{} {}', icon, 'Valid' if valid else 'Expired')
    is_valid_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(OAuthLoginHistory)
class OAuthLoginHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'provider_badge', 'status_badge',
        'ip_address', 'is_new_account', 'timestamp',
    ]
    list_filter = ['provider', 'status', 'is_new_account', 'timestamp']
    search_fields = ['user__username', 'ip_address', 'error_message']
    readonly_fields = ['id', 'timestamp']
    raw_id_fields = ['user']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Event Details', {
            'fields': ('user', 'provider', 'status', 'is_new_account')
        }),
        ('Network', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Error Info', {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def provider_badge(self, obj):
        colors = {
            'google': '#4285F4', 'github': '#24292f',
            'linkedin': '#0a66c2', 'microsoft': '#0078d4',
            'facebook': '#1877f2', 'twitter': '#000000',
        }
        color = colors.get(obj.provider, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 7px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_provider_display(),
        )
    provider_badge.short_description = 'Provider'

    def status_badge(self, obj):
        styles = {
            'success':   ('background:#d4edda;color:#155724', '✅'),
            'failed':    ('background:#f8d7da;color:#721c24', '❌'),
            'cancelled': ('background:#fff3cd;color:#856404', '⚠️'),
            'error':     ('background:#f8d7da;color:#721c24', '🔥'),
        }
        style, icon = styles.get(obj.status, ('background:#e2e3e5;color:#383d41', 'ℹ️'))
        return format_html(
            '<span style="{};padding:2px 8px;border-radius:4px;font-size:11px;">{} {}</span>',
            style, icon, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
