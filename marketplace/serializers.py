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


# ===========================================================================
# STAGE 2 — FREELANCER SERIALIZERS
# ===========================================================================

class FreelancerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    skills_list = serializers.ListField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        from .models import FreelancerProfile
        model = FreelancerProfile
        fields = [
            'id', 'username', 'email', 'full_name', 'professional_title',
            'phone', 'location', 'skills', 'skills_list', 'experience',
            'bio', 'portfolio_website', 'github_url', 'linkedin_url',
            'hourly_rate', 'avatar_url', 'created_at',
        ]
        read_only_fields = ['id', 'username', 'email', 'skills_list', 'created_at']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class FreelancerProjectPublicSerializer(serializers.ModelSerializer):
    """Sanitized public project view for Freelancer project search."""
    skills_list = serializers.ListField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    duration_display = serializers.CharField(source='get_expected_duration_display', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_company = serializers.SerializerMethodField()
    client_location = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceProject
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'required_skills', 'skills_list', 'budget', 'budget_type',
            'expected_duration', 'duration_display', 'deadline',
            'experience_level', 'status', 'client_name', 'client_company',
            'client_location', 'has_applied', 'created_at',
        ]
        read_only_fields = fields

    def get_client_name(self, obj):
        return obj.client.display_name

    def get_client_company(self, obj):
        return obj.client.company_name or 'Independent Client'

    def get_client_location(self, obj):
        return obj.client.location or 'Remote'

    def get_has_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.applications.filter(freelancer=request.user).exists()
        return False


class FreelancerProjectWorkspaceSerializer(serializers.ModelSerializer):
    """Workspace serializer for an assigned project — includes client contact info."""
    skills_list = serializers.ListField(read_only=True)
    client_contact = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceProject
        fields = [
            'id', 'title', 'description', 'category', 'required_skills',
            'skills_list', 'budget', 'budget_type', 'expected_duration',
            'deadline', 'status', 'progress', 'client_contact',
            'payment_info', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_client_contact(self, obj):
        request = self.context.get('request')
        # Only expose contact info if project is assigned to the requesting user
        if request and request.user == obj.assigned_freelancer:
            return {
                'client_name': obj.client.display_name,
                'company_name': obj.client.company_name,
                'email': obj.client.user.email,
                'phone': obj.client.phone or 'Not provided',
                'location': obj.client.location or 'Not specified',
                'bio': obj.client.bio,
            }
        return {
            'client_name': obj.client.display_name,
            'company_name': obj.client.company_name,
        }

    def get_payment_info(self, obj):
        pr = getattr(obj, 'payment_record', None)
        if pr:
            return {
                'total_budget': str(pr.total_budget),
                'amount_paid': str(pr.amount_paid),
                'amount_pending': str(pr.amount_pending),
                'status': pr.status,
            }
        return None


class FreelancerApplicationSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_status = serializers.CharField(source='project.status', read_only=True)
    project_budget = serializers.DecimalField(
        source='project.budget', max_digits=12, decimal_places=2, read_only=True
    )
    client_name = serializers.CharField(source='project.client.display_name', read_only=True)

    class Meta:
        model = ProjectApplication
        fields = [
            'id', 'project_id', 'project_title', 'project_status',
            'project_budget', 'client_name', 'proposal', 'proposed_price',
            'estimated_duration', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project_id', 'project_title', 'project_status',
            'project_budget', 'client_name', 'status', 'created_at', 'updated_at',
        ]


class FreelancerPaymentSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    client_name = serializers.CharField(source='project.client.display_name', read_only=True)
    amount_pending = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProjectPaymentRecord
        fields = [
            'id', 'project_id', 'project_title', 'client_name',
            'total_budget', 'amount_paid', 'amount_pending',
            'status', 'notes', 'created_at',
        ]
        read_only_fields = fields


class FreelancerReportSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    client_name = serializers.CharField(source='reported_client.display_name', read_only=True)

    class Meta:
        from .models import FreelancerReport
        model = FreelancerReport
        fields = [
            'id', 'project', 'project_title', 'reported_client',
            'client_name', 'reason', 'reason_display', 'description',
            'status', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

