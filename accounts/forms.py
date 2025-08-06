from django import forms
from django.contrib.auth import get_user_model
from .models import Account, Company
from unfold.contrib.forms.widgets import (
    UnfoldAdminTextInputWidget,
    UnfoldAdminSelectWidget,
)
from crispy_forms.layout import Layout, Fieldset, Div, Submit , HTML
from core.forms import Button, Link
from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy

User = get_user_model()

class CombinedProfileForm(forms.Form):
    # --- Campos de Usuário ---
    first_name = forms.CharField(
        label="Primeiro nome",
        max_length=150,
        required=True,
        widget=UnfoldAdminTextInputWidget(),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=UnfoldAdminTextInputWidget(),
    )
    phone = forms.CharField(
        label="Telefone",
        max_length=20,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    # --- Campos de Empresa ---
    name = forms.CharField(
        label="Nome da Empresa",
        max_length=255,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        max_length=20,
        required=False,
        widget=UnfoldAdminTextInputWidget(),
    )
    company_type = forms.ChoiceField(
        label="Tipo de Empresa",
        choices=Company.COMPANY_TYPE_CHOICES,
        required=False,
        widget=UnfoldAdminSelectWidget(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.template_pack = "unfold_crispy"
        # Espaçamento vertical entre fieldsets
        self.helper.form_class = "space-y-6"

        self.helper.layout = Layout(
            Fieldset(
                "Usuário",
                # grid com 2 colunas e gap de 4
                Div(
                    "first_name",
                    "last_name",
                    css_class="grid grid-cols-1 md:grid-cols-2 gap-4"
                ),
                Div(
                    "email",
                    "phone",
                    css_class="grid grid-cols-1 md:grid-cols-2 gap-4"
                ),
                css_class="space-y-4"
            ),
            Fieldset(
                "Empresa",
                Div(
                    "name",
                    "company_type",
                    css_class="grid grid-cols-1 md:grid-cols-2 gap-4"
                ),
                Div(
                    "cnpj",
                    css_class="grid grid-cols-1 md:grid-cols-2 gap-4"
                ),
                css_class="space-y-4"
            ),
            Div(
                Link( text="Voltar", href=reverse_lazy("admin:index"), type="secondary"),
                Link( text="Alterar senha", href=reverse_lazy("admin:password_change"), type="secondary"),
                Button(text="Atualizar", type="primary", name="submit"),
                css_class="flex justify-end w-full"
            ),
        )
