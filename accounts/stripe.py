# accounts/signals.py
# Sincronizador entre Account do Django e Customer no Stripe
# Configure também no apps.py para importar este módulo no ready().

import stripe
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from stripe.error import InvalidRequestError

from djstripe.models import Customer
from .models import Account

# Defina sua chave antes de chamadas à API
def _set_stripe_key():
    stripe.api_key = (
        settings.STRIPE_LIVE_SECRET_KEY
        if settings.STRIPE_LIVE_MODE
        else settings.STRIPE_TEST_SECRET_KEY
    )

@receiver(post_save, sender=Account)
def sync_stripe_customer(sender, instance, created, **kwargs):
    """
    Ao criar Account, cria Customer no Stripe.
    Ao atualizar Account, sincroniza email/metadata.
    """
    _set_stripe_key()

    # Se não temos ainda stripe_customer_id, criamos
    if created and not instance.stripe_customer_id:
        cust = stripe.Customer.create(
            email=instance.email,
            metadata={'account_id': instance.pk}
        )
        instance.stripe_customer_id = cust['id']
        instance.save(update_fields=['stripe_customer_id'])
        Customer.sync_from_stripe_data(cust)
        return

    # Se já existe, atualiza email e metadata
    if instance.stripe_customer_id:
        try:
            stripe.Customer.modify(
                instance.stripe_customer_id,
                email=instance.email,
                metadata={'account_id': instance.pk}
            )
            # opcional: sync local djstripe
            stripe_data = stripe.Customer.retrieve(instance.stripe_customer_id)
            Customer.sync_from_stripe_data(stripe_data)
        except InvalidRequestError:
            # Cliente pode ter sido removido no Stripe
            pass

@receiver(post_delete, sender=Account)
def delete_stripe_customer(sender, instance, **kwargs):
    """
    Ao deletar Account, opcionalmente remove Customer do Stripe.
    Cuidado: apaga histórico no Stripe!
    """
    if not instance.stripe_customer_id:
        return
    _set_stripe_key()
    try:
        stripe.Customer.delete(instance.stripe_customer_id)
    except InvalidRequestError:
        pass
