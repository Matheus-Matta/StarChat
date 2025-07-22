# core/models.py
from django.db import models
from .account import Account
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

class Company(models.Model):
    COMPANY_TYPE_CHOICES = [
        ('retail', _('Varejo')),
        ('technology', _('Tecnologia')),
        ('industry', _('Indústria')),
        ('health', _('Saúde')),
        ('educational', _('Educacional')),
        ('financial', _('Financeiro')),
        ('civil_construction', _('Construção Civil')),
        ('services', _('Serviços')),
        ('commerce', _('Comércio')),
        ('agriculture', _('Agricultura')),
        ('tourism', _('Turismo')),
        ('food', _('Alimentos')),
        ('automotive', _('Automotivo')),
        ('energy', _('Energia')),
        ('logistics', _('Logística')),
        ('others', _('Outros')),
    ]
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='company',
        verbose_name=_('Conta')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Nome')
    )
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name=_('CNPJ')
    )
    billing_address = models.JSONField(
        verbose_name=_('Endereço de cobrança')
    )
    company_type = models.CharField(
        max_length=20,
        choices=COMPANY_TYPE_CHOICES,
        verbose_name=_('Tipo de empresa')
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.name
        

