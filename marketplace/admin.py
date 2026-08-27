"""
Marketplace admin registration
"""
from django.contrib import admin
from .models import (
    ClientProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'company_name', 'location', 'created_at']
    search_fields = ['full_name', 'user__email', 'company_name']
    list_filter = ['created_at']
    raw_id_fields = ['user']


@admin.register(MarketplaceProject)
class MarketplaceProjectAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'client', 'category', 'budget', 'status',
        'application_count', 'deadline', 'created_at'
    ]
    list_filter = ['status', 'category', 'experience_level', 'budget_type']
    search_fields = ['title', 'client__full_name', 'description']
    raw_id_fields = ['client', 'assigned_freelancer']
    readonly_fields = ['created_at', 'updated_at']

    def application_count(self, obj):
        return obj.applications.count()
    application_count.short_description = 'Applications'


@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ['freelancer', 'project', 'proposed_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['freelancer__username', 'project__title']
    raw_id_fields = ['freelancer', 'project']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProjectPaymentRecord)
class ProjectPaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['project', 'total_budget', 'amount_paid', 'status', 'created_at']
    list_filter = ['status']
    raw_id_fields = ['project']


@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status']
    search_fields = ['reporter__full_name', 'description']
    raw_id_fields = ['reporter', 'reported_user', 'project']
    readonly_fields = ['created_at', 'updated_at']
