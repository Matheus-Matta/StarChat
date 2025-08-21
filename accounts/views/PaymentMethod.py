# plans/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin

import json
import stripe
from djstripe.models import Customer, PaymentMethod as DJPaymentMethod

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_customer_for_user(user):
    """
    Retorna o objeto Customer do dj-stripe associado ao usuário.
    Se não existir, levanta erro sem criar nada.
    """
    account = getattr(user, "account", None)
    if not account or not account.stripe_customer_id:
        raise ValueError("Usuário não possui stripe_customer_id definido.")

    try:
        customer = Customer.objects.get(id=account.stripe_customer_id)
    except ObjectDoesNotExist:
        raise ValueError(f"Cliente com ID {account.stripe_customer_id} não encontrado no dj-stripe.")

    return customer

class PaymentMethod(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    template_name = "admin/payment_method.html"
    title = "Métodos de Pagamento"
    permission_required = ()
    
    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")

        customer = get_customer_for_user(request.user)

        # SetupIntent para o Payment Element
        # Se quiser apenas cartão, use payment_method_types=["card"].
        setup_intent = stripe.SetupIntent.create(
            customer=customer.id,
            automatic_payment_methods={"enabled": True},
            usage="off_session",
        )

        # Lista cartões do cliente
        stripe_pms = stripe.PaymentMethod.list(customer=customer.id, type="card")
        stripe_cust = stripe.Customer.retrieve(customer.id)
        default_pm_id = (stripe_cust.get("invoice_settings") or {}).get("default_payment_method")

        ctx = self.get_context_data(
            stripe_publishable_key=settings.STRIPE_PUBLISHABLE_KEY,
            setup_intent_client_secret=setup_intent.client_secret,
            payment_methods=stripe_pms.data,
            default_payment_method_id=default_pm_id,
        )
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        """
        Recebe:
          - JSON com {"payment_method_id": "pm_xxx", "make_default": true/false}
          - OU form override para PUT/DELETE (_method)
        """
        method_override = (request.POST.get("_method") or "").upper()
        if method_override == "PUT":
            return self._make_default(request)
        if method_override == "DELETE":
            return self._delete_card(request)

        # Adicionar/anexar PM
        try:
            payload = json.loads((request.body or b"").decode() or "{}")
        except json.JSONDecodeError:
            payload = {}

        pm_id = payload.get("payment_method_id") or request.POST.get("payment_method_id")
        make_default = payload.get("make_default", True if request.POST.get("make_default", "true") in ("", "true") else False)

        if not pm_id:
            messages.error(request, "Nenhum cartão informado.")
            return redirect(request.path)

        customer = get_customer_for_user(request.user)

        try:
            pm = stripe.PaymentMethod.retrieve(pm_id)
            # anexa ao customer caso ainda não esteja
            if (pm.get("customer") or (pm.get("customer", {}) or {}).get("id")) != customer.id:
                stripe.PaymentMethod.attach(pm_id, customer=customer.id)

            if make_default:
                stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": pm_id})

            # sincroniza no dj-stripe (opcional; webhook já cobre)
            try:
                DJPaymentMethod.sync_from_stripe_data(stripe.PaymentMethod.retrieve(pm_id))
            except Exception:
                pass

            messages.success(request, "Cartão adicionado com sucesso.")
            return redirect(request.path)

        except stripe.error.StripeError as e:
            messages.error(request, getattr(e, "user_message", str(e)))
            return redirect(request.path)

    # ---- auxiliares PUT/DELETE via form override ----
    def _make_default(self, request):
        pm_id = request.POST.get("payment_method_id")
        if not pm_id:
            messages.error(request, "Informe o cartão para definir como padrão.")
            return redirect(request.path)

        customer = get_customer_for_user(request.user)
        try:
            pm = stripe.PaymentMethod.retrieve(pm_id)
            # só por segurança, valida o owner
            pm_customer_id = pm.get("customer") if isinstance(pm.get("customer"), str) else (pm.get("customer", {}) or {}).get("id")
            if pm_customer_id != customer.id:
                messages.error(request, "Cartão não pertence ao cliente.")
                return redirect(request.path)

            stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": pm_id})
            messages.success(request, "Cartão definido como padrão.")
        except stripe.error.StripeError as e:
            messages.error(request, getattr(e, "user_message", str(e)))
        return redirect(request.path)

    def _delete_card(self, request):
        pm_id = request.POST.get("payment_method_id")
        if not pm_id:
            messages.error(request, "Informe o cartão para remover.")
            return redirect(request.path)

        customer = get_customer_for_user(request.user)
        try:
            # Se default, limpa antes
            cust = stripe.Customer.retrieve(customer.id)
            default_pm_id = (cust.get("invoice_settings") or {}).get("default_payment_method")
            if default_pm_id == pm_id:
                stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": None})
            stripe.PaymentMethod.detach(pm_id)
            messages.success(request, "Cartão removido.")
        except stripe.error.StripeError as e:
            messages.error(request, getattr(e, "user_message", str(e)))
        return redirect(request.path)
