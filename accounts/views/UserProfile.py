from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from unfold.views import UnfoldModelAdminViewMixin
from accounts.forms import CombinedProfileForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from accounts.models import Company
class UserProfileView(UnfoldModelAdminViewMixin, FormView):
    title = "Meu Perfil"
    permission_required = ()
    template_name = "admin/user_profile.html"
    form_class = CombinedProfileForm
    success_url = reverse_lazy("admin:user_profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        account = getattr(user, "account", None)
        company = getattr(account, "company", None) if account else None
        kwargs.update({
            "user": user,
            "account": account,
            "company": company,
        })
        return kwargs

    def form_valid(self, form):
        # Deixa o form fazer todo o trabalho (user, account, company e address)
        form.save()
        messages.success(self.request, "Perfil atualizado com sucesso.")
        return super().form_valid(form)

