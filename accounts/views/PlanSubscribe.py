# plans/views.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from django.urls import reverse_lazy
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from stripe.error import InvalidRequestError
import stripe

from accounts.forms import CombinedProfileForm
from accounts.models import Plan
from accounts.stripe_utils import delete_other_draft_invoices, void_other_open_invoices
from accounts.builder.checkout import StripeCheckoutBuilder  # checkout builder para conta FREE
from unfold.views import UnfoldModelAdminViewMixin
from accounts.utils import enforce_agent_limit, enforce_inbox_limit
stripe.api_key = settings.STRIPE_SECRET_KEY

# Pode sobrescrever via settings: STRIPE_ALLOWED_PAYMENT_METHOD_TYPES = ["card","boleto","pix"]
DEFAULT_ALLOWED_PM_TYPES: List[str] = ["card", "boleto", "pix"]
VALID_SUB_STATUSES: Set[str] = {"active", "trialing", "past_due", "unpaid", "incomplete", "paused"}


class PlanSubscribe(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    """
    Atualização/criação de assinatura:
      - Cartão: troca direta (charge_automatically) ou via Portal (caso "simples").
      - PIX/Bolet o: define send_invoice + days_until_due e envia a fatura (pagamento off-session).
      - Sem assinatura ativa: usa Checkout (StripeCheckoutBuilder).
    Provisionamento/alteração efetiva do plano é feito nos webhooks (invoice.paid), não aqui.
    """

    template_name = "admin/plan_subscribe.html"
    title = "Alterar Plano"
    permission_required: tuple = ()

    # ========================= Utilities por-request =========================

    def _get_origin(self, request: HttpRequest) -> str:
        use_xfh = getattr(settings, "USE_X_FORWARDED_HOST", False)
        proto = (request.META.get("HTTP_X_FORWARDED_PROTO") or request.scheme).split(",")[0].strip()
        host = request.META.get("HTTP_X_FORWARDED_HOST") if use_xfh else request.get_host()
        return f"{proto}://{host}"

    def _get_urls(self, request: HttpRequest) -> Dict[str, str]:
        origin = self._get_origin(request)
        return {
            "success_url": f"{origin}{reverse('admin:index')}",
            "cancel_url": f"{origin}{request.path}",
            "return_url": f"{origin}{reverse('admin:index')}",
        }

    def _account_supported_pm_types(self) -> Set[str]:
        """
        Descobre os payment_method_types ativos na conta (PaymentMethodConfiguration).
        Se a API não retornar nada, usa DEFAULT_ALLOWED_PM_TYPES.
        """
        supported: Set[str] = set()
        try:
            pmc = stripe.PaymentMethodConfiguration.list(limit=100)
            for cfg in pmc.auto_paging_iter():
                if cfg.get("active"):
                    for t in (cfg.get("payment_method_types") or []):
                        supported.add(t)
        except Exception:
            pass

        if not supported:
            supported.update(getattr(settings, "STRIPE_ALLOWED_PAYMENT_METHOD_TYPES", DEFAULT_ALLOWED_PM_TYPES))
        return supported

    def _allowed_methods_from_mode(self, pay_mode: str, supported: Set[str]) -> List[str]:
        desired_map = {
            "card": ["card"],
            "pix": ["pix"],
            "boleto": ["boleto"],
            "pix_boleto": ["pix", "boleto"],
        }
        desired = desired_map.get(pay_mode, ["card"])
        allowed = [t for t in desired if t in supported]
        if not allowed:
            return ["boleto"] if "boleto" in supported else ["card"]
        return allowed

    def _get_plan_or_redirect(self, request: HttpRequest, plan_id: Optional[str]) -> Optional[Plan]:
        if not plan_id:
            messages.error(request, "Plano não encontrado.")
            return None
        plan = Plan.objects.filter(pk=plan_id, is_active=True).first()
        if not plan or plan.is_plan_staff:
            messages.error(request, "Plano não encontrado.")
            return None
        if plan.is_free:
            messages.info(request, "O plano gratuito não pode ser alterado.")
            return None
        return plan

    def _ensure_customer(self, request: HttpRequest, account) -> bool:
        try:
            if not getattr(account, "stripe_customer_id", None):
                customer = stripe.Customer.create(email=account.email, metadata={"account_id": str(account.pk)})
                account.stripe_customer_id = customer["id"]
                account.save(update_fields=["stripe_customer_id"])
            return True
        except Exception:
            messages.error(request, "Falha ao preparar o cliente no Stripe.")
            return False

    def _list_active_sub(self, customer_id: str) -> Optional[dict]:
        subs = stripe.Subscription.list(
            customer=customer_id,
            status="all",
            expand=["data.items.data.price"],
            limit=20,
        )
        candidates = [s for s in subs.data if s.get("status") in VALID_SUB_STATUSES]
        candidates.sort(key=lambda s: int(s.get("current_period_start", 0)), reverse=True)
        return candidates[0] if candidates else None

    def _cancel_extra_active_subs(self, customer_id: str) -> None:
        try:
            subs = stripe.Subscription.list(customer=customer_id, status="all", limit=20)
            candidates = [s for s in subs.data if s.get("status") in VALID_SUB_STATUSES]
            for extra in candidates[1:]:
                try:
                    stripe.Subscription.modify(extra["id"], cancel_at_period_end=True, proration_behavior="none")
                except Exception:
                    pass
        except Exception:
            pass

    def _resolve_base_price(self, plan: Plan, interval: str) -> Optional[str]:
        return plan.billing_yearly_price_id if interval == "year" else plan.billing_monthly_price_id

    def _price_ids_for_extras(self, plan: Plan, interval: str) -> Dict[str, Optional[str]]:
        if interval == "year":
            return {
                "extra_agent_price_id": getattr(plan, "billing_extra_agent_price_id_yearly", None),
                "extra_inbox_price_id": getattr(plan, "billing_extra_inbox_price_id_yearly", None),
            }
        return {
            "extra_agent_price_id": getattr(plan, "billing_extra_agent_price_id", None),
            "extra_inbox_price_id": getattr(plan, "billing_extra_inbox_price_id", None),
        }

    def _get_base_item_from_sub(self, sub: dict) -> Optional[dict]:
        items = (sub.get("items") or {}).get("data", []) or []
        return next(
            (it for it in items if (it.get("price", {}) or {}).get("metadata", {}).get("kind") not in {"extra_agent", "extra_inbox"}),
            items[0] if items else None,
        )

    def _interval_from_price_obj(self, price_obj: Optional[dict]) -> Optional[str]:
        try:
            return ((price_obj or {}).get("recurring") or {}).get("interval")
        except Exception:
            return None

    def _interval_changed(self, sub: dict, desired_interval: str) -> bool:
        base_item = self._get_base_item_from_sub(sub)
        current_interval = self._interval_from_price_obj((base_item or {}).get("price"))
        return (current_interval is None) or (current_interval != desired_interval)

    def _build_incremental_items(
        self,
        sub: dict,
        plan: Plan,
        interval: str,
        base_price_id: str,
        extra_agents: int,
        extra_inboxes: int,
    ) -> List[dict]:
        """Monta a lista incremental de items para Subscription.modify."""
        items_param: List[dict] = []
        items_data = (sub.get("items") or {}).get("data", []) or []

        base_item = self._get_base_item_from_sub(sub)
        if base_item:
            items_param.append({"id": base_item["id"], "price": base_price_id, "quantity": 1})
        else:
            items_param.append({"price": base_price_id, "quantity": 1})

        prices = self._price_ids_for_extras(plan, interval)
        ea_price = prices["extra_agent_price_id"]
        ei_price = prices["extra_inbox_price_id"]

        agent_item = next(
            (it for it in items_data if (it.get("price", {}) or {}).get("metadata", {}).get("kind") == "extra_agent"),
            None,
        )
        if extra_agents and ea_price:
            items_param.append(
                {"id": agent_item["id"], "price": ea_price, "quantity": extra_agents} if agent_item
                else {"price": ea_price, "quantity": extra_agents}
            )
        elif agent_item:
            items_param.append({"id": agent_item["id"], "deleted": True})

        inbox_item = next(
            (it for it in items_data if (it.get("price", {}) or {}).get("metadata", {}).get("kind") == "extra_inbox"),
            None,
        )
        if extra_inboxes and ei_price:
            items_param.append(
                {"id": inbox_item["id"], "price": ei_price, "quantity": extra_inboxes} if inbox_item
                else {"price": ei_price, "quantity": extra_inboxes}
            )
        elif inbox_item:
            items_param.append({"id": inbox_item["id"], "deleted": True})

        return items_param

    def _get_portal_configuration_id(self) -> Optional[str]:
        cfg_id = getattr(settings, "STRIPE_PORTAL_CONFIGURATION_ID", None)
        if cfg_id:
            return cfg_id
        try:
            confs = stripe.billing_portal.Configuration.list(limit=1)
            if confs.data:
                return confs.data[0]["id"]
        except Exception:
            pass
        return None

    def _finalize_send_and_link(self, request: HttpRequest, account, invoice_id: str) -> Optional[str]:
        """
        Finaliza (se preciso), envia e devolve hosted_invoice_url.
        Também aplica higiene (void open / delete drafts) com try/except silencioso.
        """
        try:
            void_other_open_invoices(account.stripe_customer_id, keep_invoice_id=invoice_id)
            delete_other_draft_invoices(account.stripe_customer_id, keep_invoice_id=invoice_id)
        except Exception:
            pass

        inv = stripe.Invoice.retrieve(invoice_id)
        if inv.get("status") == "draft":
            inv = stripe.Invoice.finalize_invoice(invoice_id)

        # Evita "herdar" PM default
        try:
            stripe.Invoice.modify(invoice_id, default_payment_method=None)
        except Exception:
            pass

        try:
            stripe.Invoice.send_invoice(invoice_id)
        except Exception:
            pass

        pay_url = inv.get("hosted_invoice_url")
        if not pay_url:
            messages.error(request, "Não foi possível gerar o link de pagamento da fatura.")
            return None
        return pay_url
    
    # ========================= GET =========================

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")

        if not CombinedProfileForm.is_profile_complete(
            user=request.user, account=account, company=getattr(account, "company", None)
        ):
            messages.error(request, "Seu perfil ainda precisa ser completado.")
            return redirect("admin:user_profile")

        plan = self._get_plan_or_redirect(request, kwargs.get("plan_id"))
        if not plan:
            return redirect("admin:index")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        account = getattr(self.request.user, "account", None)
        plan = Plan.objects.filter(pk=kwargs.get("plan_id")).first()

        ctx["next_plan"] = plan
        ctx["current_plan"] = getattr(account, "plan", None)
        ctx["cancel_url"] = reverse("admin:index")

        other_plans = (
            Plan.objects.filter(is_active=True, is_plan_staff=False)
            .exclude(pk=getattr(account.plan, "pk", None))
            .order_by("monthly_price")
        )
        ctx["other_plans"] = other_plans

        # Métodos suportados
        supported = self._account_supported_pm_types()
        ctx["supports_pix"] = "pix" in supported
        ctx["supports_boleto"] = "boleto" in supported

        # Cartões salvos
        saved_cards, default_pm_id = [], None
        if account and getattr(account, "stripe_customer_id", None):
            try:
                cust = stripe.Customer.retrieve(
                    account.stripe_customer_id,
                    expand=["invoice_settings.default_payment_method"],
                )
                dpm = (cust.get("invoice_settings") or {}).get("default_payment_method")
                default_pm_id = dpm.get("id") if isinstance(dpm, dict) else (dpm if isinstance(dpm, str) else None)

                pms = stripe.PaymentMethod.list(customer=account.stripe_customer_id, type="card", limit=20)
                for pm in pms.data:
                    card = pm.get("card") or {}
                    saved_cards.append(
                        {
                            "id": pm["id"],
                            "brand": card.get("brand"),
                            "last4": card.get("last4"),
                            "exp_month": card.get("exp_month"),
                            "exp_year": card.get("exp_year"),
                            "is_default": pm["id"] == default_pm_id,
                        }
                    )
            except Exception:
                saved_cards, default_pm_id = [], None

            # Assinatura ativa?
            try:
                sub = self._list_active_sub(account.stripe_customer_id)
                ctx["has_active_subscription"] = bool(sub)
            except Exception:
                ctx["has_active_subscription"] = False
        else:
            ctx["has_active_subscription"] = False

        ctx["saved_cards"] = saved_cards
        ctx["default_pm_id"] = default_pm_id
        return ctx

    # ========================= POST =========================

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # -------- Pré-condições --------
        account = getattr(request.user, "account", None)
        if not account:
            messages.error(request, "Conta não encontrada.")
            return redirect("admin:index")

        if not CombinedProfileForm.is_profile_complete(
            user=request.user, account=account, company=getattr(account, "company", None)
        ):
            messages.error(request, "Seu perfil ainda precisa ser completado.")
            return redirect("admin:user_profile")

        plan = self._get_plan_or_redirect(request, request.POST.get("plan_id"))
        if not plan:
            messages.error(request, "Plano inválido.")
            return redirect("admin:index")

        interval = (request.POST.get("interval") or "month").strip()
        if interval not in {"month", "year"}:
            messages.error(request, "Intervalo inválido.")
            return redirect("admin:index")

        pay_mode = (request.POST.get("pay_mode") or "card").strip().lower()
        if pay_mode not in {"card", "boleto", "pix", "pix_boleto"}:
            pay_mode = "card"

        try:
            extra_agents = max(0, int(request.POST.get("extra_agents", "0") or 0))
            extra_inboxes = max(0, int(request.POST.get("extra_inboxes", "0") or 0))
        except ValueError:
            messages.error(request, "Valores inválidos para extras.")
            return redirect(request.path)

        if not self._ensure_customer(request, account):
            return redirect(request.path)

        base_price_id = self._resolve_base_price(plan, interval)
        if not base_price_id:
            messages.error(request, "Preço base indisponível para o ciclo escolhido.")
            return redirect(request.path)

        urls = self._get_urls(request)
        success_url = urls["success_url"]
        return_url = urls["return_url"]
        
        # --------- VALIDAÇÃO DE LIMITES (ANTES DE QUALQUER UPDATE/CHECKOUT) ---------
        included_agents = plan.included_agents
        included_inboxes = plan.included_inboxes
        total_agents_requested = included_agents + extra_agents
        total_inboxes_requested = included_inboxes + extra_inboxes
        print(total_agents_requested, total_inboxes_requested, included_agents, included_inboxes, extra_agents, extra_inboxes)
        resp = enforce_agent_limit(request, account, total_agents_requested, redirect_to=reverse_lazy("admin:account_agents"))
        if resp:
            return resp
        resp = enforce_inbox_limit(request, account, total_inboxes_requested, redirect_to=reverse_lazy("admin:account_inboxes"))
        if resp:
            return resp
        
        # -------- Assinatura atual --------
        active_sub = self._list_active_sub(account.stripe_customer_id)
        self._cancel_extra_active_subs(account.stripe_customer_id)

        # ====================== UPDATE: já existe assinatura ======================
        if active_sub:
            desired_interval = "year" if interval == "year" else "month"
            interval_changed = self._interval_changed(active_sub, desired_interval)

            if pay_mode == "card":
                # 1) Se troca simples do item base (sem extras e 1 item), manda para o Portal.
                items_count = len((active_sub.get("items") or {}).get("data", []) or [])
                if items_count == 1 and not (extra_agents or extra_inboxes):
                    try:
                        # Preenche metadados para a fatura de pró-rata
                        stripe.Subscription.modify(
                            active_sub["id"],
                            metadata={
                                "account_id": str(account.pk),
                                "selected_plan_id": str(plan.pk),
                                "selected_interval": interval,
                                "extra_agents": "0",
                                "extra_inboxes": "0",
                            },
                        )
                    except Exception:
                        pass

                    portal_cfg = self._get_portal_configuration_id()
                    if portal_cfg:
                        base_item = self._get_base_item_from_sub(active_sub) or {}
                        session = stripe.billing_portal.Session.create(
                            customer=account.stripe_customer_id,
                            return_url=return_url,
                            configuration=portal_cfg,
                            flow_data={
                                "type": "subscription_update_confirm",
                                "subscription_update_confirm": {
                                    "subscription": active_sub["id"],
                                    "items": [{"id": base_item.get("id"), "price": base_price_id, "quantity": 1}],
                                },
                            },
                        )
                        return redirect(session.url, permanent=False)

                # 2) Update direto via API (charge_automatically)
                try:
                    update_kwargs = dict(
                        items=self._build_incremental_items(
                            active_sub, plan, interval, base_price_id, extra_agents, extra_inboxes
                        ),
                        proration_behavior="create_prorations",
                        collection_method="charge_automatically",
                        payment_settings={"save_default_payment_method": "on_subscription"},
                        default_payment_method=(request.POST.get("pm_id") or None),
                        metadata={
                            "account_id": str(account.pk),
                            "selected_plan_id": str(plan.pk),
                            "selected_interval": interval,
                            "extra_agents": str(extra_agents or 0),
                            "extra_inboxes": str(extra_inboxes or 0),
                        },
                    )
                    update_kwargs["billing_cycle_anchor"] = "now" if interval_changed else "unchanged"

                    stripe.Subscription.modify(active_sub["id"], **update_kwargs)
                    messages.success(request, "Plano atualizado. A cobrança será feita automaticamente no cartão.")
                    return redirect(success_url)
                except Exception as e:
                    messages.error(request, f"Falha ao atualizar assinatura (cartão): {e}")
                    return redirect(request.path)

            # ---------------- PIX / BOLETO ----------------
            supported = self._account_supported_pm_types()
            try:
                allowed = self._allowed_methods_from_mode(pay_mode, supported)
                due_days = 3 if "boleto" in allowed else 1  # PIX: 1 dia; Boleto: 3 dias

                # (A) força send_invoice e remove PM default
                try:
                    stripe.Subscription.modify(
                        active_sub["id"],
                        collection_method="send_invoice",
                        days_until_due=due_days,
                        default_payment_method=None,
                        payment_settings=None,  # alguns ambientes aceitam limpar tudo
                    )
                except InvalidRequestError:
                    # fallback: limpa o essencial
                    stripe.Subscription.modify(
                        active_sub["id"],
                        collection_method="send_invoice",
                        days_until_due=due_days,
                        default_payment_method=None,
                    )

                # (B) também limpa default_payment_method do Customer (não "herdar" na Invoice)
                try:
                    stripe.Customer.modify(
                        account.stripe_customer_id,
                        invoice_settings={"default_payment_method": None},
                    )
                except Exception:
                    pass

                # (C) Update principal com items + tipos permitidos
                update_kwargs = dict(
                    items=self._build_incremental_items(
                        active_sub, plan, interval, base_price_id, extra_agents, extra_inboxes
                    ),
                    proration_behavior="create_prorations",
                    collection_method="send_invoice",
                    days_until_due=due_days,
                    default_payment_method=None,
                    payment_settings={"payment_method_types": allowed},
                    metadata={
                        "account_id": str(account.pk),
                        "selected_plan_id": str(plan.pk),
                        "selected_interval": interval,
                        "extra_agents": str(extra_agents or 0),
                        "extra_inboxes": str(extra_inboxes or 0),
                    },
                    expand=["latest_invoice"],
                )
                update_kwargs["billing_cycle_anchor"] = "now" if interval_changed else "unchanged"

                try:
                    updated = stripe.Subscription.modify(active_sub["id"], **update_kwargs)
                except InvalidRequestError as e:
                    msg = str(e) or ""
                    # PIX não habilitado → cai para boleto
                    if "payment_settings[payment_method_types]" in msg and "pix" in allowed:
                        update_kwargs["payment_settings"]["payment_method_types"] = ["boleto"]
                        update_kwargs["days_until_due"] = 3
                        updated = stripe.Subscription.modify(active_sub["id"], **update_kwargs)
                        messages.warning(
                            request, "PIX não está habilitado/compatível. Usamos boleto para concluir a atualização."
                        )
                    # default_payment_method herdado → limpa e repete
                    elif "default_payment_method" in msg:
                        try:
                            stripe.Subscription.modify(active_sub["id"], default_payment_method=None)
                        except Exception:
                            pass
                        try:
                            stripe.Customer.modify(
                                account.stripe_customer_id,
                                invoice_settings={"default_payment_method": None},
                            )
                        except Exception:
                            pass
                        updated = stripe.Subscription.modify(active_sub["id"], **update_kwargs)
                    else:
                        messages.error(request, f"Falha (pix/boleto): {e}")
                        return redirect(request.path)

                inv = updated.get("latest_invoice")
                if not inv:
                    messages.error(request, "Não foi possível obter a fatura da atualização.")
                    return redirect(request.path)

                pay_url = self._finalize_send_and_link(request, account, inv["id"])
                if not pay_url:
                    return redirect(request.path)
                return redirect(pay_url)

            except Exception as e:
                messages.error(request, f"Falha ao atualizar assinatura ({pay_mode}): {e}")
                return redirect(request.path)

        # ====================== SEM ASSINATURA VIVA → CRIAR VIA CHECKOUT ======================
        try:
            builder = StripeCheckoutBuilder(
                account=account,
                plan=plan,
                interval=interval,
                extra_agents=extra_agents,
                extra_inboxes=extra_inboxes,
                success_url=success_url,
                cancel_url=urls["cancel_url"],
            )
            session = builder.create_subscription_session(pay_mode=pay_mode)
            return redirect(session.url, permanent=False)

        except InvalidRequestError as e:
            msg = (str(e) or "").lower()
            if any(k in msg for k in ("payment_method", "payment_method_types", "payment_method_configuration")):
                messages.warning(request, "O método escolhido não está habilitado. Abrimos checkout no cartão.")
                session = builder.create_subscription_session(pay_mode="card")
                return redirect(session.url, permanent=False)

            messages.error(request, f"Falha ao criar checkout: {getattr(e, 'user_message', str(e))}")
            return redirect(request.path)

        except Exception as e:
            messages.error(request, f"Falha inesperada ao criar o checkout: {e}")
            return redirect(request.path)
