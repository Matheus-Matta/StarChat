# plans/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from django.shortcuts import redirect
from django.contrib import messages
from accounts.models import Plan

class PlanSubscribed(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    """
    View de assinaturas, rodando dentro do layout Unfold/Admin,
    recebendo 'model_admin' via as_view(model_admin=self).
    """
    template_name = "admin/plan_subscribed.html"
    title = "Plano Assinado"
    permission_required = ()
    
    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current = self.request.user.account.plan
        ctx["current_plan"] = current
        ctx["other_plans"]  = Plan.objects.filter(is_active=True, is_plan_staff=False).exclude(pk=current.pk).order_by("monthly_price")
        from starchat.features import CHATWOOT_FEATURES
        
        features_flags  = CHATWOOT_FEATURES["features"]
        features_labels = CHATWOOT_FEATURES["labels"]

        # monta lista só com os rótulos habilitados
        ctx["features"] = [
            features_labels[key]
            for key, enabled in features_flags.items()
            if enabled and key in features_labels
        ]

        return ctx

