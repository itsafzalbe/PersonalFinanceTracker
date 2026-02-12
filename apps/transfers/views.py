

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from decimal import Decimal
from .models import *
from .forms import *
from apps.cards.models import *
from django.db.models.functions import TruncMonth

@login_required
def transfer_create(request):
    if request.method == 'POST':
        form = CardTransferForm(request.POST, user =request.user)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.user = request.user
            try:
                transfer.save()
                messages.success(
                    request,
                    f"Successfully transfered {transfer.amount:,.2f} {transfer.from_card.currency.code}"
                    f"From {transfer.from_card.card_name} to {transfer.to_card.card_name}"

                )
                return redirect('transfers:transfer_detail', pk=transfer.pk)
            except Exception as e:
                messages.error(request, f"Transfer failed: {str(e)}")
                return redirect('transfers:transfer_create')
    else:
        form = CardTransferForm(user = request.user)
    
    user_cards = Card.objects.filter(user=request.user, status='active')

    context = {
        'form': form,
        'user_cards': user_cards,
    }
    return render(request, 'transfers/transfer_create.html', context)



@login_required
def transfer_list(request):
    transfers = CardTransfer.objects.filter(user=request.user).select_related('from_card', 'to_card', 'from_card__currency', 'to_card__currency')
    card_filter = request.GET.get('card')
    if card_filter:
        transfers = transfers.filter(Q(from_card_id=card_filter) | Q(to_card_id=card_filter))
    
    total_transferred= transfers.filter(from_card__currency__code=request.user.default_currency).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    context = {
        'transfers': transfers,
        'total_transferred': total_transferred,
        'user_cards': Card.objects.filter(user=request.user,status='active'),
        'card_filter': card_filter

    }
    return render(request, 'transfers/transfer_list.html', context)


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(
        CardTransfer.objects.select_related(
            'from_card', 'to_card',
            'from_card__currency', 'to_card__currency',
            'from_card__card_type', 'to_card__card_type'
        ),
        pk=pk,
        user= request.user
    )
    context = {
        'transfer': transfer
    }
    return render(request, 'transfers/transfer_detail.html', context)





@login_required
def get_exchange_rate(request):
    from_currency_code = request.GET.get('from')
    to_currency_code = request.GET.get('to')

    if not from_currency_code or not to_currency_code:
        return JsonResponse({'error': 'Missing currency codes'}, status =400)
    
    try:
        from_currency = Currency.objects.get(code=from_currency_code)
        to_currency = Currency.objects.get(code=to_currency_code)

        if from_currency == to_currency:
            return JsonResponse({
                'rate': 1.0,
                'from_currency': from_currency_code,
                'to_currency': to_currency_code,
                'same_currency': True
            })
        rate = ExchangeRate.get_latest_rate(from_currency, to_currency)

        if rate:
            return JsonResponse({
                'rate': float(rate),
                'from_currency': from_currency_code,
                'to_currency': to_currency_code,
                'same_currency': False
            })
        else:
            return JsonResponse({
                'error': f"Exchange rate not available for {from_currency_code} to {to_currency_code}"
            }, status=404)
    
    except Currency.DoesNotExist:
        return JsonResponse({'error': "Invalid currency code"}, status = 400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status = 500)









@login_required
def calculate_transfer(request):
    amount = request.GET.get('amount')
    from_card_id= request.GET.get('from_card')
    to_card_id = request.GET.get('to_card')

    try:
        amount = Decimal(amount)
        from_card = Card.objects.get(id=from_card_id, user=request.user)
        to_card = Card.objects.get(id=to_card_id, user=request.user)

        if from_card == to_card:
            return JsonResponse({'error': 'Cannot transfer to same card'}, status=400)
        
        if amount > from_card.balance:
            return JsonResponse({
                'error': 'Insufficient balance',
                'available': float(from_card.balance)
            }, status=400)
        
        if from_card.currency != to_card.currency:
            rate = ExchangeRate.get_latest_rate(from_card.currency, to_card.currency)
            converted_amount = amount * rate
        else:
            rate = Decimal('1.0')
            converted_amount = amount
        
        return JsonResponse({
            'amount': float(amount),
            'converted_amount': float(converted_amount),
            'exchange_rate': float(rate),
            'from_currency': from_card.currency.code,
            'to_currency': to_card.currency.code,
            'from_balance': float(from_card.balance),
            'to_balance': float(to_card.balance),
            'new_from_balance': float(from_card.balance - amount),
            'new_to_balance': float(to_card.balance + converted_amount),
        })
    
    except (ValueError, Card.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=400)
    


@login_required
def transfer_history(request):
    transfers = CardTransfer.objects.filter( user=request.user ).select_related('from_card', 'to_card')
    monthly_stats = transfers.annotate( month=TruncMonth('created_at')).values('month').annotate( count=Count('id'), total=Sum('amount')).order_by('-month')
    context = {
        'transfers': transfers[:20],
        'monthly_stats': monthly_stats[:6],
        'total_count': transfers.count(),
    }
    return render(request, 'transfers/transfer_history.html', context)





