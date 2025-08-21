# core/context_processors.py
from .models import SiteConfig, Screenshot, SiteService
from django.conf import settings

def site_config(request):
    """
    Retorna a primeira SiteConfig ativa (is_active=True),
    para ficar disponível em todos os templates.
    """
    config = SiteConfig.objects.filter(is_active=True).first()
    print(config)
    return {
        'site_config': config,
        'starchat_url': settings.CHATWOOT_URL,
        'services': SiteService.objects.filter(is_active=True).order_by('order'),
    }
