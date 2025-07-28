# core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_svg_image_form_field import SvgAndImageFormField
from django.urls import reverse
from config.unfold.admin import BaseAdmin
from unfold.admin import TabularInline
from django import forms
from .models import SiteConfig, Screenshot

class ScreenshotAdminForm(forms.ModelForm):
    class Meta:
        model = Screenshot
        fields = "__all__"
        field_classes = {
            'image': SvgAndImageFormField,
        }
        
class SiteConfigAdminForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = "__all__"
        field_classes = {
            'favicon': SvgAndImageFormField,
            'logo': SvgAndImageFormField,
            'logo_footer': SvgAndImageFormField,
            'hero_image': SvgAndImageFormField,
            'widget_image': SvgAndImageFormField,
            'auto_image': SvgAndImageFormField,
        }


class ScreenshotInline(TabularInline):
    model = Screenshot
    form = type(
        "ScreenshotInlineForm",
        (forms.ModelForm,),
        {
            "Meta": type("Meta", (), {
                "model": Screenshot,
                "fields": ("image",),
                "field_classes": {
                    'image': SvgAndImageFormField,
                }
            })
        }
    )
    extra = 0
    show_add_button_in_list = True           # mantém botão "+" para adicionar
    verbose_name = _("Screenshot")
    verbose_name_plural = _("Screenshots")

    # mantemos apenas preview_button como readonly
    readonly_fields = ("preview_button",)
    fields = ("image", "preview_button")     # sem delete_button

    def preview_button(self, obj):
        if obj and obj.image:
            return format_html(
                '<a href="{}" target="_blank" class="unfold-button unfold-button--primary">Preview</a>',
                obj.image.url
            )
        return _("Sem imagem")
    preview_button.short_description = _("Visualizar")


@admin.register(SiteConfig)
class SiteConfigAdmin(BaseAdmin):
    form = SiteConfigAdminForm
    inlines = [ScreenshotInline]
    list_display = ["name", "is_active", "created_at"]
    search_fields = ["name", "email", "phone"]
    fieldsets = (
        (_("Informações Gerais"), {"fields": ("name", "is_active")}),
        (_("Logos e Imagens"), {
            "fields": (
                "favicon","logo", "logo_footer",
                "hero_image", "widget_image", "auto_image",
            )
        }),
        (_("Contato e Endereço"), {"fields": ("phone", "email", "address")}),
        (_("Redes Sociais"), {"fields": ("instagram", "whatsapp", "twitter", "linkedin")}),
    )


@admin.register(Screenshot)
class ScreenshotAdmin(BaseAdmin):
    form = ScreenshotAdminForm
    list_display = ["__str__", "siteconfig", "preview_button"]
    readonly_fields = ("preview_button",)

    def preview_button(self, obj):
        if obj and obj.image:
            return format_html(
                '<a href="{}" target="_blank" class="unfold-button unfold-button--primary">'
                'Preview</a>', obj.image.url
            )
        return format_html('<span class="text-gray-400 italic">Sem imagem</span>')
    preview_button.short_description = _("Visualizar")
