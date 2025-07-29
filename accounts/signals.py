# accounts/signals.py
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone

@receiver(post_migrate)
def create_default_plans_and_admin(sender, **kwargs):
    # Só roda quando o app 'accounts' finaliza a migrate
    if sender.name != 'accounts':
        return

    # ==== 1) Cria/atualiza os 4 planos iniciais ====
    Plan = apps.get_model('accounts', 'Plan')
    default_plans = [
        {
            'name': 'free',
            'description': 'Plano Free gratuito com recursos básicos.',
            'included_agents': 1,
            'extra_agent_price': 0,
            'included_inboxes': 1,
            'extra_inbox_price': 0,
            'requires_payment': False,
            'monthly_price': 0,
            'yearly_price': 0,
            'is_active': True,
        },
        {
            'name': 'standard',
            'description': 'Plano Standard com recursos intermediários.',
            'included_agents': 5,
            'extra_agent_price': 15.00,
            'included_inboxes': 3,
            'extra_inbox_price': 25.00,
            'monthly_price': 49.90,
            'yearly_price': 499.00,
            'is_active': True,
        },
        {
            'name': 'premium',
            'description': 'Plano Premium com ferramentas avançadas.',
            'included_agents': 10,
            'extra_agent_price': 10.00,
            'included_inboxes': 5,
            'extra_inbox_price': 20.00,
            'monthly_price': 99.90,
            'yearly_price': 999.00,
            'is_active': True,
        },
        {
            'name': 'business',
            'description': 'Plano Business para grandes operações.',
            'included_agents': 20,
            'extra_agent_price': 8.00,
            'included_inboxes': 10,
            'extra_inbox_price': 15.00,
            'monthly_price': 199.90,
            'yearly_price': 1999.00,
            'is_active': True,
        },
        {
            'name': 'admin',
            'description': 'plano admin.',
            'included_agents': 1000,
            'extra_agent_price': 0,
            'included_inboxes': 1000,
            'extra_inbox_price': 0,
            'monthly_price': 0,
            'yearly_price': 0,
            'is_active': True,
            'requires_payment': False,
            'is_plan_staff': True,
        },
    ]

    for data in default_plans:
        plan, created = Plan.objects.update_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            print(f'✔ Plano "{data["name"]}" criado')
        else:
            print(f'→ Plano "{data["name"]}" atualizado')

    # ==== 2) Cria a conta padrão usando o plano "free" ====
    Account = apps.get_model('accounts', 'Account')
    free_plan = Plan.objects.get(name='admin')
    admin_email = os.getenv('DEFAULT_ADMIN_EMAIL')
    account, created_acc = Account.objects.get_or_create(
        email=admin_email,
        defaults={
            'plan': free_plan,
            'status': 'active',
            'start_date': timezone.now(),
        }
    )
    if created_acc:
        print(f'✔ Conta padrão criada para {admin_email}')
    else:
        print(f'→ Conta para {admin_email} já existia')

    # ==== 3) Cria/atualiza o superusuário padrão ====
    User = get_user_model()
    username = os.getenv('DEFAULT_ADMIN_USERNAME')
    password = os.getenv('DEFAULT_ADMIN_PASSWORD')

    user, created_user = User.objects.get_or_create(
        username=username,
        defaults={
            'email': admin_email,
            'account': account,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created_user:
        user.set_password(password)
        user.save()
        print(f'✔ Superusuário "{username}" criado')
    else:
        updated = False
        if not user.is_superuser:
            user.is_superuser = True
            updated = True
        if not user.is_staff:
            user.is_staff = True
            updated = True
        if user.account != account:
            user.account = account
            updated = True
        if updated:
            user.save()
            print(f'→ Superusuário "{username}" atualizado')

    # ==== 4) Garante a Company vinculada à conta ====
    Company = apps.get_model('accounts', 'Company')
    comp_defaults = {
        'name': os.getenv('DEFAULT_COMPANY_NAME', 'Starchat Master Co'),
        'cnpj': os.getenv('DEFAULT_COMPANY_CNPJ', '00.000.000/0001-00'),
        'billing_address': {},
        'company_type': 'others',
    }
    company, created_c = Company.objects.get_or_create(
        account=account,
        defaults=comp_defaults
    )
    if created_c:
        print(f'✔ Company padrão criada para conta {admin_email}')
    else:
        print(f'→ Company para conta {admin_email} já existia')
