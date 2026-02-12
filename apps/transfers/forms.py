from django import forms
from decimal import Decimal
from .models import *
from apps.cards.models import *

class CardTransferForm(forms.ModelForm):
    class Meta:
        model = CardTransfer
        fields = ['from_card', 'to_card', 'amount', 'description']
        widgets = {
            'from_card': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True,
                'id': 'fromCard',

            }),
            'to_card': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True,
                'id': 'toCard',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True,
                'id': 'transferAmount',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional note for this transfer',
                'maxlength': 255
            }),
            
        }
        labels = {
            'from_card': 'From Card',
            'to_card': 'To Card',
            'amount': 'Amount to Transfer',
            'description': 'Description(Optional)'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            user_cards = Card.objects.filter(user=user, status='active').select_related('currency', 'card_type')

            self.fields['from_card'].queryset = user_cards
            self.fields['to_card'].queryset = user_cards

            self.fields['from_card'].label_from_instance =self.card_label
            self.fields['to_card'].label_from_instance =self.card_label
    
    def card_label(self, obj):
        return f"{obj.card_name} - {obj.balance:,.2f} {obj.currency.code}"
    
    def clean(self):
        cleaned_data = super().clean()
        from_card = cleaned_data.get('from_card')
        to_card = cleaned_data.get('to_card')
        amount = cleaned_data.get('amount')

        if from_card and to_card and amount:
            if from_card == to_card:
                raise forms.ValidationError('Cannot transfer to the same card. Please select different cards')
            
            if amount > from_card.balance:
                raise forms.ValidationError(
                    f"Insufficient balance in {from_card.card_name}."
                    f"Available: {from_card.balance:,.2f} {from_card.currency.code}"
                )
            
            if amount < Decimal('0.01'):
                raise forms.ValidationError('Transfer amount must be at least 0.01')
            
            if from_card.currency !=to_card.currency:
                rate = ExchangeRate.get_latest_rate(from_card.currency, to_card.currency)
                if not rate:
                    raise forms.ValidationError(
                        f'Exchange rate not available for {from_card.currency.code}'
                        f"to {to_card.currency.code}. Please contact support"
                    )
                
                cleaned_data['exchange_rate'] = rate
                cleaned_data['converted_amount']= amount*rate
            else:
                cleaned_data['exchange_rate'] = Decimal('1.000000')
                cleaned_data['converted_amount'] = amount
        
        return cleaned_data

            

class QuickTransferForm(forms.Form):
    from_card = forms.ModelChoiceField(
        queryset=Card.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'required': True 
        }),
        label='From'                               
    )

    to_card = forms.ModelChoiceField(
        queryset=Card.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'required': True 
        }),
        label='To'                               
    )

    amount= forms.DecimalField(
        max_digits=15, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        label='Amount'
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            user_cards = Card.objects.filter(user =user, status='active')
            self.fields['from_card'].queryset = user_cards
            self.fields['to_card'].queryset = user_cards
