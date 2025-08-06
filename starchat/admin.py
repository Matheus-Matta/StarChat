from django.contrib import admin

from config.unfold.admin import BaseAdmin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _
from .models import ChatwootAccount


class ChatwootAccountAdmin(BaseAdmin):
    list_display = ("account", "chatwoot_id", "created_at", "updated_at")
    search_fields = ("account__name", "chatwoot_id")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.helper = FormHelper()
        form.helper.add_input(Submit("submit", _("Save")))
        return form


admin.site.register(ChatwootAccount, ChatwootAccountAdmin)

