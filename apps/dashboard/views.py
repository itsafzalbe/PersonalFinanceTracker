

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone


@login_required
def dashboard_view(request):
    from apps.transactions.models import Transaction
    from apps.cards.models import Card
    from apps.budgets.models import Budget
    
    user = request.user
    
    total_cards = Card.objects.filter(user=user, status='active').count()
    total_transactions = Transaction.objects.filter(user=user).count()
    total_budgets = Budget.objects.filter(user=user).count()
    

    from apps.cards.models import ExchangeRate, Currency
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
    
    recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:10]
    
    active_budgets = Budget.objects.filter(user=user)[:5]
    
    context = {
        'total_cards': total_cards,
        'total_transactions': total_transactions,
        'total_budgets': total_budgets,
        'total_balance': total_balance,
        'currency': user.default_currency,
        'recent_transactions': recent_transactions,
        'active_budgets': active_budgets,
        'member_since': user.created_at,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def statistics_view(request):
    from apps.transactions.models import Transaction
    from apps.cards.models import Card
    from apps.budgets.models import Budget
    from apps.cards.models import ExchangeRate, Currency
    
    user = request.user
    user_currency = Currency.objects.get(code=user.default_currency)
    
    total_cards = Card.objects.filter(user=user, status='active').count()
    total_transactions = Transaction.objects.filter(user=user).count()
    total_budgets = Budget.objects.filter(user=user).count()
    

    total_balance = 0
    cards = Card.objects.filter(user=user, status='active')
    for card in cards:
        if card.currency == user_currency:
            total_balance += card.balance
        else:
            converted = ExchangeRate.convert(card.balance, card.currency, user_currency)
            if converted:
                total_balance += converted
    

    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_income = Transaction.objects.filter(
        user=user,
        type='income',
        date__gte=current_month
    ).aggregate(
        total=Sum('amount_in_user_currency')
    )['total'] or 0
        
    monthly_expenses = Transaction.objects.filter(
        user=user,
        type='expense',
        date__gte=current_month
    ).aggregate(
        total=Sum('amount_in_user_currency')
    )['total'] or 0
    
    context = {
        'total_cards': total_cards,
        'total_transactions': total_transactions,
        'total_budgets': total_budgets,
        'total_balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'currency': user.default_currency,
        'member_since': user.created_at,
    }
    
    return render(request, 'statistics.html', context)

