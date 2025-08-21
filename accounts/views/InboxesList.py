# plans/views.py
import json, logging
from typing import Any, Dict, List, Optional
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin


log = logging.getLogger(__name__)

# Ajuste para o seu projeto
from starchat.services import ChatwootAccountService  # <— troque se necessário
cw = ChatwootAccountService()

class InboxesList(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    template_name = "admin/inboxes_list.html"
    title = "Lista de Inboxes"
    permission_required = ()

    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        account = user.account

        raw_inboxes: List[Dict[str, Any]] = []
        try:
            raw_inboxes = account.all_inboxes
        except Exception:
             raw_inboxes = []

        # Filtros
        q = (self.request.GET.get("q") or "").strip().lower()
        channel_filter = (self.request.GET.get("channel") or "").strip().lower()
        provider_filter = (self.request.GET.get("provider") or "").strip().lower()

        # Opções do select
        channels = sorted({(i.get("channel_type") or "").strip() for i in raw_inboxes if isinstance(i, dict)})
        if "" in channels:
            channels.remove("")
        providers = sorted({(i.get("provider") or "").strip() for i in raw_inboxes if isinstance(i, dict)})
        if "" in providers:
            providers.remove("")

        # Helpers
        def best_name(i: Dict[str, Any]) -> str:
            return i.get("name") or i.get("business_name") or i.get("website_url") or f"#{i.get('id','')}"

        def initials_from(text: str) -> str:
            if not text:
                return "IN"
            parts = [p for p in text.strip().split() if p]
            if not parts:
                return "IN"
            f = parts[0][0]
            l = parts[-1][0] if len(parts) > 1 else (parts[0][1] if len(parts[0]) > 1 else parts[0][0])
            return (f + l).upper()

        # Pré-processa e filtra
        processed: List[Dict[str, Any]] = []
        for i in raw_inboxes:
            if not isinstance(i, Dict):
                continue

            display_name = best_name(i)
            hay = " ".join([
                str(display_name), str(i.get("business_name") or ""), str(i.get("website_url") or "")
            ]).lower()

            if q and q not in hay:
                continue
            if channel_filter and str(i.get("channel_type") or "").lower() != channel_filter:
                continue
            if provider_filter and str(i.get("provider") or "").lower() != provider_filter:
                continue

            d = {**i}
            d["display_name"] = display_name
            d["initials"] = initials_from(display_name)
            processed.append(d)

        # Paginação
        page_number = self.request.GET.get("page") or 1
        paginator = Paginator(processed, 25)
        page_obj = paginator.get_page(page_number)

        # Contexto
        ctx["object_list"] = list(page_obj.object_list)
        ctx["paginator"] = paginator
        ctx["page_obj"] = page_obj
        ctx["search_q"] = q
        ctx["channels"] = channels
        ctx["providers"] = providers
        ctx["filter_channel"] = channel_filter
        ctx["filter_provider"] = provider_filter

        # URL de bulk delete (namespace admin)
        ctx["delete_url"] = reverse("admin:account_inboxes")
        return ctx
    
    def delete(self, request, *args, **kwargs):
        user = request.user
        account = getattr(user, "account", None)
        if not account or not account.plan:
            return JsonResponse({"ok": False, "error": "Sem permissão"}, status=403)

        try:
            payload = json.loads(request.body or "{}")
            ids = payload.get("ids") or []
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

        if not ids:
            return JsonResponse({"ok": False, "error": "IDs ausentes"}, status=400)
        
        delete_ids = []
        for id in ids:
            try:
                is_deleted = cw.delete_inbox(account.chatwoot_account.chatwoot_id, id, user.user_chatwoot_id)
                if is_deleted:
                    delete_ids.append(id)
            except Exception as e:
                log.error('Error deleting inbox %s: %s', id, e)
                pass
                
        return JsonResponse({"ok": True, "deleted": delete_ids}, status=200)

