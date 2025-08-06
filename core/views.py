from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin import AdminSite
from accounts.models import Account

def home_view(request):
   
    return render(request, 'admin/home_admin.html')
    