from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from unfold.views import UnfoldModelAdminViewMixin
from accounts.forms import CombinedProfileForm

class UserProfileView(UnfoldModelAdminViewMixin, FormView):
    title = "Meu Perfil"
    permission_required = ()
    template_name = "admin/user_profile.html"
    form_class = CombinedProfileForm
    success_url = reverse_lazy("admin:user_profile")

    def get_initial(self):
        user = self.request.user
        acct = getattr(user, "account", None)
        comp = getattr(acct, "company", None) if acct else None
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": acct.phone,
            "name": comp.name if comp else "",
            "cnpj": comp.cnpj if comp else "",
            "company_type": comp.company_type if comp else None,
        }

    def form_valid(self, form):
        user = self.request.user
        acct = user.account
        comp = getattr(acct, "company", None)

        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.email = form.cleaned_data["email"]
        user.save()

        acct.plan = form.cleaned_data["plan"]
        acct.phone = form.cleaned_data["phone"]
        acct.save()

        if comp:
            comp.name = form.cleaned_data["name"]
            comp.cnpj = form.cleaned_data["cnpj"]
            comp.company_type = form.cleaned_data["company_type"]
            comp.save()

        return super().form_valid(form)
