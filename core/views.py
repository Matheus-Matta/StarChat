from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin import AdminSite
from accounts.models import Account
from django.http import HttpResponse
from django.conf import settings

def home_view(request):
    return render(request, 'admin/home_admin.html')
    
def robots_txt(request):
    domain = settings.DOMAIN
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {domain}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
