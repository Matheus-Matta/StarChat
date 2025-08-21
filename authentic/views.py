from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import logging
import stripe
from djstripe.models import Customer

from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)

# Configure a chave do Stripe (ideal: use STRIPE_SECRET_KEY e variáveis de ambiente)
stripe.api_key = getattr(settings, "STRIPE_TEST_SECRET_KEY", None) or getattr(settings, "STRIPE_SECRET_KEY", "")

# Duração padrão do "lembrar-me" (30 dias), pode ser sobrescrita no settings
REMEMBER_ME_SECONDS = getattr(settings, "REMEMBER_ME_SECONDS", 60 * 60 * 24 * 30)


def _safe_redirect(request: HttpRequest, next_url: Optional[str], default: str) -> HttpResponse:
    """
    Redireciona para next_url somente se for um host permitido e esquema válido.
    Caso contrário, redireciona para 'default'.
    """
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(default)


def _create_and_sync_stripe_customer(*, email: str, account) -> Optional[str]:
    """
    Cria um Customer no Stripe e sincroniza com o dj-stripe.
    Retorna o customer_id (str) em caso de sucesso, ou None em caso de falha.
    """
    try:
        customer_data = stripe.Customer.create(
            email=email,
            metadata={"account_id": account.pk},
        )
        # Sincroniza o objeto com o dj-stripe
        Customer.sync_from_stripe_data(customer_data)
        return customer_data.get("id")
    except stripe.error.StripeError as e:
        # Erros de API do Stripe
        logger.exception("Erro Stripe ao criar Customer: %s", e)
        return None
    except Exception as e:  # segurança extra
        logger.exception("Falha inesperada ao criar/sincronizar Customer: %s", e)
        return None


@csrf_protect
@require_http_methods(["GET", "POST"])
def custom_login(request: HttpRequest) -> HttpResponse:
    """
    Autentica o usuário e aplica 'lembrar-me'.
    Respeita o parâmetro ?next= com validação de host e esquema.
    """
    # Damos preferência ao POST (se houver), senão GET; fallback: 'index'
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("index")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user is None:
                messages.error(request, _("Usuário ou senha inválidos."))
                return render(request, "auth/login.html", {"form": form, "next": next_url})

            # Login e expiração de sessão
            login(request, user)
            if form.cleaned_data.get("remember_me"):
                request.session.set_expiry(REMEMBER_ME_SECONDS)  # 30 dias (ou valor custom)
            else:
                request.session.set_expiry(0)  # expira ao fechar o navegador

            return _safe_redirect(request, next_url, default=reverse("index"))

        # Form inválido
        messages.error(request, _("Corrija os erros do formulário para continuar."))
        return render(request, "auth/login.html", {"form": form, "next": next_url})

    # GET
    return render(request, "auth/login.html", {"form": LoginForm(), "next": next_url})


@csrf_protect
@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    """
    Registra um novo usuário + Account via RegisterForm.
    Cria/sincroniza o Customer no Stripe de forma atômica.
    Faz login automático ao final e redireciona com segurança.
    """
    if request.user.is_authenticated:
        # Usuário logado não deve ver cadastro
        return redirect(reverse_lazy("admin:index"))

    next_url = request.GET.get("next") or reverse_lazy("admin:index")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if not form.is_valid():
            messages.error(request, _("Corrija os erros do formulário antes de continuar."))
            return render(request, "auth/register.html", {"form": form, "next": next_url})

        # Transação para evitar estados parciais
        with transaction.atomic():
            # O form deve retornar (user, account)
            user, account = form.save()

            # Cria o Customer no Stripe se ainda não existir
            if not getattr(account, "stripe_customer_id", None):
                customer_id = _create_and_sync_stripe_customer(email=user.email, account=account)

                if not customer_id:
                    # Qualquer erro de Stripe aborta este passo, mas mantém o user/account criados.
                    # Você pode decidir levantar exceção para rollback total, se preferir.
                    messages.warning(
                        request,
                        _("Cadastro concluído, porém houve um problema ao criar seu cadastro de cobrança. "
                          "Nossa equipe será notificada."),
                    )
                else:
                    account.stripe_customer_id = customer_id
                    account.save(update_fields=["stripe_customer_id"])

        # Autentica e realiza login automático
        auth_user = authenticate(
            request,
            username=user.username,
            password=form.cleaned_data["password"],
        )
        if auth_user is not None:
            login(request, auth_user)
            return _safe_redirect(request, next_url, default=reverse("admin:index"))

        messages.error(request, _("Erro ao autenticar após cadastro."))
        return render(request, "auth/register.html", {"form": form, "next": next_url})

    # GET
    return render(request, "auth/register.html", {"form": RegisterForm(), "next": next_url})
