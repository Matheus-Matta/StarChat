# services/models.py
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager

class SiteService(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Título"),
        help_text=_("Título do serviço"),
    )
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_("Subtítulo"),
        help_text=_("Frase menor ou slogan do serviço"),
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL amigável (gerado automaticamente a partir do título)"),
    )
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Classe de Ícone"),
        help_text=_("Por exemplo: 'fas fa-robot' ou 'flaticon-puzzle'"),
    )
    excerpt = models.TextField(
        blank=True,
        verbose_name=_("Resumo"),
        help_text=_("Pequena descrição usada na listagem"),
    )
    body = RichTextField(
        verbose_name=_("Conteúdo"),
        help_text=_("Texto completo, com formatação (CKEditor)"),
    )
    
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Separe as tags por vírgula"),
        default='',
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Publicado"),
        help_text=_("Desmarque para ocultar da página pública"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Ordem"),
        help_text=_("Define a ordem de exibição; menor vem primeiro"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em"),
    )

    class Meta:
        verbose_name = _("Serviço")
        verbose_name_plural = _("Serviços")
        ordering = ('order', 'title')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Gera slug automático se não fornecido
        if not self.slug:
            base = slugify(self.title)[:180]
            slug = base
            idx = self.id
            while SiteService.objects.filter(slug=slug).exists():
                slug = f"{base}-{idx}"
                idx += 1
            self.slug = slug
        super().save(*args, **kwargs)
