import stripe
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from djstripe.models import Customer, Invoice
from .plan import Plan
from stripe.error import InvalidRequestError
from djstripe.models import Customer, Invoice, Subscription
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
        if not self.stripe_customer_id:
            return None
        return Customer.objects.filter(id=self.stripe_customer_id).first()

    @property
    def last_payment_amount(self) -> float:
        cust = self.djstripe_customer
        if not cust:
            return 0.0
        inv = Invoice.objects.filter(
            customer=cust,
            paid=True
        ).order_by('-created').first()
        if not inv:
            return 0.0
        return float(inv.amount_paid or inv.total or 0)

    @property
    def next_payment_amount(self) -> float:
        if not self.stripe_customer_id:
            return 0.0
        stripe.api_key = (
            settings.STRIPE_LIVE_SECRET_KEY
            if settings.STRIPE_LIVE_MODE
            else settings.STRIPE_TEST_SECRET_KEY
        )
        try:
            preview = stripe.Invoice.upcoming(customer=self.stripe_customer_id)
            return float(preview.amount_due or preview.total or 0)
        except InvalidRequestError as e:
            if "No upcoming invoices" in str(e):
                return 0.0
            return 0.0

    def payment_difference(self) -> dict:
        prev = self.last_payment_amount
        nxt = self.next_payment_amount
        diff = round(nxt - prev, 2)
        return {
            'previous': prev,
            'next': nxt,
            'difference': abs(diff),
            'direction': 'higher' if diff > 0 else ('lower' if diff < 0 else 'same'),
        }

    @property
    def days_until_next_payment(self) -> int:
        # Se a próxima fatura existir, calcula dias para próxima cobrança
        # Usa upcoming invoice date do subscription se disponível
        # Aqui usamos next_payment_amount como indicativo, mas poderia basear-se em subscription.current_period_end
        # Para simplicidade, retornamos dias baseado em next_payment_date se armazenado
        # Caso contrário, retorna 0
        from datetime import datetime
        if self.plan.is_free:
            return _('Plano gratuito')
        # Se tiver data futura, usar next_payment_date
        if hasattr(self, 'next_payment_date') and self.next_payment_date:
            today = date.today()
            dy = max((self.next_payment_date.date() - today).days, 0)
            return _(f'Até próxima cobrança {dy} dias')
        return _('Sem próxima cobrança definida')

    def calculate_price(self) -> float:
        """
        Calcula preço com base no plano e extras:
          base (mensal/anual) + agentes + inboxes extras.
        """
        # Se não há plano associado, sem custo
        if not self.plan:
            return 0.0
        # Base mensal ou anual vem do plano
        base = {
            "month": self.plan.monthly_price,
            "year": self.plan.yearly_price,
        }.get(self.payment_interval, self.plan.monthly_price)
        
        # Cálculo de custos extras
        agents_cost = self.extra_agents * self.plan.extra_agent_price
        inboxes_cost = self.extra_inboxes * self.plan.extra_inbox_price
        return float(base + agents_cost + inboxes_cost)
    
    @property
    def payment_interval(self) -> str | None:
        """
        Retorna 'Mensal' ou 'Anual' baseado na assinatura ativa do cliente no Stripe.
        """
        cust = self.djstripe_customer
        if not cust:
            return None
        sub = Subscription.objects.filter(
            customer=cust, 
            status="active"
        ).order_by("-current_period_start").first()
        if not sub:
            return None
        # sub.plan.interval vem como 'month' ou 'year'
        return {
            "month": _("Mensal"),
            "year":  _("Anual"),
        }.get(sub.plan.interval, None)

    @property
    def agents_info(self) -> dict:
        """
        Returns a dict with:
          - used: number of agents currently in use
          - max:  total seats (plan + extras)
          - free: remaining seats (never negative)
        """
        used = len(self.chatwoot_account.all_agents)
        maximum = (self.plan.included_agents if self.plan else 0) + self.extra_agents
        free = max(maximum - used, 0)
        return {
            'used': used,
            'max': maximum,
            'free': free
        }
        
    @property
    def inboxes_info(self) -> dict:
        """
        Returns a dict with:
          - used: number of agents currently in use
          - max:  total seats (plan + extras)
          - free: remaining seats (never negative)
        """
        used = len(self.chatwoot_account.all_inboxes)
        maximum = (self.plan.included_inboxes if self.plan else 0) + self.extra_inboxes
        free = max(maximum - used, 0)
        return {
            'used': used,
            'max': maximum,
            'free': free
        }