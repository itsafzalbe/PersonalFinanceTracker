from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .models import CustomUser
from .forms import *
from .utils import send_verification_email



def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            existing_user = CustomUser.objects.filter(email=email).first()
            if existing_user and existing_user.auth_status == 'done':
                messages.error(request, 'User with this email already exists. Please login.')
                return redirect('accounts:login')
            
            if existing_user and existing_user.auth_status in ['new', 'code_verified']:
                user = existing_user
            else:
                user = CustomUser.objects.create(email=email, auth_status='new')

            code = user.generate_verification_code()
            
            try:
                send_verification_email(user.email, code)
                request.session['verification_user_id'] = user.id
                messages.success(request, 'Verification code sent to your email!')
                return redirect('accounts:verify-code')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
    else:
        form = SignupForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def verify_code_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Please start the registration process first.')
        return redirect('accounts:signup')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            
            if user.verify_code(code):
                messages.success(request, 'Email verified successfully! Please complete your registration.')
                return redirect('accounts:complete_registration')
            else:
                messages.error(request, 'Invalid or expired verification code.')
    else:
        form = VerifyCodeForm()
    
    can_resend = user.can_resend_code()
    
    return render(request, 'accounts/verify_code.html', {
        'form': form,
        'can_resend': can_resend,
        'email': user.email
    })


@require_http_methods(["POST"])
def resend_code_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Please start the registration process first.')
        return redirect('accounts:signup')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.auth_status == 'done':
        messages.error(request, 'Email already verified and registration completed.')
        return redirect('accounts:login')
    
    if not user.can_resend_code():
        messages.error(request, 'Please wait 2 minutes before requesting a new code.')
        return redirect('accounts:verify-code')
    
    code = user.generate_verification_code()
    
    try:
        send_verification_email(user.email, code)
        messages.success(request, 'New verification code sent to your email!')
    except Exception as e:
        messages.error(request, f'Failed to send email: {str(e)}')
    
    return redirect('accounts:verify-code')


def complete_registration_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Please start the registration process first.')
        return redirect('accounts:signup')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.auth_status != 'code_verified':
        messages.error(request, 'Please verify your email first.')
        return redirect('accounts:verify-code')
    
    if request.method == 'POST':
        form = CompleteRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user.complete_registration(
                    username=form.cleaned_data['username'],
                    first_name=form.cleaned_data.get('first_name', ''),
                    last_name=form.cleaned_data.get('last_name', ''),
                    password=form.cleaned_data['password'],
                    phone_number=form.cleaned_data.get('phone_number'),
                    date_of_birth=form.cleaned_data.get('date_of_birth'),
                )
                
     
                login(request, user, backend='django.contrib.auth.backends.ModelBackend') # here specified which backend authentiacted the user - login must know that 
                

                del request.session['verification_user_id']
                
                messages.success(request, 'Registration completed successfully! Welcome to your finance tracker!')
                return redirect('dashboard:dashboard')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = CompleteRegistrationForm()
    
    return render(request, 'accounts/complete_registration.html', {'form': form})


def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            

            user = authenticate(request, username=username, password=password)
            

            if not user:
                try:
                    user_obj = CustomUser.objects.get(email=username.lower())
                    user = authenticate(request, username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if user is not None:
                if user.auth_status == 'done':
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    
                    next_page = request.GET.get('next') or 'dashboard:dashboard'
                    return redirect(next_page)
                else:
                    messages.error(request, 'Please complete your registration first.')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')
    return redirect('dashboard:dashboard')


@login_required
def profile_view(request):

    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def update_profile_view(request):

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UpdateProfileForm(instance=request.user)
    
    return render(request, 'accounts/update_profile.html', {'form': form})


@login_required
def change_password_view(request):

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    else:
        form = ChangePasswordForm(user=request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def delete_account_view(request):
    password = request.POST.get('password')
    
    if not password:
        messages.error(request, 'Password is required to delete account.')
        return redirect('accounts:profile')
    
    if not request.user.check_password(password):
        messages.error(request, 'Invalid password.')
        return redirect('accounts:profile')
    
    user = request.user
    logout(request)
    user.delete()
    
    messages.success(request, 'Your account has been deleted successfully.')
    return redirect('accounts:signup')





def check_username_availability(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    username = request.GET.get('username')
    if not username:
        return JsonResponse({'error': 'Username parameter is required'}, status=400)
    
    exists = CustomUser.objects.filter(username=username).exclude(id=request.user.id).exists()
    return JsonResponse({'available': not exists})


def check_email_availability(request):
    email = request.GET.get('email')
    if not email:
        return JsonResponse({'error': 'Email parameter is required'}, status=400)
    
    user = CustomUser.objects.filter(email=email.lower()).first()
    
    if user and user.auth_status == 'done':
        available = False
    else:
        available = True
    
    return JsonResponse({'available': available})