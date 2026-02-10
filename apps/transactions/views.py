from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import  timedelta
from decimal import Decimal

from .models import *
from apps.cards.models import *
from .forms import *



class CategoryListView(LoginRequiredMixin, ListView):
    template_name = "categories/list.html"
    context_object_name = "categories"
    
    def get_queryset(self):
        user = self.request.user
        qs = Category.objects.filter(
            Q(user=None) | Q(user=user),
            is_active=True
        )
        
        cat_type = self.request.GET.get('type')
        if cat_type in ['income', 'expense']:
            qs = qs.filter(type=cat_type)
        
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        
        return qs.order_by('type', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        all_categories = Category.objects.filter(
            Q(user=None) | Q(user=user),
            is_active=True
        )
        context['income_count'] = all_categories.filter(type='income').count()
        context['expense_count'] = all_categories.filter(type='expense').count()
        context['total_count'] = all_categories.count()
        
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "categories/form.html"
    success_url = reverse_lazy('transactions:tcategory_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Category'
        context['button_text'] = 'Create Category'
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "categories/form.html"
    success_url = reverse_lazy('transactions:tcategory_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        context['button_text'] = 'Update Category'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "categories/confirm_delete.html"
    success_url = reverse_lazy('transactions:category_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        if category.user is None:
            messages.error(request, "Cannot delete default categories.")
            return redirect('transactions:category_list')
        
        if category.transactions.exists():
            messages.error(request, "Cannot delete category with existing transactions. Set it as inactive instead.")
            return redirect('transactions:category_list')
        
        category_name = category.name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return result


class TransactionListView(LoginRequiredMixin, ListView):
    template_name = "transactions/list.html"
    context_object_name = "transactions"
    paginate_by = 20
    
    def get_queryset(self):
        qs = Transaction.objects.filter(
            user=self.request.user
        ).select_related(
            'card', 'category', 'card__currency', 'card__card_type'
        ).prefetch_related('transaction_tags__tag')
        
        transaction_type = self.request.GET.get('type')
        if transaction_type in ['income', 'expense']:
            qs = qs.filter(type=transaction_type)
        
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        card_id = self.request.GET.get('card')
        if card_id:
            qs = qs.filter(card_id=card_id)
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        return qs.order_by('-date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        all_transactions = Transaction.objects.filter(user=user)
        
        income_total = all_transactions.filter(type='income').aggregate(
            total=Sum('amount_in_user_currency')
        )['total'] or Decimal('0')
        
        expense_total = all_transactions.filter(type='expense').aggregate(
            total=Sum('amount_in_user_currency')
        )['total'] or Decimal('0')
        
        context['income_total'] = income_total
        context['expense_total'] = expense_total
        context['net_balance'] = income_total - expense_total
        context['total_transactions'] = all_transactions.count()
        
        context['categories'] = Category.objects.filter(
            Q(user=None) | Q(user=user),
            is_active=True
        ).order_by('type', 'name')
        context['cards'] = Card.objects.filter(user=user, status='active')
        context['filter_form'] = TransactionFilterForm(self.request.GET)
        
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = "transactions/detail.html"
    context_object_name = "transaction"
    
    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user
        ).select_related(
            'card', 'category', 'card__currency', 'card__card_type'
        ).prefetch_related('transaction_tags__tag')


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/form.html"
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Transaction'
        context['button_text'] = 'Add Transaction'
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        response = super().form_valid(form)
        
        tag_ids = self.request.POST.getlist('tags')
        if tag_ids:
            for tag_id in tag_ids:
                try:
                    tag = TransactionTag.objects.get(id=tag_id)
                    if tag.user is None or tag.user == self.request.user:
                        TransactionTagRelation.objects.create(
                            transaction=self.object,
                            tag=tag
                        )
                except TransactionTag.DoesNotExist:
                    pass
        
        messages.success(self.request, 'Transaction added successfully!')
        return response


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/form.html"
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Transaction'
        context['button_text'] = 'Update Transaction'
        context['current_tags'] = self.object.transaction_tags.values_list('tag_id', flat=True)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        tag_ids = self.request.POST.getlist('tags')

        TransactionTagRelation.objects.filter(transaction=self.object).delete()
        
        if tag_ids:
            for tag_id in tag_ids:
                try:
                    tag = TransactionTag.objects.get(id=tag_id)
                    if tag.user is None or tag.user == self.request.user:
                        TransactionTagRelation.objects.create(
                            transaction=self.object,
                            tag=tag
                        )
                except TransactionTag.DoesNotExist:
                    pass
        
        messages.success(self.request, 'Transaction updated successfully!')
        return response


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "transactions/confirm_delete.html"
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        transaction = self.get_object()
        transaction_title = transaction.title
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Transaction "{transaction_title}" deleted successfully.')
        return result


class TransactionStatisticsView(LoginRequiredMixin, ListView):
    template_name = "transactions/statistics.html"
    context_object_name = "transactions"
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        period = self.request.GET.get('period', 'month')
        
        today = timezone.now().date()
        if period == 'today':
            start_date = today
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month+1, day=1) - timedelta(days=1)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        else:
            start_date = today.replace(day=1)
            end_date = today
        
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        income_total = transactions.filter(type='income').aggregate(
            total=Sum('amount_in_user_currency')
        )['total'] or Decimal('0')
        
        expense_total = transactions.filter(type='expense').aggregate(
            total=Sum('amount_in_user_currency')
        )['total'] or Decimal('0')
        
        category_breakdown = transactions.values(
            'category__name', 'category__icon', 'type'
        ).annotate(
            total=Sum('amount_in_user_currency'),
            count=Count('id')
        ).order_by('-total')
        
        top_expense_categories = transactions.filter(type='expense').values(
            'category__name', 'category__icon',
        ).annotate(
            total=Sum('amount_in_user_currency')
        ).order_by('-total')[:5]
        
        top_income_categories = transactions.filter(type='income').values(
            'category__name', 'category__icon'
        ).annotate(
            total=Sum('amount_in_user_currency')
        ).order_by('-total')[:5]
        
        context.update({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'income_total': income_total,
            'expense_total': expense_total,
            'net_balance': income_total - expense_total,
            'income_count': transactions.filter(type='income').count(),
            'expense_count': transactions.filter(type='expense').count(),
            'total_count': transactions.count(),
            'category_breakdown': category_breakdown,
            'top_expense_categories': top_expense_categories,
            'top_income_categories': top_income_categories,
            'currency': user.default_currency,
        })
        
        return context


class BulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        transaction_ids = request.POST.getlist('transaction_ids')
        
        if not transaction_ids:
            messages.error(request, 'No transactions selected.')
            return redirect('transactions:transaction_list')
        
        transactions = Transaction.objects.filter(
            user=request.user,
            id__in=transaction_ids
        )
        
        count = transactions.count()
        transactions.delete()
        
        messages.success(request, f'{count} transaction(s) deleted successfully.')
        return redirect('transactions:transaction_list')



class TransactionTagListView(LoginRequiredMixin, ListView):
    template_name = "transactions/tags_list.html"
    context_object_name = "tags"
    
    def get_queryset(self):
        user = self.request.user
        return TransactionTag.objects.filter(
            Q(user=None) | Q(user=user)
        ).order_by('name')


class TransactionTagCreateView(LoginRequiredMixin, CreateView):
    model = TransactionTag
    form_class = TransactionTagForm
    template_name = "transactions/tag_form.html"
    success_url = reverse_lazy('transactions:transaction_tag_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Tag "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class TransactionTagDeleteView(LoginRequiredMixin, DeleteView):
    model = TransactionTag
    template_name = "transactions/tag_confirm_delete.html"
    success_url = reverse_lazy('transactions:transaction_tag_list')
    
    def get_queryset(self):
        return TransactionTag.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        tag = self.get_object()
        
        if tag.user is None:
            messages.error(request, "Cannot delete default tags.")
            return redirect('transactions:transaction_tag_list')
        
        tag_name = tag.name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Tag "{tag_name}" deleted successfully.')
        return result