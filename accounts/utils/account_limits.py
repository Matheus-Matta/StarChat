# accounts/limits.py
from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


# ---------------- Utils ----------------

def _to_int(value: Any, default: int = 0) -> int:
    """Converte valor para int com fallback seguro."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_usage_info(account: Any, kind: str) -> Tuple[Optional[int], Mapping[str, Any]]:
    """
    Lê informações de uso a partir de account:
      - kind='agents'  -> usa account.agents_info
      - kind='inboxes' -> usa account.inboxes_info

    Retorna (used, raw_dict). Se não encontrar, used será None.
    """
    field_name = f"{kind}_info"
    raw = getattr(account, field_name, None) or {}
    if not isinstance(raw, dict):
        raw = {}

    used = raw.get("used")
    used = _to_int(used, default=None) if used is not None else None
    return used, raw


def _enforce_not_below_current_usage(
    request: HttpRequest,
    *,
    kind_label: str,
    used: Optional[int],
    requested_total: int,
    redirect_to: str,
) -> Optional[HttpResponse]:
    """
    Se o uso atual (used) for maior que o novo limite solicitado (requested_total),
    retorna redirect com mensagem de erro. Caso contrário, retorna None.
    """
    if used is None:
        messages.error(request, f"Não foi possível validar o uso atual de {kind_label}.")
        return redirect(redirect_to)

    requested_total = _to_int(requested_total, 0)
    if used > requested_total:
        messages.error(
            request,
            f"Você já utiliza {used} {kind_label}. "
            f"Para alterar o limite para {requested_total}, reduza seu uso antes."
        )
        return redirect(redirect_to)

    return None


# ---------------- Regras públicas ----------------

def enforce_agent_limit(
    request: HttpRequest,
    account: Any,
    requested_total_agents: int,
    redirect_to: str,
) -> Optional[HttpResponse]:
    """
    Garante que o novo limite de AGENTES (requested_total_agents) não seja menor
    do que o uso atual (account.agents_info['used']).

    Se violar, retorna redirect(redirect_to) com messages.error.
    Se estiver ok, retorna None.

    Obs.: 'requested_total_agents' deve ser o TOTAL pretendido após a mudança
    (incluídos + extras), não apenas a quantidade de extras.
    """
    used, _raw = _get_usage_info(account, "agents")
    return _enforce_not_below_current_usage(
        request,
        kind_label="agentes",
        used=used,
        requested_total=requested_total_agents,
        redirect_to=redirect_to,
    )


def enforce_inbox_limit(
    request: HttpRequest,
    account: Any,
    requested_total_inboxes: int,
    redirect_to: str,
) -> Optional[HttpResponse]:
    """
    Garante que o novo limite de INBOXES (requested_total_inboxes) não seja menor
    do que o uso atual (account.inboxes_info['used']).

    Se violar, retorna redirect(redirect_to) com messages.error.
    Se estiver ok, retorna None.

    Obs.: 'requested_total_inboxes' deve ser o TOTAL pretendido após a mudança
    (incluídas + extras), não apenas a quantidade de extras.
    """
    used, _raw = _get_usage_info(account, "inboxes")
    return _enforce_not_below_current_usage(
        request,
        kind_label="inboxes",
        used=used,
        requested_total=requested_total_inboxes,
        redirect_to=redirect_to,
    )
