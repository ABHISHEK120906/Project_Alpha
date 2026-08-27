"""
Marketplace serializers — used by Client API endpoints.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    ClientProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
)


class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'username', 'email', 'full_name', 'phone',
            'company_name', 'company_description', 'location', 'bio',
            'avatar_url', 'created_at',
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class ProjectApplicationSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.SerializerMethodField()
    freelancer_username = serializers.SerializerMethodField()

    class Meta:
        model = ProjectApplication
        fields = [
            'id', 'freelancer', 'freelancer_name', 'freelancer_username',
            'proposal', 'proposed_price', 'estimated_duration',
            'status', 'created_at',
        ]
        read_only_fields = ['id', 'freelancer', 'status', 'created_at']

    def get_freelancer_name(self, obj):
        profile = getattr(obj.freelancer, 'freelancer_profile', None)
        if profile:
            return profile.full_name
        return obj.freelancer.get_full_name() or obj.freelancer.username

    def get_freelancer_username(self, obj):
        return obj.freelancer.username


class MarketplaceProjectSerializer(serializers.ModelSerializer):
    application_count = serializers.IntegerField(read_only=True)
    pending_application_count = serializers.IntegerField(read_only=True)
    skills_list = serializers.ListField(read_only=True)
    client_name = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = MarketplaceProject
        fields = [
            'id', 'title', 'description', 'category', 'required_skills',
            'skills_list', 'budget', 'budget_type', 'expected_duration',
            'deadline', 'experience_level', 'status', 'progress',
            'assigned_freelancer', 'application_count',
            'pending_application_count', 'client_name',
            'is_overdue', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'application_count', 'pending_application_count',
            'skills_list', 'client_name', 'is_overdue',
            'created_at', 'updated_at',
        ]

    def get_client_name(self, obj):
        return obj.client.display_name


class ProjectPaymentRecordSerializer(serializers.ModelSerializer):
    amount_pending = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = ProjectPaymentRecord
        fields = [
            'id', 'project', 'project_title',
            'total_budget', 'amount_paid', 'amount_pending',
            'status', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'amount_pending', 'project_title', 'created_at']


class ProjectReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectReport
        fields = [
            'id', 'reported_user', 'project', 'reason',
            'description', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']
