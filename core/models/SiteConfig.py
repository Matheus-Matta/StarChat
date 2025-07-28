from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
import os

class SiteConfig(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nome"), unique=True)
    
    is_active = models.BooleanField(default=False, verbose_name=_("Ativo"))

    images_path = 'site/images/'
    favicon = models.ImageField(upload_to=images_path, blank=True, null=True)
    logo = models.ImageField(upload_to=images_path, blank=True, null=True)
    logo_footer = models.ImageField(upload_to=images_path, blank=True, null=True)
    hero_image = models.ImageField(upload_to=images_path, blank=True, null=True)
    widget_image = models.ImageField(upload_to=images_path, blank=True, null=True)
    auto_image = models.ImageField(upload_to=images_path, blank=True, null=True)

    screenshot = models.OneToOneField(
        'Screenshot',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='siteconfig_via',
        verbose_name=_("Screenshot de destaque")
    )

    instagram = models.URLField(blank=True, null=True)
    whatsapp = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _("Configuração do Site")
        verbose_name_plural = _("Configurações do Site")

    def save(self, *args, **kwargs):
        if self.is_active:
            SiteConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Screenshot(models.Model):
    siteconfig = models.ForeignKey(
        SiteConfig,
        related_name='screenshots',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    image = models.FileField(upload_to='site/screenshots/')