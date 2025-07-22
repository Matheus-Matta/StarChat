#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
bulk_translate_po.py

Entra em `locale/`, detecta cada subpasta de idioma e, para cada
<lang>/LC_MESSAGES/django.po, traduz apenas os msgstr vazios.
Preserva e valida placeholders Python no estilo %(nome)s,
garantindo que msgid e msgstr tenham exatamente os mesmos nomes.
"""

import sys, types, re
from pathlib import Path
import polib
from deep_translator import GoogleTranslator

# ─── stub do módulo cgi para Python ≥3.12 ─────────────────────────────────────
import sys as _sys, types as _types
_stub = _types.ModuleType('cgi')
_stub.parse_header = lambda v: (v.split(';',1)[0], {})
_stub.FieldStorage = type('FieldStorage', (), {})
_sys.modules['cgi'] = _stub
# ───────────────────────────────────────────────────────────────────────────────

# regex para encontrar placeholders no estilo Python
PLACEHOLDER_RE = re.compile(r'%\([^)]+\)[A-Za-z]')

def detect_languages(locale_root: Path):
    return [d.name for d in locale_root.iterdir() if d.is_dir()]

def normalize_target(lang_code: str) -> str:
    return lang_code.split('_')[0].lower()

def translate_po(po_path: Path, target_lang: str):
    try:
        po = polib.pofile(str(po_path))
    except Exception as e:
        print(f'✖ Não foi possível ler {po_path}: {e}')
        return

    translator = GoogleTranslator(source='auto', target=target_lang)
    updated = False

    for entry in po:
        # pula quem já tiver tradução ou msgid vazio
        if not entry.msgid or entry.msgstr.strip():
            continue

        original = entry.msgid
        # extrai placeholders originais
        ph_orig = PLACEHOLDER_RE.findall(original)

        # mascara placeholders por tokens __PH0__, __PH1__…
        sanitized = original
        for i, ph in enumerate(ph_orig):
            sanitized = sanitized.replace(ph, f"__PH{i}__")

        # tenta traduzir
        try:
            translated = translator.translate(sanitized) or ''
        except Exception as e:
            print(f'[{target_lang}] ✖ Erro traduzindo “{original}”: {e}')
            # fallback para copiar o texto original
            entry.msgstr = original
            continue

        # restaura placeholders (case‑insensitive)
        for i, ph in enumerate(ph_orig):
            translated = re.sub(
                re.escape(f"__PH{i}__"),
                ph,
                translated,
                flags=re.IGNORECASE
            )

        # extrai placeholders do traduzido
        ph_trans = PLACEHOLDER_RE.findall(translated)

        # se a lista não bater, **não** usamos essa tradução automática
        if sorted(ph_orig) != sorted(ph_trans):
            print(f'[{target_lang}] ⚠️ Placeholder mismatch em “{original}”')
            print(f'         orig: {ph_orig}, trans: {ph_trans}')
            # fallback: copia msgid como msgstr
            entry.msgstr = original
        else:
            entry.msgstr = translated
            print(f'[{target_lang}] ✔ “{original}” → “{translated}”')
            updated = True

    # garante nenhum msgstr seja None
    for e in po:
        if e.msgstr is None:
            e.msgstr = ''

    if updated:
        try:
            po.save(str(po_path))
            print(f'✔ Salvo: {po_path}\n')
        except Exception as e:
            print(f'✖ Falha ao salvar {po_path}: {e}')
    else:
        print(f'— Nenhuma mudança em {po_path}\n')

def main():
    base_dir    = Path(__file__).resolve().parent
    locale_root = base_dir / 'locale'
    if not locale_root.is_dir():
        print(f'✖ Não achei “locale/” em {base_dir}')
        sys.exit(1)

    for lang in detect_languages(locale_root):
        po_file = locale_root / lang / 'LC_MESSAGES' / 'django.po'
        if po_file.exists():
            tgt = normalize_target(lang)
            print(f'→ Processando {po_file} (target="{tgt}")')
            translate_po(po_file, tgt)
        else:
            print(f'— Ignorando {lang}: sem {po_file}')

if __name__ == '__main__':
    main()
