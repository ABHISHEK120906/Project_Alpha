"""
Marketplace forms — Client Registration, Profile, Project, Report
"""
from django import forms
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from .models import (
    ClientProfile,
    FreelancerProfile,
    MarketplaceProject,
    ProjectApplication,
    ProjectPaymentRecord,
    ProjectReport,
    FreelancerReport,
)


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
            profile__role__in=['user', 'freelancer']
        ).select_related('profile')


# ===========================================================================
# STAGE 2 — FREELANCER FORMS
# ===========================================================================

class FreelancerRegistrationForm(forms.Form):
    """
    Full Freelancer registration: name, email, password, phone, professional title,
    skills, experience, bio, portfolio links, hourly rate, avatar.
    """
    full_name = forms.CharField(
        label='Full Name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name',
            'autocomplete': 'name',
            'id': 'freelancer-reg-fullname',
        }),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@domain.com',
            'autocomplete': 'email',
            'id': 'freelancer-reg-email',
        }),
    )
    phone = forms.CharField(
        label='Phone / WhatsApp (optional)',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
            'id': 'freelancer-reg-phone',
        }),
    )
    professional_title = forms.CharField(
        label='Professional Title',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Senior Full-Stack Developer | Python & AI Specialist',
            'id': 'freelancer-reg-title',
        }),
    )
    skills = forms.CharField(
        label='Key Skills',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Python, Django, React, PostgreSQL, TailwindCSS',
            'id': 'freelancer-reg-skills',
        }),
        help_text='Comma-separated skills',
    )
    experience = forms.CharField(
        label='Years / Background Experience',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 5+ years of building production SaaS & web apps',
            'id': 'freelancer-reg-exp',
        }),
    )
    hourly_rate = forms.DecimalField(
        label='Hourly Rate (INR ₹ / hr, optional)',
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1500',
            'id': 'freelancer-reg-rate',
        }),
    )
    portfolio_website = forms.URLField(
        label='Portfolio / Personal Website (optional)',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://yourportfolio.dev',
            'id': 'freelancer-reg-portfolio',
        }),
    )
    github_url = forms.URLField(
        label='GitHub Profile (optional)',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/username',
            'id': 'freelancer-reg-github',
        }),
    )
    linkedin_url = forms.URLField(
        label='LinkedIn Profile (optional)',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://linkedin.com/in/username',
            'id': 'freelancer-reg-linkedin',
        }),
    )
    bio = forms.CharField(
        label='About You / Bio',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Share your expertise, problem-solving skills, and past successes...',
            'id': 'freelancer-reg-bio',
        }),
    )
    password1 = forms.CharField(
        label='Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password (min 8 chars)',
            'autocomplete': 'new-password',
            'id': 'freelancer-reg-pass1',
        }),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password',
            'autocomplete': 'new-password',
            'id': 'freelancer-reg-pass2',
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
        """Create User + UserProfile(role='freelancer') + FreelancerProfile."""
        email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name']
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        first_name = full_name.split()[0] if full_name else ''
        last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password1'],
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        from core.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'freelancer'
        profile.is_verified = True
        profile.phone_number = self.cleaned_data.get('phone', '')
        profile.skills = self.cleaned_data.get('skills', '')
        profile.experience = self.cleaned_data.get('experience', '')
        profile.bio = self.cleaned_data.get('bio', '')
        profile.portfolio_website = self.cleaned_data.get('portfolio_website') or None
        profile.social_github = self.cleaned_data.get('github_url') or None
        profile.social_linkedin = self.cleaned_data.get('linkedin_url') or None
        profile.save()

        from .models import FreelancerProfile
        freelancer_profile = FreelancerProfile.objects.create(
            user=user,
            full_name=full_name,
            professional_title=self.cleaned_data.get('professional_title', ''),
            phone=self.cleaned_data.get('phone', ''),
            skills=self.cleaned_data.get('skills', ''),
            experience=self.cleaned_data.get('experience', ''),
            bio=self.cleaned_data.get('bio', ''),
            portfolio_website=self.cleaned_data.get('portfolio_website') or None,
            github_url=self.cleaned_data.get('github_url') or None,
            linkedin_url=self.cleaned_data.get('linkedin_url') or None,
            hourly_rate=self.cleaned_data.get('hourly_rate') or None,
        )

        return user, freelancer_profile


class FreelancerProfileForm(forms.ModelForm):
    """Edit FreelancerProfile fields."""
    class Meta:
        from .models import FreelancerProfile
        model = FreelancerProfile
        fields = [
            'full_name',
            'professional_title',
            'phone',
            'location',
            'hourly_rate',
            'skills',
            'experience',
            'portfolio_website',
            'github_url',
            'linkedin_url',
            'bio',
            'avatar',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'professional_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full-Stack Python Architect'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mumbai, India'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hourly Rate in INR'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, React, PostgreSQL'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years of experience'}),
            'portfolio_website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your bio...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FreelancerEmailForm(forms.ModelForm):
    """Update Freelancer email on User model."""
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        user_id = self.instance.pk if self.instance else None
        if User.objects.filter(email__iexact=email).exclude(pk=user_id).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class ProjectApplicationForm(forms.ModelForm):
    """Application form for Freelancers applying to an open MarketplaceProject."""
    class Meta:
        from .models import ProjectApplication
        model = ProjectApplication
        fields = ['proposal', 'proposed_price', 'estimated_duration']
        widgets = {
            'proposal': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Explain why you are the best fit for this project, your relevant experience, approach, and deliverables...',
                'id': 'application-proposal',
            }),
            'proposed_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 25000',
                'id': 'application-price',
            }),
            'estimated_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2 weeks / 1 month',
                'id': 'application-duration',
            }),
        }

    def clean_proposed_price(self):
        price = self.cleaned_data.get('proposed_price')
        if price is not None and price < 0:
            raise forms.ValidationError("Proposed price cannot be negative.")
        return price


class ProjectProgressUpdateForm(forms.Form):
    """Form for Freelancers to update the progress percentage on assigned projects."""
    progress = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'id': 'workspace-progress-input',
        }),
        help_text='Enter a progress percentage from 0 to 100.',
    )


class FreelancerReportForm(forms.ModelForm):
    """Form for Freelancer to submit a support report against a Client or project."""
    class Meta:
        from .models import FreelancerReport
        model = FreelancerReport
        fields = ['project', 'reported_client', 'reason', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control', 'id': 'report-project'}),
            'reported_client': forms.Select(attrs={'class': 'form-control', 'id': 'report-client'}),
            'reason': forms.Select(attrs={'class': 'form-control', 'id': 'report-reason'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please provide comprehensive details regarding the issue...',
                'id': 'report-description',
            }),
        }

    def __init__(self, *args, freelancer_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ClientProfile, MarketplaceProject
        self.fields['reported_client'].required = False
        self.fields['reported_client'].empty_label = 'Select client (optional)'
        self.fields['project'].required = False
        self.fields['project'].empty_label = 'Select project (optional)'
        if freelancer_profile:
            # Projects applied to or assigned to this freelancer
            self.fields['project'].queryset = MarketplaceProject.objects.filter(
                models.Q(assigned_freelancer=freelancer_profile.user) |
                models.Q(applications__freelancer=freelancer_profile.user)
            ).distinct()
        self.fields['reported_client'].queryset = ClientProfile.objects.all()


# ---------------------------------------------------------------------------
# Freelancer Verification Forms
# ---------------------------------------------------------------------------

class FreelancerEmailVerifyForm(forms.Form):
    """Form to verify freelancer email with OTP or confirmation code."""
    otp_code = forms.CharField(
        label='6-Digit Verification Code',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP (e.g. 123456)',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'id': 'verify-email-otp',
        }),
        help_text='A 6-digit verification code has been generated for your registered email.',
    )

    def clean_otp_code(self):
        otp = self.cleaned_data.get('otp_code', '').strip()
        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit numerical OTP code.")
        return otp


class FreelancerPhoneVerifyForm(forms.Form):
    """Form to verify freelancer mobile number with OTP."""
    phone_number = forms.CharField(
        label='Mobile Phone Number',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
            'id': 'verify-phone-input',
        }),
    )
    otp_code = forms.CharField(
        label='SMS Verification Code',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit SMS OTP (e.g. 654321)',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'id': 'verify-phone-otp',
        }),
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone

    def clean_otp_code(self):
        otp = self.cleaned_data.get('otp_code', '').strip()
        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit numerical OTP code.")
        return otp


class FreelancerIdentityVerifyForm(forms.Form):
    """Form for submitting identity verification details."""
    IDENTITY_TYPES = [
        ('Aadhaar / National ID', 'Aadhaar / National ID Card'),
        ('Passport', 'Passport'),
        ('Voter ID', 'Voter Identity Card'),
        ("Driver's License", "Driver's License"),
    ]

    identity_type = forms.ChoiceField(
        choices=IDENTITY_TYPES,
        label='Government ID Document Type',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'verify-id-type',
        }),
    )
    legal_name = forms.CharField(
        label='Full Legal Name (as printed on ID)',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Abhishek Kumar Sharma',
            'id': 'verify-id-name',
        }),
    )
    id_number = forms.CharField(
        label='Document Reference / ID Number',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 1234 5678 9012 or Passport Number',
            'id': 'verify-id-number',
        }),
        help_text='Your document number is encrypted and processed securely. It is NEVER exposed to clients.',
    )

    def clean_legal_name(self):
        name = self.cleaned_data.get('legal_name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError("Please provide your full legal name as it appears on your ID.")
        return name

    def clean_id_number(self):
        val = self.cleaned_data.get('id_number', '').strip()
        if len(val) < 4:
            raise forms.ValidationError("Please enter a valid document identification number.")
        return val


class FreelancerPANVerifyForm(forms.Form):
    """Form for PAN verification with strict Indian PAN format validation."""
    pan_number = forms.CharField(
        label='Permanent Account Number (PAN)',
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'ABCDE1234F',
            'maxlength': '10',
            'id': 'verify-pan-number',
            'style': 'text-transform: uppercase; letter-spacing: 2px; font-family: monospace; font-weight: 700;',
        }),
        help_text='Enter 10-character alphanumeric PAN (e.g. ABCDE1234F). Only masked representation (XXXXXX1234) is retained.',
    )

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number', '').strip().upper()
        pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_regex, pan):
            raise forms.ValidationError(
                "Invalid PAN format. Standard PAN format must be 5 uppercase letters, 4 digits, and 1 letter (e.g., ABCDE1234F)."
            )
        return pan


class FreelancerPaymentVerifyForm(forms.Form):
    """Form to simulate secure payment / payout onboarding KYC."""
    PROVIDER_CHOICES = [
        ('razorpay', 'Razorpay Linked Account (Verified Payouts)'),
        ('upi', 'UPI KYC / Virtual Payment Address'),
        ('bank_account', 'Direct Bank Account KYC (NEFT/IMPS)'),
    ]

    account_provider = forms.ChoiceField(
        choices=PROVIDER_CHOICES,
        label='Payout / Payment Onboarding Method',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'verify-payment-provider',
        }),
    )
    account_holder_name = forms.CharField(
        label='Bank / Account Holder Name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name matching your bank account',
            'id': 'verify-payment-holder',
        }),
    )
    account_identifier = forms.CharField(
        label='Account Number / UPI ID / Razorpay ID',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. yourname@okhdfcbank or Bank Account No',
            'id': 'verify-payment-identifier',
        }),
        help_text='Payment details are securely masked for KYC verification signals only.',
    )

    def clean_account_holder_name(self):
        name = self.cleaned_data.get('account_holder_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Please provide the account holder name.")
        return name

    def clean_account_identifier(self):
        val = self.cleaned_data.get('account_identifier', '').strip()
        if len(val) < 4:
            raise forms.ValidationError("Please provide a valid account or UPI identifier.")
        return val


class AdminVerificationReviewForm(forms.Form):
    """Form for platform admin to review and approve/reject a freelancer verification."""
    ACTION_CHOICES = [
        ('approve', 'Approve Verification (Grant Verified Status)'),
        ('reject', 'Reject Verification (Request Corrections)'),
        ('suspend', 'Suspend Verification'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'admin-ver-action'}),
    )
    admin_notes = forms.CharField(
        label='Administrative Notes / Reason',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional explanation or feedback for the freelancer...',
            'id': 'admin-ver-notes',
        }),
    )


