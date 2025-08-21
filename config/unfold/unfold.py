from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static
from django.conf import settings  # <- para decidir test/live do Stripe
import os 

def _stripe_customers_url(request) -> str:
    """
    Monta a URL do Customer no Stripe Dashboard para o usuário atual.
    - Não importa nada de apps; usa apenas request.user.*.
    - Ajusta test/live com base em uma flag nas settings (ex.: STRIPE_LIVE_MODE).
    """
    # Descobre o ID do customer da forma mais segura possível sem imports
    account = getattr(request.user, "account", None)
    customer_id = getattr(account, "stripe_customer_id", None)

    # Test/live — ajuste a lógica à sua realidade:
    # True -> live, False/None -> test
    is_live_mode = bool(getattr(settings, "STRIPE_LIVE_MODE", False))
    base = "https://dashboard.stripe.com" if is_live_mode else "https://dashboard.stripe.com/test"

    # Se não tem customer_id, manda para o dashboard principal (ou retorne '' para desabilitar)
    if not customer_id:
        return f"{base}"

    return f"{base}/customers/{customer_id}"

UNFOLD = {
    "SHOW_LANGUAGES":   True,
    "SITE_TITLE":       _("Starchat"),
    "SITE_HEADER":      _("Starchat"),
    "SITE_SUBHEADER":   _("Painel de Controle"),
    "SITE_SYMBOL": "star",
    "DASHBOARD_CALLBACK": "core.admin.dashboard_context",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("assets/images/favicon.svg"),
        },
    ],
    "SITE_URL":         reverse_lazy("page:index"),
    "SITE_DROPDOWN": [
        {
            "icon": "book",
            "title": _("Documentação"),
            "link":  "https://docs.starchat.com",
            "attrs": {"target": "_blank"},
        },
        {
            "icon":  "link",
            "title": _("Site principal"),
            "link":  reverse_lazy("page:index"),
        },
    ],
    "SIDEBAR": {
        "show_search":           True,
        "show_all_applications": True,
        "navigation": [
            {
                "title":       _("Navegação"),
                "separator":   False,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Início"),
                        "icon":  "home",
                        "link":  reverse_lazy("admin:index"),
                    },
                    {
                        "title":       _("Planos"),
                        "icon":        "credit_card",
                        "link":        reverse_lazy("admin:accounts_plan_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Serviços"),
                        "icon":        "service_toolbox",
                        "link":        reverse_lazy("admin:core_siteservice_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Contas"),
                        "icon":        "business_center",
                        "link":        reverse_lazy("admin:accounts_account_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Usuários"),
                        "icon":        "person",
                        "link":        reverse_lazy("admin:accounts_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Grupos"),
                        "icon":        "group",
                        "link":        reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Permissões"),
                        "icon":        "security",
                        "link":        reverse_lazy("admin:auth_permission_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Traduções"),
                        "icon":  "translate",
                        "link":  reverse_lazy("rosetta-file-list", kwargs={"po_filter": "project"}),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Configurações"),
                        "icon":        "settings",
                        "link":        reverse_lazy("admin:core_siteconfig_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Agentes"),
                        "icon":        "headset_mic",
                        "link":        reverse_lazy("admin:account_agents"),
                    },
                    {
                        "title":       _("Canais"),
                        "icon":        "inbox",
                        "link":        reverse_lazy("admin:account_inboxes"),
                    },
                    {
                        "title":       _("Faturas"),
                        "icon":        "receipt",
                        "link":        reverse_lazy("admin:account_invoices"),
                    },
                    {
                        "title":       _("Assinatura"),
                        "icon":        "credit_card",
                        "link":        reverse_lazy("admin:plan_subscribed"),
                    },
                    {
                        "title":       _("Formas de pagamento"),
                        "icon":        "payments",
                        "link":        reverse_lazy("admin:account_payments"),
                    },
                ],
            },
            {
                "title":       _("Links"),
                "icon":        "link",
                "separator":   False,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Página do cliente (Stripe)"),
                        "icon": "link",
                        "link": reverse_lazy("stripe_customer_portal"),
                        "permission": lambda request: (
                            hasattr(request.user, "is_authenticated") and request.user.is_authenticated
                            and hasattr(request.user, "account")
                            and getattr(getattr(request.user, "account", None), "stripe_customer_id", None) is not None
                        ),
                        "attrs": {"target": "_blank"},
                    },
                    {
                        "title": _("Starchat Dashboard"),
                        "icon":  "analytics",
                        "attrs": {"target": "_blank"},
                        "link":  getattr(settings, "CHATWOOT_URL",  os.getenv("CHATWOOT_URL")),
                        "permission": lambda request: request.user.is_authenticated,
                    },
                ],
            },
        ],
    },
    "COLORS": {
        "base": {
            "50":  "249, 250, 251",   # #F9FAFB
            "100": "243, 244, 246",   # #F3F4F6
            "200": "229, 231, 235",   # #E5E7EB
            "300": "209, 213, 219",   # #D1D5DB
            "400": "156, 163, 175",   # #9CA3AF
            "500": "107, 114, 128",   # #6B7280
            "600": "75,  85,  99",    # #4B5563
            "700": "55,  69,  77",    # #374151
            "800": "31,  41,  55",    # #1F2937
            "900": "17,  18,  27",    # #111827
        },
        "primary": {
             "50":  "241, 236, 254",  # #F1ECFE
             "100": "233, 217, 252",  # #E9D9FC
             "200": "216, 180, 254",  # #D8B4FE
             "300": "192, 132, 252",  # #C084FC
             "400": "168,  85, 247",  # #A855F7
             "500": "81,  56, 238",   # #5138EE,
             "600": "70,  48, 206",   # #4630CE,
             "700": "58,  39, 175",   # #3A27AF,
             "800": "47,  32, 144",   # #2F2090
             "900": "36,  24, 112",   # #241870
             "950": "23,  15,  75",   # #170F4B
        },
    },
    "ACCOUNT": {
        "navigation": [
                {
                    "title": _("Alterar senha"),
                    "icon":  "lock",
                    "link":  reverse_lazy("admin:password_change"),
                    "permission": lambda request: request.user.has_usable_password(),
                },  
                {
                    "title": _("Meu perfil"),
                    "icon":  "person",
                    "link": reverse_lazy("admin:user_profile"),
                    "permission": lambda request: request.user.is_authenticated,
                },   
            ],
    },
}
