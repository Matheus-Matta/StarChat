from django.utils.translation import gettext as _

CHATWOOT_FEATURES = {
    "features": {
        "agent_bots": True,
        "agent_management": True,
        "auto_resolve_conversations": True,
        "automations": True,
        "crm": True,
        "crm_integration": True,
        "campaigns": True,
        "canned_responses": True,
        "chatwoot_v4": True,
        "custom_attributes": True,
        "custom_reply_domain": True,
        "custom_reply_email": True,

        # passa de "email_channel" → "channel_email"
        "channel_email": True,

        "email_continuity_on_api_channel": True,

        # passa de "facebook_channel" → "channel_facebook"
        "channel_facebook": True,

        "help_center": True,
        "ip_lookup": True,
        "inbound_emails": True,
        "inbox_management": True,

        # passa de "instagram_channel" → "channel_instagram"
        "channel_instagram": True,

        "integrations": True,
        "labels": True,
        "linear_integration": True,
        "macros": True,
        "notion_integration": True,
        "reports": True,
        "team_management": True,
        "voice_recorder": True,

        # passa de "website_channel" → "channel_website"
        "channel_website": True,

        "whatsapp_campaign": True,
        "whatsapp_embedded_signup": True,
        "audit_logs": True,

        # passa de "captain" → "captain_integration"
        "captain_integration": False,

        "custom_roles": True,
        "disable_branding": True,
        "sla": True
    },
    'labels': {
        "agent_bots":                    _("Bots de Agente"),
        "agent_management":              _("Gerenciamento de Agentes"),
        "auto_resolve_conversations":    _("Resolução Automática de Conversas"),
        "automations":                   _("Automatizações"),
        "crm":                           _("CRM"),
        "crm_integration":               _("Integração com CRM"),
        "campaigns":                     _("Campanhas"),
        "canned_responses":              _("Respostas Prontas"),
        "custom_attributes":             _("Atributos Personalizados"),
        "custom_reply_domain":           _("Domínio de Resposta Customizado"),
        "custom_reply_email":            _("E-mail de Resposta Customizado"),
        "channel_email":                 _("E-mail como Canal"),
        "email_continuity_on_api_channel": _("Continuidade de E-mail em Canal API"),
        "channel_facebook":              _("Canal Facebook"),
        "help_center":                   _("Central de Ajuda"),
        "ip_lookup":                     _("Busca de IP"),
        "inbound_emails":                _("E-mails Recebidos"),
        "inbox_management":              _("Gerenciamento de Inboxes"),
        "channel_instagram":             _("Canal Instagram"),
        "integrations":                  _("Integrações"),
        "labels":                        _("Etiquetas"),
        "linear_integration":            _("Integração Linear"),
        "macros":                        _("Macros"),
        "notion_integration":            _("Integração Notion"),
        "reports":                       _("Relatórios"),
        "team_management":               _("Gerenciamento de Equipes"),
        "voice_recorder":                _("Gravador de Voz"),
        "channel_website":               _("Canal Website"),
        "whatsapp_campaign":             _("Campanhas WhatsApp"),
        "whatsapp_embedded_signup":      _("Cadastro Embedded WhatsApp"),
        "audit_logs":                    _("Logs de Auditoria"),
        "captain_integration":           _("Integração Captain"),
        "custom_roles":                  _("Funções Customizadas"),
        "sla":                           _("Acordo de Nível de Serviço"),
    }
}
