"""
Marketplace forms — Client Registration, Profile, Project, Report
"""
from django import forms
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from .models import ClientProfile, MarketplaceProject, ProjectReport


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class ClientRegistrationForm(forms.Form):
    """
    Full client registration: name, email, password, phone, company.
    """
    full_name = forms.CharField(
        label='Full Name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name',
            'autocomplete': 'name',
        }),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@company.com',
            'autocomplete': 'email',
        }),
    )
    phone = forms.CharField(
        label='Phone Number',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
        }),
    )
    company_name = forms.CharField(
        label='Company Name (optional)',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your company or organisation',
        }),
    )
    password1 = forms.CharField(
        label='Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password',
            'autocomplete': 'new-password',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned

    def save(self):
        """Create User + ClientProfile. Return (user, client_profile)."""
        email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name']
        # Use email prefix as username (ensure uniqueness)
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password1'],
            first_name=full_name.split()[0] if full_name else '',
            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            is_active=True,
        )

        # Create/update UserProfile with client role
        from core.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'client'
        profile.is_verified = True
        profile.phone_number = self.cleaned_data.get('phone', '')
        profile.save()

        # Create ClientProfile
        client_profile = ClientProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=self.cleaned_data.get('phone', ''),
            company_name=self.cleaned_data.get('company_name', ''),
        )

        return user, client_profile


# ---------------------------------------------------------------------------
# Profile Edit
# ---------------------------------------------------------------------------

class ClientProfileForm(forms.ModelForm):
    """Edit ClientProfile fields."""
    class Meta:
        model = ClientProfile
        fields = [
            'full_name', 'phone', 'company_name',
            'company_description', 'location', 'bio', 'avatar',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 98765 43210',
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company or organisation name',
            }),
            'company_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of your company',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell freelancers about yourself or your projects',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }


class ClientEmailForm(forms.ModelForm):
    """Edit the User's email separately."""
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'you@company.com',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use.")
        return email


# ---------------------------------------------------------------------------
# Post a Project
# ---------------------------------------------------------------------------

class MarketplaceProjectForm(forms.ModelForm):
    """Form for Client to post or edit a Marketplace Project."""

    class Meta:
        model = MarketplaceProject
        fields = [
            'title', 'description', 'category',
            'required_skills', 'budget', 'budget_type',
            'expected_duration', 'deadline', 'experience_level',
            'attachment', 'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. E-Commerce Website Development',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe your project in detail — goals, features, requirements...',
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'required_skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'HTML, CSS, JavaScript, Django (comma-separated)',
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '40000',
                'step': '0.01',
                'min': '0',
            }),
            'budget_type': forms.Select(attrs={'class': 'form-control'}),
            'expected_duration': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices available to client
        self.fields['status'].choices = [
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed'),
        ]

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise forms.ValidationError("Budget cannot be negative.")
        return budget


# ---------------------------------------------------------------------------
# Support / Report
# ---------------------------------------------------------------------------

class ProjectReportForm(forms.ModelForm):
    """Form for Client to submit a support report."""
    class Meta:
        model = ProjectReport
        fields = ['project', 'reported_user', 'reason', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'reported_user': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue in detail...',
            }),
        }

    def __init__(self, *args, client_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reported_user'].required = False
        self.fields['reported_user'].empty_label = 'Select freelancer (optional)'
        self.fields['project'].required = False
        self.fields['project'].empty_label = 'Select project (optional)'
        if client_profile:
            self.fields['project'].queryset = MarketplaceProject.objects.filter(
                client=client_profile
            )
        # Freelancer choices: users who have applied to client's projects (Stage 2 will populate)
        from django.contrib.auth.models import User
        # For now show all non-client, non-admin users
        from core.models import UserProfile
        self.fields['reported_user'].queryset = User.objects.filter(
            profile__role='user'
        ).select_related('profile')
