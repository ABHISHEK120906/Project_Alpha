"""
Admin DRF Serializers for Platform Administration & Moderation (Stage 3)
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import UserProfile
from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
    MarketplaceDispute,
    PlatformSupportTicket,
)


class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    is_suspended = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    total_projects = serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'display_name',
            'role', 'is_active', 'is_suspended', 'is_verified', 'date_joined',
            'last_login', 'total_projects', 'total_applications'
        ]

    def get_role(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.role if profile else 'user'

    def get_is_suspended(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.is_suspended if profile else False

    def get_is_verified(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.is_verified if profile else True

    def get_display_name(self, obj):
        if hasattr(obj, 'client_profile'):
            return obj.client_profile.full_name
        if hasattr(obj, 'freelancer_profile'):
            return obj.freelancer_profile.full_name
        return obj.get_full_name() or obj.username

    def get_total_projects(self, obj):
        if hasattr(obj, 'client_profile'):
            return obj.client_profile.projects.count()
        return obj.assigned_marketplace_projects.count()

    def get_total_applications(self, obj):
        return obj.project_applications.count()


class AdminMarketplaceProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.display_name', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    freelancer_name = serializers.SerializerMethodField()
    freelancer_email = serializers.SerializerMethodField()
    application_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MarketplaceProject
        fields = [
            'id', 'title', 'description', 'category', 'required_skills',
            'budget', 'budget_type', 'expected_duration', 'deadline',
            'experience_level', 'status', 'progress', 'client', 'client_name',
            'client_email', 'assigned_freelancer', 'freelancer_name',
            'freelancer_email', 'application_count', 'created_at', 'updated_at'
        ]

    def get_freelancer_name(self, obj):
        if obj.assigned_freelancer:
            profile = getattr(obj.assigned_freelancer, 'freelancer_profile', None)
            return profile.full_name if profile else obj.assigned_freelancer.username
        return None

    def get_freelancer_email(self, obj):
        return obj.assigned_freelancer.email if obj.assigned_freelancer else None


class AdminProjectApplicationSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)
    client_name = serializers.CharField(source='project.client.display_name', read_only=True)
    freelancer_name = serializers.SerializerMethodField()
    freelancer_email = serializers.EmailField(source='freelancer.email', read_only=True)

    class Meta:
        model = ProjectApplication
        fields = [
            'id', 'project', 'project_title', 'client_name', 'freelancer',
            'freelancer_name', 'freelancer_email', 'proposal', 'proposed_price',
            'estimated_duration', 'status', 'created_at', 'updated_at'
        ]

    def get_freelancer_name(self, obj):
        profile = getattr(obj.freelancer, 'freelancer_profile', None)
        return profile.full_name if profile else obj.freelancer.username


class AdminProjectReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='reporter.display_name', read_only=True)
    reporter_email = serializers.EmailField(source='reporter.user.email', read_only=True)
    reported_username = serializers.CharField(source='reported_user.username', read_only=True, default=None)
    project_title = serializers.CharField(source='project.title', read_only=True, default=None)

    class Meta:
        model = ProjectReport
        fields = [
            'id', 'reporter', 'reporter_name', 'reporter_email',
            'reported_user', 'reported_username', 'project', 'project_title',
            'reason', 'description', 'status', 'admin_notes',
            'created_at', 'updated_at'
        ]


class AdminFreelancerReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='freelancer.display_name', read_only=True)
    reporter_email = serializers.EmailField(source='freelancer.user.email', read_only=True)
    reported_client_name = serializers.CharField(source='reported_client.display_name', read_only=True, default=None)
    project_title = serializers.CharField(source='project.title', read_only=True, default=None)

    class Meta:
        model = FreelancerReport
        fields = [
            'id', 'freelancer', 'reporter_name', 'reporter_email',
            'reported_client', 'reported_client_name', 'project', 'project_title',
            'reason', 'description', 'status', 'admin_notes',
            'created_at', 'updated_at'
        ]


class AdminMarketplaceDisputeSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)
    opened_by_username = serializers.CharField(source='opened_by.username', read_only=True)
    client_name = serializers.CharField(source='client.display_name', read_only=True)
    freelancer_name = serializers.SerializerMethodField()
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True, default=None)

    class Meta:
        model = MarketplaceDispute
        fields = [
            'id', 'project', 'project_title', 'opened_by', 'opened_by_username',
            'client', 'client_name', 'freelancer', 'freelancer_name',
            'category', 'title', 'description', 'evidence', 'status',
            'resolution_type', 'resolution', 'resolved_by', 'resolved_by_username',
            'admin_notes', 'created_at', 'updated_at'
        ]

    def get_freelancer_name(self, obj):
        return obj.freelancer.display_name if obj.freelancer else None


class AdminPlatformSupportTicketSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    assigned_admin_username = serializers.CharField(source='assigned_admin.username', read_only=True, default=None)

    class Meta:
        model = PlatformSupportTicket
        fields = [
            'id', 'user', 'username', 'user_email', 'role', 'category',
            'subject', 'message', 'status', 'admin_response',
            'assigned_admin', 'assigned_admin_username', 'created_at', 'updated_at'
        ]
