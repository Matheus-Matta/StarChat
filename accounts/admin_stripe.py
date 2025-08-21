from django.contrib import admin, messages
from django import forms
from django.conf import settings

import stripe
from djstripe.models import Invoice as DJInvoice, Customer as DJCustomer


# -------- Form só-leitura (evita editar o que vem do Stripe) --------
class ReadonlyInvoiceForm(forms.ModelForm):
    class Meta:
        model = DJInvoice
        # Mostra campos que fazem sentido inspecionar no admin
        fields = (
            "id", "customer", "status", "currency", "total", "amount_due",
            "amount_paid", "attempted", "paid", "number", "invoice_pdf",
            "period_start", "period_end", "created", "livemode"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.disabled = True  # torna o form só-leitura no admin

    def save(self, commit=True):
        # Bloqueia qualquer tentativa de salvar via admin
        raise forms.ValidationError(
            "Invoices são gerenciadas pela Stripe/dj-stripe e não devem ser editadas manualmente."
        )


# -------- Helpers de formatação --------
def _to_brl(amount_cents):
    if amount_cents is None:
        return "R$ 0,00"
    return f"R$ {amount_cents/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@admin.register(DJInvoice)
class InvoiceAdmin(admin.ModelAdmin):
    form = ReadonlyInvoiceForm

    list_display = (
        "id",
        "customer_link",
        "status",
        "total_brl",
        "amount_paid_brl",
        "created",
        "pdf_link",
        "livemode",
    )
    list_filter = ("status", "livemode", "currency", "created")
    search_fields = ("id", "number", "customer__id", "customer__email")
    ordering = ("-created",)
    readonly_fields = [f.name for f in DJInvoice._meta.fields]

    actions = ["sync_from_stripe", "sync_selected_from_stripe"]

    # ----- Colunas formatadas -----
    def customer_link(self, obj):
        cust = obj.customer  # djstripe.models.Customer
        if not cust:
            return "-"
        # mostra e-mail se houver
        return getattr(cust, "email", cust.id) or cust.id
    customer_link.short_description = "Cliente"

    def total_brl(self, obj):
        return _to_brl(obj.total)
    total_brl.short_description = "Total"

    def amount_paid_brl(self, obj):
        return _to_brl(obj.amount_paid)
    amount_paid_brl.short_description = "Pago"

    def pdf_link(self, obj):
        if getattr(obj, "invoice_pdf", None):
            return f'<a href="{obj.invoice_pdf}" target="_blank">PDF</a>'
        return "-"
    pdf_link.short_description = "Fatura (PDF)"
    pdf_link.allow_tags = True

    # ----- Ações -----
    def _configure_stripe(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def sync_from_stripe(self, request, queryset):
        """
        Sincroniza cada invoice selecionada buscando no Stripe e aplicando
        o payload no objeto dj-stripe correspondente.
        """
        self._configure_stripe()
        updated = 0
        errors = 0
        for inv in queryset:
            try:
                si = stripe.Invoice.retrieve(inv.id)  # carrega da Stripe
                DJInvoice.sync_from_stripe_data(si)   # aplica no dj-stripe
                updated += 1
            except Exception as e:
                errors += 1
        if updated:
            messages.success(request, f"{updated} invoice(s) sincronizada(s) com sucesso.")
        if errors:
            messages.warning(request, f"{errors} invoice(s) falharam ao sincronizar.")
    sync_from_stripe.short_description = "Sincronizar do Stripe (para selecionadas)"

    def sync_selected_from_stripe(self, request, queryset):
        # alias mais explícito para a mesma ação (opcional)
        return self.sync_from_stripe(request, queryset)
    sync_selected_from_stripe.short_description = "Sincronizar (Stripe → dj-stripe)"
