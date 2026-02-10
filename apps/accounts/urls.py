from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    path('signup/', views.signup_view, name='signup'),
    path('verify-code/', views.verify_code_view, name='verify-code'),
    path('resend-code/', views.resend_code_view, name='resend-code'),
    path('complete-registration/', views.complete_registration_view, name='complete_registration'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    

    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
    

    
    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/check-email/', views.check_email_availability, name='check_email'),
]
