# accounts/stripe_utils.py
import logging
import stripe
from django.conf import settings

log = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

def _sid(obj):
    # normaliza: objeto Stripe, dict expandido ou id string
    if isinstance(obj, str):
        return obj
    return getattr(obj, "id", None) or (obj.get("id") if isinstance(obj, dict) else None)

def void_other_open_invoices(customer_id: str, keep_invoice_id: str | None = None) -> int:
    """Anula (void) todas as invoices 'open' do cliente, exceto a keep."""
    if not customer_id:
        return 0
    n = 0
    for inv in stripe.Invoice.list(customer=customer_id, status="open", limit=100).auto_paging_iter():
        inv_id = _sid(inv)
        if keep_invoice_id and inv_id == keep_invoice_id:
            continue
        try:
            stripe.Invoice.void_invoice(inv_id)
            n += 1
        except Exception as e:
            log.warning("Não consegui void invoice %s: %s", inv_id, e)
    return n

def delete_other_draft_invoices(customer_id: str, keep_invoice_id: str | None = None) -> int:
    """Deleta invoices 'draft' do cliente, exceto a keep."""
    if not customer_id:
        return 0
    n = 0
    for inv in stripe.Invoice.list(customer=customer_id, status="draft", limit=100).auto_paging_iter():
        inv_id = _sid(inv)
        if keep_invoice_id and inv_id == keep_invoice_id:
            continue
        try:
            stripe.Invoice.delete(inv_id)
            n += 1
        except Exception as e:
            log.warning("Não consegui deletar draft %s: %s", inv_id, e)
    return n
