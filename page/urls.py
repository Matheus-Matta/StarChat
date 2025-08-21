from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy
from .views import SiteServiceDetailView
from django.shortcuts import render

app_name = 'page'

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    path('services/<slug:slug>', SiteServiceDetailView.as_view(), name='service_detail'),
    path('sobre-nos/', views.about_us, name='sobre_nos'),
    
    path('termos-de-uso/', lambda request: render(request, 'partials/termos-de-uso.html'), name='terms'),
    path('politica-de-privacidade/', lambda request: render(request, 'partials/politica-de-privacidade.html'), name='policy'),
]
