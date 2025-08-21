# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from unfold.contrib.forms.widgets import UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div
from core.forms import Button, Link
from django.urls import reverse_lazy
from django_countries import countries

from accounts.models import Account, Company, Address

import re

User = get_user_model()

_CNPJ_RE_DIGITS = re.compile(r"\D+")

def country_choices_br_first():
    all_choices = list(countries)
    br = [c for c in all_choices if c[0] == "BR"]
    rest = [c for c in all_choices if c[0] != "BR"]
    return br + rest

def _digits_only(value: str) -> str:
    return _CNPJ_RE_DIGITS.sub("", value or "")

def _validate_cnpj_digits(cnpj: str) -> str:
    c = _digits_only(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        raise forms.ValidationError(_("CNPJ inválido."))

    def _calc(digs, weights):
        s = sum(int(d) * w for d, w in zip(digs, weights))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    d1 = _calc(c[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    d2 = _calc(c[:12] + d1, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    if c[-2:] != d1 + d2:
        raise forms.ValidationError(_("CNPJ inválido."))
    return c

def _format_cnpj(c14: str) -> str:
    c = _digits_only(c14)
    if len(c) != 14:
        return c14
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"

class CombinedProfileForm(forms.Form):
    # Usuário
    first_name = forms.CharField(label=_("Primeiro nome"), max_length=150, required=True,
                                 widget=UnfoldAdminTextInputWidget())
    last_name  = forms.CharField(label=_("Sobrenome"), max_length=150, required=False,
                                 widget=UnfoldAdminTextInputWidget())
    email      = forms.EmailField(label=_("E-mail"), required=True,
                                  widget=UnfoldAdminTextInputWidget())
    phone      = forms.CharField(label=_("Telefone"), max_length=20, required=True,
                                 widget=UnfoldAdminTextInputWidget())

    # Empresa
    name         = forms.CharField(label=_("Nome da Empresa"), max_length=255, required=True,
                                   widget=UnfoldAdminTextInputWidget())
    cnpj         = forms.CharField(label=_("CNPJ"), max_length=20, required=True,
                                   widget=UnfoldAdminTextInputWidget())
    company_type = forms.ChoiceField(label=_("Tipo de Empresa"),
                                     choices=Company.COMPANY_TYPE_CHOICES, required=True,
                                     widget=UnfoldAdminSelectWidget())

    # Endereço (cobrança)
    addr_line1        = forms.CharField(label=_("Endereço"), max_length=255, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_number       = forms.CharField(label=_("Número"), max_length=30, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_line2        = forms.CharField(label=_("Complemento"), max_length=255, required=False,
                                        widget=UnfoldAdminTextInputWidget())
    addr_neighborhood = forms.CharField(label=_("Bairro"), max_length=100, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_city         = forms.CharField(label=_("Cidade"), max_length=100, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_state        = forms.CharField(label=_("Estado/Província"), max_length=100, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_postal_code  = forms.CharField(label=_("CEP/Código Postal"), max_length=20, required=True,
                                        widget=UnfoldAdminTextInputWidget())
    addr_country      = forms.ChoiceField(
        label=_("País"),
        required=True,
        choices=country_choices_br_first(),
        initial="BR",
        widget=UnfoldAdminSelectWidget(attrs={"data-placeholder": _("Selecione o país")}),
    )

    def __init__(self, *args, **kwargs):
        self.user    = kwargs.pop("user", None)
        self.account = kwargs.pop("account", None)
        self.company = kwargs.pop("company", None)

        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.template_pack = "unfold_crispy"
        self.helper.form_class = "space-y-6"

        u, a, c = self.user, self.account, self.company
        addr = a.addresses.filter(type=Address.BILLING, is_default=True).first() if a else None

        # User initial
        if u:
            self.fields["first_name"].initial = u.first_name
            self.fields["last_name"].initial  = u.last_name
            self.fields["email"].initial      = u.email

        # Account initial
        if a:
            self.fields["phone"].initial = a.phone

        # Company initial
        if c:
            self.fields["name"].initial         = c.name
            self.fields["cnpj"].initial         = c.cnpj
            self.fields["company_type"].initial = c.company_type

        # Address initial
        if addr:
            self.fields["addr_line1"].initial        = addr.line1
            self.fields["addr_number"].initial       = addr.number
            self.fields["addr_line2"].initial        = addr.line2
            self.fields["addr_neighborhood"].initial = addr.neighborhood
            self.fields["addr_city"].initial         = addr.city
            self.fields["addr_state"].initial        = addr.state
            self.fields["addr_postal_code"].initial  = addr.postal_code
            self.fields["addr_country"].initial      = getattr(addr.country, "code", None) or addr.country
        else:
            self.fields["addr_country"].initial = "BR"

        self.helper.layout = Layout(
            Fieldset(
                _("Usuário"),
                Div("first_name", "last_name", css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                Div("email", "phone",     css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                css_class="space-y-4"
            ),
            Fieldset(
                _("Empresa"),
                Div("name", "company_type", css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                Div("cnpj",                 css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                css_class="space-y-4"
            ),
            Fieldset(
                _("Endereço da empresa"),
                Div("addr_line1", "addr_number",              css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                Div("addr_line2", "addr_neighborhood",        css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                Div("addr_city", "addr_state",                css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                Div("addr_postal_code", "addr_country",       css_class="grid grid-cols-1 md:grid-cols-2 gap-4"),
                css_class="space-y-4"
            ),
            Div(
                Link(text=_("Voltar"),         href=reverse_lazy("admin:index"),           type="secondary"),
                Link(text=_("Alterar senha"),  href=reverse_lazy("admin:password_change"), type="secondary"),
                Button(text=_("Atualizar"),    type="primary", name="submit"),
                css_class="flex justify-end w-full mb-4"
            ),
        )

    # ---- Valida CNPJ (unicidade e dígitos) ----
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj") or ""
        cnpj_digits = _validate_cnpj_digits(cnpj)

        current_company = getattr(self, "company", None)
        for other in Company.objects.only("pk", "cnpj"):
            if other.pk == getattr(current_company, "pk", None):
                continue
            if _digits_only(other.cnpj) == cnpj_digits:
                raise forms.ValidationError(_("Já existe uma empresa cadastrada com este CNPJ."))

        self.cleaned_data["_cnpj_digits"] = cnpj_digits
        return _format_cnpj(cnpj_digits)

    # ---- Persistência ----
    def save(self):
        cd = self.cleaned_data
        u, a, c = self.user, self.account, self.company

        # User
        if u:
            u.first_name = cd["first_name"]
            u.last_name  = cd["last_name"]
            u.email      = cd["email"]
            u.save(update_fields=["first_name", "last_name", "email"])

        # Account
        if a:
            a.phone = cd.get("phone") or a.phone
            if u and a.email != u.email:
                a.email = u.email
            a.save(update_fields=["phone", "email"])

        # Company
        if c:
            c.name         = cd.get("name") or c.name
            c.cnpj         = _format_cnpj(cd.get("_cnpj_digits")) if cd.get("_cnpj_digits") else c.cnpj
            c.company_type = cd.get("company_type") or c.company_type
            c.save(update_fields=["name", "cnpj", "company_type"])

        # Address (billing)
        if a:
            addr = a.addresses.filter(type=Address.BILLING, is_default=True).first() or Address(account=a)
            addr.type         = Address.BILLING
            addr.name         = (c.name if c and c.name else (u.email if u else ""))
            addr.line1        = cd["addr_line1"]
            addr.number       = cd.get("addr_number") or ""
            addr.line2        = cd.get("addr_line2") or ""
            addr.neighborhood = cd.get("addr_neighborhood") or ""
            addr.city         = cd["addr_city"]
            addr.state        = cd.get("addr_state") or ""
            addr.postal_code  = cd["addr_postal_code"]
            addr.country      = cd["addr_country"]
            addr.phone        = a.phone or ""
            addr.tax_id       = (c.cnpj if c and c.cnpj else "")
            addr.is_default   = True

            Address.objects.filter(
                account=a, type=Address.BILLING, is_default=True
            ).exclude(pk=getattr(addr, "pk", None)).update(is_default=False)

            addr.save()

        return a

    @classmethod
    def profile_status(cls, *, user, account=None, company=None) -> dict:
        """
        Verifica se todos os campos obrigatórios do formulário estão preenchidos
        com base nos dados atuais (User/Account/Company/Address).
        Retorna:
          {
            "complete": bool,
            "missing": [{"field": "addr_city", "label": "Cidade"}, ...],
            "percent": int   # 0..100
          }
        """
        # instanciamos o form só pra pegar labels e saber quais são os required
        form = cls(user=user, account=account, company=company)
        required_fields = [name for name, f in form.fields.items() if f.required]

        # pega endereço de cobrança atual
        addr = None
        if account:
            addr = (
                account.addresses.filter(type=Address.BILLING, is_default=True).first()
                or account.addresses.filter(type=Address.BILLING).first()
            )

        # mapeia os valores atuais do “perfil” para os nomes do form
        def _country_code(v):
            return getattr(v, "code", v) if v else ""

        values = {
            # usuário
            "first_name": getattr(user, "first_name", ""),
            "last_name":  getattr(user, "last_name", ""),  # opcional
            "email":      getattr(user, "email", ""),
            # account
            "phone":      getattr(account, "phone", ""),
            # empresa
            "name":         getattr(company, "name", ""),
            "cnpj":         getattr(company, "cnpj", ""),
            "company_type": getattr(company, "company_type", ""),
            # endereço (cobrança)
            "addr_line1":        getattr(addr, "line1", "") if addr else "",
            "addr_number":       getattr(addr, "number", "") if addr else "",
            "addr_line2":        getattr(addr, "line2", "") if addr else "",  # opcional
            "addr_neighborhood": getattr(addr, "neighborhood", "") if addr else "",
            "addr_city":         getattr(addr, "city", "") if addr else "",
            "addr_state":        getattr(addr, "state", "") if addr else "",
            "addr_postal_code":  getattr(addr, "postal_code", "") if addr else "",
            "addr_country":      _country_code(getattr(addr, "country", "")) if addr else "BR",
        }

        # identifica faltantes
        missing_names = [
            name for name in required_fields
            if not str(values.get(name) or "").strip()
        ]
        missing = [{"field": n, "label": form.fields[n].label} for n in missing_names]

        total_req = max(len(required_fields), 1)
        percent = int(round(100 * (total_req - len(missing)) / total_req))

        return {
            "complete": len(missing) == 0,
            "missing": missing,
            "percent": percent,
        }

    @classmethod
    def is_profile_complete(cls, *, user, account=None, company=None) -> bool:
        """Atalho que retorna só True/False."""
        return cls.profile_status(user=user, account=account, company=company)["complete"]
