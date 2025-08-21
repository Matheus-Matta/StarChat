# plans/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from django.http import JsonResponse
from django.template.loader import render_to_string

class AccountCapacity(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    template_name = ""
    title = "Alterar Plano"
    permission_required = ()
    
    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account:
            return JsonResponse({"error": "account_not_found"}, status=404)

        agents_html = render_to_string(
            "partials/components/card-agents.html", {"agents": account.agents_info, "plan_id": account.plan.id}
        )
        inboxes_html = render_to_string(
            "partials/components/card-inboxes.html", {"inboxes": account.inboxes_info, "plan_id": account.plan.id}
        )
        data = {"agents_html": agents_html, "inboxes_html": inboxes_html}
        return JsonResponse(data, status=200)
