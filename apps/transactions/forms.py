from django import forms
from decimal import Decimal
from .models import Transaction, Category, TransactionTag
from apps.cards.models import Card


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'type', 'title', 'amount', 'card', 'category',
            'date', 'description', 'location',
        ]
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Grocery shopping',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'card': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add notes about this transaction (optional)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where did this happen? (optional)'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['card'].queryset = Card.objects.filter(
                user=self.user,
                status='active'
            )
            
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=None) | Q(user=self.user),
                is_active=True
            ).order_by('type', 'name')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'icon', 'parent_category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name',
                'required': True
            }),
            'type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., bi-cart, bi-home, bi-car'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'parent_category': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_category'].queryset = Category.objects.filter(
            parent_category__isnull=True,
            is_active=True
        )
        self.fields['parent_category'].required = False


class TransactionTagForm(forms.ModelForm):
    class Meta:
        model = TransactionTag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tag name',
                'required': True
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }


class TransactionFilterForm(forms.Form):
    type = forms.ChoiceField(
        choices=[('', 'All Types'), ('income', 'Income'), ('expense', 'Expense')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )
    card = forms.ModelChoiceField(
        queryset=Card.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Cards'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search transactions...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=None) | Q(user=user),
                is_active=True
            ).order_by('type', 'name')
            
            self.fields['card'].queryset = Card.objects.filter(
                user=user,
                status='active'
            )


class BulkDeleteForm(forms.Form):
    transaction_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=True
    )