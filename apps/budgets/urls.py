from django.urls import path
from .views import *


app_name = 'budgets'


urlpatterns = [


    path('budgets/', BudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/', BudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/<int:pk>/update/', BudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', BudgetDeleteView.as_view(), name='budget_delete'),
    path('budgets/overview/', BudgetOverviewView.as_view(), name='budget_overview'),
    path('budgets/active/', BudgetActiveView.as_view(), name='budget_active'),
    path('budgets/alerts/', BudgetAlertsView.as_view(), name='budget_alerts'),
    path('budgets/by-category/', BudgetByCategoryView.as_view(), name='budget_by_category'),
    path('budgets/by-period/', BudgetByPeriodView.as_view(), name='budget_by_period'),
    path('budgets/<int:pk>/progress/', BudgetProgressView.as_view(), name='budget_progress'),
    path('budgets/<int:pk>/spending-history/', BudgetSpendingHistoryView.as_view(), name='budget_spending_history'),
    path('budgets/<int:pk>/toggle-active/', BudgetToggleActiveView.as_view(), name='budget_toggle_active'),


]