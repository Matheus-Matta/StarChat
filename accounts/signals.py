import os
import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def create_default_plans_and_admin(sender, **kwargs):
    # Apenas executa para o app 'accounts'
    if sender.name != 'accounts':
        return

    # 1) Cria/atualiza os planos iniciais
    Plan = apps.get_model('accounts', 'Plan')
    if not Plan.objects.exists():
        default_plans = [
            {
                'name': 'admin',
                'description': 'Plano Admin com acesso total.',
                'included_agents': 1000,
                'extra_agent_price': 0,
                'included_inboxes': 1000,
                'extra_inbox_price': 0,
                'requires_payment': False,
                'monthly_price': 0,
                'yearly_price': 0,
                'is_active': True,
                'is_plan_staff': True,
                'hex_color': '#EF4444',
            },
            {
                'name': 'free',
                'description': 'Plano Free com acesso limitado.',
                'included_agents': 1,
                'extra_agent_price': 0,
                'included_inboxes': 1,
                'extra_inbox_price': 0,
                'requires_payment': False,
                'monthly_price': 0,
                'yearly_price': 0,
                'is_active': True,
                'is_plan_staff': False,
                'hex_color': "#c2c2c2",
            },
        ]
        for data in default_plans:
            plan, created = Plan.objects.update_or_create(
                name=data['name'],
                defaults={k: v for k, v in data.items() if k != 'name'}
            )
            if created:
                print(f'✔ Plano "{data["name"]}" criado')

    # 2) Cria/obtém a conta padrão usando o plano 'free'
    Account = apps.get_model('accounts', 'Account')
    if not Account.objects.exists():
        admin_email = os.getenv('DEFAULT_ADMIN_EMAIL')
        if not admin_email:
            logger.warning('DEFAULT_ADMIN_EMAIL não configurado; pulando criação de conta padrão')
            return

        try:
            free_plan = Plan.objects.get(name='admin')
        except Plan.DoesNotExist:
            logger.error("Plano 'free' não encontrado; pulando criação de conta padrão")
            return

        account, acc_created = Account.objects.get_or_create(
            email=admin_email,
            defaults={'plan': free_plan}
        )
        if acc_created:
            print(f'✔ Conta padrão criada para {admin_email}')

    # 3) Cria/obtém o superusuário padrão
    User = get_user_model()
    admin_username = os.getenv('DEFAULT_ADMIN_USERNAME')
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
    if not User.objects.exists() and admin_username and admin_password:
        user, user_created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'account': account,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if user_created:
            user.set_password(admin_password)
            user._raw_password = admin_password
            user.save()
            print(f'✔ Superusuário "{admin_username}" criado')

    # 4) Cria/obtém a Company vinculada à conta
    Company = apps.get_model('accounts', 'Company')
    if not Company.objects.exists():
        comp_defaults = {
            'name': os.getenv('DEFAULT_COMPANY_NAME', 'Starchat Master Co'),
            'cnpj': os.getenv('DEFAULT_COMPANY_CNPJ', '00.000.000/0001-00'),
            'company_type': 'others',
        }
        company, comp_created = Company.objects.get_or_create(
            account=account,
            defaults=comp_defaults
        )
        if comp_created:
            print(f'✔ Company padrão criada para conta {admin_email}')

