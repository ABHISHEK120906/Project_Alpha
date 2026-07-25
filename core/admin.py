from django.contrib import admin
from .models import Client, Project, Payment, Task, Note, ActivityLog


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'company']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Additional Details', {
            'fields': ('address', 'status', 'notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'status', 'priority', 'progress', 'deadline', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['name', 'client__name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'client', 'description')
        }),
        ('Project Details', {
            'fields': ('status', 'priority', 'progress')
        }),
        ('Dates & Budget', {
            'fields': ('start_date', 'deadline', 'budget')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['project', 'amount', 'status', 'payment_method', 'due_date', 'paid_date']
    list_filter = ['status', 'payment_method', 'due_date']
    search_fields = ['project__name', 'invoice_number', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('project', 'amount', 'status', 'payment_method')
        }),
        ('Dates & Details', {
            'fields': ('due_date', 'paid_date', 'invoice_number', 'description')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'project__name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'project', 'description')
        }),
        ('Task Details', {
            'fields': ('status', 'priority', 'due_date')
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'get_related_object', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_related_object(self, obj):
        if obj.project:
            return f"Project: {obj.project.name}"
        elif obj.client:
            return f"Client: {obj.client.name}"
        return "N/A"
    get_related_object.short_description = 'Related To'
    
    fieldsets = (
        ('Note Information', {
            'fields': ('title', 'content', 'is_private')
        }),
        ('Related Objects', {
            'fields': ('project', 'client')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_type', 'description', 'timestamp']
    list_filter = ['action', 'model_type', 'timestamp']
    search_fields = ['user__username', 'description']
    readonly_fields = ['id', 'timestamp']
    
    def has_add_permission(self, request):
        return False  # Prevent manual addition of activity logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing of activity logs
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'action', 'model_type', 'model_id', 'description')
        }),
        ('Technical Details', {
            'fields': ('timestamp', 'ip_address')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
