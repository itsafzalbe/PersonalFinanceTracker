from django.urls import path
from . import views

app_name = 'transfers'

urlpatterns = [
    path('', views.transfer_list, name='transfer_list'),
    path('create/', views.transfer_create, name='transfer_create'),
    path('<int:pk>/', views.transfer_detail, name='transfer_detail'),
    path('history/', views.transfer_history, name='transfer_history'),
    path('api/exchange-rate/', views.get_exchange_rate, name='get_exchange_rate'),
    path('api/calculate/', views.calculate_transfer, name='calculate_transfer'),
]