from django import forms
from django.core.validators import EmailValidator, RegexValidator
from .models import Client, Project, Payment, Task, Note


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