# services/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps

@receiver(post_migrate)
def create_default_site_services(sender, **kwargs):
    
    if sender.name != 'core':
        return
    
    SiteService = apps.get_model('core', 'SiteService')

    if SiteService.objects.exists():
        return
    
    default_services = [
        {
            'title': 'Multicanal',
            'subtitle': 'Conecte todos os canais em um só lugar',
            'icon_class': 'fas fa-project-diagram',
            'excerpt': 'instagram, WhatsApp, Telegram, Email e Live Chat.',
            'body': '<p>Atenda clientes via Instagram, WhatsApp, Telegram, Email, Live Chat e muito mais.</p>',
            'tags': 'multicanal,comunicação,chat',
            'is_active': True,
            'order': 1,
        },
        {
            'title': 'Funções e Auditoria',
            'subtitle': 'Controle total e rastreamento de ações',
            'icon_class': 'fas fa-clipboard-check',
            'excerpt': 'Monitore cada ação com controle de funções e auditoria.',
            'body': '<p>Defina permissões por usuário e registre todo histórico de operações.</p>',
            'tags': 'segurança,auditoria,permissões',
            'is_active': True,
            'order': 2,
        },
        {
            'title': 'Times e Agentes',
            'subtitle': 'Organize equipes e distribua atendimentos',
            'icon_class': 'fas fa-users',
            'excerpt': 'Organização de times e agentes para distribuir tarefas.',
            'body': '<p>Crie equipes, atribua agentes e gerencie cargas de trabalho.</p>',
            'tags': 'equipe,agentes,gestão',
            'is_active': True,
            'order': 3,
        },
        {
            'title': 'Relatórios',
            'subtitle': 'Métricas e dashboards em tempo real',
            'icon_class': 'fas fa-chart-bar',
            'excerpt': 'Gráficos e métricas de desempenho detalhadas.',
            'body': '<p>Visualize relatórios de atendimento, tempo de resposta e satisfação.</p>',
            'tags': 'relatórios,analytics,dashboard',
            'is_active': True,
            'order': 4,
        },
        {
            'title': 'Automações',
            'subtitle': 'Macros e fluxos inteligentes',
            'icon_class': 'fas fa-cogs',
            'excerpt': 'Automações e macros inteligentes para agilizar processos.',
            'body': '<p>Configure gatilhos, respostas automáticas e workflows avançados.</p>',
            'tags': 'automações,macros,workflow',
            'is_active': True,
            'order': 5,
        },
        {
            'title': 'Robôs com IA',
            'subtitle': 'Chatbots inteligentes para atendimento',
            'icon_class': 'fas fa-robot',
            'excerpt': 'Robôs de atendimento com IA para respostas automáticas.',
            'body': '<p>Implemente chatbots que compreendem e respondem em linguagem natural.</p>',
            'tags': 'chatbot,ia,inteligência artificial',
            'is_active': True,
            'order': 6,
        },
        {
            'title': 'Integrações',
            'subtitle': 'Conecte com as principais plataformas',
            'icon_class': 'fas fa-plug',
            'excerpt': 'ChatGPT, Dialogflow, Dyte e LeadSquared em um só lugar.',
            'body': '<p>Integre com ChatGPT, Dialogflow, Dyte, LeadSquared e outras APIs.</p>',
            'tags': 'integrações,api,webhooks',
            'is_active': True,
            'order': 7,
        },
        {
            'title': 'HelperCenter',
            'subtitle': 'Base de conhecimento e suporte VIP',
            'icon_class': 'fas fa-info-circle',
            'excerpt': 'HelperCenter para suporte e conhecimento em atendimentos.',
            'body': '<p>Ofereça artigos, FAQs e guias internos diretamente no painel.</p>',
            'tags': 'suporte,helpdesk,conhecimento',
            'is_active': True,
            'order': 8,
        },
        {
            'title': 'SLA e CSAT',
            'subtitle': 'Garantia de qualidade e satisfação',
            'icon_class': 'fas fa-stopwatch',
            'excerpt': 'SLA e CSAT definidos para garantir qualidade e satisfação.',
            'body': '<p>Monitore seus acordos de serviço e índices de satisfação de clientes.</p>',
            'tags': 'sla,csat,qualidade',
            'is_active': True,
            'order': 9,
        },
        {
            'title': 'Campanhas',
            'subtitle': 'Envio de mensagens em massa',
            'icon_class': 'fas fa-bullhorn',
            'excerpt': 'SMS, Live Chat e WhatsApp para alcançar todos os canais.',
            'body': '<p>Crie e gerencie campanhas de SMS, chat ao vivo e WhatsApp.</p>',
            'tags': 'campanhas,marketing,comunicação',
            'is_active': True,
            'order': 10,
        },
    ]

    for svc in default_services:
        # Atualiza ou cria com base no título único
        obj, created = SiteService.objects.update_or_create(
            title=svc['title'],
            defaults=svc
        )
        if created:
            print(f'✔ Serviço "{svc["title"]}" criado')
