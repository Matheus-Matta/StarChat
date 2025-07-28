# accounts/signals.py

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Account , Plan, Company
from .apps import AccountsConfig
import os
from django.utils import timezone
User = get_user_model()

@receiver(post_migrate)
def create_master_plan_account_and_admin(sender, **kwargs):

    # 1) Cria o plano Master (preço 0)
    plan_master, created_plan = Plan.objects.get_or_create(
        plan_type='master',
        name='Master',
        defaults={'price': 0, 'description': 'Plano Master gratuito', 'is_active': True}
    )
    if created_plan:
        print('✔ Plano "Master" criado com preço 0')

    # 2) Cria a conta padrão usando esse plano
    account_email = os.getenv('DEFAULT_ADMIN_EMAIL')
    account_qs = Account.objects.filter(email=account_email)

    if account_qs.exists():
        account = account_qs.first()
        created_acc = False
    else:
        account = Account.objects.create(
            email=account_email,
            plan=plan_master,
            status='active',
            start_date=timezone.now()
        )
        created_acc = True

    if created_acc:
        print(f'✔ Conta padrão criada para: {account_email} com plano Master')

    # 3) Cria o superadmin padrão ligado à conta Master
    username = os.getenv('DEFAULT_ADMIN_USERNAME')
    email = os.getenv('DEFAULT_ADMIN_EMAIL')
    password = os.getenv('DEFAULT_ADMIN_PASSWORD')

    user, created_user = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'account': account}
    )
    if created_user:
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f'✔ Superusuário "{username}" criado e associado à conta Master')
    else:
        # Caso já exista, assegura vínculo com conta e flags
        updated = False
        if user.account != account:
            user.account = account
            updated = True
        if not user.is_superuser or not user.is_staff:
            user.is_superuser = user.is_staff = True
            updated = True
        if updated:
            user.save()
            print(f'→ Superusuário "{username}" atualizado para conta Master')

    # (Opcional) Se quiser criar uma Company vinculada à conta, descomente:
    Company.objects.get_or_create(account=account, defaults={
        'name': os.getenv('DEFAULT_COMPANY_NAME', 'Starchat Master Co'),
        'cnpj': os.getenv('DEFAULT_COMPANY_CNPJ', '00.000.000/0001-00'),
        'billing_address': {},
        'company_type': 'others',
    })
