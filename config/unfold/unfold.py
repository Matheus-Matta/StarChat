from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE":       _("Starchat"),
    "SITE_HEADER":      _("Starchat"),
    "SITE_SUBHEADER":   _("Painel de Controle"),
    "SHOW_LANGUAGES":   True,
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
                "icon":        "menu",
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
                ],
            },
        ],
    },
}
