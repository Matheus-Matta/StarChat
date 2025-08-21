# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q

from djstripe.models import Invoice as DJInvoice, Customer as DJCustomer
from unfold.views import UnfoldModelAdminViewMixin


class InvoiceList(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    template_name = "admin/invoices_list.html"
    title = _("Faturas")
    permission_required = ()

    # --- helpers ------------------------------------------------------------
    def _get_account_and_customer(self):
        """Retorna (account, djstripe_customer) sem criar nada novo."""
        account = getattr(self.request.user, "account", None)
        if not account or not account.stripe_customer_id:
            return account, None

        dj_cust = DJCustomer.objects.filter(id=account.stripe_customer_id).first()
        return account, dj_cust

    # --- queryset base (sempre filtrado no customer do usuário) -------------
    def _base_queryset(self):
        qs = DJInvoice.objects.select_related("customer").order_by("-created")

        account, dj_cust = self._get_account_and_customer()
        if not dj_cust:
            # Sem customer conhecido → nada a listar
            return DJInvoice.objects.none()

        return qs.filter(customer=dj_cust)

    def get_queryset(self):
        qs = self._base_queryset()

        q = (self.request.GET.get("q") or "").strip()
        status = self.request.GET.get("status") or ""
        paid = self.request.GET.get("paid")  # '1' | '0' | None

        if q:
            qs = qs.filter(
                Q(id__icontains=q) |
                Q(number__icontains=q) |
                Q(customer__id__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if paid in ("0", "1"):
            qs = qs.filter(paid=(paid == "1"))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Se não houver customer, já avisa o usuário
        account, dj_cust = self._get_account_and_customer()
        if not dj_cust:
            messages.info(
                self.request,
                _("Nenhum cliente Stripe vinculado à sua conta. Cadastre um método de pagamento para começar.")
            )

        qs = self.get_queryset()
        page = int(self.request.GET.get("page", 1))
        per_page = int(self.request.GET.get("per_page", 20))

        from django.core.paginator import Paginator
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        ctx.update(
            {
                "page_obj": page_obj,
                "paginator": paginator,
                "object_list": page_obj.object_list,
                "search_q": self.request.GET.get("q", ""),
                "filter_status": self.request.GET.get("status", ""),
                "filter_paid": self.request.GET.get("paid", ""),
                "status_choices": ["draft", "open", "paid", "uncollectible", "void"],
                "djstripe_customer": dj_cust,
                "account": account,
            }
        )
        return ctx
