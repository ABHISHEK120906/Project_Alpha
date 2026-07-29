"""
FreelanceTrack — DRF Serializers
Ensures outgoing responses are strictly typed, sanitized, and contain only required data.
"""

from rest_framework import serializers
from .models import Client, Project, Payment, Task, Note, ActivityLog


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'company', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client', 'client_name', 'description', 
            'status', 'status_display', 'priority', 'priority_display',
            'start_date', 'deadline', 'budget', 'progress', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'project', 'project_name', 'amount', 'status',
            'status_display', 'payment_method', 'due_date', 'paid_date',
            'invoice_number', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'project', 'project_name', 'description',
            'status', 'status_display', 'priority', 'due_date',
            'estimated_hours', 'actual_hours', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'project', 'client',
            'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Strips sensitive IP addresses from user-facing activity log responses."""
    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'model_type', 'model_id', 'description', 'timestamp']
        read_only_fields = ['id', 'action', 'model_type', 'model_id', 'description', 'timestamp']


class DashboardStatsSerializer(serializers.Serializer):
    """Aggregated Dashboard statistics payload for API responses."""
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_projects_count = serializers.IntegerField()
    total_clients_count = serializers.IntegerField()
    pending_tasks_count = serializers.IntegerField()
    monthly_earnings = serializers.ListField(child=serializers.DictField())
    status_distribution = serializers.DictField()
    recent_projects = ProjectSerializer(many=True)
