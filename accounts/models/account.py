# accounts/models.py
from django.db import models
from .plan import Plan
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

class Account(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name=_('Plano'))
    status = models.CharField(max_length=20, choices=[('active', _('Ativo')), ('inactive', _('Inativo'))], verbose_name=_('Status'))
    start_date = models.DateTimeField(verbose_name=_('Data de início'))
    end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data de fim'))
    trial_end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data de fim do trial'))
    
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('Telefone'))
    email = models.EmailField(max_length=255, verbose_name=_('Email'))
    
    payment_method = models.CharField(max_length=50, verbose_name=_('Método de pagamento'))
    customer_id_payment = models.CharField(max_length=255, verbose_name=_('ID do cliente no pagamento'))
    payment_status = models.CharField(max_length=50, verbose_name=_('Status do pagamento'))
    last_payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data da última cobrança'))
    next_payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data da próxima cobrança'))
    failed_payments = models.IntegerField(default=0, verbose_name=_('Pagamentos falhados'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Criado em'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Atualizado em'))
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Conta')
        verbose_name_plural = _('Contas')

    def __str__(self):
        return f"Conta #{self.id}"


