# core/views.py
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from accounts.models import Account

@user_passes_test(lambda u: u.is_staff)
def api_agents(request):
    """
    Retorna JSON com contas paginadas.
    Query params:
      - page (padrão 1)
      - page_size (padrão 10)
    """
    page      = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    qs = Account.objects.order_by("email")
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    rows = []
    for acc in page_obj:
        rows.append({
            "id":          acc.id,
            "email":       acc.email,
            "plan":        acc.plan.name if acc.plan else None,
            "created_at":  acc.created_at.strftime("%Y-%m-%d"),
        })

    return JsonResponse({
        "meta": {
            "page":         page_obj.number,
            "page_size":    page_size,
            "total_pages":  paginator.num_pages,
            "total_count":  paginator.count,
        },
        "rows": rows,
    })
