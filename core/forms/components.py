from crispy_forms.layout import HTML
from django.urls import reverse, NoReverseMatch

# Mapeamento de tipos para classes Tailwind/Unfold
BUTTON_TYPE_CLASSES = {
    "primary": "bg-primary-600 text-white" ,
    "secondary": "font-medium flex group items-center gap-2 px-3 py-2 rounded-default justify-center whitespace-nowrap cursor-pointer border border-base-200 bg-white text-font-important-light dark:border-base-700 dark:bg-transparent dark:text-font-important-dark",
    "warning": "bg-warning-600 text-white",
    "danger": "bg-red-500 text-white",
    "success": "bg-success-600 text-white",
    "info": "bg-info-600 text-white",
    'link': "bg-transparent text-primary-600 text-center underline",
    'transparent': "bg-transparent dark:text-white text-primary-600",
    
}

def build_html_tag(tag, text, css_class, attrs):
    extra_attrs = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<{tag} class="cursor-pointer font-medium px-3 py-2 ml-2 rounded-default {css_class}" {extra_attrs}>{text}</{tag}>'

class Button(HTML):
    """
    Layout object para um <button type="submit"> estilizado.
    - text: texto interno do botão
    - type: uma das chaves de BUTTON_TYPE_CLASSES
    - name: atributo name do botão (opcional)
    """
    def __init__(self, text, type="primary", name=None, **attrs):
        css_class = BUTTON_TYPE_CLASSES.get(type, BUTTON_TYPE_CLASSES["primary"])
        if name:
            attrs['name'] = name
        html = build_html_tag("button", text, css_class, attrs)
        super().__init__(html)

class Link(HTML):
    """
    Layout object para um <a> estilizado como botão.
    - text: texto do link
    - href: URL direta
    - url_name: nome de rota Django (se fornecido, tem prioridade sobre href)
    - type: cor/tipo (mesma lógica de BUTTON_TYPE_CLASSES)
    """
    def __init__(self, text, href=None, type="primary", **attrs):
        href = href or "#"
        css_class = BUTTON_TYPE_CLASSES.get(type, BUTTON_TYPE_CLASSES["secondary"])
        attrs['href'] = href
        html = build_html_tag("a", text, css_class, attrs)
        super().__init__(html)

