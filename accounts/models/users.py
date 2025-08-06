# accounts/models/user.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from .account import Account
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='users',
    )
    
    user_chatwoot_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Chatwoot User ID'),
        help_text=_("ID do usuário no Chatwoot, se aplicável")
    )
    
    ROLE_CHOICES = (
        ('administrator', _('Administrator')),
        ('agent', _('Agent')),
    )

    role = models.CharField(
        max_length=100,
        choices=ROLE_CHOICES,
        verbose_name=_('Tipo de usuário'),
        default='agent',
    )
    
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        self.username = self.email
        self.account.email = self.email
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.account.email if self.account else self.get_full_name() or self.email