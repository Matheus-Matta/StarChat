# plans/views.py
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator

from unfold.views import UnfoldModelAdminViewMixin
from accounts.models import Plan  # já existia

from starchat.services import ChatwootAccountService
from django.contrib.auth import get_user_model

chatwoot_service = ChatwootAccountService()

class AgentsList(LoginRequiredMixin, UnfoldModelAdminViewMixin, TemplateView):
    """
    Lista de agentes no layout do Unfold/Admin com busca e filtro por função (role).
    """
    template_name = "admin/agents_list.html"
    title = "Lista de Agentes"
    permission_required = ()

    def get(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            messages.error(request, "Você precisa ter uma conta/assinatura para ver esta página.")
            return redirect("admin:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        account = self.request.user.account

        # Origem dos agentes (lista de dicts) – ajuste conforme sua integração
        raw_agents = [a for a in list(account.all_agents or []) if a.get("id") != self.request.user.user_chatwoot_id]
        
        # Coleta de roles únicas a partir dos dados retornados
        roles = sorted({(a.get("role") or "").strip() for a in raw_agents if a is not None})
        if "" in roles:
            # Mantém vazio no fim da lista apenas internamente; no template existe a opção "Todas"
            roles.remove("")
        ctx["roles"] = roles

        # Filtros vindos da querystring
        q = (self.request.GET.get("q") or "").strip().lower()
        role_filter = (self.request.GET.get("role") or "").strip().lower()

        # Funções auxiliares
        def best_name(a: dict) -> str:
            return a.get("name") or a.get("available_name") or a.get("email") or f"#{a.get('id', '')}"

        def initials_from(text: str) -> str:
            if not text:
                return "AG"
            parts = [p for p in text.strip().split() if p]
            if not parts:
                return "AG"
            first = parts[0][0]
            last = parts[-1][0] if len(parts) > 1 else (parts[0][1] if len(parts[0]) > 1 else parts[0][0])
            return (first + last).upper()

        # Pré-processa e filtra
        processed = []
        for a in raw_agents:
            if not isinstance(a, dict):
                continue
            display_name = best_name(a)
            # Busca (nome, available_name, email)
            if q:
                hay = " ".join([
                    str(display_name),
                    str(a.get("available_name") or ""),
                    str(a.get("email") or ""),
                ]).lower()
                if q not in hay:
                    continue
            # Filtro por role
            if role_filter and (str(a.get("role") or "").lower() != role_filter):
                continue

            a = {**a}  # copia rasa para não mutar o original
            a["display_name"] = display_name
            a["initials"] = initials_from(display_name)
            processed.append(a)

        # Paginação
        page_number = self.request.GET.get("page") or 1
        paginator = Paginator(processed, 25)
        page_obj = paginator.get_page(page_number)

        # Contexto esperado no template (compatível com o HTML acima)
        ctx["object_list"] = list(page_obj.object_list)
        ctx["paginator"] = paginator
        ctx["page_obj"] = page_obj
        ctx["search_q"] = q
        ctx["filter_role"] = role_filter
        return ctx
    
    def delete(self, request, *args, **kwargs):
        account = getattr(request.user, "account", None)
        if not account or not account.plan:
            return JsonResponse({"ok": False, "error": "Sem permissão"}, status=403)

        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            payload = {}

        ids = payload.get("ids") or request.POST.getlist("ids")
        if not ids:
            return JsonResponse({"ok": False, "error": "IDs ausentes"}, status=400)

        # Converte para int quando possível
        try:
            ids = [int(x) for x in ids]
        except Exception:
            ids = [str(x) for x in ids]
        delete_ids = []
        
        for id in ids:
            is_deleted = chatwoot_service.remove_agent(account.chatwoot_account.chatwoot_id, id, request.user.user_chatwoot_id)
            if is_deleted:
                delete_ids.append(id)
            
            
        return JsonResponse({"ok": True, "deleted": delete_ids}, status=200)