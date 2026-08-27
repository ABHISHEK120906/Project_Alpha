"""
Admin Forms for Marketplace Moderation & Dispute Management (Stage 3)
"""
from django import forms
from .models import (
    MarketplaceDispute,
    PlatformSupportTicket,
    ProjectReport,
    FreelancerReport,
    MarketplaceProject,
)


class DisputeResolutionForm(forms.ModelForm):
    """Admin form to record findings, notes, and resolution for a dispute."""
    class Meta:
        model = MarketplaceDispute
        fields = ['status', 'resolution_type', 'resolution', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'resolution_type': forms.Select(attrs={'class': 'form-select'}),
            'resolution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain the rationale and resolution decision clearly to both parties...'
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal administrative notes, investigative logs, evidence review...'
            }),
        }


class DisputeCreateForm(forms.ModelForm):
    """Admin form to manually open a dispute."""
    class Meta:
        model = MarketplaceDispute
        fields = [
            'project', 'category', 'title', 'description', 'evidence', 'admin_notes'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dispute Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed dispute reason...'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Relevant transaction IDs, logs, or message links...'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Administrative notes...'}),
        }


class ReportResolutionForm(forms.Form):
    """Admin form to resolve a client or freelancer report."""
    status = forms.ChoiceField(
        choices=[
            ('under_review', 'Under Review'),
            ('resolved', 'Resolved'),
            ('rejected', 'Rejected / Dismissed'),
            ('closed', 'Closed'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    action_taken = forms.ChoiceField(
        choices=[
            ('no_action', 'No Action Required (Cleared)'),
            ('warning_issued', 'Official Warning Issued'),
            ('account_suspended', 'Suspend Reported User Account'),
            ('project_closed', 'Close Inappropriate Project'),
            ('escalated_to_dispute', 'Escalate to Formal Dispute'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Administrative verdict notes...'
        })
    )


class SupportTicketResponseForm(forms.ModelForm):
    """Admin form to respond to and update a support ticket."""
    class Meta:
        model = PlatformSupportTicket
        fields = ['status', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide official platform support response to the user...'
            }),
        }


class UserModerationForm(forms.Form):
    """Admin form to toggle user active/suspended state with a reason."""
    action = forms.ChoiceField(
        choices=[
            ('suspend', 'Suspend Account'),
            ('unsuspend', 'Unsuspend / Reactivate Account'),
            ('deactivate', 'Deactivate (Soft Disable)'),
            ('activate', 'Activate Account'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Audit reason for this action...'
        })
    )


class ProjectModerationForm(forms.ModelForm):
    """Admin form to moderate and update marketplace project status."""
    moderation_action = forms.ChoiceField(
        choices=[
            ('no_change', 'Update Details / Keep Current Status'),
            ('close', 'Close Project (Moderate / Terminate)'),
            ('reopen', 'Reopen Project'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for moderation action...'})
    )

    class Meta:
        model = MarketplaceProject
        fields = ['status', 'title', 'category', 'budget']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }
