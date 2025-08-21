from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import F, Value
from django.db.models.functions import Replace
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import re

from accounts.models import Plan, Account, Company

User = get_user_model()


# --- helpers CNPJ ---
def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def _cnpj_check_digits(cnpj_digits: str) -> bool:
    if len(cnpj_digits) != 14:
        return False
    if cnpj_digits == cnpj_digits[0] * 14:
        return False

    nums = [int(x) for x in cnpj_digits]

    # DV1
    w1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    r = sum(n*w for n, w in zip(nums[:12], w1)) % 11
    dv1 = 0 if r < 2 else 11 - r

    # DV2
    w2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
    r = sum(n*w for n, w in zip(nums[:13], w2)) % 11
    dv2 = 0 if r < 2 else 11 - r

    return nums[12] == dv1 and nums[13] == dv2

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    remember_me = forms.BooleanField(required=False)

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'placeholder': 'seu@email.com'})
    )
    phone = forms.CharField(
        label=_("Telefone"),
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000'})
    )
    password = forms.CharField(
        label=_("Senha"),
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'}),
    )
    confirm_password = forms.CharField(
        label=_("Confirmar Senha"),
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme sua senha'}),
    )

    company_name = forms.CharField(
        label=_("Nome da Empresa"),
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Digite o nome da empresa'})
    )
    
    cnpj = forms.CharField(
        label=_("CNPJ"),
        max_length=18,
        widget=forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'})
    )
    
    company_type = forms.ChoiceField(
        label=_("Tipo de Empresa"),
        choices=Company.COMPANY_TYPE_CHOICES,
    )

    def clean_email(self):
        e = self.cleaned_data['email']
        if User.objects.filter(email=e).exists():
            raise ValidationError(_('Este email já está em uso.'))
        return e
    
    def clean_cnpj(self):
        raw = self.cleaned_data.get("cnpj", "")
        digits = _only_digits(raw)

        if not _cnpj_check_digits(digits):
            raise ValidationError(_("CNPJ inválido."))

        # checagem de duplicidade ignorando pontuação
        # (funciona mesmo se no banco houver CNPJ com máscara)
        exists = Company.objects.annotate(
            cnpj_digits=Replace(
                Replace(
                    Replace(F("cnpj"), Value("."), Value("")),
                    Value("-"), Value("")
                ),
                Value("/"), Value("")
            )
        ).filter(cnpj_digits=digits).exists()

        if exists:
            raise ValidationError(_("Este CNPJ já está em uso."))

        # normalize: salvar só dígitos (recomendado)
        return digits

    def clean(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            return self.add_error('email', _('Já existe uma conta com este email.'))
        
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', _('As senhas não coincidem.'))
        return cleaned

    def save(self):
        data = self.cleaned_data
        
        plan_obj = Plan.objects.get(name='free')
        if not plan_obj:
            self.add_error(None, _('Plano não encontrado entre em contato com o suporte.'))
            return 
        
        account = Account.objects.create(
            plan=plan_obj,
            phone=data['phone'],
            email=data['email'],
        )

        Company.objects.create(
            account=account,
            name=data['company_name'],
            cnpj=data['cnpj'],
            company_type=data['company_type'],
        )
        
        raw_password = data['password']

        user = User(
            account=account,
            first_name=data['company_name'],
            username=data['email'],
            email=data['email'],
            role='administrator',
            is_staff=True,
        )
        user.set_password(raw_password) 
        user._raw_password = raw_password
        user.save()

        return user, account
