from django import forms
from decimal import Decimal
from .models import Budget
from apps.transactions.models import Category
from apps.cards.models import Currency


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'name', 'category', 'amount', 'currency', 'period',
            'alert_threshold', 'is_active', 'start_date',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Monthly Groceries Budget',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'period': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'alert_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '80',
                'min': '0',
                'max': '100',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=None) | Q(user=user),
                type='expense',
                is_active=True
            ).order_by('name')
            
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            ).order_by('code')
        
        if not self.instance.pk:
            self.fields['alert_threshold'].initial = 80


class BudgetFilterForm(forms.Form):
    period = forms.ChoiceField(
        choices=[('', 'All Periods')] + list(Budget.PERIOD_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=None) | Q(user=user),
                type='expense',
                is_active=True
            ).order_by('name')