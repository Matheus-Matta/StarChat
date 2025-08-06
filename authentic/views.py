from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from .forms import LoginForm, RegisterForm
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import stripe
from djstripe.models import Customer
from .forms import RegisterForm
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY  # modo teste

@csrf_protect
def custom_login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'index'
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)

                # Expiração da sessão
                if form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(60 * 60 * 24 * 30)  # 30 dias
                else:
                    request.session.set_expiry(0)  # até o navegador fechar

                # Segurança: valida se o next está no mesmo domínio
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('index')
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form, 'next': next_url})




@csrf_protect
def register(request):
    # Se o usuário já estiver logado, manda pro admin
    if request.user.is_authenticated:
        return redirect(reverse_lazy('admin:index'))

    # Pega o next (se vier via GET ?next=...)
    next_url = request.GET.get('next') or reverse_lazy('admin:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # cria user e account via form.save()
            user, account = form.save()

            # 1) Criar Customer no Stripe (modo teste)
            if not account.stripe_customer_id:
                customer_data = stripe.Customer.create(
                    email=user.email,
                    metadata={'account_id': account.pk}
                )
                # 2) Salvar o ID na conta
                account.stripe_customer_id = customer_data['id']
                account.save(update_fields=['stripe_customer_id'])
                # 3) Sincronizar com dj-stripe
                Customer.sync_from_stripe_data(customer_data)

            # Autentica e faz login automático
            auth_user = authenticate(
                request,
                username=user.username,
                password=form.cleaned_data['password']
            )
            if auth_user is not None:
                login(request, auth_user)
                # Garantir que next seja uma URL segura
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect(reverse('admin:index'))
            else:
                messages.error(request, "Erro ao autenticar após cadastro.")
        else:
            messages.error(request, "Corrija os erros do formulário antes de continuar.")

    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {
        'form': form,
        'next': next_url,
    })