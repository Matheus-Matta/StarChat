# accounts/signals.py
# Sincronizador entre Account do Django e Customer no Stripe
# Configure também no apps.py para importar este módulo no ready().

import hashlib
import logging
import re
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction, connection
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from djstripe.models import Customer
from stripe.error import InvalidRequestError
from .models import Account, Plan, Address

log = logging.getLogger(__name__)


class StripeService:
    """Serviço centralizado para operações do Stripe"""
    
    @staticmethod
    def configure_api_key():
        """Define a chave da API do Stripe"""
        stripe.api_key = (
            settings.STRIPE_LIVE_SECRET_KEY
            if settings.STRIPE_LIVE_MODE
            else settings.STRIPE_TEST_SECRET_KEY
        )

    @staticmethod
    def create_idempotency_key(key: str) -> str:
        """Gera chave de idempotência"""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def amount_to_cents(value) -> int:
        """Converte valor para centavos"""
        return int(Decimal(value) * 100)

    @staticmethod
    def safe_retrieve(retrieve_fn, object_id: str):
        """Recupera objeto do Stripe com tratamento de erro e ignora deletados."""
        if not object_id:
            return None
        try:
            obj = retrieve_fn(str(object_id))
            # trate objetos deletados/arquivados como inexistentes
            if getattr(obj, "deleted", False):
                return None
            return obj
        except InvalidRequestError as e:
            if getattr(e, "code", None) == "resource_missing" or "No such" in str(e):
                return None
            raise
        
    @staticmethod
    def idem_product_create_key(plan) -> str:
        base = (
            f"product:create:{plan.pk}:"
            f"{plan.name}:{plan.description or ''}:"
            f"{int(bool(plan.is_active))}:"
            f"{plan.included_agents}:{plan.included_inboxes}:"
            f"{int(bool(plan.requires_payment))}"
        )
        return StripeService.create_idempotency_key(base)
    
    @staticmethod
    def idem_product_modify_key(plan) -> str:
        base = (
            f"product:modify:{plan.pk}:"
            f"{plan.name}:{plan.description or ''}:"
            f"{int(bool(plan.is_active))}"
        )
        return StripeService.create_idempotency_key(base)

    @staticmethod
    def idem_price_create_key(plan, field: str, amount_cents: int, interval: str = "month") -> str:
        base = f"price:create:{plan.pk}:{field}:{amount_cents}:{interval}"
        return StripeService.create_idempotency_key(base)

    @staticmethod
    def idem_price_nickname_key(price_id: str, nickname: str) -> str:
        return StripeService.create_idempotency_key(f"price:nickname:{price_id}:{nickname}")

    @staticmethod
    def idem_price_deactivate_key(price_id: str) -> str:
        return StripeService.create_idempotency_key(f"price:deactivate:{price_id}")

    @staticmethod
    def idem_product_default_price_key(product_id: str, price_id: str) -> str:
        return StripeService.create_idempotency_key(f"product:default_price:{product_id}:{price_id}")

class StripeCustomerManager:
    """Gerencia sincronização de clientes com o Stripe"""
    
    def __init__(self):
        self.service = StripeService()
        
    def _get_billing_address(self, account: Account):
        try:
            return account.addresses.filter(
                type="billing", is_default=True
            ).first() or account.addresses.filter(type="billing").first()
        except Exception:
            return None
        
    def _customer_payload(self, account: Account) -> dict:
        """Monta o payload completo do Customer (inclui endereço/telefone/nome quando houver)."""
        payload = {
            "email": account.email,
            "metadata": {"account_id": account.pk},
        }
        # nome preferencial: nome da empresa; fallback: email
        company = getattr(account, "company", None)
        name = (getattr(company, "name", None) or account.email) if company else account.email
        if name:
            payload["name"] = name
        if account.phone:
            payload["phone"] = account.phone

        addr = self._get_billing_address(account)
        if addr:
            addr_dict = addr.as_stripe_address()
            payload["address"] = addr_dict
            # opcional: manter shipping em sincronia também
            payload["shipping"] = {
                "name": name,
                "phone": account.phone or None,
                "address": addr_dict,
            }
        return payload
    
    def sync_customer(self, account: Account, created: bool):
        """Sincroniza conta com cliente do Stripe"""
        self.service.configure_api_key()

        if created and not account.stripe_customer_id:
            self._create_stripe_customer(account)
        elif account.stripe_customer_id:
            self._update_stripe_customer(account)
    
    def _create_stripe_customer(self, account: Account):
        """Cria novo cliente no Stripe"""
        customer = stripe.Customer.create(**self._customer_payload(account))
        account.stripe_customer_id = customer["id"]
        account.save(update_fields=["stripe_customer_id"])
        Customer.sync_from_stripe_data(customer)

    def _update_stripe_customer(self, account: Account):
        """Atualiza cliente existente no Stripe"""
        try:
            stripe.Customer.modify(
                account.stripe_customer_id,
                **self._customer_payload(account)
            )
            # Sincroniza dados locais
            stripe_data = stripe.Customer.retrieve(account.stripe_customer_id)
            Customer.sync_from_stripe_data(stripe_data)
        except InvalidRequestError:
            log.warning(
                "Erro ao atualizar cliente %s - pode ter sido removido",
                account.stripe_customer_id
            )
    
    def delete_customer(self, account: Account):
        """Remove cliente do Stripe"""
        if not account.stripe_customer_id:
            return
            
        self.service.configure_api_key()
        try:
            stripe.Customer.delete(account.stripe_customer_id)
        except InvalidRequestError:
            log.warning("Erro ao deletar cliente %s", account.stripe_customer_id)

    def delete_plan_resources(self, plan: Plan):
        """Desativa preços e deleta/arquiva o produto no Stripe ao remover o Plan."""
        self.service.configure_api_key()

        product_id = plan.stripe_product_id
        known_price_ids = [
            plan.billing_monthly_price_id,
            plan.billing_yearly_price_id,
            plan.billing_extra_agent_price_id,
            plan.billing_extra_inbox_price_id,
        ]

        # 1) Desativa preços conhecidos por ID (se existirem)
        for pid in filter(None, known_price_ids):
            price = self.service.safe_retrieve(stripe.Price.retrieve, pid)
            if price and getattr(price, "active", True):
                try:
                    stripe.Price.modify(
                        price.id,
                        active=False,
                        idempotency_key=self.service.create_idempotency_key(f"price:deactivate:{price.id}"),
                    )
                except InvalidRequestError:
                    # já sumiu no Stripe ou não pode ser alterado → ignora
                    pass

        # 2) Se o produto existir, desativa TODOS os preços dele
        if product_id:
            product = self.service.safe_retrieve(stripe.Product.retrieve, product_id)
            if product:
                try:
                    for p in stripe.Price.list(product=product_id, limit=100).auto_paging_iter():
                        if getattr(p, "active", True):
                            try:
                                stripe.Price.modify(
                                    p.id,
                                    active=False,
                                    idempotency_key=self.service.create_idempotency_key(f"price:deactivate:{p.id}")
                                )
                            except InvalidRequestError:
                                pass
                except InvalidRequestError:
                    # listar preços falhou? segue para tentar deletar/arquivar o product mesmo assim
                    pass

                # 3) Tenta deletar o Product; se falhar, arquiva
                try:
                    stripe.Product.delete(product_id)
                except InvalidRequestError:
                    try:
                        stripe.Product.modify(product_id, active=False)
                    except InvalidRequestError:
                        pass
class StripePlanManager:
    """Gerencia sincronização de planos com produtos/preços do Stripe"""
    
    # Mapeamento de campos para IDs de preço
    PRICE_FIELD_MAP = {
        "monthly_price": "billing_monthly_price_id",
        "yearly_price": "billing_yearly_price_id", 
        "extra_agent_price": "billing_extra_agent_price_id",
        "extra_inbox_price": "billing_extra_inbox_price_id",
    }
    
    # Tipos de preço
    PRICE_KINDS = {
        "monthly_price": "monthly",
        "yearly_price": "yearly",
        "extra_agent_price": "extra_agent",
        "extra_inbox_price": "extra_inbox",
    }
    
    def __init__(self):
        self.service = StripeService()
    
    def sync_plan(self, plan: Plan, old_values: dict = None):
        """Sincroniza plano com produto e preços do Stripe"""
        self.old_values = old_values or {}
        
        def _sync_with_retry():
            try:
                self._sync_plan_implementation(plan)
            except InvalidRequestError as e:
                if self._handle_missing_resources(e, plan):
                    self._sync_plan_implementation(plan)
                else:
                    log.warning("Erro do Stripe ao sincronizar plano %s: %s", plan.pk, e)
            except Exception:
                log.exception("Erro inesperado ao sincronizar plano %s", plan.pk)
        
        # Executa após commit para evitar problemas de concorrência
        transaction.on_commit(_sync_with_retry)
    
    def _sync_plan_implementation(self, plan: Plan):
        """Implementação principal da sincronização"""
        self.service.configure_api_key()
        
        # Recarrega dados mais recentes
        plan.refresh_from_db()
        
        # 1. Garante produto no Stripe
        product_id = self._ensure_product(plan)
        
        # 2. Sincroniza todos os preços (todos mensais conforme especificado)
        price_ids = self._sync_all_prices(plan, product_id)
        
        # 3. Define preço padrão do produto
        self._set_default_price(product_id, price_ids['monthly'])
    
    def _ensure_product(self, plan: Plan) -> str:
        """Garante que o produto existe no Stripe"""
        existing_product = self.service.safe_retrieve(stripe.Product.retrieve, plan.stripe_product_id)
        
        if not existing_product:
            return self._create_product(plan)
        
        if self._product_needs_update(plan):
            self._update_product(existing_product.id, plan)
        
        return existing_product.id
    
    def _create_product(self, plan: Plan) -> str:
        product = stripe.Product.create(
            name=plan.name,
            description=plan.description or "",
            active=bool(plan.is_active),
            metadata=self._get_product_metadata(plan),
            idempotency_key=self.service.idem_product_create_key(plan),
        )
        Plan.objects.filter(pk=plan.pk).update(stripe_product_id=product.id)
        return product.id

    def _update_product(self, product_id: str, plan: Plan):
        stripe.Product.modify(
            product_id,
            name=plan.name,
            description=plan.description or "",
            active=bool(plan.is_active),
            metadata=self._get_product_metadata(plan),
            idempotency_key=self.service.idem_product_modify_key(plan),
        )
    
    def _get_product_metadata(self, plan: Plan) -> dict:
        """Retorna metadata do produto"""
        return {
            "plan_id": str(plan.pk),
            "included_agents": str(plan.included_agents),
            "included_inboxes": str(plan.included_inboxes),
            "requires_payment": str(plan.requires_payment).lower(),
        }
    
    def _product_needs_update(self, plan: Plan) -> bool:
        """Verifica se produto precisa ser atualizado"""
        return (
            plan.name != self.old_values.get("name") or
            (plan.description or "") != (self.old_values.get("description") or "") or
            bool(plan.is_active) != bool(self.old_values.get("is_active"))
        )
    
    def _sync_all_prices(self, plan: Plan, product_id: str) -> dict:
        """Sincroniza todos os preços do plano"""
        price_ids = {}
        
        for field, price_field in self.PRICE_FIELD_MAP.items():
            nickname = self._get_price_nickname(plan, field)
            price_id = self._sync_single_price(plan, product_id, field, nickname)
            price_type = field.replace('_price', '')
            price_ids[price_type] = price_id
        
        return price_ids
    
    def _entries(self, plan: Plan) -> list[dict]:
        svc = self.service

        def cents(v):  # helper local
            return svc.amount_to_cents(v or 0)

        return [
            # Base do plano
            {
                "field_label": "monthly_price",
                "plan_id_field": "billing_monthly_price_id",
                "kind": "base",
                "interval": "month",
                "amount_cents": cents(plan.monthly_price),
            },
            {
                "field_label": "yearly_price",
                "plan_id_field": "billing_yearly_price_id",
                "kind": "base",
                "interval": "year",
                "amount_cents": cents(plan.yearly_price),
            },

            # Extras: agente
            {
                "field_label": "extra_agent_price (monthly)",
                "plan_id_field": "billing_extra_agent_price_id",
                "kind": "extra_agent",
                "interval": "month",
                "amount_cents": cents(plan.extra_agent_price),
            },
            {
                "field_label": "extra_agent_price (yearly)",
                "plan_id_field": "billing_extra_agent_price_id_yearly",
                "kind": "extra_agent",
                "interval": "year",
                "amount_cents": cents(plan.extra_agent_price) * 12,
            },

            # Extras: inbox
            {
                "field_label": "extra_inbox_price (monthly)",
                "plan_id_field": "billing_extra_inbox_price_id",
                "kind": "extra_inbox",
                "interval": "month",
                "amount_cents": cents(plan.extra_inbox_price),
            },
            {
                "field_label": "extra_inbox_price (yearly)",
                "plan_id_field": "billing_extra_inbox_price_id_yearly",
                "kind": "extra_inbox",
                "interval": "year",
                "amount_cents": cents(plan.extra_inbox_price) * 12,
            },
        ]

    def _get_price_nickname(self, plan: Plan, kind: str, interval: str) -> str:
        base = plan.name
        if kind == "base":
            return f"{base} - {'Mensal' if interval=='month' else 'Anual'}"
        if kind == "extra_agent":
            return f"{base} - Agente Extra ({'mensal' if interval=='month' else 'anual'})"
        if kind == "extra_inbox":
            return f"{base} - Inbox Extra ({'mensal' if interval=='month' else 'anual'})"
        return base

    def _price_matches(self, price, amount_cents: int, interval: str) -> bool:
        return (
            getattr(price, "unit_amount", None) == amount_cents and
            getattr(price, "currency", "").lower() == "brl" and
            (price.recurring or {}).get("interval") == interval
        )

    def _create_price(
        self,
        plan: Plan,
        product_id: str,
        amount_cents: int,
        nickname: str,
        kind: str,
        interval: str,
        idempo_key: str,
    ):
        return stripe.Price.create(
            product=product_id,
            unit_amount=amount_cents,
            currency="brl",
            nickname=nickname,
            recurring={"interval": interval},
            metadata={
                "plan_id": str(plan.pk),
                "kind": kind,
                "interval": interval,
            },
            idempotency_key=idempo_key,
        )

    def _archive_old_prices(self, product_id: str, keep_id: str, plan_id: int, kind: str, interval: str):
        for price in stripe.Price.list(product=product_id, limit=100).auto_paging_iter():
            metadata = getattr(price, "metadata", {}) or {}
            if (
                price.id != keep_id
                and getattr(price, "active", True)
                and metadata.get("plan_id") == str(plan_id)
                and metadata.get("kind") == kind
                and metadata.get("interval") == interval
            ):
                stripe.Price.modify(
                    price.id,
                    active=False,
                    idempotency_key=self.service.idem_price_deactivate_key(price.id),
                )

    def _sync_all_prices(self, plan: Plan, product_id: str) -> dict:
        """
        Cria/atualiza todos os prices do plano (base mensal/anual + extras mensal/anual).
        Retorna dict com ids relevantes; usamos o mensal como default_price.
        """
        out = {"base_month": None}

        for entry in self._entries(plan):
            plan_id_field = entry["plan_id_field"]
            kind = entry["kind"]
            interval = entry["interval"]
            amount_cents = entry["amount_cents"]

            nickname = self._get_price_nickname(plan, kind, interval)

            existing_id = getattr(plan, plan_id_field, None)
            existing_price = self.service.safe_retrieve(stripe.Price.retrieve, existing_id)

            # só consideramos o existente se pertencer a este product
            if existing_price and str(existing_price.product) != str(product_id):
                existing_price = None

            if existing_price and self._price_matches(existing_price, amount_cents, interval):
                # Atualiza somente nickname se mudou
                if (existing_price.nickname or "") != (nickname or ""):
                    stripe.Price.modify(
                        existing_price.id,
                        nickname=nickname,
                        idempotency_key=self.service.idem_price_nickname_key(existing_price.id, nickname),
                    )
                keep_id = existing_price.id
            else:
                # Criar um novo price
                idempo_key = self.service.idem_price_create_key(plan, plan_id_field, amount_cents, interval)
                new_price = self._create_price(
                    plan=plan,
                    product_id=product_id,
                    amount_cents=amount_cents,
                    nickname=nickname,
                    kind=kind,
                    interval=interval,
                    idempo_key=idempo_key,
                )
                keep_id = new_price.id
                # salvar o ID no Plan
                Plan.objects.filter(pk=plan.pk).update(**{plan_id_field: keep_id})

            # arquivar “irmãos” do mesmo kind+interval
            self._archive_old_prices(product_id, keep_id, plan.pk, kind, interval)

            # guardamos o base mensal pra virar default_price do product
            if kind == "base" and interval == "month":
                out["base_month"] = keep_id

        return out

    def _set_default_price(self, product_id: str, monthly_price_id: str):
        if monthly_price_id and self.service.safe_retrieve(stripe.Price.retrieve, monthly_price_id):
            stripe.Product.modify(
                product_id,
                default_price=monthly_price_id,
                idempotency_key=self.service.idem_product_default_price_key(product_id, monthly_price_id),
            )
    
    def _handle_missing_resources(self, error: InvalidRequestError, plan: Plan) -> bool:
        """Trata recursos faltantes no Stripe e limpa IDs inválidos"""
        if not ("No such product" in str(error) or "No such price" in str(error)):
            return False
        
        missing_id = self._extract_missing_id(str(error))
        if not missing_id:
            return False
        
        updates = self._get_cleanup_updates(missing_id, plan)
        if not updates:
            return False
        
        Plan.objects.filter(pk=plan.pk).update(**updates)
        log.warning("IDs inválidos removidos (%s) para plano %s; refazendo sincronização", updates, plan.pk)
        
        return True
    
    def _extract_missing_id(self, error_message: str) -> str:
        """Extrai ID do recurso faltante da mensagem de erro"""
        match = re.search(r"(prod|price)_[A-Za-z0-9]+", error_message)
        return match.group(0) if match else None
    
    def _get_cleanup_updates(self, missing_id: str, plan: Plan) -> dict:
        """Retorna atualizações para limpar IDs inválidos"""
        updates = {}
        
        if missing_id.startswith("prod_"):
            updates["stripe_product_id"] = None
        else:
            id_mappings = {
                plan.billing_monthly_price_id: "billing_monthly_price_id",
                plan.billing_yearly_price_id: "billing_yearly_price_id", 
                plan.billing_extra_agent_price_id: "billing_extra_agent_price_id",
                plan.billing_extra_agent_price_id_yearly: "billing_extra_agent_price_id_yearly",
                plan.billing_extra_inbox_price_id: "billing_extra_inbox_price_id",
                plan.billing_extra_inbox_price_id_yearly: "billing_extra_inbox_price_id_yearly",
            }
            
            if missing_id in id_mappings:
                updates[id_mappings[missing_id]] = None
        
        return updates

    def delete_plan_resources(self, plan: Plan):
        """Desativa preços e deleta/arquiva o produto no Stripe ao remover o Plan."""
        self.service.configure_api_key()

        product_id = plan.stripe_product_id
        known_price_ids = [
            plan.billing_monthly_price_id,
            plan.billing_yearly_price_id,
            plan.billing_extra_agent_price_id_yearly,
            plan.billing_extra_inbox_price_id,
            plan.billing_extra_inbox_price_id_yearly,
        ]

        # 1) Desativa preços conhecidos por ID (se existirem)
        for pid in filter(None, known_price_ids):
            price = self.service.safe_retrieve(stripe.Price.retrieve, pid)
            if price and getattr(price, "active", True):
                try:
                    stripe.Price.modify(
                        price.id,
                        active=False,
                        idempotency_key=self.service.create_idempotency_key(f"price:deactivate:{price.id}"),
                    )
                except InvalidRequestError:
                    # já sumiu no Stripe ou não pode ser alterado → ignora
                    pass

        # 2) Se o produto existir, desativa TODOS os preços dele
        if product_id:
            product = self.service.safe_retrieve(stripe.Product.retrieve, product_id)
            if product:
                try:
                    for p in stripe.Price.list(product=product_id, limit=100).auto_paging_iter():
                        if getattr(p, "active", True):
                            try:
                                stripe.Price.modify(
                                    p.id,
                                    active=False,
                                    idempotency_key=self.service.create_idempotency_key(f"price:deactivate:{p.id}")
                                )
                            except InvalidRequestError:
                                pass
                except InvalidRequestError:
                    # listar preços falhou? segue para tentar deletar/arquivar o product mesmo assim
                    pass

                # 3) Tenta deletar o Product; se falhar, arquiva
                try:
                    stripe.Product.delete(product_id)
                except InvalidRequestError:
                    try:
                        stripe.Product.modify(product_id, active=False)
                    except InvalidRequestError:
                        pass
              
                    

# Instâncias dos gerenciadores
customer_manager = StripeCustomerManager()
plan_manager = StripePlanManager()


@receiver(post_save, sender=Account)
def sync_stripe_customer(sender, instance, created, **kwargs):
    """Sincroniza Account com Customer do Stripe"""
    customer_manager.sync_customer(instance, created)


@receiver(post_delete, sender=Account)
def delete_stripe_customer(sender, instance, **kwargs):
    """Remove Customer do Stripe ao deletar Account"""
    customer_manager.delete_customer(instance)
    
@receiver(post_save, sender=Address)
def sync_customer_address_on_address_change(sender, instance, created, **kwargs):
    """Quando o endereço de cobrança mudar/criar, atualiza o Customer no Stripe."""
    try:
        account = instance.account
    except Exception:
        return
    if not account or not account.stripe_customer_id:
        return
    # só endereços de cobrança interessam
    if instance.type != "billing":
        return
    # reusa a lógica do manager
    customer_manager.sync_customer(account, created=False)

@receiver(pre_save, sender=Plan)
def cache_plan_old_values(sender, instance, **kwargs):
    """Cache dos valores anteriores do plano para comparação"""
    if not instance.pk:
        return
    
    try:
        old_plan = Plan.objects.get(pk=instance.pk)
        instance._old_values = {
            "name": old_plan.name,
            "description": old_plan.description,
            "is_active": old_plan.is_active,
            "monthly_price": old_plan.monthly_price,
            "yearly_price": old_plan.yearly_price,
            "extra_agent_price": old_plan.extra_agent_price,
            "extra_inbox_price": old_plan.extra_inbox_price,
            "stripe_product_id": old_plan.stripe_product_id,
            "billing_monthly_price_id": old_plan.billing_monthly_price_id,
            "billing_yearly_price_id": old_plan.billing_yearly_price_id,
            "billing_extra_agent_price_id": old_plan.billing_extra_agent_price_id,
            "billing_extra_inbox_price_id": old_plan.billing_extra_inbox_price_id,
        }
    except Plan.DoesNotExist:
        instance._old_values = {}

def ignore_admin_plan(instance):
    """Ignora a sincronização do plano Admin."""
    if instance.name == "admin":
        instance._old_values = {}
        return True
    return False


@receiver(post_save, sender=Plan)
def sync_stripe_plan(sender, instance, created, **kwargs):
    """Sincroniza Plan com Product e Prices do Stripe"""
    if ignore_admin_plan(instance):
        return
    old_values = getattr(instance, "_old_values", {})
    plan_manager.sync_plan(instance, old_values)
      
@receiver(post_delete, sender=Plan)
def delete_stripe_plan(sender, instance, **kwargs):
    """Ao deletar o Plan no Django, limpa recursos no Stripe."""
    if ignore_admin_plan(instance):
        return
    def _do():
        try:
            plan_manager.delete_plan_resources(instance)
        except Exception:
            log.exception("Falha ao apagar recursos do Stripe para Plan %s", instance.pk)
    # se estiver dentro de transação (admin usa atomic), só roda após o commit
    if connection.in_atomic_block:
        transaction.on_commit(_do)
    else:
        _do()