from django import forms
from .models import *

class SupportForm(forms.ModelForm):
    class Meta:
        model =SuppportMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your message...',
                'required': True,
            })
        }
        lables = {'message': ''}