from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from simple_history.admin import SimpleHistoryAdmin
from config.unfold.admin import BaseAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter, ChoicesRadioFilter
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from .views import UserProfileView
from unfold.admin import ModelAdmin
from .models import Plan, Account, Company
from djstripe.models import Customer, Invoice
import stripe
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = get_user_model()


@admin.register(Plan)
class PlanAdmin(BaseAdmin, SimpleHistoryAdmin):
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
            'fields': ('monthly_price', 'yearly_price', 'requires_payment', 'billing_price_id',),
        }),
        ('Status', {
            'fields': ('is_active','is_favorite', 'is_plan_staff'),
        }),
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

@admin.register(Company)
class CompanyAdmin(BaseAdmin, SimpleHistoryAdmin):
    fieldsets = (
        ('Dados da Empresa', {
            'fields': (
                'account',                  
                ('name', 'cnpj'),
                'billing_address',
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
        "last_payment_amount_display",
        "next_payment_amount_display",
        "payment_difference_display",
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

    @admin.display(description='Endereço de Cobrança')
    def get_billing_address(self, obj):
        return obj.company.billing_address if hasattr(obj, 'company') else '-'

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
        custom = self.admin_site.admin_view(
            UserProfileView.as_view(model_admin=self)
        )
        return super().get_urls() + [
          path("profile", custom, name="user_profile"),
        ] 
        
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



