from django import forms
from decimal import Decimal
from apps.cards.models import Card, Currency, CardType


class CurrencyConversionForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        })
    )
    from_currency = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    to_currency = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        currency_choices = [(c.code, f"{c.code} - {c.name}") 
                           for c in Currency.objects.filter(is_active=True).order_by('code')]
        self.fields['from_currency'].choices = currency_choices
        self.fields['to_currency'].choices = currency_choices


class CardBalanceUpdateForm(forms.Form):
    new_balance = forms.DecimalField(
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new balance',
            'step': '0.01'
        })
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for balance update (optional)',
            'rows': 3
        })
    )


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = [
            "card_name",
            "bank_name",
            "card_type",
            "currency",
            "balance",
            "card_number_last4",
            "status",
        ]
        widgets = {
            'card_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., My Visa Card'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Hamkorbank'
            }),
            'card_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'card_number_last4': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last 4 digits',
                'maxlength': '4',
                'pattern': '[0-9]{4}'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card_type'].queryset = CardType.objects.filter(is_active=True)
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)