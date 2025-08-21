"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from accounts.views import StripeCustomerPortalView

urlpatterns = [
    path('stripe/', include("djstripe.urls", namespace="djstripe")),
    
    path('app/', admin.site.urls),

    # Primeiro trate as URLs específicas do Stripe

    # Depois suas rotas de app principais
    path('auth/', include('authentic.urls')),
    path('accounts/', include('accounts.urls')),
    
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # Por fim, os catch-all
    path('', include('page.urls')),
    path('', include('core.urls')),
    
    
    path("stripe/portal/", StripeCustomerPortalView.as_view(), name="stripe_customer_portal"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()