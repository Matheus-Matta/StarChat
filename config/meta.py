from core.models import SiteConfig
keys = None
if SiteConfig.objects.exists():
    conf = SiteConfig.objects.filter(is_active=True).first()
    keys = conf.tags.split(",")[0]
    print(keys)
    
META_DEFAULT_KEYWORDS = keys