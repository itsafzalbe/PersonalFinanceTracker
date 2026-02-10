from django.views.generic import ListView, FormView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum

from apps.cards.models import *
from .forms import *


class CurrencyListView(LoginRequiredMixin, ListView):
    template_name = "currency/list.html"
    context_object_name = "currencies"

    def get_queryset(self):
        qs = Currency.objects.filter(is_active=True)
        q = self.request.GET.get("search")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        return qs.order_by("code")


class CurrencyConvertView(LoginRequiredMixin, FormView):
    template_name = "currency/convert.html"
    form_class = CurrencyConversionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['currencies'] = Currency.objects.filter(is_active=True).order_by('code')
        return context

    def form_valid(self, form):
        amount = form.cleaned_data["amount"]
        from_code = form.cleaned_data["from_currency"]
        to_code = form.cleaned_data["to_currency"]

        try:
            from_currency = Currency.objects.get(code=from_code)
            to_currency = Currency.objects.get(code=to_code)
        except Currency.DoesNotExist:
            messages.error(self.request, "Invalid currency code")
            return self.form_invalid(form)

        converted = ExchangeRate.convert(amount, from_currency, to_currency)
        if converted is None:
            messages.error(self.request, "No exchange rate found")
            return self.form_invalid(form)

        rate = ExchangeRate.get_latest_rate(from_currency, to_currency)

        return render(self.request, self.template_name, {
            "form": form,
            "currencies": Currency.objects.filter(is_active=True).order_by('code'),
            "result": {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted": converted,
                "rate": rate,
                "date": timezone.now().date(),
            }
        })


class CardTypeListView(LoginRequiredMixin, ListView):
    template_name = "cards/card_types.html"
    context_object_name = "card_types"

    def get_queryset(self):
        return CardType.objects.filter(is_active=True).order_by("name")


class CardListView(LoginRequiredMixin, ListView):
    template_name = "cards/list.html"
    context_object_name = "cards"

    def get_queryset(self):
        qs = Card.objects.filter(
            user=self.request.user
        ).select_related("card_type", "currency")

        # optional status filter. if the user wnats to see active we hsow the only cards with that status, if not show all 
        status_filter = self.request.GET.get("status") 
        if status_filter:
            qs = qs.filter(status=status_filter)

        q = self.request.GET.get("search")
        if q:
            qs = qs.filter(
                Q(card_name__icontains=q) |
                Q(bank_name__icontains=q) |
                Q(card_number_last4__icontains=q)
            )

        return qs.order_by("-is_default", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        user_currency = Currency.objects.get(code=user.default_currency)
        total_balance = 0
        
        cards = Card.objects.filter(user=user, status='active')
        for card in cards:
            if card.currency == user_currency:
                total_balance += card.balance
            else:
                converted = ExchangeRate.convert(card.balance, card.currency, user_currency)
                if converted:
                    total_balance += converted
        
        context['total_balance'] = total_balance
        context['user_currency'] = user.default_currency
        context['active_cards_count'] = cards.count()
        context['card_types'] = CardType.objects.filter(is_active=True)
        
        return context


class CardDetailView(LoginRequiredMixin, DetailView):
    model = Card
    template_name = "cards/detail.html"
    context_object_name = "card"

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user).select_related('card_type', 'currency')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card = self.object

        context['recent_transactions'] = card.transactions.all().order_by('-date')[:10]
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['monthly_expenses'] = card.transactions.filter(
            type='expense',
            date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['monthly_income'] = card.transactions.filter(
            type='income',
            date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return context


class CardCreateView(LoginRequiredMixin, CreateView):
    template_name = "cards/form.html"
    form_class = CardForm
    success_url = reverse_lazy("cards:cards_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Card'
        context['button_text'] = 'Add Card'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Card "{form.instance.card_name}" added successfully!')
        return super().form_valid(form)


class CardUpdateView(LoginRequiredMixin, UpdateView):
    model = Card
    form_class = CardForm
    template_name = "cards/form.html"
    success_url = reverse_lazy("cards:cards_list")

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Card'
        context['button_text'] = 'Update Card'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Card "{form.instance.card_name}" updated successfully!')
        return super().form_valid(form)


class CardDeleteView(LoginRequiredMixin, DeleteView):
    model = Card
    template_name = "cards/confirm_delete.html"
    success_url = reverse_lazy("cards:cards_list")

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        card = self.get_object()

        if card.transactions.exists():
            messages.error(request, "Cannot delete card with existing transactions. Archive it instead.")
            return redirect('cards:card_detail', pk=card.pk)

        active_cards = Card.objects.filter(user=request.user, status="active")
        if active_cards.count() == 1 and card.status == "active":
            messages.error(request, "Cannot delete your only active card.")
            return redirect('cards:card_detail', pk=card.pk)

        card_name = card.card_name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Card "{card_name}" deleted successfully.')
        return result


class CardUpdateBalanceView(LoginRequiredMixin, FormView):
    form_class = CardBalanceUpdateForm
    template_name = "cards/update_balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card'] = get_object_or_404(Card, pk=self.kwargs["pk"], user=self.request.user)
        return context

    def form_valid(self, form):
        card = get_object_or_404(Card, pk=self.kwargs["pk"], user=self.request.user)
        old_balance = card.balance
        new_balance = form.cleaned_data["new_balance"]

        card.balance = new_balance
        card.save()

        messages.success(self.request, f'Balance updated from {old_balance} to {new_balance} {card.currency.code}')

        return render(self.request, self.template_name, {
            "card": card,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "difference": new_balance - old_balance,
            "reason": form.cleaned_data.get("reason"),
            "success": True
        })


class CardChangeStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        card = get_object_or_404(Card, pk=pk, user=request.user)
        status = request.POST.get("status")

        if status not in ["active", "inactive", "blocked"]:
            messages.error(request, "Invalid status")
            return redirect("cards:card_detail", pk=pk)

        if status in ["inactive", "blocked"]:
            card.is_default = False

        old_status = card.get_status_display()
        card.status = status
        card.save()

        messages.success(request, f'Card status changed from {old_status} to {card.get_status_display()}')
        return redirect("cards:card_detail", pk=pk)


class CardSetDefaultView(LoginRequiredMixin, View):
    def post(self, request, pk):
        card = get_object_or_404(Card, pk=pk, user=request.user)
        
        if card.status != 'active':
            messages.error(request, "Only active cards can be set as default")
            return redirect("cards:card_detail", pk=pk)
        
        Card.objects.filter(user=request.user).update(is_default=False)
        
        card.is_default = True
        card.save()
        
        messages.success(request, f'{card.card_name} is now your default card')
        return redirect("cards:cards_list")