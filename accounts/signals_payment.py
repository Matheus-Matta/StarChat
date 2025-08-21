"""DJStripe subscription signals with clean code architecture."""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Set
from enum import Enum

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

import stripe
from djstripe.models import Subscription as DJSubscription

from accounts.models import Account, Plan
from accounts.utils import get_free_plan

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionStatus(Enum):
    """Subscription status categories."""
    BILLABLE = {"trialing", "active", "past_due"}
    NON_BILLABLE = {"canceled", "unpaid", "incomplete", "incomplete_expired", "paused"}


@dataclass
class SubscriptionExtras:
    """Data class for subscription extras."""
    agents: int = 0
    inboxes: int = 0
    
    @classmethod
    def empty(cls) -> 'SubscriptionExtras':
        """Create empty extras."""
        return cls(0, 0)


@dataclass
class SubscriptionMetadata:
    """Data class for subscription metadata."""
    extra_agents: Optional[int] = None
    extra_inboxes: Optional[int] = None
    selected_plan_id: Optional[int] = None
    
    @classmethod
    def from_subscription(cls, subscription: DJSubscription) -> 'SubscriptionMetadata':
        """Extract metadata from subscription."""
        try:
            metadata = subscription.metadata or {}
            return cls(
                extra_agents=SafeConverter.to_int(metadata.get("extra_agents")),
                extra_inboxes=SafeConverter.to_int(metadata.get("extra_inboxes")),
                selected_plan_id=SafeConverter.to_int(metadata.get("selected_plan_id"))
            )
        except Exception:
            logger.exception("Failed to extract metadata from subscription %s", subscription.id)
            return cls()


@dataclass
class AccountUpdateData:
    """Data class for account update information."""
    status: str
    plan: Optional[Plan]
    extras: SubscriptionExtras
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


class SafeConverter:
    """Safe conversion utilities."""
    
    @staticmethod
    def to_int(value) -> Optional[int]:
        """Safely convert value to integer."""
        try:
            return None if value is None else int(value)
        except (ValueError, TypeError):
            return None


class StripeAPIClient:
    """Wrapper for Stripe API calls with error handling."""
    
    @staticmethod
    def retrieve_subscription(subscription_id: str, expand: Optional[List[str]] = None) -> Optional[dict]:
        """Safely retrieve subscription from Stripe."""
        try:
            return stripe.Subscription.retrieve(subscription_id, expand=expand)
        except Exception:
            logger.exception("Failed to retrieve subscription %s from Stripe", subscription_id)
            return None


class PriceIdExtractor:
    """Handles extraction of price IDs from different sources."""
    
    @staticmethod
    def from_database(subscription: DJSubscription) -> List[str]:
        """Extract price IDs from database subscription items."""
        price_ids = []
        try:
            for item in subscription.items.all():
                price = getattr(item, "price", None)
                price_id = getattr(price, "id", None)
                if price_id:
                    price_ids.append(price_id)
        except Exception:
            logger.exception("Failed to read items from subscription %s", subscription.id)
        return price_ids
    
    @staticmethod
    def from_stripe_api(subscription_id: str) -> List[str]:
        """Extract price IDs from Stripe API."""
        subscription_data = StripeAPIClient.retrieve_subscription(
            subscription_id, 
            expand=["items.data.price"]
        )
        
        if not subscription_data:
            return []
        
        items = subscription_data.get("items", {}).get("data", [])
        return [
            item["price"]["id"]
            for item in items
            if item.get("price") and item["price"].get("id")
        ]


class PlanResolver:
    """Resolves plans from price IDs."""
    
    @staticmethod
    def find_by_price_ids(price_ids: List[str]) -> Optional[Plan]:
        """Find plan by price IDs."""
        if not price_ids:
            return None
        
        # Try monthly plans first
        plan = Plan.objects.filter(billing_monthly_price_id__in=price_ids).first()
        if plan:
            return plan
        
        # Then try yearly plans
        return Plan.objects.filter(billing_yearly_price_id__in=price_ids).first()


class ExtrasCalculator:
    """Calculates subscription extras from various sources."""
    
    @staticmethod
    def _get_price_id_sets(plan: Optional[Plan]) -> Tuple[Set[str], Set[str]]:
        """Get agent and inbox price ID sets from plan."""
        if not plan:
            return set(), set()
        
        agent_ids = {
            getattr(plan, "billing_extra_agent_price_id", None),
            getattr(plan, "billing_extra_agent_price_id_yearly", None),
        }
        inbox_ids = {
            getattr(plan, "billing_extra_inbox_price_id", None),
            getattr(plan, "billing_extra_inbox_price_id_yearly", None),
        }
        
        agent_ids.discard(None)
        inbox_ids.discard(None)
        
        return agent_ids, inbox_ids
    
    @staticmethod
    def from_database_items(plan: Optional[Plan], subscription: DJSubscription) -> SubscriptionExtras:
        """Calculate extras from database subscription items."""
        agent_ids, inbox_ids = ExtrasCalculator._get_price_id_sets(plan)
        extras = SubscriptionExtras()
        
        try:
            for item in subscription.items.all():
                price = getattr(item, "price", None)
                price_id = getattr(price, "id", None)
                quantity = SafeConverter.to_int(getattr(item, "quantity", 0)) or 0
                
                if price_id in agent_ids:
                    extras.agents = quantity
                elif price_id in inbox_ids:
                    extras.inboxes = quantity
        except Exception:
            logger.exception("Failed to derive extras from database for subscription %s", subscription.id)
        
        return extras
    
    @staticmethod
    def from_stripe_api(plan: Optional[Plan], subscription_id: str) -> SubscriptionExtras:
        """Calculate extras from Stripe API."""
        agent_ids, inbox_ids = ExtrasCalculator._get_price_id_sets(plan)
        extras = SubscriptionExtras()
        
        subscription_data = StripeAPIClient.retrieve_subscription(
            subscription_id, 
            expand=["items.data.price"]
        )
        
        if not subscription_data:
            return extras
        
        try:
            items = subscription_data.get("items", {}).get("data", [])
            for item in items:
                price = item.get("price", {})
                price_id = price.get("id")
                quantity = SafeConverter.to_int(item.get("quantity", 0)) or 0
                
                if price_id in agent_ids:
                    extras.agents = quantity
                elif price_id in inbox_ids:
                    extras.inboxes = quantity
        except Exception:
            logger.exception("Failed to derive extras from Stripe API for subscription %s", subscription_id)
        
        return extras


class AccountFinder:
    """Finds accounts associated with subscriptions."""
    
    @staticmethod
    def find_by_subscription(subscription: DJSubscription) -> Optional[Account]:
        """Find account by subscription (customer_id first, then metadata)."""
        # Priority 1: customer_id
        if subscription.customer_id:
            account = Account.objects.filter(stripe_customer_id=subscription.customer_id).first()
            if account:
                return account
        
        # Priority 2: metadata fallback
        try:
            metadata = subscription.metadata or {}
            account_id = metadata.get("account_id")
            if account_id:
                return Account.objects.filter(pk=account_id).first()
        except Exception:
            logger.exception("Failed to extract account_id from metadata for subscription %s", subscription.id)
        
        return None


class SubscriptionValidator:
    """Validates subscription status and activity."""
    
    @staticmethod
    def is_locally_active(subscription: DJSubscription) -> bool:
        """Check if subscription is active based on local data."""
        try:
            return (
                subscription.status in SubscriptionStatus.BILLABLE.value and
                not getattr(subscription, "ended_at", None)
            )
        except Exception:
            return False
    
    @staticmethod
    def is_stripe_active(subscription: DJSubscription) -> Optional[bool]:
        """Check if subscription is active via Stripe API."""
        subscription_data = StripeAPIClient.retrieve_subscription(subscription.id)
        if not subscription_data:
            return None
        
        status = subscription_data.get("status")
        return status in SubscriptionStatus.BILLABLE.value
    
    @staticmethod
    def is_really_active(subscription: DJSubscription) -> bool:
        """Combine local and Stripe validation."""
        local_active = SubscriptionValidator.is_locally_active(subscription)
        stripe_active = SubscriptionValidator.is_stripe_active(subscription)
        
        # If Stripe check fails, use local validation
        return stripe_active if stripe_active is not None else local_active


class SubscriptionProcessor:
    """Main processor for subscription updates."""
    
    def __init__(self):
        self.price_extractor = PriceIdExtractor()
        self.plan_resolver = PlanResolver()
        self.extras_calculator = ExtrasCalculator()
        self.validator = SubscriptionValidator()
    
    def should_keep_access(self, subscription: DJSubscription) -> bool:
        """Determine if subscription should maintain access."""
        if subscription.status in SubscriptionStatus.BILLABLE.value:
            return True
        
        # Handle cancel_at_period_end cases
        cancel_at_end = getattr(subscription, "cancel_at_period_end", False)
        return cancel_at_end and subscription.status not in SubscriptionStatus.NON_BILLABLE.value
    
    def resolve_plan(self, subscription: DJSubscription, keep_access: bool) -> Optional[Plan]:
        """Resolve the appropriate plan for the subscription."""
        if not keep_access:
            return get_free_plan()
        
        # Try database first
        price_ids = self.price_extractor.from_database(subscription)
        plan = self.plan_resolver.find_by_price_ids(price_ids)
        
        # Fallback to Stripe API if no plan found
        if not plan:
            live_price_ids = self.price_extractor.from_stripe_api(subscription.id)
            plan = self.plan_resolver.find_by_price_ids(live_price_ids)
        
        return plan
    
    def calculate_extras(self, subscription: DJSubscription, plan: Optional[Plan], 
                        keep_access: bool) -> SubscriptionExtras:
        """Calculate subscription extras with metadata priority."""
        if not keep_access:
            return SubscriptionExtras.empty()
        
        metadata = SubscriptionMetadata.from_subscription(subscription)
        
        # If metadata has both values, use them
        if metadata.extra_agents is not None and metadata.extra_inboxes is not None:
            return SubscriptionExtras(metadata.extra_agents, metadata.extra_inboxes)
        
        # Try database items
        db_extras = self.extras_calculator.from_database_items(plan, subscription)
        
        # If no metadata and no database extras, try Stripe API
        if (metadata.extra_agents is None and metadata.extra_inboxes is None and 
            db_extras.agents == 0 and db_extras.inboxes == 0):
            api_extras = self.extras_calculator.from_stripe_api(plan, subscription.id)
            return SubscriptionExtras(
                metadata.extra_agents or api_extras.agents,
                metadata.extra_inboxes or api_extras.inboxes
            )
        
        # Combine metadata with database
        return SubscriptionExtras(
            metadata.extra_agents or db_extras.agents,
            metadata.extra_inboxes or db_extras.inboxes
        )
    
    def create_update_data(self, subscription: DJSubscription) -> AccountUpdateData:
        """Create account update data from subscription."""
        keep_access = self.should_keep_access(subscription)
        plan = self.resolve_plan(subscription, keep_access)
        extras = self.calculate_extras(subscription, plan, keep_access)
        
        # Handle metadata plan override
        metadata = SubscriptionMetadata.from_subscription(subscription)
        if metadata.selected_plan_id and keep_access:
            try:
                plan = Plan.objects.get(pk=metadata.selected_plan_id)
            except Plan.DoesNotExist:
                logger.warning("Selected plan %s not found in metadata", metadata.selected_plan_id)
        
        return AccountUpdateData(
            status="active" if keep_access else "suspended",
            plan=plan,
            extras=extras,
            stripe_customer_id=subscription.customer_id,
            stripe_subscription_id=subscription.id if keep_access else None
        )
    
    def apply_updates_to_account(self, account: Account, update_data: AccountUpdateData) -> None:
        """Apply updates to account with atomic transaction."""
        updates = []
        
        with transaction.atomic():
            # Status update
            if getattr(account, "status", None) != update_data.status:
                account.status = update_data.status
                updates.append("status")
            
            # Plan update
            if update_data.plan and account.plan_id != update_data.plan.pk:
                account.plan = update_data.plan
                updates.append("plan")
            
            # Extras updates
            if hasattr(account, "extra_agents") and account.extra_agents != update_data.extras.agents:
                account.extra_agents = update_data.extras.agents
                updates.append("extra_agents")
            
            if hasattr(account, "extra_inboxes") and account.extra_inboxes != update_data.extras.inboxes:
                account.extra_inboxes = update_data.extras.inboxes
                updates.append("extra_inboxes")
            
            # Stripe IDs updates
            if (hasattr(account, "stripe_customer_id") and 
                not account.stripe_customer_id and update_data.stripe_customer_id):
                account.stripe_customer_id = update_data.stripe_customer_id
                updates.append("stripe_customer_id")
            
            if hasattr(account, "stripe_subscription_id"):
                current_sub_id = getattr(account, "stripe_subscription_id", None)
                if current_sub_id != update_data.stripe_subscription_id:
                    account.stripe_subscription_id = update_data.stripe_subscription_id
                    updates.append("stripe_subscription_id")
            
            # Save if there are updates
            if updates:
                account.save(update_fields=updates)
                logger.info("Updated account %s with fields: %s", account.id, ", ".join(updates))
    
    def process_subscription_update(self, subscription: DJSubscription) -> bool:
        """Process a subscription update."""
        account = AccountFinder.find_by_subscription(subscription)
        if not account:
            logger.warning("Account not found for subscription %s", subscription.id)
            return False
        
        # For non-billable statuses, apply normal rules
        if subscription.status in SubscriptionStatus.NON_BILLABLE.value:
            update_data = self.create_update_data(subscription)
            self.apply_updates_to_account(account, update_data)
            return True
        
        # For potentially billable statuses, validate first
        if not self.validator.is_really_active(subscription):
            logger.info(
                "Subscription %s is not really active yet; skipping account update", 
                subscription.id
            )
            return False
        
        update_data = self.create_update_data(subscription)
        self.apply_updates_to_account(account, update_data)
        return True
    
    def process_subscription_deletion(self, subscription: DJSubscription) -> bool:
        """Process subscription deletion."""
        account = AccountFinder.find_by_subscription(subscription)
        if not account:
            logger.warning("Account not found for deleted subscription %s", subscription.id)
            return False
        
        free_plan = get_free_plan()
        with transaction.atomic():
            account.plan = free_plan
            account.extra_agents = 0
            account.extra_inboxes = 0
            account.save(update_fields=["plan", "extra_agents", "extra_inboxes"])
        
        logger.info("Reset account %s to free plan after subscription deletion", account.id)
        return True


# Global processor instance
subscription_processor = SubscriptionProcessor()


# Signal Handlers

@receiver(post_save, sender=DJSubscription, dispatch_uid="accounts.on_subscription_saved")
def on_subscription_saved(sender, instance: DJSubscription, created, **kwargs):
    """Handle subscription save events."""
    try:
        subscription_processor.process_subscription_update(instance)
    except Exception:
        logger.exception("Failed to process subscription update %s", instance.id)


@receiver(post_delete, sender=DJSubscription, dispatch_uid="accounts.on_subscription_deleted")
def on_subscription_deleted(sender, instance: DJSubscription, **kwargs):
    """Handle subscription deletion events."""
    try:
        subscription_processor.process_subscription_deletion(instance)
    except Exception:
        logger.exception("Failed to process subscription deletion %s", instance.id)