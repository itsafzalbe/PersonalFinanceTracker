from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class SignupForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        
        user = CustomUser.objects.filter(email=email).first()
        if user and user.auth_status == 'done':
            raise ValidationError('An account with this email already exists.')
        
        return email


class VerifyCodeForm(forms.Form):
    code = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234',
            'maxlength': '4',
            'autocomplete': 'off',
            'pattern': '[0-9]{4}',
            'required': True
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit():
            raise ValidationError('Code must contain only digits.')
        return code


class CompleteRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
            'required': True
        })
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name (optional)',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name (optional)',
            'autocomplete': 'family-name'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
            'required': True
        })
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
            'required': True
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998912345678',
            'autocomplete': 'tel'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'autocomplete': 'bday'
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        

        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        
        if username.startswith('user_'):
            raise ValidationError('Username cannot start with "user_".')
        
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autocomplete': 'username',
            'required': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'required': True
        })
    )


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'default_currency']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998912345678'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'default_currency': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def clean_username(self):
        username = self.cleaned_data['username']

        if CustomUser.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise ValidationError('This username is already taken.')
        
        if username.startswith('user_'):
            raise ValidationError('Username cannot start with "user_".')
        
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        
        return username


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password',
            'autocomplete': 'current-password',
            'required': True
        })
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
            'required': True
        })
    )
    
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
            'required': True
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        
        if self.user and not self.user.check_password(old_password):
            raise ValidationError('Current password is incorrect.')
        
        return old_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        
        try:
            validate_password(new_password, self.user)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })

        return cleaned_data