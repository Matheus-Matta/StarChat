# plans/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

class Plan(models.Model):
    TYPE_CHOICES = [
        ('free', _('Gratuito')),
        ('premium', _('Premium')),
        ('master', _('Master')),
    ]
    plan_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='free',
        verbose_name=_('Tipo de Plano')
    )
    name = models.CharField(blank=True, null=True, max_length=100, verbose_name=_('Nome'))
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_('Preço'))
    description = models.TextField(blank=True, verbose_name=_('Descrição'))
    is_active = models.BooleanField(default=True, verbose_name=_('Ativo'))

    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Plano')
        verbose_name_plural = _('Planos')

    def __str__(self):
        return f"{self.get_plan_type_display()}"
