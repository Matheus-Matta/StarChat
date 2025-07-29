import threading
from django.contrib import admin
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesRadioFilter,
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth import get_user_model
User = get_user_model()

from config.unfold.admin import BaseAdmin
# Base admin class combining Unfold theme, history and crispy forms

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('permissions',)

@admin.register(Permission)
class PermissionAdmin(BaseAdmin):
    list_display = ('name', 'codename', 'content_type')
    list_filter = (('content_type', ChoicesRadioFilter),)
    search_fields = ('name', 'codename')
    ordering = ('content_type__app_label', 'content_type__model', 'codename')

@admin.register(ContentType)
class ContentTypeAdmin(BaseAdmin):
    list_display = ('app_label', 'model')
    search_fields = ('app_label', 'model')
    ordering = ('app_label', 'model')

