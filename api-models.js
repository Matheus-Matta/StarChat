(() => {
  'use strict';

  const A = '/api/v1/accounts/1';
  const V2 = '/api/v2/accounts/1';
  const resource = (id, title, path, description, method = 'GET', body) => ({ id, title, path, description, method, body });
  const groups = [
    { title:'Conversas', resources:[
      resource('conversations','Conversas',`${A}/conversations`,'Liste e filtre as conversas da conta.'),
      resource('messages','Mensagens',`${A}/conversations/42/messages`,'Envie uma mensagem pública ou uma nota interna.','POST',{ content:'Olá! Como posso ajudar?', message_type:'outgoing', private:false }),
      resource('assignments','Atribuições',`${A}/conversations/42/assignments`,'Atribua uma conversa a um agente ou time.','POST',{ assignee_id:7, team_id:3 }),
      resource('conversation-labels','Etiquetas da conversa',`${A}/conversations/42/labels`,'Consulte ou substitua as etiquetas de uma conversa.','POST',{ labels:['cliente-vip','prioridade-alta'] }),
      resource('participants','Participantes',`${A}/conversations/42/participants`,'Consulte os participantes associados à conversa.'),
      resource('direct-uploads','Uploads da conversa',`${A}/conversations/42/direct_uploads`,'Crie um upload para anexar arquivos ao atendimento.','POST',{ file_name:'comprovante.pdf', content_type:'application/pdf' }),
      resource('conversation-custom-attributes','Atributos da conversa',`${A}/conversations/42/custom_attributes`,'Atualize atributos personalizados da conversa.','POST',{ custom_attributes:{ numero_pedido:'PED-1042', prioridade:'alta' } }),
      resource('transcript','Transcrição',`${A}/conversations/42/transcript`,'Obtenha ou solicite a transcrição de uma conversa.'),
      resource('conversation-bulk-actions','Ações em lote',`${A}/conversations/bulk_actions`,'Execute a mesma alteração em várias conversas.','POST',{ conversation_ids:[42,43], action:'resolve' }),
      resource('calls','Chamadas',`${A}/calls`,'Consulte registros de chamadas associados à conta.'),
      resource('whatsapp-calls','Chamadas do WhatsApp',`${A}/whatsapp_calls`,'Consulte chamadas realizadas pelo canal WhatsApp.')
    ]},
    { title:'Contatos e empresas', resources:[
      resource('contacts','Contatos',`${A}/contacts`,'Liste contatos ou crie um novo perfil.','POST',{ name:'Maria Silva', email:'maria@exemplo.com.br', phone_number:'+5521999999999', identifier:'cliente-123' }),
      resource('contact-conversations','Conversas do contato',`${A}/contacts/25/conversations`,'Liste o histórico de conversas de um contato.'),
      resource('contact-inboxes','Vínculos de canal',`${A}/contacts/25/contact_inboxes`,'Consulte os vínculos do contato com caixas de entrada.'),
      resource('contact-labels','Etiquetas do contato',`${A}/contacts/25/labels`,'Aplique etiquetas ao cadastro do contato.','POST',{ labels:['lead','cliente-vip'] }),
      resource('contact-notes','Notas do contato',`${A}/contacts/25/notes`,'Registre uma anotação interna no contato.','POST',{ content:'Cliente prefere contato no período da manhã.' }),
      resource('companies','Empresas',`${A}/companies`,'Liste empresas ou cadastre uma organização.','POST',{ name:'Empresa Exemplo', domain:'exemplo.com.br', industry:'Tecnologia' }),
      resource('company-contacts','Contatos da empresa',`${A}/companies/8/contacts`,'Liste os contatos vinculados a uma empresa.'),
      resource('company-conversations','Conversas da empresa',`${A}/companies/8/conversations`,'Consulte conversas de todos os contatos da empresa.'),
      resource('company-notes','Notas da empresa',`${A}/companies/8/notes`,'Adicione contexto interno ao cadastro da empresa.','POST',{ content:'Contrato renovado até dezembro.' }),
      resource('data-imports','Importações de dados',`${A}/data_imports`,'Acompanhe importações de contatos e outros registros.')
    ]},
    { title:'Caixas e canais', resources:[
      resource('inboxes','Caixas de entrada',`${A}/inboxes`,'Liste as caixas de entrada disponíveis na conta.'),
      resource('inbox-members','Membros da caixa',`${A}/inboxes/9/inbox_members`,'Consulte os agentes autorizados em uma caixa.'),
      resource('evolution-channel','Canal Evolution',`${A}/channels/evolution_channel`,'Consulte a configuração do canal Evolution.'),
      resource('whatsapp-channel','Canal WhatsApp',`${A}/whatsapp`,'Consulte recursos e configurações do WhatsApp.'),
      resource('channel-callbacks','Callbacks de canais',`${A}/callbacks`,'Acompanhe callbacks usados na autorização de canais.'),
      resource('google-email','E-mail Google',`${A}/google`,'Inicie ou consulte a integração OAuth do Google.'),
      resource('microsoft-email-api','E-mail Microsoft',`${A}/microsoft`,'Inicie ou consulte a integração OAuth da Microsoft.')
    ]},
    { title:'Atendimento', resources:[
      resource('agents','Agentes',`${A}/agents`,'Liste os agentes da conta.'),
      resource('teams','Times',`${A}/teams`,'Liste ou crie times de atendimento.','POST',{ name:'Suporte N2', description:'Casos técnicos avançados', allow_auto_assign:true }),
      resource('assignable-agents','Agentes atribuíveis',`${A}/assignable_agents`,'Consulte quem pode receber uma conversa.'),
      resource('custom-roles','Funções personalizadas',`${A}/custom_roles`,'Liste funções e conjuntos de permissões.'),
      resource('capacity-policies','Políticas de capacidade',`${A}/agent_capacity_policies`,'Consulte limites de conversas por agente.'),
      resource('assignment-policies','Políticas de atribuição',`${A}/assignment_policies`,'Consulte regras de distribuição automática.'),
      resource('canned-responses','Respostas rápidas',`${A}/canned_responses`,'Liste ou crie respostas reutilizáveis.','POST',{ short_code:'boas_vindas', content:'Olá {{contact.name}}, como posso ajudar?' }),
      resource('macros','Macros',`${A}/macros`,'Consulte sequências de ações disponíveis.'),
      resource('account-labels','Etiquetas da conta',`${A}/labels`,'Liste ou crie etiquetas globais.','POST',{ title:'cliente-vip', description:'Clientes prioritários', color:'#7C3AED' }),
      resource('custom-attribute-definitions','Definições de atributos',`${A}/custom_attribute_definitions`,'Consulte os campos personalizados da conta.'),
      resource('custom-filters','Filtros personalizados',`${A}/custom_filters`,'Liste filtros salvos por usuários e equipes.')
    ]},
    { title:'Automação e SLA', resources:[
      resource('automation-rules','Regras de automação',`${A}/automation_rules`,'Liste as automações configuradas na conta.'),
      resource('sla-policies','Políticas de SLA',`${A}/sla_policies`,'Consulte metas de resposta e resolução.'),
      resource('applied-slas','SLAs aplicados',`${A}/applied_slas`,'Consulte as políticas efetivamente aplicadas.'),
      resource('conversation-flows','Fluxos de conversa',`${A}/conversation_flows`,'Liste fluxos de reengajamento e resolução automática.'),
      resource('protocol-policies','Políticas de protocolo',`${A}/protocol_policies`,'Consulte regras de numeração e prefixos.'),
      resource('protocols','Protocolos',`${A}/protocols`,'Liste protocolos de atendimento gerados.'),
      resource('protocol-comments','Comentários de protocolo',`${A}/protocols/1024/protocol_comments`,'Consulte ou registre comentários em um protocolo.','POST',{ content:'Validação concluída pelo suporte.' })
    ]},
    { title:'Cosmos IA', resources:[
      resource('cosmos-assistants','Assistentes',`${A}/cosmos/assistants`,'Liste os assistentes de IA da conta.'),
      resource('cosmos-scenarios','Cenários',`${A}/cosmos/assistants/7/scenarios`,'Consulte cenários configurados para um assistente.'),
      resource('cosmos-inboxes','Caixas do assistente',`${A}/cosmos/assistants/7/inboxes`,'Liste as caixas conectadas ao assistente.'),
      resource('cosmos-guardrails','Limites de atuação',`${A}/cosmos/assistants/7/guardrails`,'Consulte as regras de segurança do assistente.'),
      resource('cosmos-response-guidelines','Diretrizes de resposta',`${A}/cosmos/assistants/7/response_guidelines`,'Liste as orientações de tom e formato.'),
      resource('cosmos-documents','Documentos',`${A}/cosmos/documents`,'Consulte documentos da base de conhecimento.'),
      resource('cosmos-assistant-responses','Respostas do assistente',`${A}/cosmos/assistant_responses`,'Analise respostas produzidas pelo Cosmos.'),
      resource('cosmos-faq-suggestions','Sugestões de FAQ',`${A}/cosmos/faq_suggestions`,'Liste perguntas frequentes sugeridas.'),
      resource('cosmos-custom-tools','Ferramentas personalizadas',`${A}/cosmos/custom_tools`,'Consulte ferramentas externas disponíveis ao assistente.'),
      resource('cosmos-copilot-threads','Threads do copiloto',`${A}/cosmos/copilot_threads`,'Liste sessões de conversa com o copiloto.'),
      resource('cosmos-copilot-messages','Mensagens do copiloto',`${A}/cosmos/copilot_threads/9/copilot_messages`,'Consulte mensagens de uma thread do copiloto.'),
      resource('cosmos-agent-sessions','Sessões de agentes',`${A}/cosmos/agent_sessions`,'Consulte sessões de agentes do Cosmos.'),
      resource('cosmos-bulk-actions','Ações em lote do Cosmos',`${A}/cosmos/bulk_actions`,'Acompanhe operações em lote da base de IA.'),
      resource('cosmos-message-reports','Relatórios de mensagem',`${A}/cosmos/message_reports`,'Consulte feedback e relatórios de respostas.')
    ]},
    { title:'Relatórios', resources:[
      resource('reports','Relatórios',`${V2}/reports`,'Consulte métricas agregadas da operação.'),
      resource('report-summary','Resumo de relatórios',`${V2}/reports/summary`,'Obtenha um resumo para o período informado.'),
      resource('report-drilldown','Detalhamento de relatórios',`${V2}/reports/drilldown`,'Detalhe uma métrica por agente, time ou caixa.'),
      resource('csat-responses','Respostas de CSAT',`${V2}/csat_survey_responses`,'Liste avaliações de satisfação recebidas.'),
      resource('reporting-events','Eventos de relatório',`${V2}/reporting_events`,'Consulte eventos usados na composição dos indicadores.')
    ]},
    { title:'Campanhas e portais', resources:[
      resource('campaigns','Campanhas',`${A}/campaigns`,'Liste campanhas da conta.'),
      resource('campaign-contacts','Contatos da campanha',`${A}/campaigns/12/campaign_contacts`,'Consulte os destinatários de uma campanha.'),
      resource('portals','Portais',`${A}/portals`,'Liste portais públicos da central de ajuda.'),
      resource('portal-categories','Categorias do portal',`${A}/portals/4/categories`,'Consulte as categorias de um portal.'),
      resource('portal-articles','Artigos do portal',`${A}/portals/4/articles`,'Liste os artigos publicados no portal.')
    ]},
    { title:'Integrações e administração', resources:[
      resource('integration-apps','Aplicativos de integração',`${A}/integrations/apps`,'Liste aplicativos disponíveis para integração.'),
      resource('integration-hooks','Hooks de integração',`${A}/integrations/hooks`,'Consulte conexões ativas com aplicativos externos.'),
      resource('webhooks-model','Webhooks',`${A}/webhooks`,'Liste ou crie destinos de eventos.','POST',{ url:'https://api.exemplo.com.br/webhooks/starchats', subscriptions:['message_created','conversation_updated'] }),
      resource('dashboard-apps','Dashboard Apps',`${A}/dashboard_apps`,'Liste aplicativos exibidos na conversa.'),
      resource('agent-bots','Bots de agente',`${A}/agent_bots`,'Consulte bots configurados na conta.'),
      resource('audit-logs','Logs de auditoria',`${A}/audit_logs`,'Liste eventos de segurança e administração.'),
      resource('saml-settings','Configurações SAML',`${A}/saml_settings`,'Consulte a configuração de login corporativo.'),
      resource('notification-settings','Preferências de notificação',`${A}/notification_settings`,'Consulte as preferências do usuário.'),
      resource('notifications','Notificações',`${A}/notifications`,'Liste notificações do usuário autenticado.'),
      resource('uploads','Uploads',`${A}/upload`,'Prepare um arquivo para uso em mensagens e conteúdos.','POST',{ file_name:'anexo.pdf', content_type:'application/pdf' }),
      resource('branded-email-layout','Layout de e-mail',`${A}/branded_email_layout`,'Consulte a personalização de e-mails da conta.'),
      resource('onboarding','Onboarding',`${A}/onboarding`,'Consulte o progresso de configuração inicial.')
    ]}
  ];

  const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' })[character]);
  const fullUrl = path => `https://SEU_DOMINIO${path}`;
  const requestObject = item => {
    const request = { method:item.method, url:fullUrl(item.path), headers:{ api_access_token:'SEU_TOKEN', 'Content-Type':'application/json' } };
    if (item.body) request.body = item.body;
    return request;
  };
  const pythonLiteral = value => JSON.stringify(value, null, 2).replace(/\btrue\b/g,'True').replace(/\bfalse\b/g,'False').replace(/\bnull\b/g,'None');
  const pythonExample = item => {
    const lines = [`import requests`, ``, `url = "${fullUrl(item.path)}"`, `headers = {`, `    "api_access_token": "SEU_TOKEN",`, `    "Content-Type": "application/json",`, `}`];
    if (item.body) lines.push(`payload = ${pythonLiteral(item.body)}`);
    lines.push(``, `response = requests.${item.method.toLowerCase()}(`, `    url,`, `    headers=headers,${item.body ? '\n    json=payload,' : ''}`, `)`, `response.raise_for_status()`, `print(response.json())`);
    return lines.join('\n');
  };
  const javascriptExample = item => {
    const options = [`  method: '${item.method}',`, `  headers: {`, `    api_access_token: 'SEU_TOKEN',`, `    'Content-Type': 'application/json',`, `  },`];
    if (item.body) options.push(`  body: JSON.stringify(${JSON.stringify(item.body, null, 2).split('\n').join('\n  ')}),`);
    return [`const response = await fetch(`, `  '${fullUrl(item.path)}',`, `  {`, ...options, `  }`, `);`, ``, `if (!response.ok) throw new Error(\`HTTP \${response.status}\`);`, `const data = await response.json();`, `console.log(data);`].join('\n');
  };
  const panel = (item, language, label, code, selected = false) => `<div class="code-panel" role="tabpanel" id="${item.id}-${language}-panel" aria-labelledby="${item.id}-${language}-tab"${selected ? '' : ' hidden'}><pre><code>${escapeHtml(code)}</code></pre></div>`;
  const example = item => `<div class="api-example" data-code-tabs>
    <div class="code-tabs" role="tablist" aria-label="Exemplos de ${escapeHtml(item.title)}">
      <button class="code-tab active" type="button" role="tab" id="${item.id}-json-tab" aria-controls="${item.id}-json-panel" aria-selected="true" data-language="json">JSON</button>
      <button class="code-tab" type="button" role="tab" id="${item.id}-python-tab" aria-controls="${item.id}-python-panel" aria-selected="false" data-language="python">Python</button>
      <button class="code-tab" type="button" role="tab" id="${item.id}-javascript-tab" aria-controls="${item.id}-javascript-panel" aria-selected="false" data-language="javascript">JavaScript</button>
    </div>
    ${panel(item,'json','JSON',JSON.stringify(requestObject(item),null,2),true)}
    ${panel(item,'python','Python',pythonExample(item))}
    ${panel(item,'javascript','JavaScript',javascriptExample(item))}
  </div>`;
  const section = (item, group) => `<section class="api-section api-model" id="model-${item.id}">
    <span class="api-kicker">${escapeHtml(group.title)}</span><h2>${escapeHtml(item.title)}</h2>
    <p>${escapeHtml(item.description)}</p>
    <div class="endpoint"><span class="method ${item.method.toLowerCase()}">${item.method}</span><code>${escapeHtml(item.path)}</code></div>
    ${example(item)}
  </section>`;

  const nav = document.querySelector('#api-model-nav');
  const content = document.querySelector('#api-model-sections');
  if (!nav || !content) return;
  nav.innerHTML = groups.map(group => `<div class="api-nav-group"><strong>${escapeHtml(group.title)}</strong>${group.resources.map(item => `<a href="#model-${item.id}">${escapeHtml(item.title)}</a>`).join('')}</div>`).join('');
  content.innerHTML = groups.map(group => group.resources.map(item => section(item,group)).join('')).join('');
  if (window.location.hash) {
    window.requestAnimationFrame(() => document.querySelector(window.location.hash)?.scrollIntoView());
  }
})();
