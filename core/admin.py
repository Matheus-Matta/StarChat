# core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_svg_image_form_field import SvgAndImageFormField
from django.urls import reverse
from config.unfold.admin import BaseAdmin
from unfold.admin import TabularInline
from django import forms
from .models import SiteConfig, Screenshot, SiteService
from taggit.forms import TagWidget
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models
import json

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
    fieldsets = [
        (_("Informações Gerais"), {"fields": ["name", "is_active"]}),
        (_("SEO"), {
            "fields": ["tags", "meta_title", "meta_description"],
            "description": _("Palavras‑chave, título e descrição para SEO"),
        }),
        (_("Logos e Imagens"), {
            "fields": [
                "favicon", "logo", "logo_footer",
                "hero_image", "widget_image", "auto_image",
            ],
        }),
        (_("Contato e Endereço"), {
            "fields": ["phone", "email", "address"],
        }),
        (_("Redes Sociais"), {
            "fields": ["instagram", "whatsapp", "twitter", "linkedin"],
        }),
        (_("Sobre Nós"), {
            "fields": [
                "about_body",
            ],
            "description": _("Conteúdo e imagens para a seção Sobre Nós do site"),
        }),
    ]



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

@admin.register(SiteService)
class SiteServiceAdmin(BaseAdmin):
    list_display        = ('title','subtitle','is_active','order')
    list_filter         = ('is_active',)
    search_fields       = ('title','subtitle','tags__name')
    ordering            = ('order',)
    prepopulated_fields = {'slug': ('title',)}
    
    

def dashboard_context(request, context):
    # 1) Dados do usuário
    account = getattr(request.user, "account", None)
    plan = account.plan if account else None

    # 2) Montar labels e séries para o gráfico de cobranças do ano
    #    aqui você deve puxar do seu modelo de cobranças reais;
    #    pra demo vamos criar dados dummy:
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    pagas =   [120,150, 90,200,170,130,   0,  0,   0,  0,   0,   0]
    a_vencer=[ 30, 50, 60,  0,  0,  0,  20, 40,  80,100,  90, 110]

    context.update({
        "account": account,
        "plan": plan,
        "chart_labels": json.dumps(meses),
        "chart_paid":   json.dumps(pagas),
        "chart_due":    json.dumps(a_vencer),
    })
    return context
