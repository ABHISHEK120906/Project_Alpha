from django import forms
from django.core.validators import EmailValidator, RegexValidator, validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Client, Project, Payment, Task, Note, UserProfile,
                     Income, Expense, Invoice, InvoiceItem, CalendarEvent,
                     ProjectFile, ProjectComment)


class ClientForm(forms.ModelForm):
    """
    Form for creating and updating Client instances
    """
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'company', 'address', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter additional notes'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            validator = EmailValidator()
            validator(email)
        return email


class ProjectForm(forms.ModelForm):
    """
    Form for creating and updating Project instances
    """
    class Meta:
        model = Project
        fields = ['client', 'name', 'description', 'status', 'priority', 
                  'start_date', 'deadline', 'budget', 'progress']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter project description'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget amount',
                'step': '0.01'
            }),
            'progress': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter progress (0-100)',
                'min': '0',
                'max': '100'
            }),
        }
    
    def clean_progress(self):
        progress = self.cleaned_data.get('progress')
        if progress is not None:
            if progress < 0 or progress > 100:
                raise forms.ValidationError('Progress must be between 0 and 100')
        return progress
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise forms.ValidationError('Budget cannot be negative')
        return budget


class PaymentForm(forms.ModelForm):
    """
    Form for creating and updating Payment instances
    """
    class Meta:
        model = Payment
        fields = ['project', 'amount', 'status', 'payment_method', 
                  'due_date', 'paid_date', 'description', 'invoice_number']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment amount',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'paid_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter payment description'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter invoice number'
            }),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0')
        return amount


class TaskForm(forms.ModelForm):
    """
    Form for creating and updating Task instances
    """
    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'status', 'priority', 
                  'due_date', 'estimated_hours', 'actual_hours']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter estimated hours',
                'step': '0.25'
            }),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter actual hours',
                'step': '0.25'
            }),
        }
    
    def clean_estimated_hours(self):
        hours = self.cleaned_data.get('estimated_hours')
        if hours is not None and hours < 0:
            raise forms.ValidationError('Estimated hours cannot be negative')
        return hours
    
    def clean_actual_hours(self):
        hours = self.cleaned_data.get('actual_hours')
        if hours is not None and hours < 0:
            raise forms.ValidationError('Actual hours cannot be negative')
        return hours


class NoteForm(forms.ModelForm):
    """
    Form for creating and updating Note instances
    """
    class Meta:
        model = Note
        fields = ['project', 'client', 'title', 'content', 'is_private']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter note title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter note content'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        client = cleaned_data.get('client')
        
        if not project and not client:
            raise forms.ValidationError(
                'Either a project or client must be selected'
            )
        
        if project and client:
            raise forms.ValidationError(
                'Note can be associated with either a project or a client, not both'
            )
        
        return cleaned_data


class SearchForm(forms.Form):
    """
    Generic search form for filtering records
    """
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class UserBasicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address', 'bio', 'skills',
                  'experience', 'portfolio_website', 'social_github', 'social_linkedin', 'social_twitter']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your address'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell clients about yourself'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, React, UI/UX Design'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5+ years full-stack freelance development'}),
            'portfolio_website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'social_github': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username'}),
            'social_linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'social_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/username'}),
        }


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['title', 'client', 'project', 'amount', 'category', 'date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Website Deposit'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional details...'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'project', 'amount', 'category', 'date', 'receipt', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Adobe Creative Cloud'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional details...'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'client', 'project', 'issue_date', 'due_date', 'status', 'tax_rate', 'discount_amount', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INV-2026-001'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '10'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment terms or bank details...'}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Line item description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'event_type', 'start_time', 'end_time', 'project', 'task', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event title'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'task': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}),
        }


class ProjectFileForm(forms.ModelForm):
    class Meta:
        model = ProjectFile
        fields = ['project', 'file']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ProjectCommentForm(forms.ModelForm):
    class Meta:
        model = ProjectComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write an internal note or comment...'}),
        }


class UserRegistrationForm(UserCreationForm):
    """
    Mandatory registration form requiring valid email verification.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-control'}),
        help_text="A verification link will be sent to this email address."
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("Email address is strictly required.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")

        # Check for duplicate email across all existing accounts
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email address is already registered. Please log in or use a different email.")

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        if username.lower() == 'svathi':
            raise ValidationError("The username 'Svathi' is reserved for Super Admin and cannot be registered.")

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose a different one.")

        return username