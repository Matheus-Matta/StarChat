# core/context_processors.py
from .models import Plan

def active_plans(request):
    return {
        'plans': Plan.objects.filter(is_active=True, is_plan_staff=False).order_by('monthly_price')
    }
