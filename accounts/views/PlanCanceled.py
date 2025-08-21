# plans/views.py (view de cancelamento)
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from stripe.error import StripeError
from django.urls import reverse_lazy
from accounts.utils import get_free_plan , enforce_agent_limit , enforce_inbox_limit
from djstripe.models import Subscription as DJSubscription, Customer as DJCustomer

stripe.api_key = settings.STRIPE_SECRET_KEY

# Status considerados "vivos" (podem existir no Stripe e precisam ser achados para cancelar)
VALID_SUB_STATUSES = {"active", "trialing", "past_due", "unpaid", "incomplete", "paused"}


class PlanCanceled(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    template_name = "admin/plan_canceled.html"
    title = "Cancelar assinatura"
    permission_required = ()

    # ---------------------- helpers ----------------------
    def _get_account(self):
        return getattr(self.request.user, "account", None)

    def _stripe_connect_kwargs(self):
        connect_acct = getattr(settings, "STRIPE_CONNECT_ACCOUNT_ID", None)
        return {"stripe_account": connect_acct} if connect_acct else {}

    def _get_active_subscription_from_api(self):
        """
        Busca a assinatura no Stripe pelo customer_id. Se houver várias "vivas",
        usa a mais recente (current_period_start). Se houver id salvo na Account,
        tenta priorizar.
        """
        account = self._get_account()
        if not account or not account.stripe_customer_id:
            return None

        # 1) Prioriza o id salvo, se existir e for válido
        if getattr(account, "stripe_subscription_id", None):
            try:
                sub = stripe.Subscription.retrieve(
                    account.stripe_subscription_id,
                    **self._stripe_connect_kwargs(),
                )
                if sub and sub.get("status") in VALID_SUB_STATUSES and sub.get("customer") == account.stripe_customer_id:
                    return sub
            except StripeError:
                pass  # continua para varrer por customer

        # 2) Varre por customer
        subs = stripe.Subscription.list(
            customer=account.stripe_customer_id,
            status="all",
            limit=20,
            expand=["data.items"],  # precisamos dos itens para achar o item base
            **self._stripe_connect_kwargs(),
        )
        candidates = [s for s in subs.data if s.get("status") in VALID_SUB_STATUSES]
        candidates.sort(key=lambda s: int(s.get("current_period_start", 0)), reverse=True)
        return candidates[0] if candidates else None

    def _sync_djstripe(self, stripe_sub_obj):
        try:
            DJSubscription.sync_from_stripe_data(stripe_sub_obj)
        except Exception:
            pass  # não quebra a UX

    def _get_base_item_from_sub(self, sub_obj: dict):
        """
        Devolve o item "base" da assinatura (não-extra).
        Se não identificar pela metadata.kind, usa o primeiro item.
        """
        items = (sub_obj or {}).get("items") or {}
        data = items.get("data") or []
        if not data:
            return None
        for it in data:
            md = ((it.get("price") or {}).get("metadata")) or {}
            if md.get("kind") not in {"extra_agent", "extra_inbox"}:
                return it
        return data[0]

    def _cancel_subscription(self, when: str = "period_end") -> bool:
        """
        Cancela assinatura no Stripe (fonte da verdade) e sincroniza dj-stripe.
        when: "period_end" (padrão) ou "now"
        """
        account = self._get_account()
        if not account or not account.stripe_customer_id:
            messages.error(self.request, "Conta ou cliente Stripe não encontrado.")
            return False

        sub = self._get_active_subscription_from_api()
        if not sub:
            messages.error(self.request, "Nenhuma assinatura ativa encontrada para este cliente.")
            return False

        try:
            if when == "now":
                canceled = stripe.Subscription.cancel(sub["id"], **self._stripe_connect_kwargs())
                self._sync_djstripe(canceled)
                # opcional: limpe o ID local se tiver esse campo
                if hasattr(account, "stripe_subscription_id"):
                    try:
                        if account.stripe_subscription_id == sub["id"]:
                            account.stripe_subscription_id = None
                            account.save(update_fields=["stripe_subscription_id"])
                    except Exception:
                        pass
                messages.success(
                    self.request,
                    "Assinatura cancelada imediatamente. Se precisar de reembolso do período não utilizado, contate o suporte."
                )
            else:
                updated = stripe.Subscription.modify(
                    sub["id"],
                    cancel_at_period_end=True,
                    **self._stripe_connect_kwargs(),
                )
                self._sync_djstripe(updated)
                messages.success(
                    self.request,
                    "Cancelamento agendado para o fim do período atual. Você manterá o acesso até a data de renovação."
                )
            return True

        except StripeError as e:
            umsg = getattr(e, "user_message", "") or str(e)
            if "No such subscription" in umsg or "does not exist" in umsg:
                messages.error(
                    self.request,
                    "Não foi possível localizar essa assinatura no Stripe para a sua API key. "
                    "Verifique se o objeto foi criado no mesmo ambiente (test/live) e na mesma conta (Connect)."
                )
            else:
                messages.error(self.request, f"Falha ao cancelar a assinatura: {umsg}")
        except Exception:
            messages.error(self.request, "Ocorreu um erro inesperado ao cancelar a assinatura.")
        return False

    def get(self, request, *args, **kwargs):
        account = self._get_account()
        
        free_plan = get_free_plan()
        
        # --------- VALIDAÇÃO DE LIMITES (ANTES DE QUALQUER UPDATE/CHECKOUT) ---------
        resp = enforce_agent_limit(request, account, free_plan.included_agents, redirect_to=reverse_lazy("admin:account_agents"))
        if resp:
            messages.warning(request, "Não e possivel alterar para o plano free sem antes excluir todos os agentes.")
            return resp
        resp = enforce_inbox_limit(request, account, free_plan.included_inboxes, redirect_to=reverse_lazy("admin:account_inboxes"))
        if resp:
            messages.warning(request, "Não e possivel alterar para o plano free sem antes deixar apenas 1 inbox.")
            return resp
        
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")

        # Se já está em plano staff ou free, não há o que cancelar
        if getattr(account.plan, "is_plan_staff", False) or getattr(account.plan, "is_free", False):
            messages.warning(request, "Nenhuma assinatura ativa encontrada.")
            return redirect("admin:index")

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Aceita um input name="when" com 'now' ou 'period_end' (padrão: 'period_end').
        """
        when = (request.POST.get("when") or "period_end").strip()
        if when not in ("now", "period_end"):
            when = "period_end"
            
        free_plan = get_free_plan()
        
        account = self._get_account()
        
        ok = self._cancel_subscription(when=when)

        if when == "now" and ok and account:
            try:
                with transaction.atomic():
                    account.plan = free_plan
                    account.extra_agents = 0
                    account.extra_inboxes = 0
                    account.save(update_fields=["plan", "extra_agents", "extra_inboxes"])
            except Exception as e:
                messages.error(self.request, f"Ocorreu um erro ao cancelar a assinatura: {e}")
                return redirect("admin:plan_subscribed")

        if not ok:
            return redirect("admin:plan_subscribed")

        return redirect("admin:index")
