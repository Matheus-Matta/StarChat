from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from accounts.models.account import Account
from starchat.services import ChatwootAccountService
from django.contrib.auth import get_user_model
User = get_user_model()

class ChatwootAccount(models.Model):
    # Assumes your SaaS uses a custom user/account model
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name="chatwoot_account",
    )
    # Numeric Chatwoot account ID
    chatwoot_id = models.PositiveIntegerField(unique=True, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "starchat_chatwoot_account"

    @property
    def all_agents(self):
        user = User.objects.filter(account=self.account, role='administrator').first()
        if not user:
            return []
        CW = ChatwootAccountService()
        agents = CW.get_all_agents(self.chatwoot_id, user_id=user.user_chatwoot_id)
        return agents
    
    @property
    def all_inboxes(self):
        user = User.objects.filter(account=self.account, role='administrator').first()
        if not user:
            return []
        CW = ChatwootAccountService()
        inboxes = CW.list_inboxes(self.chatwoot_id, user_id=user.user_chatwoot_id)
        return inboxes