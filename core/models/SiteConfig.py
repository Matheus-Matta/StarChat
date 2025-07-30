from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
import os
from ckeditor.fields import RichTextField

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
    
    tags = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_("Tags"),
        help_text=_("Palavras‑chave separadas por vírgula para SEO")
    )
    meta_title = models.CharField(
        max_length=60, blank=True, default='',
        verbose_name=_("Meta Title"),
        help_text=_("Título para title e Open Graph (até ~60 caracteres)")
    )
    meta_description = models.CharField(
        max_length=160, blank=True, default='',
        verbose_name=_("Meta Description"),
        help_text=_("Descrição para meta description e OG (até ~160 caracteres)")
    )
    about_body = RichTextField(
        blank=True, default='',
        verbose_name=_("Corpo Sobre Nós"),
        help_text=_("Texto livre (HTML simples) para a seção Sobre Nós")
    )
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