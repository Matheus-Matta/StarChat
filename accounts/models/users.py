# accounts/models/user.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from .account import Account
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='users',
    )
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        
        if not self.username:
            self.username = self.email
            
        super().save(*args, **kwargs)