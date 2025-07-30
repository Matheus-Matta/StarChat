from django.shortcuts import render
from django.views.generic import DetailView
from core.models import SiteService

# Create your views here.

def index(request):
    return render(request, 'index.html')

class SiteServiceDetailView(DetailView):
    model = SiteService
    template_name = 'partials/service_page.html'
    context_object_name = 'service'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['services'] = SiteService.objects.filter(is_active=True).order_by('order')
        return ctx
    
def about_us(request):
    return render(request, 'partials/sobre-nos.html', {'title': 'Sobre Nós'})