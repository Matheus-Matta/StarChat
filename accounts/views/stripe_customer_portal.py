# accounts/views/stripe_customer_portal.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeCustomerPortalView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not getattr(account, "stripe_customer_id", None):
            messages.error(request, "Cliente Stripe não encontrado para sua conta.")
            return redirect("admin:plan_subscribed")

        return_url = request.build_absolute_uri(reverse("admin:index"))

        try:
            sess_kwargs = {
                "customer": account.stripe_customer_id,
                "return_url": return_url,
                **self._stripe_connect_kwargs(),
            }

            cfg_id = self._portal_configuration_id()
            if cfg_id:
                sess_kwargs["configuration"] = cfg_id

            session = stripe.billing_portal.Session.create(**sess_kwargs)
            return redirect(session.url)

        except Exception as e:
            messages.error(request, f"Não foi possível abrir o Portal do Cliente: {e}")
            return redirect("admin:plan_subscribed")

    def _stripe_connect_kwargs(self):
        acct = getattr(settings, "STRIPE_CONNECT_ACCOUNT_ID", None)
        return {"stripe_account": acct} if acct else {}

    def _portal_configuration_id(self):
        cfg_id = getattr(settings, "STRIPE_PORTAL_CONFIGURATION_ID", None)
        if cfg_id:
            return cfg_id
        try:
            confs = stripe.billing_portal.Configuration.list(
                limit=1, **self._stripe_connect_kwargs()
            )
            if confs.data:
                return confs.data[0]["id"]
        except Exception:
            pass
        return None
