# billing/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import re

try:
    # opcional (recomendado): pip install django-countries
    from django_countries.fields import CountryField
    COUNTRY_FIELD = CountryField
    COUNTRY_KW = {"default": "BR"}
except Exception:
    COUNTRY_FIELD = models.CharField
    COUNTRY_KW = {"max_length": 2, "default": "BR"}  # ISO-3166-1 alpha-2

CEP_RE = r"^\d{5}-?\d{3}$"

class Address(models.Model):
    BILLING = "billing"
    SHIPPING = "shipping"
    OTHER = "other"
    TYPE_CHOICES = [
        (BILLING,  _("Cobrança")),
        (SHIPPING, _("Entrega")),
        (OTHER,    _("Outro")),
    ]

    type = models.CharField(_("Tipo"), max_length=12, choices=TYPE_CHOICES, default=BILLING)
    is_default = models.BooleanField(_("Padrão"), default=False)

    name = models.CharField(_("Nome/Empresa"), max_length=255, blank=True)
    line1 = models.CharField(_("Endereço (linha 1)"), max_length=255)
    number = models.CharField(_("Número"), max_length=30, blank=True)
    line2 = models.CharField(_("Complemento"), max_length=255, blank=True)
    neighborhood = models.CharField(_("Bairro"), max_length=100, blank=True)

    city = models.CharField(_("Cidade"), max_length=100)
    state = models.CharField(_("Estado/Província"), max_length=100, blank=True)
    
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Conta"),
    )
    
    postal_code = models.CharField(
        _("CEP/Código Postal"),
        max_length=20,
        validators=[RegexValidator(r"^[A-Za-z0-9\- ]{3,12}$", _("Código postal inválido"))],
    )
    country = COUNTRY_FIELD(_("País"), **COUNTRY_KW)

    phone = models.CharField(_("Telefone"), max_length=30, blank=True)
    tax_id = models.CharField(_("CNPJ/CPF"), max_length=32, blank=True)  # opcional p/ notas/Stripe Tax

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # troque a antiga constraint global…
            # models.UniqueConstraint(fields=["type"], condition=models.Q(is_default=True), name="unique_default_address_per_type"),
            # …por esta, escopada por conta:
            models.UniqueConstraint(
                fields=["account", "type"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_type_per_account",
            ),
        ]

    def save(self, *args, **kwargs):
        # opcional, evita IntegrityError quando marcar outro padrão na mesma conta/tipo
        if self.is_default and self.account_id:
            Address.objects.filter(
                account_id=self.account_id,
                type=self.type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} • {self.line1}"

    # ---- validações úteis ----
    def clean(self):
        super().clean()
        code = getattr(self.country, "code", None) or self.country
        if code == "BR":
            if not re.match(CEP_RE, self.postal_code or ""):
                from django.core.exceptions import ValidationError
                raise ValidationError({"postal_code": _("CEP deve estar no formato 00000-000")})

    # ---- helpers ----
    @property
    def postal_code_normalized(self) -> str:
        code = getattr(self.country, "code", None) or self.country
        if code == "BR":
            digits = re.sub(r"\D", "", self.postal_code or "")
            return f"{digits[:5]}-{digits[5:8]}" if len(digits) == 8 else (self.postal_code or "")
        return (self.postal_code or "").upper()

    def as_stripe_address(self) -> dict:
        """Formata no payload esperado pelo Stripe."""
        code = getattr(self.country, "code", None) or self.country
        line1 = f"{self.line1} {self.number}".strip()
        line2_parts = [p for p in [self.neighborhood, self.line2] if p]
        return {
            "line1": line1[:500],
            "line2": (", ".join(line2_parts) or None),
            "postal_code": re.sub(r"\s", "", self.postal_code_normalized),
            "city": self.city,
            "state": self.state or None,
            "country": code,  # ISO-3166-1 alpha-2
        }