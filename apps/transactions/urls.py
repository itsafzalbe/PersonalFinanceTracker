from django.urls import path
from .views import *



app_name = "transactions"

urlpatterns = [


    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('transactions/statistics/', TransactionStatisticsView.as_view(), name='transaction_statistics'),
    path('transactions/bulk-delete/', BulkDeleteView.as_view(), name='transaction_bulk_delete'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    path('tags/', TransactionTagListView.as_view(), name='transaction_tag_list'),
    path('tags/create/', TransactionTagCreateView.as_view(), name='transaction_tag_create'),
    path('tags/<int:pk>/delete/', TransactionTagDeleteView.as_view(), name='transaction_tag_delete'),

    
]