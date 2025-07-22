from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy

app_name = 'page'

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
]
