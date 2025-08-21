from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy
from django.shortcuts import redirect

app_name = 'accounts'

urlpatterns = [
    path('login/', lambda request: redirect('admin:login'), name='accounts_login'),
    
    
]

