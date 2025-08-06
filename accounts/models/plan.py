# plans/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from colorfield.fields import ColorField
from datetime import date
import os

class Plan(models.Model):
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nome'),
        help_text=_("Nome do plano"),
        default='',
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descrição'),
        help_text=_("Descrição detalhada do plano")
    )
    
    requires_payment = models.BooleanField(
        default=True,
        verbose_name=_("Requer Cobrança"),
        help_text=_("Desmarque para planos gratuitos, sem cobrança automática")
    )
    
    billing_price_id = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=_("ID de Preço (Stripe/PSP)"),
        help_text=_("Use no gateway para criar/iniciar assinaturas; vazio=pago manual")
    )
    
    # Agentes
    included_agents = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Agentes Incluídos'),
        help_text=_('Quantidade de agentes inclusos no plano')
    )
    extra_agent_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=0,
        verbose_name=_('Preço por Agente Extra'),
        help_text=_('Valor cobrado por agente além do inclusos')
    )

    # Caixas de entrada (inboxes)
    included_inboxes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Inboxes Incluídas'),
        help_text=_('Quantidade de inboxes inclusas no plano')
    )
    extra_inbox_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=0,
        verbose_name=_('Preço por Inbox Extra'),
        help_text=_('Valor cobrado por inbox além das inclusas')
    )

    monthly_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name=_('Preço Mensal'),
        help_text=_('Valor da assinatura mensal')
    )
    
    yearly_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name=_('Preço Anual'),
        help_text=_('Valor da assinatura anual (geralmente com desconto)')
    )
    


    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Ativo'),
        help_text=_('Apenas planos ativos são oferecidos no front-end')
    )
    
    is_plan_staff = models.BooleanField(
        default=False,
        verbose_name=_('Plano de Equipe'),
        help_text=_('Marque se este plano é um plano de equipe')
    )
    
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=_('Favorito'),
        help_text=_('Marque se este plano é um plano favorito')
    )

    hex_color = ColorField(
        max_length=7,
        verbose_name=_('Cor'),
        help_text=_('Código de cor em hexadecimal (ex: #FF0000)'),
        blank=True,
        null=True,
    )

       
    history = HistoricalRecords()
    
    @property
    def is_free(self):
        if self.monthly_price == 0 and self.yearly_price == 0:
            return True
        
    class Meta:
        verbose_name = _('Plano')
        verbose_name_plural = _('Planos')
        
    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        if self.is_favorite:
            Plan.objects.filter(is_favorite=True).exclude(pk=self.pk).update(is_favorite=False)
        super().save(*args, **kwargs)