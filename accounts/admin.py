from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from simple_history.admin import SimpleHistoryAdmin
from config.unfold.admin import BaseAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter, ChoicesRadioFilter
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from .views import *
from unfold.admin import ModelAdmin
from .models import Plan, Account, Company, Address
from djstripe.models import Customer, Invoice
import stripe
from django.utils.translation import gettext_lazy as _
from django.conf import settings
User = get_user_model()


@admin.register(Plan)
class PlanAdmin(BaseAdmin, admin.ModelAdmin):
    
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'description','hex_color'),
        }),
        ('Agentes', {
            'fields': ('included_agents', 'extra_agent_price'),
        }),
        ('Inboxes', {
            'fields': ('included_inboxes', 'extra_inbox_price'),
        }),
        ('Assinatura', {
            'fields': ('monthly_price', 'yearly_price', 'requires_payment', ),
        }),
        ('Status', {
            'fields': ('is_active','is_favorite', 'is_plan_staff'),
        }),
        ('Stripe', {
            'fields': ('stripe_product_id', 'billing_monthly_price_id', 'billing_yearly_price_id', 'billing_extra_agent_price_id', 'billing_extra_inbox_price_id'),
        }),
    )

    readonly_fields = (
        'stripe_product_id', 'billing_monthly_price_id', 'billing_yearly_price_id',
        'billing_extra_agent_price_id', 'billing_extra_inbox_price_id'
    )
    list_display = (
        'name',
        'included_agents', 'included_inboxes',
        'monthly_price', 'yearly_price',
        'is_active', 'is_favorite', 'is_plan_staff'
    )
    list_filter = ('is_active', 'name')
    search_fields = ('name', 'description')
    ordering = ('-is_active', 'name')
    
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("subscribed/", self.admin_site.admin_view( 
                PlanSubscribed.as_view(model_admin=self)
                ),
                name="plan_subscribed",
            ),
            path("subscribe/<int:plan_id>/", self.admin_site.admin_view( 
                PlanSubscribe.as_view(model_admin=self)
                ),
                name="plan_subscribe",
            ),
            path("canceled/", self.admin_site.admin_view( 
                PlanCanceled.as_view(model_admin=self)
                ),
                name="plan_canceled",
            ),
        ]
        return custom + urls  
        
    
@admin.register(Company)
class CompanyAdmin(BaseAdmin, SimpleHistoryAdmin):
    fieldsets = (
        ('Dados da Empresa', {
            'fields': (
                'account',                  
                ('name', 'cnpj'),
                'company_type',
            )
        }),
    )
    list_display = (
        'account', 'name', 'cnpj', 'company_type'
    )
    list_filter = ('company_type',)
    search_fields = ('name', 'cnpj', 'account__email')
    ordering = ('name',)
    



@admin.register(Account)
class AccountAdmin(BaseAdmin, SimpleHistoryAdmin):
    list_display = (
        "email",
        "plan",
        "calculate_price",
        "extra_agents",
        "extra_inboxes",
        "status",
        "get_company_link",
    )

    readonly_fields = (
        "calculate_price",
        "last_payment_amount_display",
        "next_payment_amount_display",
        "payment_difference_display",
        "created_at",
        "updated_at",
        "get_company_link",
        "get_company_name",
        "get_company_cnpj",
        "get_billing_address",
        "get_company_type",
        "get_chatwoot_account",
    )

    fieldsets = (
        (_("Cobrança"), {
            "fields": (
                "stripe_customer_id",
                "plan",
                "calculate_price",
            )
        }),
        (_("Contato"), {
            "fields": (
                "email",
                "phone",
            )
        }),
        (_("Extras"), {
            "fields": (
                "extra_agents",
                "extra_inboxes",
            )
        }),
        (_("Pagamentos Stripe"), {
            "fields": (
                "last_payment_amount_display",
                "next_payment_amount_display",
                "payment_difference_display",
            )
        }),
        (_("Empresa"), {
            "fields": (                
                "get_company_link",
                "get_company_name",
                "get_company_cnpj",
                "get_billing_address",
                "get_company_type",
            )
        }),
        (_("Metadados"), {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
        (_("Chatwoot"), {
            "fields": (
                "get_chatwoot_account",
                'status',
            )
        }),
    )

    @admin.display(description=_("Último pagamento"))
    def last_payment_amount_display(self, obj):
        amt = obj.last_payment_amount
        return f"R$ {amt:.2f}"  

    @admin.display(description=_("Próximo pagamento (prévia)"))
    def next_payment_amount_display(self, obj):
        amt = obj.next_payment_amount
        return f"R$ {amt:.2f}"  

    @admin.display(description=_("Diferença"))
    def payment_difference_display(self, obj):
        diff = obj.payment_difference()
        val = diff["difference"]
        sign = "+" if diff["direction"] == "higher" else ("-" if diff["direction"] == "lower" else "")
        return f"{sign}R$ {val:.2f}"
    
    @admin.display(description='Empresa (clique para editar)')
    def get_company_link(self, obj):
        if hasattr(obj, 'company'):
            url = reverse('admin:accounts_company_change', args=[obj.company.pk])
            return format_html('<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>', url, obj.company.name)
        return '-'

    @admin.display(description='Nome')
    def get_company_name(self, obj):
        return obj.company.name if hasattr(obj, 'company') else '-'

    @admin.display(description='CNPJ')
    def get_company_cnpj(self, obj):
        return obj.company.cnpj if hasattr(obj, 'company') else '-'

    @admin.display(description=_("Endereço de Cobrança"))
    def get_billing_address(self, obj):
        company = getattr(obj, "company", None)
        addr = getattr(company, "billing_address", None) if company else None

        app_label = Address._meta.app_label
        model_name = Address._meta.model_name

        try:
            if addr:
                url = reverse(f"admin:{app_label}_{model_name}_change", args=[addr.pk])
                label = f"{addr.line1} {addr.number or ''}, {addr.city} - {addr.postal_code}"
                return format_html(
                    '<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>',
                    url, label.strip()
                )
            else:
                add_url = reverse(f"admin:{app_label}_{model_name}_add")
                return format_html(
                    '<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>',
                    add_url, _("Adicionar endereço")
                )
        except NoReverseMatch:
            # Caso o model não esteja registrado no admin
            return _("(Endereço não registrado no admin)")

    @admin.display(description='Tipo de Empresa')
    def get_company_type(self, obj):
        return obj.company.get_company_type_display() if hasattr(obj, 'company') else '-'
    
    @admin.display(description='ID Conta do Chatwoot')
    def get_chatwoot_account(self, obj):
        """Retorna a conta do Chatwoot associada, se existir."""
        if hasattr(obj, 'chatwoot_account'):
            url = reverse('admin:starchat_chatwootaccount_change', args=[obj.chatwoot_account.pk])
            return format_html('<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>', url, obj.chatwoot_account.pk)
        return '-'


@admin.register(User)
class UserAdmin(BaseAdmin, DjangoUserAdmin):
    filter_horizontal = ('groups', 'user_permissions',)

    fieldsets = (
        ('Usuário', {
            'classes': ('tab-user',),
            'fields': (
                'username', 'password', 'user_chatwoot_id',
                'first_name', 'last_name', 'email','role',
            )
        }),
        ('Permissões', {
            'classes': ('tab-user',),
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions',
            )
        }),
        ('Conta', {
            'classes': ('tab-account',),
            'fields': (
                'get_account_email',
                'get_account_plan',
                'get_account_status',
            ),
            'description': 'Clique no email para editar a conta',
        }),
        ('Empresa', {
            'classes': ('tab-company',),
            'fields': (
                'get_company_name',
                'get_company_cnpj',
            ),
            'description': 'Clique no nome para editar a empresa',
        }),
    )

    readonly_fields = (
        'get_account_email',
        'get_account_plan',
        'get_account_status',
        'get_company_name',
        'get_company_cnpj',
    )

    list_display = ('username','email','get_account_plan','is_active')
    search_fields = ('username','email',)
    ordering = ('username',)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("profile/", self.admin_site.admin_view( 
                UserProfileView.as_view(model_admin=self)
                ),
                name="user_profile",
            ),
            path("capacity/", self.admin_site.admin_view( 
                AccountCapacity.as_view(model_admin=self)
                ),
                name="account_capacity",
            ),
            path("payments/", self.admin_site.admin_view( 
                PaymentMethod.as_view(model_admin=self)
                ),
                name="account_payments",
            ),
            path("invoices/", self.admin_site.admin_view( 
                InvoiceList.as_view(model_admin=self)
                ),
                name="account_invoices",
            ),  
            path("agents/", self.admin_site.admin_view( 
                AgentsList.as_view(model_admin=self)
                ),
                name="account_agents",
            ), 
            path("inboxes/", self.admin_site.admin_view( 
                InboxesList.as_view(model_admin=self)
                ),
                name="account_inboxes",
            ), 
        ]
        return custom + urls   
    
           
    @admin.display(description='Email da Conta')
    def get_account_email(self, obj):
        acct = getattr(obj, 'account', None)
        if not acct:
            return '-'
        url = reverse('admin:accounts_account_change', args=[acct.pk])
        return format_html('<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>', url, acct.email)

    @admin.display(description='Plano')
    def get_account_plan(self, obj):
        return obj.account.plan.name if getattr(obj, 'account', None) and obj.account.plan else '-'

    @admin.display(description='Status')
    def get_account_status(self, obj):
        return obj.account.status if hasattr(obj, 'account') else '-'

    @admin.display(description='Empresa')
    def get_company_name(self, obj):
        acct = getattr(obj, 'account', None)
        comp = getattr(acct, 'company', None) if acct else None
        if not comp:
            return '-'
        url = reverse('admin:accounts_company_change', args=[comp.pk])
        return format_html('<a class="text-blue-600 underline hover:no-underline" href="{}">{}</a>', url, comp.name)

    @admin.display(description='CNPJ')
    def get_company_cnpj(self, obj):
        acct = getattr(obj, 'account', None)
        comp = getattr(acct, 'company', None) if acct else None
        return comp.cnpj if comp else '-'

@admin.register(Address)
class AddressAdmin(BaseAdmin, admin.ModelAdmin):
    fieldsets = (
        (_("Identificação"), {
            "fields": ("type", "is_default", "name"),
        }),
        (_("Endereço"), {
            "fields": (("line1", "number"), "line2", "neighborhood"),
        }),
        (_("Localização"), {
            "fields": (("city", "state"), ("postal_code", "country")),
        }),
        (_("Contato/Documento"), {
            "fields": ("phone", "tax_id"),
        }),
        (_("Metadados"), {
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")
    list_display = (
        "type", "is_default", "name", "line1", "number",
        "city", "state", "postal_code", "country", "updated_at",
    )
    list_filter = ("type", "is_default", "country")
    search_fields = ("name", "line1", "postal_code", "city", "state")
    ordering = ("-updated_at",)
