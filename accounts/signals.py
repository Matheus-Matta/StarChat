import os
import logging
from django.db import transaction
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def create_default_plans_and_admin(sender, **kwargs):
    # Rode só quando as migrações do app 'accounts' terminarem
    if sender.name != "accounts":
        return

    Plan = apps.get_model("accounts", "Plan")
    Account = apps.get_model("accounts", "Account")
    Company = apps.get_model("accounts", "Company")
    User = get_user_model()

    # 👉 Guard: só roda quando o banco está “vazio” para esses modelos
    if Plan.objects.exists() or Account.objects.exists() or Company.objects.exists() or User.objects.exists():
        # Já tem dados; não cria nada de novo
        return

    admin_email    = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    with transaction.atomic():
        # 1) Planos básicos
        admin_plan, _ = Plan.objects.update_or_create(
            name="admin",
            defaults={
                "description": "Plano Admin com acesso total.",
                "included_agents": 1000,
                "extra_agent_price": 0,
                "included_inboxes": 1000,
                "extra_inbox_price": 0,
                "requires_payment": False,
                "monthly_price": 0,
                "yearly_price": 0,
                "is_active": True,
                "is_plan_staff": True,
                "hex_color": "#EF4444",
            },
        )

        free_plan, _ = Plan.objects.update_or_create(
            name="free",
            defaults={
                "description": "Plano Free com acesso limitado.",
                "included_agents": 1,
                "extra_agent_price": 0,
                "included_inboxes": 1,
                "extra_inbox_price": 0,
                "requires_payment": False,
                "monthly_price": 0,
                "yearly_price": 0,
                "is_active": True,
                "is_plan_staff": False,
                "hex_color": "#c2c2c2",
            },
        )

        # 2) Account padrão (use free_plan ou admin_plan)
        account = Account.objects.create(
            email=admin_email,
            plan=free_plan,  # troque para admin_plan se preferir
        )
        print(f'✔ Conta padrão criada para {admin_email}')

        # 3) Superusuário padrão
        user = User(
            username=admin_username,
            email=admin_email,
            account=account,
            is_staff=True,
            is_superuser=True,
        )
        user.set_password(admin_password)
        user._raw_password = admin_password
        user.save()
        print(f'✔ Superusuário "{admin_username}" criado')

        # 4) Company padrão
        Company.objects.create(
            account=account,
            name=os.getenv("DEFAULT_COMPANY_NAME", "Starchat Master Co"),
            cnpj=os.getenv("DEFAULT_COMPANY_CNPJ", "00.000.000/0001-00"),
            company_type="others",
        )
        print(f'✔ Company padrão criada para conta {admin_email}')
