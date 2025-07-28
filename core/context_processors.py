# core/context_processors.py
from .models import SiteConfig

def site_config(request):
    """
    Retorna a primeira SiteConfig ativa (is_active=True),
    para ficar disponível em todos os templates.
    """
    config = SiteConfig.objects.filter(is_active=True).first()
    return {
        'site_config': config
    }
