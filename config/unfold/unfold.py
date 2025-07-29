from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static

UNFOLD = {
    "SHOW_LANGUAGES":   True,
    "SITE_TITLE":       _("Starchat"),
    "SITE_HEADER":      _("Starchat"),
    "SITE_SUBHEADER":   _("Painel de Controle"),
    "SITE_SYMBOL": "star",
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
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Traduções"),
                        "icon":  "translate",
                        "link":  reverse_lazy("rosetta-file-list", kwargs={"po_filter": "project"}),
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
                        "title":       _("Planos"),
                        "icon":        "credit_card",
                        "link":        reverse_lazy("admin:accounts_plan_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Contas"),
                        "icon":        "account_balance",
                        "link":        reverse_lazy("admin:accounts_account_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title":       _("Configurações"),
                        "icon":        "settings",
                        "link":        reverse_lazy("admin:core_siteconfig_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
    "STYLES": [
        lambda request: static("css/style.css"),
    ],
    "COLORS": {
        "base": {
            "50":  "250, 250, 250",   # #FAFAFA
            "50":  "250, 250, 250",   # #FAFAFA
            "200": "200, 200, 200",   # #C8C8C8
            "300": "160, 160, 160",   # #A0A0A0
            "400": "120, 120, 120",   # #787878
            "500": " 90,  90,  90",   # #5A5A5A
            "600": " 60,  60,  60",   # #3C3C3C
            "700": " 40,  40,  40",   # #282828
            "800": " 21,  21,  21",   # #151515
            "900": " 15,  15,  15",   # #0F0F0F,
            "950": " 5,  5,  5",      # #050505,
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
}
