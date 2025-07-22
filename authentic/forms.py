from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from accounts.models import Plan, Account, Company
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model
User = get_user_model()

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
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )
    confirm_password = forms.CharField(
        label=_("Confirmar Senha"),
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
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
        c = self.cleaned_data["cnpj"]
        if Company.objects.filter(cnpj=c).exists():
            raise ValidationError(_('Este Cnpj já está em uso.'))
        return c

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', _('As senhas não coincidem.'))
        return cleaned

    def save(self):
        data = self.cleaned_data
        
        plan_obj, _ = Plan.objects.get_or_create(
            name='Free',
            defaults={'price': 0, 'is_active': True}
        )
        
        account = Account.objects.create(
            plan=plan_obj,
            status='active',
            start_date=timezone.now(),
            payment_method='manual',
            customer_id_payment='',
            payment_status='free',
            phone=data['phone'],
            email=data['email'],
        )
        
        user = User.objects.create_user(
            account=account,
            username=data['email'],
            email=data['email'],
            password=data['password'],
            is_staff=True,
        )
        
        user.save()

        # 4) cria a empresa (gera slug automaticamente e sem billing_address)
        Company.objects.create(
            account=account,
            name=data['company_name'],
            cnpj=data['cnpj'],
            billing_address={},
            company_type=data['company_type'],
        )

        return user, account
