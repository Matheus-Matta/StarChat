import stripe
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from djstripe.models import Customer, Invoice
from .plan import Plan
from stripe.error import StripeError, InvalidRequestError
from djstripe.models import Customer, Invoice, Subscription
import logging
from datetime import datetime, date
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

log = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class Account(models.Model):
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Stripe Customer ID"),
        help_text=_("ID do cliente no Stripe para cobranças"),
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        verbose_name=_('Plano'),
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Telefone'),
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name=_('Email'),
    )
    extra_agents = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Agentes extras'),
    )
    extra_inboxes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Inboxes extras'),
    )
    status = models.CharField(
        choices=(
            ('active', _('Ativo')),
            ('suspended', _('Inativo')),
        ),
        max_length=255,
        default='active',
        verbose_name=_('Status'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Criado em'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Atualizado em'),
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Conta')
        verbose_name_plural = _('Contas')

    def __str__(self):
        return self.company.name if hasattr(self, 'company') else self.email

    @property
    def djstripe_customer(self):
        """
        Se você quiser manter dj-stripe para outras telas, ótimo,
        mas não use aqui para montar valores (evita diferença de unidade).
        """
        if not self.stripe_customer_id:
            return None
        try:
            return Customer.objects.filter(id=self.stripe_customer_id).first() or \
                   Customer.objects.filter(id=self.stripe_customer_id).first()
        except Exception:
            return None

    @property
    def last_payment_amount(self) -> float:
        """Última fatura paga em REAIS (Stripe API → centavos /100)."""
        if not self.stripe_customer_id:
            return 0.0
        try:
            invs = stripe.Invoice.list(customer=self.stripe_customer_id, limit=1, status='paid')
            inv = invs.data[0] if invs.data else None
            if not inv:
                return 0.0
            cents = inv.get("amount_paid") or inv.get("total") or 0
            return float(Decimal(cents) / Decimal(100))
        except StripeError:
            return 0.0

    @property
    def next_payment_amount(self) -> float:
        """Próxima fatura prevista em REAIS (Stripe API → centavos /100)."""
        if not self.stripe_customer_id:
            return 0.0
        try:
            preview = stripe.Invoice.upcoming(customer=self.stripe_customer_id)
            cents = (preview.get("amount_due") or preview.get("total") or 0) if preview else 0
            return float(Decimal(cents) / Decimal(100))
        except StripeError:
            return 0.0

    def payment_difference(self) -> dict:
        """Comparação coerente (ambos em R$)."""
        prev = self.last_payment_amount
        nxt = self.next_payment_amount
        diff = round(nxt - prev, 2)
        return {
            "previous": round(prev, 2),
            "next": round(nxt, 2),
            "difference": abs(diff),
            "direction": "higher" if diff > 0 else ("lower" if diff < 0 else "same"),
        }
        
    def _active_subscription(self):
        """Pega a assinatura ativa do Stripe (não dj-stripe)"""
        if not self.stripe_customer_id:
            return None
        try:
            subs = stripe.Subscription.list(customer=self.stripe_customer_id, status='active', limit=1)
            return subs.data[0] if subs.data else None
        except StripeError:
            return None
        
    def _interval_key(self) -> str:
        """
        'month' ou 'year' baseado na assinatura ativa do Stripe.
        Se não achar, default = 'month'.
        """
        sub = self._active_subscription()
        try:
            interval = sub["items"]["data"][0]["plan"]["interval"] if sub else "month"
            return interval if interval in ("month", "year") else "month"
        except Exception:
            return "month"   
             
    @property
    def days_until_next_payment(self):
        """
        Retorna string legível com dias restantes (ex.: 'Até próxima cobrança 12 dias')
        usando current_period_end da assinatura ativa.
        """
        sub = self._active_subscription()
        if not sub:
            return _('Sem próxima cobrança')

        try:
            ts = sub.get("current_period_end")
            if not ts:
                return _('Sem próxima cobrança')
            next_date = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            today = timezone.localdate()
            dy = max((next_date - today).days, 0)
            return _('Cobrança em %(days)s dias') % {"days": dy}
        except Exception:
            return _('Sem próxima cobrança')
        
    @property
    def calculate_price(self) -> float:
        """
        Retorna o preço do ciclo atual (mensal ou anual) com extras.
        Regras:
        - Base: monthly_price (se 'month') ou yearly_price (se 'year').
        - Extras:
            • Se houver campos anuais (ex.: extra_agent_price_yearly), usa-os quando interval='year'.
            • Senão, para interval='year', usa o preço mensal * 12.
        Tudo em reais (não em centavos).
        """
        if not self.plan:
            return 0.0

        def _dec(v) -> Decimal:
            return Decimal(str(v or 0))

        interval = self._interval_key()  # "month" | "year"

        # Base do plano
        base = _dec(self.plan.monthly_price if interval == "month" else self.plan.yearly_price)

        # ---- Extras: escolher a tarifa correta por intervalo ----
        if interval == "year":
            # Tenta usar campos anuais, se existirem; senão, mensal * 12
            agent_unit = getattr(self.plan, "extra_agent_price_yearly", None)
            inbox_unit = getattr(self.plan, "extra_inbox_price_yearly", None)

            agent_unit = _dec(agent_unit) if agent_unit is not None else _dec(self.plan.extra_agent_price) * 12
            inbox_unit = _dec(inbox_unit) if inbox_unit is not None else _dec(self.plan.extra_inbox_price) * 12
        else:
            agent_unit = _dec(self.plan.extra_agent_price)
            inbox_unit = _dec(self.plan.extra_inbox_price)

        agents_cost  = _dec(self.extra_agents)  * agent_unit
        inboxes_cost = _dec(self.extra_inboxes) * inbox_unit

        total = (base + agents_cost + inboxes_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(total)

    @property
    def payment_interval(self) -> str:
        """String legível (Mensal/Anual) a partir do intervalo real do Stripe."""
        key = self._interval_key()
        return {"month": _("Mensal"), "year": _("Anual")}.get(key, _("Mensal"))
        
    @property
    def all_agents(self):
        return self.chatwoot_account.all_agents
    
    @property
    def agents_info(self) -> dict:
        """
        Returns a dict with:
          - used: number of agents currently in use
          - max:  total seats (plan + extras)
          - free: remaining seats (never negative)
        """
        try:
            used = len(self.chatwoot_account.all_agents)
            maximum = (self.plan.included_agents if self.plan else 0) + self.extra_agents
            free = max(maximum - used, 0)
            return {
                'used': used,
                'max': maximum,
                'free': free
            }
        except Exception:
            log.exception("Erro ao obter informações dos agentes")
            return {'used': 0, 'max': 0, 'free': 0}
        
    @property
    def all_inboxes(self):
        return self.chatwoot_account.all_inboxes
    
    @property
    def inboxes_info(self) -> dict:
        """
        Returns a dict with:
          - used: number of agents currently in use
          - max:  total seats (plan + extras)
          - free: remaining seats (never negative)
        """
        try:
            used = len(self.chatwoot_account.all_inboxes)
            maximum = (self.plan.included_inboxes if self.plan else 0) + self.extra_inboxes
            free = max(maximum - used, 0)
            return {
                'used': used,
                'max': maximum,
                'free': free
            }
        except Exception:
            log.exception("Erro ao obter informações das caixas de entrada")
            return {'used': 0, 'max': 0, 'free': 0}

    @property
    def list_billing(self, limit: int = 5):
        """
        Retorna as últimas `limit` faturas (invoices) já pagas ou pendentes,
        para exibir no histórico de cobranças.
        
        
        """
        
        cust = self.djstripe_customer
        if not cust:
            return []
        invoices = (
            Invoice.objects
                   .filter(customer=cust)
                   .order_by("-created")
                   [:limit]
        )
        data = [
            {
                "id": inv.id,
                "amount_paid": float(inv.amount_paid or inv.total or 0) / 100,  # em reais
                "status": inv.status,
                "period_start": inv.period_start,
                "period_end": inv.period_end,
                "invoice_pdf": inv.invoice_pdf,  # link para o PDF
                "created": inv.created,
                "hosted_invoice_url": inv.hosted_invoice_url,
            }
            for inv in invoices
        ]
        return data 
    
    @property
    def list_payment_methods(self):
        if not self.stripe_customer_id:
            return []

        try:
            pm_list = stripe.PaymentMethod.list(
                customer=self.stripe_customer_id,
                type="card",
            )
            cust = stripe.Customer.retrieve(self.stripe_customer_id)
            default_pm = (cust.get("invoice_settings") or {}).get("default_payment_method")
            # default_pm pode ser string "pm_xxx" ou objeto
            default_pm_id = (
                default_pm if isinstance(default_pm, str) else (default_pm or {}).get("id")
            )
        except InvalidRequestError:
            return []

        methods = []
        for pm in pm_list.data:
            card = pm.card
            methods.append({
                "id": pm.id,
                "brand": card.brand,
                "last4": card.last4,
                "exp_month": card.exp_month,
                "exp_year": card.exp_year,
                "is_default": pm.id == default_pm_id,
            })
        return methods
    
    @property
    def credit_balance(self) -> float:
        """
        Retorna o crédito disponível do cliente em REAIS (R$).
        - Se sua conta Stripe já usa multi-saldo: usa `invoice_credit_balance['BRL']`.
        (normalmente positivo quando há crédito)
        - Fallback legado: usa `customer.balance` (inteiro em centavos),
        onde valor NEGATIVO significa crédito. Nesse caso, devolvemos o módulo.
        """
        if not self.stripe_customer_id:
            return 0.0
        try:
            # Tenta trazer o mapa de créditos por moeda
            cust = stripe.Customer.retrieve(
                self.stripe_customer_id,
                expand=["invoice_credit_balance"]
            )

            # 1) Novo formato (mapa por moeda)
            icb = getattr(cust, "invoice_credit_balance", None) or cust.get("invoice_credit_balance")
            if isinstance(icb, dict) and icb:
                cents = icb.get("BRL") or icb.get("brl") or 0
                # Em geral já é >= 0. Garantimos que crédito não fique negativo.
                credit = max(Decimal(cents), Decimal(0)) / Decimal(100)
                return float(credit.quantize(Decimal("0.01")))

            # 2) Legado: customer.balance (centavos). Negativo = crédito.
            cents_legacy = int(cust.get("balance") or 0)
            credit = Decimal(-cents_legacy) / Decimal(100) if cents_legacy < 0 else Decimal(0)
            return float(credit.quantize(Decimal("0.01")))

        except StripeError:
            return 0.0
        except Exception:
            return 0.0