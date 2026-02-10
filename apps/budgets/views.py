from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from datetime import timedelta, date
from decimal import Decimal
from collections import defaultdict

from .models import Budget
from .forms import BudgetForm
from .filters import BudgetFilter


class BudgetListView(LoginRequiredMixin, ListView):


    model = Budget
    template_name = 'budgets/list.html'
    context_object_name = 'budgets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Budget.objects.filter(user=self.request.user).select_related('category', 'currency')
        

        self.filterset = BudgetFilter(self.request.GET, queryset=queryset)
        queryset = self.filterset.qs
        

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(category__name__icontains=search_query)
            )
    
        ordering = self.request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['search_query'] = self.request.GET.get('search', '')
        context['ordering'] = self.request.GET.get('ordering', '-created_at')
        
        for budget in context['budgets']:
            budget.spent = budget.get_spent_amount()
            budget.percentage = budget.get_percentage_used()
            budget.remaining = budget.amount - budget.spent
            budget.over_budget = budget.is_over_budget()
        
        return context



class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budgets/detail.html'
    context_object_name = 'budget'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category', 'currency')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget = self.object
        
        context['spent'] = budget.get_spent_amount()
        context['percentage'] = budget.get_percentage_used()
        context['remaining'] = budget.amount - context['spent']
        context['is_over_budget'] = budget.is_over_budget()
        
        return context



class BudgetCreateView(LoginRequiredMixin, CreateView):

    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/form.html'
    success_url = reverse_lazy('budgets:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context

    def form_valid(self, form):
        category = form.cleaned_data['category']
        period = form.cleaned_data['period']
        
        existing = Budget.objects.filter(
            user=self.request.user,
            category=category,
            period=period,
            is_active=True
        ).exists()
        
        if existing:
            messages.error(
                self.request,
                f"You already have an active {period} budget for {category.name}. "
                "Update the existing budget or deactivate it first."
            )
            return self.form_invalid(form)
        
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Budget "{self.object.name}" created successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('budgets:detail', kwargs={'pk': self.object.pk})


class BudgetUpdateView(LoginRequiredMixin, UpdateView):

    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/form.html'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Budget "{self.object.name}" updated successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('budgets:detail', kwargs={'pk': self.object.pk})


class BudgetDeleteView(LoginRequiredMixin, DeleteView):

    model = Budget
    template_name = 'budgets/confirm_delete.html'
    success_url = reverse_lazy('budgets:list')

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        budget = self.get_object()
        messages.success(request, f'Budget "{budget.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)



class BudgetProgressView(LoginRequiredMixin, DetailView):

    model = Budget
    template_name = 'budgets/progress.html'
    context_object_name = 'budget'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category', 'currency')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget = self.object
        
        spent = budget.get_spent_amount()
        percentage = budget.get_percentage_used()
        remaining = budget.amount - spent
        
        today = date.today()
        
        if budget.period == 'weekly':
            period_start = today - timedelta(days=today.weekday())
            period_end = period_start + timedelta(days=6)
        elif budget.period == 'monthly':
            period_start = today.replace(day=1)
            if today.month == 12:
                period_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif budget.period == 'yearly':
            period_start = today.replace(month=1, day=1)
            period_end = today.replace(month=12, day=31)
        else:
            period_start = today
            period_end = today
        
        days_in_period = (period_end - period_start).days + 1
        days_elapsed = (today - period_start).days + 1
        days_remaining = (period_end - today).days
        
        average_daily_spending = spent / days_elapsed if days_elapsed > 0 else Decimal('0')
        suggested_daily_limit = remaining / days_remaining if days_remaining > 0 else Decimal('0')
        
        if budget.is_over_budget():
            status_text = 'over_budget'
        elif percentage >= budget.alert_threshold:
            status_text = 'warning'
        elif percentage >= 50:
            status_text = 'on_track'
        else:
            status_text = 'good'
        
        context.update({
            'spent': spent,
            'remaining': max(remaining, Decimal('0')),
            'percentage': percentage,
            'is_over_budget': budget.is_over_budget(),
            'period_start': period_start,
            'period_end': period_end,
            'days_total': days_in_period,
            'days_elapsed': days_elapsed,
            'days_remaining': max(days_remaining, 0),
            'average_daily_spending': average_daily_spending,
            'suggested_daily_limit': suggested_daily_limit,
            'status': status_text
        })
        
        return context


class BudgetActiveView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budgets/active.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        queryset = Budget.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('category', 'currency')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        for budget in context['budgets']:
            budget.spent = budget.get_spent_amount()
            budget.percentage = budget.get_percentage_used()
            budget.remaining = budget.amount - budget.spent
            budget.over_budget = budget.is_over_budget()
        
        return context


class BudgetOverviewView(LoginRequiredMixin, View):
    template_name = 'budgets/overview.html'

    def get(self, request):
        budgets = Budget.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('category', 'currency')
        
        if not budgets.exists():
            context = {
                'total_budgets': 0,
                'active_budgets': 0,
                'message': 'No active budgets found'
            }
            return render(request, self.template_name, context)
        
        from apps.cards.models import Currency, ExchangeRate
        u_crncy = Currency.objects.get(code=request.user.default_currency)
        
        total_budget_amount = Decimal('0')
        total_spent = Decimal('0')
        budgets_over_limit = 0
        budgets_at_warning = 0
        budgets_data = []
        
        for bdgt in budgets:
            if bdgt.currency == u_crncy:
                budget_amount = bdgt.amount
                spent_amount = bdgt.get_spent_amount()
            else:
                budget_amount = ExchangeRate.convert(bdgt.amount, bdgt.currency, u_crncy) or bdgt.amount
                spent_amount_original = bdgt.get_spent_amount()
                spent_amount = ExchangeRate.convert(spent_amount_original, bdgt.currency, u_crncy) or spent_amount_original
            
            total_budget_amount += budget_amount
            total_spent += spent_amount
            
            percentage = bdgt.get_percentage_used()
            if bdgt.is_over_budget():
                budgets_over_limit += 1
            elif percentage >= bdgt.alert_threshold:
                budgets_at_warning += 1
            
            bdgt.spent = bdgt.get_spent_amount()
            bdgt.percentage = percentage
            bdgt.over_budget = bdgt.is_over_budget()
            bdgt.remaining = bdgt.amount - bdgt.spent
            budgets_data.append(bdgt)
        
        total_remaining = total_budget_amount - total_spent
        overall_percentage = (total_spent / total_budget_amount * 100) if total_budget_amount > 0 else 0
        
        context = {
            'total_budgets': budgets.count(),
            'active_budgets': budgets.filter(is_active=True).count(),
            'total_budget_amount': total_budget_amount,
            'total_spent': total_spent,
            'total_remaining': total_remaining,
            'overall_percentage': round(overall_percentage, 2),
            'budgets_over_limit': budgets_over_limit,
            'budgets_at_warning': budgets_at_warning,
            'currency': request.user.default_currency,
            'budgets': budgets_data
        }
        
        return render(request, self.template_name, context)


class BudgetAlertsView(LoginRequiredMixin, View):

    template_name = 'budgets/alerts.html'

    def get(self, request):
        budgets = Budget.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('category', 'currency')
        
        alerts = []
        
        for budget in budgets:
            percentage = budget.get_percentage_used()
            
            if budget.is_over_budget():
                over_amount = budget.get_spent_amount() - budget.amount
                alerts.append({
                    'budget': budget,
                    'alert_type': 'over_budget',
                    'severity': 'high',
                    'message': f"You have exceeded your {budget.name} budget by {over_amount:,.0f} {budget.currency.code}",
                    'percentage_used': percentage
                })
            elif percentage >= budget.alert_threshold:
                remaining = budget.amount - budget.get_spent_amount()
                alerts.append({
                    'budget': budget,
                    'alert_type': 'warning',
                    'severity': 'medium',
                    'message': f"You have used {percentage:.1f}% of your {budget.name}. {remaining:,.0f} {budget.currency.code} remaining",
                    'percentage_used': percentage
                })
        
        alerts.sort(key=lambda x: (x['severity'] == 'medium', -x['percentage_used']))
        
        context = {
            'alert_count': len(alerts),
            'alerts': alerts
        }
        
        return render(request, self.template_name, context)


class BudgetToggleActiveView(LoginRequiredMixin, View):

    
    def post(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        
        budget.is_active = not budget.is_active
        budget.save()
        
        status_text = 'activated' if budget.is_active else 'deactivated'
        messages.success(request, f'Budget "{budget.name}" {status_text} successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'message': f"Budget {status_text}",
                'is_active': budget.is_active,
            })
        
        return redirect('budgets:detail', pk=pk)



class BudgetByCategoryView(LoginRequiredMixin, View):
    """
    GET /budgets/by-category/ - Get budgets grouped by category
    """
    template_name = 'budgets/by_category.html'

    def get(self, request):
        budgets = Budget.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('category', 'currency')
        
        categories_dict = defaultdict(list)
        
        for budget in budgets:
            budget.spent = budget.get_spent_amount()
            budget.percentage = budget.get_percentage_used()
            budget.over_budget = budget.is_over_budget()
            budget.remaining = budget.amount - budget.spent
            
            categories_dict[budget.category.id].append(budget)
        
        categories_list = []
        for category_id, budgets_list in categories_dict.items():
            if budgets_list:
                category = budgets_list[0].category
                categories_list.append({
                    'category': category,
                    'budgets': budgets_list
                })
        
        context = {
            'categories': categories_list
        }
        
        return render(request, self.template_name, context)


class BudgetByPeriodView(LoginRequiredMixin, View):
    template_name = 'budgets/by_period.html'

    def get(self, request):
        budgets = Budget.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('category', 'currency')
        
        periods = {
            'weekly': [],
            'monthly': [],
            'yearly': []
        }
        
        for budget in budgets:
            budget.spent = budget.get_spent_amount()
            budget.percentage = budget.get_percentage_used()
            budget.over_budget = budget.is_over_budget()
            budget.remaining = budget.amount - budget.spent
            
            periods[budget.period].append(budget)
        
        context = {
            'periods': periods
        }
        
        return render(request, self.template_name, context)


class BudgetSpendingHistoryView(LoginRequiredMixin, DetailView):

    model = Budget
    template_name = 'budgets/spending_history.html'
    context_object_name = 'budget'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category', 'currency')

    def get_context_data(self, **kwargs):
        from apps.transactions.models import Transaction
        from django.db.models.functions import TruncMonth
        
        context = super().get_context_data(**kwargs)
        budget = self.object
        
        months_back = int(self.request.GET.get('months_back', 6))
        
        today = timezone.now().date()
        start_date = today - timedelta(days=30 * months_back)
        
        transactions = Transaction.objects.filter(
            user=self.request.user,
            category=budget.category,
            type='expense',
            date__gte=start_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount_in_user_currency')
        ).order_by('month')
        
        history = []
        for item in transactions:
            month = item['month']
            spent = item['total']
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            
            history.append({
                'period': month.strftime('%Y-%m'),
                'month_name': month.strftime('%B %Y'),
                'spent': spent,
                'amount': budget.amount,
                'percentage': round(percentage, 2),
                'was_over_budget': spent > budget.amount
            })
        
        context['history'] = history
        context['months_back'] = months_back
        
        return context