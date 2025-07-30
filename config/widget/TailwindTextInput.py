from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# 1) Defina seu widget customizado
from django.forms.widgets import TextInput as DjangoTextInput

class TailwindTextInput(DjangoTextInput):
    """
    Input de texto embrulhado com Tailwind/Unfold,
    e suporte a `help_text` via attrs.
    """
    DEFAULT_CLASSES = (
        'border border-base-200 bg-white font-medium '
        'min-w-20 placeholder-base-400 rounded-default '
        'shadow-xs text-font-default-light text-sm '
        'focus:outline-2 focus:-outline-offset-2 '
        'focus:outline-primary-600 '
        'dark:bg-base-900 dark:border-base-700 '
        'dark:text-font-default-dark '
        'px-3 py-2 w-full max-w-2xl'
    )

    def __init__(self, attrs=None):
        attrs = attrs or {}
        # mescla classes padrão
        orig = attrs.get('class', '')
        attrs['class'] = f"{self.DEFAULT_CLASSES} {orig}".strip()
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # gera o <input> normal
        html_input = super().render(name, value, attrs, renderer)

        # pega o help_text se passou em attrs
        help_txt = (attrs or {}).get('help_text') or self.attrs.get('help_text', '')
        help_html = ''
        if help_txt:
            help_html = format_html(
                '<div class="leading-relaxed mt-2 text-xs">{}</div>',
                help_txt
            )

        # envolve tudo no wrapper que você queria
        return format_html(
            '<div class="grow relative">'
            '  <div class="max-w-2xl relative w-full">{}</div>'
            '  {}'
            '</div>',
            mark_safe(html_input),
            mark_safe(help_html),
        )