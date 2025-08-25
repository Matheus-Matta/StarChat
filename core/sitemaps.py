# core/sitemaps.py (ou no app principal)
from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.urls import reverse
from .models import SiteService

class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    def items(self):
        return ['home', 'services', 'contact', 'about', 'terms', 'policy']
    def location(self, item):
        return reverse(item)

class ServiceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    def items(self): return SiteService.objects.filter(is_active=True)
    def lastmod(self, obj): return obj.updated_at
    def location(self, obj): return reverse("service_detail", args=[obj.slug])
