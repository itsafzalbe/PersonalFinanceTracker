from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from .models import SuppportMessage
from .forms import SupportForm



@login_required
def user_chat(request):
    user_message = SuppportMessage.objects.filter(user= request.user).order_by('created_at')
    user_message.filter(is_admin_reply = True, is_read = False).update(is_read=True)

    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            message =form.save(commit=False)
            message.user = request.user
            message.is_admin_reply = False
            message.is_read = False
            message.save()
            messages.success(request, 'Message sent')
            return redirect('support:user_chat')
    else:
        form = SupportForm()
    
    context = {
        'chat_messages': user_message,
        'form': form
    }
    return render(request, 'support/user_chat.html', context)



@staff_member_required
def admin_chat_list(request):
    User = get_user_model()

    users_w_messages = User.objects.filter(support__isnull = False).distinct()

    user_data = []
    for user in users_w_messages:
        unread_count = SuppportMessage.objects.filter(user=user, is_admin_reply = False, is_read = False).count()
        last_message = SuppportMessage.objects.filter(user=user).order_by('-created_at').first()
        user_data.append({
            'user': user,
            'unread_count': unread_count,
            'last_message': last_message
        })
    user_data.sort(
        key = lambda x: (
            x['unread_count'],
            x['last_message'].created_at if x['last_message'] else None

        ),
        reverse=True
    )

    context = {
        'user_data': user_data,
    }
    return render(request, 'support/admin_chat_list.html', context)
    



@staff_member_required
def admin_chat_detail(request, user_id):
    User = get_user_model()

    chat_user = get_object_or_404(User, id = user_id)
    user_message = SuppportMessage.objects.filter(user=chat_user).order_by('created_at')

    user_message.filter(is_admin_reply=False, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            message =form.save(commit=False)
            message.user = chat_user
            message.is_admin_reply = True
            message.is_read = False
            message.save()
            messages.success(request, 'Reply sent')
            return redirect('support:admin_chat_detail', user_id=user_id)
    else:
        form = SupportForm()
    
    context = {
        'chat_user': chat_user,
        'chat_messages': user_message,
        'form': form
    }
    return render(request, 'support/admin_chat_detail.html', context)


@login_required
def get_unread_count(request):
    if request.user.is_staff:
        count = SuppportMessage.objects.filter(is_admin_reply = False, is_read = False).count()
    else:
        count = SuppportMessage.objects.filter(user=request.user, is_admin_reply=True, is_read = False).count()
    
    return JsonResponse({'unread_count': count})
