# accounts/checkout_builder.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from django.conf import settings
import stripe

@dataclass
class ModeConfig:
    pmc_id: Optional[str]
    pm_types_fallback: List[str]

class StripeCheckoutBuilder:
    """
    Constrói Checkout Sessions para assinatura (mode='subscription')
    variando os métodos de pagamento por 'pay_mode'.
    """
    def __init__(
        self,
        *,
        account,                  # obj com .stripe_customer_id e .email
        plan,                     # obj do seu Plan com prices
        interval: str,            # "month" | "year"
        extra_agents: int = 0,
        extra_inboxes: int = 0,
        success_url: str,
        cancel_url: str,
    ):
        self.account = account
        self.plan = plan
        self.interval = "year" if interval == "year" else "month"
        self.extra_agents = max(0, int(extra_agents or 0))
        self.extra_inboxes = max(0, int(extra_inboxes or 0))
        self.success_url = success_url
        self.cancel_url = cancel_url

    # ---- prices por intervalo
    def _base_price(self) -> str:
        return self.plan.billing_yearly_price_id if self.interval == "year" else self.plan.billing_monthly_price_id

    def _extra_agent_price(self) -> Optional[str]:
        return (getattr(self.plan, "billing_extra_agent_price_id_yearly", None)
                if self.interval == "year" else self.plan.billing_extra_agent_price_id)

    def _extra_inbox_price(self) -> Optional[str]:
        return (getattr(self.plan, "billing_extra_inbox_price_id_yearly", None)
                if self.interval == "year" else self.plan.billing_extra_inbox_price_id)

    def _line_items(self) -> List[Dict]:
        if not self._base_price():
            raise ValueError("Preço base indisponível para o ciclo escolhido.")
        items = [{"price": self._base_price(), "quantity": 1}]
        if self.extra_agents and self._extra_agent_price():
            items.append({"price": self._extra_agent_price(), "quantity": self.extra_agents})
        if self.extra_inboxes and self._extra_inbox_price():
            items.append({"price": self._extra_inbox_price(), "quantity": self.extra_inboxes})
        return items

    # ---- mapeia pay_mode -> PM Configuration + fallback p/ payment_method_types
    def _mode_config(self, pay_mode: str) -> ModeConfig:
        pay_mode = (pay_mode or "card").lower()
        allowed = set(getattr(settings, "STRIPE_ALLOWED_PAYMENT_METHOD_TYPES", ["card"]))

        mapping = {
            "card": ModeConfig(
                pmc_id=getattr(settings, "STRIPE_PMC_CARD", None),
                pm_types_fallback=[m for m in ["card"] if m in allowed],
            ),
            "boleto": ModeConfig(
                pmc_id=getattr(settings, "STRIPE_PMC_BOLETO", None),
                pm_types_fallback=[m for m in ["boleto"] if m in allowed],
            ),
            "pix": ModeConfig(
                pmc_id=getattr(settings, "STRIPE_PMC_PIX", None),
                pm_types_fallback=[m for m in ["pix"] if m in allowed],
            ),
            "pix_boleto": ModeConfig(
                pmc_id=getattr(settings, "STRIPE_PMC_PIX_BOLETO", None),
                pm_types_fallback=[m for m in ["pix", "boleto"] if m in allowed],
            ),
        }
        return mapping.get(pay_mode, mapping["card"])

    def create_subscription_session(self, *, pay_mode: str):
        """
        Cria uma Checkout Session de assinatura com os métodos
        de pagamento definidos pelo pay_mode.
        """
        cfg = self._mode_config(pay_mode)
        params: Dict = {
            "mode": "subscription",
            "customer": self.account.stripe_customer_id,
            "line_items": self._line_items(),
            "success_url": self.success_url,
            "cancel_url": self.cancel_url,
            # Checkout gerencia a coleta do PM; gravamos metadados úteis na assinatura:
            "subscription_data": {
                "metadata": {
                    "account_id": str(getattr(self.account, "pk", "")),
                    "selected_plan_id": str(getattr(self.plan, "pk", "")),
                    "selected_interval": self.interval,
                    "extra_agents": str(self.extra_agents or 0),
                    "extra_inboxes": str(self.extra_inboxes or 0),
                }
            },
            # ajuda para métodos locais (endereço e telefone podem ser necessários)
            "customer_update": {"name": "auto", "address": "auto"},
            "billing_address_collection": "required" if cfg.pm_types_fallback != ["card"] else "auto",
            "phone_number_collection": {"enabled": cfg.pm_types_fallback != ["card"]},
            # impostos automáticos se você usar Stripe Tax (ligue se quiser)
            "automatic_tax": {"enabled": False},
        }

        # Prefira Payment Method Configuration; caia para payment_method_types se o ID não estiver setado.
        if cfg.pmc_id:
            params["payment_method_configuration"] = cfg.pmc_id
        elif cfg.pm_types_fallback:
            params["payment_method_types"] = cfg.pm_types_fallback

        return stripe.checkout.Session.create(**params)
