import logging
from typing import Dict, Any, Optional

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from accounts.models import Account  # replace with the actual path

logger = logging.getLogger(__name__)

from .services import ChatwootAccountService
from django.contrib.auth import get_user_model
# Service instance
chatwoot_service = ChatwootAccountService()
User = get_user_model()

@receiver(post_save, sender=Account)
def sync_chatwoot_account(sender, instance: Account, created: bool, **kwargs) -> None:
    """
    Synchronizes Account changes with Chatwoot.
    
    Args:
        sender: The model class that sent the signal.
        instance: The Account instance that was saved.
        created: Boolean indicating if this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"sync_chatwoot_account: created={created}, instance={instance}")
    
    if created:
        chatwoot_service.create_chatwoot_account(instance)
    else:
        chatwoot_service.update_chatwoot_account(instance)


@receiver(pre_delete, sender=Account)
def delete_chatwoot_account(sender, instance: Account, **kwargs) -> None:
    """
    Deletes the associated Chatwoot account before deleting the Account.
    
    Args:
        sender: The model class that sent the signal.
        instance: The Account instance that will be deleted.
        **kwargs: Additional keyword arguments.
    """
    chatwoot_service.delete_chatwoot_account(instance)
    
@receiver(post_save, sender=User)
def sync_chatwoot_user(sender, instance, created, **kwargs):
    """
    - created=True: cria usuário no Chatwoot e persiste ChatwootUser
    - created=False: atualiza nome/email no Chatwoot
    """
    if created:
        data = chatwoot_service._create_chatwoot_user(instance)
    else:
        resp = data = chatwoot_service._update_chatwoot_user(instance)

@receiver(pre_delete, sender=User)
def delete_chatwoot_user(sender, instance, **kwargs):
    """
    Antes de remover um User no Django, deleta-o no Chatwoot.
    """
    data = chatwoot_service._delete_user_from_chatwoot(instance)
