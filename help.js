(() => {
  'use strict';

  const article = (title, eyebrow, description, body) => ({ title, eyebrow, description, body });
  const end = `<div class="article-end"><h2>Precisa de ajuda?</h2><p>Fale com nosso time pelo <a href="https://wa.me/5521966621486" target="_blank" rel="noopener">WhatsApp</a> ou envie um e-mail para <a href="mailto:stardev.sistemas@gmail.com">stardev.sistemas@gmail.com</a>.</p></div>`;

  const docs = {
    'inboxes': article('Caixas de entrada', 'Configuração', 'Entenda os canais, membros, horários e regras que organizam o atendimento no Starchats.', `
      <h2>O que é uma caixa de entrada</h2>
      <p>Uma caixa de entrada representa um canal de atendimento. As mensagens recebidas nesse canal viram <strong>conversas</strong> e são associadas a <strong>contatos</strong>. Um mesmo contato pode conversar por mais de um canal sem que as equipes precisem trabalhar em ferramentas separadas.</p>
      <h2>Canais disponíveis</h2>
      <p>Ao criar uma caixa de entrada, escolha somente o conector correspondente à sua operação:</p>
      <ul><li>WhatsApp Cloud API oficial, Evolution via QR Code, YCloud, Twilio e 360Dialog;</li><li>Website/widget, e-mail por IMAP/SMTP ou OAuth Google/Microsoft;</li><li>Telegram, Facebook, Instagram, SMS, Line e API.</li></ul>
      <div class="callout"><p><strong>Agente da conta não é membro automaticamente.</strong> O agente pode acessar a conta, mas só recebe e visualiza atendimentos de uma caixa quando é adicionado como membro ou possui permissão administrativa compatível.</p></div>
      <h2>Configuração essencial</h2>
      <ol class="steps"><li><strong>Adicione os membros.</strong> Selecione quem poderá atender o canal.</li><li><strong>Defina o horário comercial.</strong> Configure fuso, dias e intervalos. Mensagens fora do horário podem receber uma resposta própria.</li><li><strong>Ative a atribuição automática.</strong> Novas conversas serão distribuídas entre membros disponíveis, respeitando a capacidade configurada.</li><li><strong>Revise a inatividade.</strong> A política de inatividade determina quando uma conversa sem novas mensagens muda de estado ou pode ser encerrada.</li></ol>
      <h2>Antes de publicar</h2><p>Faça um envio real, confirme entrada e saída de mensagens, verifique o nome do remetente e teste com um agente online e outro indisponível. Em canais externos, valide também tokens, webhooks e permissões no provedor.</p>`),

    'agents': article('Agentes e funções', 'Equipe', 'Convide pessoas, escolha permissões e controle disponibilidade e capacidade de atendimento.', `
      <h2>Convidar um agente</h2><ol class="steps"><li>Abra <strong>Configurações › Agentes</strong> e escolha adicionar agente.</li><li>Informe nome, e-mail e papel.</li><li>Adicione a pessoa às caixas de entrada ou aos times necessários.</li><li>O convidado recebe um e-mail para definir o acesso.</li></ol>
      <h2>Papéis e funções</h2><p>O <strong>administrador</strong> gerencia configurações, integrações e pessoas. O <strong>agente</strong> trabalha nas conversas às quais tem acesso. Funções personalizadas permitem combinar permissões mais específicas quando o papel padrão é amplo demais.</p>
      <h2>Disponibilidade</h2><div class="table-wrap"><table><thead><tr><th>Status</th><th>Efeito operacional</th></tr></thead><tbody><tr><td>Online</td><td>Pode receber novas conversas pela atribuição automática.</td></tr><tr><td>Ocupado</td><td>Continua trabalhando, mas não deve receber novos atendimentos automáticos.</td></tr><tr><td>Invisível</td><td>Não aparece como disponível e não recebe distribuição automática.</td></tr></tbody></table></div>
      <h2>Capacidade e remoção</h2><p>O limite de capacidade evita concentrar conversas abertas em uma pessoa. Ao remover um agente, suas conversas e histórico não são apagados; reatribua atendimentos em aberto antes da remoção para que nenhum cliente fique sem responsável.</p>`),

    'teams': article('Times', 'Organização', 'Agrupe agentes por especialidade sem confundir time com canal de entrada.', `
      <h2>Time ou caixa de entrada?</h2><p>A <strong>caixa de entrada</strong> é a origem da conversa, como WhatsApp ou e-mail. O <strong>time</strong> é um grupo interno de pessoas, como Financeiro ou Suporte N2. Uma conversa pode entrar pelo WhatsApp e ser encaminhada ao time Financeiro.</p>
      <h2>Criar e usar um time</h2><ol class="steps"><li>Crie o time e descreva claramente sua responsabilidade.</li><li>Adicione os agentes que devem receber notificações e atribuições do grupo.</li><li>Na conversa, escolha <strong>Atribuir time</strong>; se necessário, escolha também um agente.</li><li>Use automações para direcionar assuntos recorrentes ao time certo.</li></ol>
      <h2>Atribuição, notificações e SLA</h2><p>Atribuir a um time não muda o canal original. Os membros recebem as notificações permitidas por suas preferências, e a atribuição automática pode escolher um agente elegível dentro do fluxo configurado. O relógio de SLA continua correndo conforme a política da caixa de entrada; transferir para outro time não reinicia prazos.</p>`),

    'labels': article('Etiquetas', 'Organização', 'Classifique conversas e contatos para filtrar, automatizar e analisar sua operação.', `
      <h2>Criar e aplicar</h2><p>Em <strong>Configurações › Etiquetas</strong>, crie um nome curto, uma descrição e uma cor fácil de reconhecer. Etiquetas pertencem à <strong>conta inteira</strong>, não a uma caixa de entrada específica.</p>
      <p>Na conversa, aplique ou remova uma etiqueta manualmente. Macros e regras de automação também podem etiquetar com base em canal, conteúdo, horário ou atributos.</p>
      <h2>Filtros e relatórios</h2><p>Use etiquetas para montar filas operacionais — por exemplo, <code>pagamento-pendente</code> — e encontrar conversas pelo filtro. Nos relatórios, elas ajudam a segmentar volume e desempenho por assunto, campanha ou prioridade.</p>
      <div class="callout warning"><p><strong>Evite duplicatas.</strong> Defina uma convenção de nomes antes de crescer: singular, minúsculas e hífen tornam a lista mais previsível.</p></div>`),

    'canned': article('Respostas rápidas', 'Produtividade', 'Crie mensagens reutilizáveis, encontre-as com “/” e personalize com variáveis.', `
      <h2>Criar uma resposta</h2><ol class="steps"><li>Abra <strong>Configurações › Respostas rápidas</strong>.</li><li>Defina um atalho fácil de lembrar, sem espaços, e escreva a mensagem.</li><li>Inclua variáveis apenas quando o dado existir no contato ou na conversa.</li><li>Salve e teste no editor de mensagens.</li></ol>
      <h2>Usar no atendimento</h2><p>No editor de uma conversa, digite <code>/</code> e parte do atalho. Selecione a resposta e revise o texto antes de enviar. A resposta entra no campo de composição; ela não é enviada automaticamente.</p>
      <h2>Variáveis</h2><p>Variáveis como <code>{{contact.name}}</code>, <code>{{contact.email}}</code>, <code>{{conversation.id}}</code> e atributos personalizados substituem valores no momento do uso. A lista disponível no editor é a referência correta para a versão instalada.</p>
      <div class="callout"><p>Uma variável sem valor pode produzir texto vazio. Escreva frases que continuem naturais quando o dado opcional não estiver preenchido.</p></div>`),

    'custom-roles': article('Funções personalizadas', 'Permissões', 'Crie papéis sob medida e conceda apenas os acessos necessários a cada perfil.', `
      <h2>Quando usar</h2><p>Use uma função personalizada quando “administrador” concede acesso demais e “agente” não atende à responsabilidade da pessoa. Exemplos comuns são supervisor, auditor e gestor de integrações.</p>
      <h2>Configurar</h2><ol class="steps"><li>Abra <strong>Configurações › Agentes › Funções personalizadas</strong>.</li><li>Dê um nome descritivo e marque as permissões necessárias.</li><li>Atribua a função aos agentes corretos.</li><li>Teste com uma conta de menor privilégio antes de aplicar em massa.</li></ol>
      <div class="callout warning"><p><strong>Princípio do menor privilégio:</strong> conceda somente o necessário e revise funções quando responsabilidades mudarem.</p></div>`),

    'custom-attributes': article('Atributos personalizados', 'Dados', 'Estruture dados de contatos e conversas, valide formatos e reutilize-os em filtros e automações.', `
      <h2>Contato ou conversa</h2><p>Um atributo de <strong>contato</strong> descreve a pessoa e permanece entre atendimentos, como plano ou cidade. Um atributo de <strong>conversa</strong> descreve um caso específico, como motivo ou número do pedido.</p>
      <h2>Tipos disponíveis</h2><p>Escolha entre texto, número, link, lista, caixa de seleção e data. O tipo controla a entrada e os operadores disponíveis em filtros e automações.</p>
      <h2>Validação com expressão regular</h2><p>Para texto, o campo <strong>padrão regex</strong> restringe valores aceitos e a <strong>dica do regex</strong> explica o formato ao usuário. Exemplo para protocolo <code>ABC-1234</code>: <code>^[A-Z]{3}-\\d{4}$</code>.</p>
      <div class="callout"><p>Teste expressões com valores válidos e inválidos. Uma regra restritiva demais pode impedir o salvamento durante o atendimento.</p></div>
      <h2>Onde reutilizar</h2><p>Atributos alimentam filtros, condições de automação e macros. No Cosmos, condições sobre atributos de contato ou conversa podem limitar o público atendido por um assistente.</p>`),

    'macros': article('Macros', 'Produtividade', 'Execute uma sequência de ações com um clique e padronize tarefas repetitivas.', `
      <h2>O que uma macro faz</h2><p>Uma macro pode combinar ações como alterar status, atribuir agente ou time, adicionar ou remover etiquetas, enviar uma mensagem e resolver a conversa.</p>
      <h2>Criar e executar</h2><ol class="steps"><li>Defina um nome orientado ao resultado, como “Encaminhar para financeiro”.</li><li>Adicione as ações na ordem em que devem acontecer.</li><li>Escolha escopo pessoal ou da conta.</li><li>Na conversa, abra o menu de macros, revise e execute.</li></ol>
      <p>Macros são acionadas manualmente por um agente. Para executar ações automaticamente quando uma condição ocorre, use uma regra de automação.</p>
      <div class="callout warning"><p>A execução pode enviar mensagens ou resolver a conversa imediatamente. Teste a sequência em uma conversa de teste antes de compartilhar com toda a conta.</p></div>`),

    'sla': article('Políticas de SLA', 'Gestão', 'Defina metas de resposta e resolução, aplique-as a caixas de entrada e acompanhe violações.', `
      <h2>As três métricas</h2><div class="table-wrap"><table><thead><tr><th>Sigla</th><th>Métrica</th><th>O que mede</th></tr></thead><tbody><tr><td>FRT</td><td>Primeira resposta</td><td>Da criação da conversa até a primeira resposta elegível.</td></tr><tr><td>NRT</td><td>Próxima resposta</td><td>De uma nova mensagem do cliente até a resposta seguinte.</td></tr><tr><td>RT</td><td>Resolução</td><td>Da criação até a resolução da conversa.</td></tr></tbody></table></div>
      <h2>Criar uma política</h2><ol class="steps"><li>Crie uma política reconhecível, como <strong>Enterprise P0</strong> ou <strong>Enterprise P1</strong>.</li><li>Defina os limites de FRT, NRT e RT.</li><li>Associe a política às caixas de entrada desejadas.</li><li>Configure notificações e responsáveis pela reação à violação.</li></ol>
      <h2>Violações</h2><p>Há violação quando o limite aplicável é ultrapassado sem que o marco esperado tenha ocorrido. Horário comercial, pausa e estados considerados podem alterar a contagem conforme a configuração da conta. Alterar responsável ou time não reinicia automaticamente o relógio.</p>`),

    'audit-logs': article('Logs de auditoria', 'Segurança', 'Investigue alterações importantes por evento, período e responsável.', `
      <h2>Eventos registrados</h2><p>Os registros cobrem login e logout; criação, alteração e remoção de agentes e times; membros de caixas de entrada; configurações da conta; caixas de entrada; webhooks; regras de automação; macros; e exclusão de conversas.</p>
      <h2>Pesquisar</h2><ol class="steps"><li>Abra <strong>Configurações › Logs de auditoria</strong>.</li><li>Defina o período mais estreito que contenha o incidente.</li><li>Filtre pela pessoa que realizou a ação, quando conhecida.</li><li>Abra o evento e compare data, objeto e valores alterados.</li></ol>
      <h2>Retenção</h2><p>O tempo disponível depende da política da implantação e do plano contratado. A própria tela mostra o intervalo consultável; exporte evidências necessárias antes que saiam da janela de retenção.</p>
      <div class="callout warning"><p>Logs ajudam na investigação, mas podem conter identificadores e valores sensíveis. Restrinja o acesso e compartilhe exportações somente com pessoas autorizadas.</p></div>`),

    'agent-bots': article('Bots de agente', 'Desenvolvedores', 'Conecte um bot por webhook, valide chamadas e transfira conversas para humanos.', `
      <h2>Criar e conectar</h2><ol class="steps"><li>Crie o bot e informe uma URL HTTPS pública para o webhook.</li><li>Copie o segredo exibido e guarde-o no cofre de segredos do seu serviço.</li><li>Associe o bot às caixas de entrada em que ele atuará.</li><li>Responda rapidamente ao webhook e processe tarefas longas em fila.</li></ol>
      <h2>Payload</h2><p>Os campos variam por evento e versão. Considere o objeto recebido como contrato versionado e ignore campos desconhecidos. Um formato típico contém evento, conta, caixa de entrada, conversa, mensagem, contato e remetente:</p>
      <pre><code>{
  "event": "message_created",
  "conversation": { "id": 123, "status": "open" },
  "message": { "id": 456, "content": "Olá", "message_type": "incoming" },
  "sender": { "id": 42, "name": "Cliente" }
}</code></pre>
      <h2>Validar e responder</h2><p>Valide a assinatura usando o corpo bruto recebido e o segredo do bot, com comparação em tempo constante. O nome do cabeçalho e o algoritmo devem seguir o valor mostrado pela sua instalação. Nunca confie apenas no IP de origem.</p>
      <pre><code>HTTP/1.1 200 OK
Content-Type: application/json

{"received":true}</code></pre>
      <h2>Transferir para humano</h2><p>Quando não houver resposta segura, altere a conversa para o estado aberto e atribua-a a um time ou agente humano pela API. Envie uma mensagem curta informando a transferência e preserve o contexto no histórico.</p>`),

    'integrations': article('Integrações', 'Visão geral', 'Conecte o Starchats aos sistemas usados por sua equipe.', `
      <h2>Integrações disponíveis</h2><div class="table-wrap"><table><thead><tr><th>Integração</th><th>Uso</th><th>Documentação</th></tr></thead><tbody><tr><td>Slack</td><td>Acompanhar e responder conversas em canais de trabalho.</td><td>Configuração na tela da integração</td></tr><tr><td>Linear</td><td>Criar e vincular issues a partir de conversas.</td><td>Configuração na tela da integração</td></tr><tr><td>Notion</td><td>Conectar conteúdo e fluxos de trabalho da equipe.</td><td>Configuração na tela da integração</td></tr><tr><td>Shopify</td><td>Consultar contexto de clientes e pedidos.</td><td>Configuração na tela da integração</td></tr><tr><td>Dialogflow</td><td>Automatizar respostas com um agente do Dialogflow.</td><td>Configuração na tela da integração</td></tr><tr><td>Webhooks</td><td>Enviar eventos em tempo real para seu sistema.</td><td><a href="/docs/webhooks/">Abrir guia</a></td></tr><tr><td>Dashboard Apps</td><td>Exibir um aplicativo no painel da conversa.</td><td><a href="/docs/dashboard-apps/">Abrir guia</a></td></tr></tbody></table></div>
      <h2>Boas práticas</h2><p>Use uma credencial de serviço dedicada, conceda o menor conjunto de permissões e registre quem é responsável por cada conexão. Após conectar, teste com dados não sensíveis e documente o processo de revogação.</p>`),

    'dashboard-apps': article('Dashboard Apps', 'Desenvolvedores', 'Incorpore um aplicativo web na barra lateral da conversa e receba contexto por postMessage.', `
      <h2>Como funciona</h2><p>Um Dashboard App é carregado em um <code>iframe</code> na barra lateral da conversa. O Starchats envia o contexto atual com <code>window.postMessage</code>, permitindo que o aplicativo mostre pedidos, assinaturas ou dados do CRM sem sair do atendimento.</p>
      <h2>Receber o contexto</h2><pre><code>window.addEventListener('message', (event) =&gt; {
  if (event.origin !== 'https://app.seudominio.com') return;
  const { event: type, data } = event.data || {};
  if (type === 'appContext') {
    renderCustomer(data.contact, data.conversation);
  }
});</code></pre>
      <p>O payload pode conter informações da conta, agente, contato e conversa. Leia os campos defensivamente, pois atributos opcionais podem não existir.</p>
      <h2>Segurança</h2><ul><li>Use HTTPS e valide sempre <code>event.origin</code>;</li><li>não use <code>*</code> como destino ao enviar dados sensíveis;</li><li>não coloque segredos no código do navegador;</li><li>autorize ações novamente no seu backend;</li><li>trate qualquer campo do contexto como dado não confiável.</li></ul>
      <div class="callout"><p>Confirme o nome exato do evento e a estrutura do payload emitidos pela versão instalada antes de publicar. O exemplo demonstra o padrão de integração, não substitui a inspeção do evento real.</p></div>`),

    'webhooks': article('Webhooks', 'Desenvolvedores', 'Receba eventos do Starchats com processamento idempotente, validação de origem e retentativas seguras.', `
      <h2>Eventos assináveis</h2><p>A instalação pode disponibilizar eventos de URL verification, mensagens, conversas, contatos e violações de SLA. Entre os mais usados estão <code>message_created</code>, <code>message_updated</code>, <code>conversation_created</code>, <code>conversation_updated</code>, <code>conversation_status_changed</code>, <code>contact_created</code>, <code>contact_updated</code> e <code>conversation_sla_breached</code>.</p>
      <h2>Formato</h2><pre><code>{
  "event": "conversation_sla_breached",
  "account": { "id": 1 },
  "inbox": { "id": 9 },
  "conversation": { "id": 123 },
  "meta": { "metric": "FRT" }
}</code></pre>
      <p>O conteúdo exato depende do evento. Identifique o tipo antes de ler o restante e aceite campos adicionais sem falhar.</p>
      <h2>Entrega e retentativa</h2><p>Responda com sucesso em poucos segundos e processe em fila. Em falhas ou timeout, o Starchats pode tentar novamente conforme a política da instalação. Como uma entrega pode se repetir, deduplique por evento ou pela combinação de tipo e identificador do objeto.</p>
      <h2>Validar a origem</h2><p>Use um segredo compartilhado e compare a assinatura calculada sobre o <strong>corpo bruto</strong>. Mantenha HTTPS, limite o tamanho da requisição e registre falhas sem gravar mensagens ou tokens em texto aberto.</p>`),

    'saml': article('SAML SSO', 'Segurança', 'Configure autenticação corporativa com seu provedor de identidade.', `
      <h2>Campos do Starchats</h2><div class="table-wrap"><table><thead><tr><th>Campo</th><th>Origem ou destino</th></tr></thead><tbody><tr><td>ACS URL</td><td>Copie do Starchats para a Reply URL/ACS do IdP.</td></tr><tr><td>SP Entity ID</td><td>Copie do Starchats para o identificador da aplicação no IdP.</td></tr><tr><td>SSO URL</td><td>Copie do IdP para o Starchats.</td></tr><tr><td>IdP Entity ID</td><td>Copie o identificador/issuer do IdP.</td></tr><tr><td>Certificado</td><td>Cole o certificado público X.509 de assinatura do IdP.</td></tr></tbody></table></div>
      <h2>Configurar</h2><ol class="steps"><li>No Okta, Microsoft Entra ID (Azure AD) ou Google Workspace, crie uma aplicação SAML personalizada.</li><li>Informe ACS URL e SP Entity ID exatamente como exibidos, incluindo <code>https://</code>.</li><li>Envie e-mail como identificador persistente do usuário e, quando solicitado, nome.</li><li>Copie SSO URL, IdP Entity ID e certificado para o Starchats.</li><li>Teste em janela anônima antes de exigir SSO para toda a equipe.</li></ol>
      <h2>Usuários existentes</h2><p>Quando o e-mail retornado pelo IdP coincide com um usuário existente, o acesso SAML deve vincular a mesma conta em vez de criar duplicata. Confirme esse fluxo antes de desativar senhas e mantenha pelo menos um método administrativo de recuperação durante a implantação.</p>`),

    'cosmos': article('Cosmos: visão geral', 'Inteligência artificial', 'Comece pelo hub do Cosmos e encontre o caminho certo para configurar conhecimento, comportamento e ferramentas.', `
      <h2>O que é o Cosmos</h2><p>Cosmos é a camada de IA do Starchats. Ele usa o conhecimento aprovado pela sua equipe para responder clientes, executar ações permitidas e transferir conversas quando a intervenção humana é mais adequada.</p>
      <h2>Configure por partes</h2><div class="doc-grid"><a class="doc-card" href="/docs/cosmos-assistants/"><small>Operação</small><strong>Assistentes</strong><p>Defina público, agenda, comportamento e caixas de entrada.</p></a><a class="doc-card" href="/docs/cosmos-documents/"><small>Conhecimento</small><strong>Documentos</strong><p>Adicione páginas web e PDFs à base de conhecimento.</p></a><a class="doc-card" href="/docs/cosmos-faqs/"><small>Conhecimento</small><strong>FAQs</strong><p>Revise perguntas sugeridas e aprove respostas confiáveis.</p></a><a class="doc-card" href="/docs/cosmos-tools/"><small>Ações</small><strong>Ferramentas</strong><p>Conecte APIs externas com parâmetros e autenticação.</p></a></div>
      <h2>Outros controles</h2><ul><li><strong>Cenários:</strong> orientam o comportamento em situações específicas;</li><li><strong>diretrizes de resposta:</strong> definem tom, formato e regras obrigatórias;</li><li><strong>limites de atuação:</strong> indicam quando responder, recusar ou transferir;</li><li><strong>playground:</strong> permite testar perguntas antes de publicar alterações.</li></ul>
      <h2>Ler as métricas</h2><div class="table-wrap"><table><thead><tr><th>Métrica</th><th>Interpretação</th></tr></thead><tbody><tr><td>Tempo economizado</td><td>Estimativa do trabalho humano evitado pela automação.</td></tr><tr><td>Resoluções que permaneceram fechadas</td><td>Casos resolvidos pelo Cosmos sem reabertura posterior.</td></tr><tr><td>Tempo mediano de resolução</td><td>Tempo central das resoluções, menos sensível a casos extremos.</td></tr><tr><td>Motivos de transferência</td><td>Por que o Cosmos entregou conversas à equipe.</td></tr><tr><td>CSAT do Cosmos</td><td>Satisfação coletada nas conversas atendidas pela IA.</td></tr></tbody></table></div>
      <div class="callout"><p>Acompanhe métricas em conjunto. Uma alta automação com muitas reaberturas ou CSAT em queda indica que conhecimento e limites precisam de revisão.</p></div>`),

    'cosmos-assistants': article('Assistentes do Cosmos', 'Primeiros passos', 'Crie um assistente, conecte caixas de entrada e escolha quando ele atende e encerra conversas.', `
      <h2>Criar e publicar</h2><ol class="steps"><li>Crie o assistente e escolha um nome que identifique sua função.</li><li>Associe documentos, FAQs, cenários e diretrizes relevantes.</li><li>Conecte as caixas de entrada onde ele poderá responder.</li><li>Teste no playground e publique quando o comportamento estiver seguro.</li></ol>
      <h2>Público e agenda</h2><p>Em <strong>Público</strong>, escolha todos os contatos ou use condições sobre atributos de contato e conversa. Em <strong>Agenda</strong>, defina atendimento sempre, somente dentro do horário comercial ou somente fora dele. O horário vem da caixa de entrada, portanto confira o fuso.</p>
      <h2>Temperatura</h2><p>Temperaturas menores tornam as respostas mais previsíveis; maiores aumentam a variação. Para suporte e processos regulados, comece baixo e só aumente depois de avaliar exemplos reais.</p>
      <h2>Quando o cliente para de responder</h2><div class="table-wrap"><table><thead><tr><th>Modo</th><th>Comportamento</th><th>Quando usar</th></tr></thead><tbody><tr><td>Aguardar o cliente</td><td>Mantém a conversa aguardando uma nova mensagem.</td><td>Jornadas longas ou pausas comuns.</td></tr><tr><td>Sempre resolver</td><td>Encerra após o período configurado.</td><td>Interações curtas e objetivas.</td></tr><tr><td>Deixar o Cosmos avaliar</td><td>A IA considera o contexto para decidir.</td><td>Recomendado como ponto de partida.</td></tr></tbody></table></div>
      <div class="callout success"><p><strong>Recomendação:</strong> comece com “deixar o Cosmos avaliar”, acompanhe reaberturas e só adote uma regra fixa se seu fluxo exigir.</p></div>`),

    'cosmos-documents': article('Documentos do Cosmos', 'Base de conhecimento', 'Adicione páginas web e PDFs, acompanhe a sincronização e corrija erros de conteúdo.', `
      <h2>Adicionar uma fonte</h2><p>Use uma <strong>URL pública</strong> para uma página web ou envie um <strong>PDF de até 10 MB</strong>. Prefira conteúdos claros, atuais e com títulos descritivos. Páginas que dependem de login não podem ser lidas.</p>
      <h2>Atualizações</h2><p>Fontes web podem ser verificadas novamente de forma automática. Use a atualização manual depois de uma mudança urgente. PDFs são cópias do arquivo enviado; para trocar seu conteúdo, envie a versão atualizada conforme o fluxo da tela.</p>
      <h2>Status de sincronização</h2><div class="table-wrap"><table><thead><tr><th>Status</th><th>O que fazer</th></tr></thead><tbody><tr><td>Atualizado</td><td>Nenhuma ação; teste uma pergunta no playground.</td></tr><tr><td>Atualizando</td><td>Aguarde o processamento.</td></tr><tr><td>Atualização travada</td><td>Tente novamente; se persistir, revise tamanho e disponibilidade.</td></tr><tr><td>Falhou</td><td>Abra o detalhe do erro e corrija a origem.</td></tr><tr><td>Ainda não atualizado</td><td>Inicie a primeira sincronização.</td></tr></tbody></table></div>
      <h2>Erros comuns</h2><ul><li><strong>Página não encontrada:</strong> corrija a URL ou publique a página;</li><li><strong>acesso negado:</strong> remova login, bloqueio por robô ou regra de firewall;</li><li><strong>tempo esgotado:</strong> melhore o tempo de resposta e tente novamente;</li><li><strong>conteúdo vazio:</strong> confirme que o texto está no HTML e não aparece apenas após scripts;</li><li><strong>PDF ilegível:</strong> use um arquivo com texto selecionável; PDFs formados só por imagens podem exigir OCR.</li></ul>`),

    'cosmos-faqs': article('FAQs do Cosmos', 'Base de conhecimento', 'Revise sugestões, aprove em lote com cuidado e melhore respostas recorrentes.', `
      <h2>De onde vêm as sugestões</h2><p>O Cosmos identifica perguntas recorrentes nas conversas e pode sugerir pares de pergunta e resposta. Sugestões não entram automaticamente na base aprovada: uma pessoa deve revisar precisão, atualidade e tom.</p>
      <h2>Fluxo de revisão</h2><ol class="steps"><li>Abra a aba <strong>Pendentes</strong> e priorize itens pelo volume indicado.</li><li>Compare a resposta sugerida com a política e a fonte oficial.</li><li>Edite ambiguidades, remova dados pessoais e deixe uma única resposta objetiva.</li><li>Aprove o item; ele passa de pendente para aprovado.</li></ol>
      <h2>Aprovação em lote</h2><p>Selecione vários itens somente quando compartilham contexto e já foram conferidos. O contador no banner mostra trabalho pendente; revisar importa porque uma resposta aprovada passa a orientar atendimentos futuros.</p>
      <div class="callout warning"><p>Não aprove respostas conflitantes para a mesma pergunta. Consolide versões e retire conteúdo vencido para evitar escolhas inconsistentes.</p></div>`),

    'cosmos-tools': article('Ferramentas personalizadas do Cosmos', 'Desenvolvedores', 'Permita que assistentes consultem ou executem APIs externas com controles de rede e autenticação.', `
      <h2>Definir uma ferramenta</h2><ol class="steps"><li>Escolha um nome que descreva uma ação, como <code>consultar_pedido</code>.</li><li>Escreva quando a ferramenta deve e não deve ser usada.</li><li>Informe um endpoint HTTPS público.</li><li>Defina parâmetros e marque os obrigatórios.</li><li>Teste respostas de sucesso e erro antes de disponibilizar ao assistente.</li></ol>
      <h2>Autenticação e parâmetros</h2><p>Use <strong>Bearer Token</strong> para tokens em cabeçalho ou <strong>Basic Auth</strong> para usuário e senha. Segredos devem ser exclusivos e revogáveis. Parâmetros podem ser <strong>String</strong>, <strong>Boolean</strong>, <strong>Array</strong> ou <strong>Object</strong>; descrições claras ajudam o modelo a preencher cada valor.</p>
      <h2>Como o assistente decide</h2><p>O nome e a descrição são parte do contrato. Explique o resultado esperado, pré-condições e significado dos parâmetros. O assistente compara a intenção do cliente com essas instruções e chama a ferramenta apenas quando julga necessário.</p>
      <h2>Proteção de rede</h2><div class="callout warning"><p>As requisições passam pelo <code>SafeFetch</code> e pelo filtro de SSRF. Endereços privados, loopback, metadados de nuvem e redirecionamentos para a rede interna são bloqueados. Publique uma fachada HTTPS segura se a API existir apenas na intranet.</p></div>
      <p>Retorne JSON pequeno, com códigos HTTP coerentes, timeout curto e mensagens de erro que não revelem segredos.</p>`),

    'whatsapp-migration': article('Migrar WhatsApp para a Cloud API', 'WhatsApp', 'Migre uma caixa Evolution/WhatsApp Web para a plataforma oficial preservando o histórico no Starchats.', `
      <h2>Antes de começar</h2><ul><li>Tenha acesso administrativo à conta e ao Meta Business Manager;</li><li>confirme que o app possui <code>whatsapp_business_messaging</code> e <code>whatsapp_business_management</code>;</li><li>faça a migração em uma janela de baixo movimento;</li><li>não exclua a caixa antiga nem conversas.</li></ul>
      <h2>Executar a migração</h2><ol class="steps"><li>Abra a caixa de entrada Evolution/WhatsApp Web e escolha a migração manual.</li><li>Autentique na Meta e selecione a empresa, WABA e número corretos.</li><li>Autorize as permissões solicitadas e conclua o assistente.</li><li>Envie e receba uma mensagem de teste e verifique modelos e webhook.</li></ol>
      <p>A migração troca a conexão do canal; contatos, conversas e mensagens já armazenados no Starchats permanecem no histórico.</p>
      <h2>“Concluída, mas precisa ser reautorizada”</h2><p>Esse estado significa que a estrutura foi migrada, mas a credencial final não pode operar o canal. Abra a reautorização, entre com um administrador da empresa correta e conceda novamente as permissões. Depois, repita o teste de entrada e saída.</p>
      <div class="callout warning"><p>Evite manter Evolution/WhatsApp Web e Cloud API enviando pelo mesmo número ao mesmo tempo. Conexões concorrentes podem causar falhas ou desconexões.</p></div>`),

    'microsoft-email': article('Configurar Microsoft para e-mail', 'Instalação', 'Registre um aplicativo no Microsoft Entra ID e conecte caixas de e-mail por OAuth.', `
      <h2>Registrar o aplicativo</h2><ol class="steps"><li>No Microsoft Entra admin center, crie um <strong>App registration</strong>.</li><li>Escolha os tipos de conta aceitos pela sua organização.</li><li>Adicione como Web a URL de redirecionamento exibida pelo Starchats.</li><li>Copie o <strong>Application (client) ID</strong>.</li><li>Crie um client secret e copie o valor imediatamente.</li></ol>
      <h2>Permissões do Microsoft Graph</h2><p>Adicione permissões delegadas necessárias para autenticar, ler e enviar e-mail e manter acesso autorizado, conforme exibidas na configuração da sua versão. Em ambientes corporativos, um administrador pode precisar conceder consentimento.</p>
      <div class="callout"><p>Use a URL de redirecionamento exatamente como exibida, incluindo esquema, domínio, caminho e barra final. Uma diferença mínima causa erro de callback.</p></div>
      <h2>Conectar ao Starchats</h2><p>No <strong>Super Admin › Configurações</strong>, cole o App ID e o valor do segredo nos campos Microsoft/Azure e salve. Reinicie os processos se a tela indicar essa necessidade. Depois, crie uma caixa de entrada de e-mail Microsoft e conclua o OAuth.</p>
      <div class="callout warning"><p>O valor do segredo expira na data escolhida no Entra. Registre essa data e faça a rotação antes do vencimento.</p></div>`),

    'pgvector': article('Instalar a extensão vector do PostgreSQL', 'Infraestrutura', 'Instale o pgvector e libere CREATE EXTENSION para concluir as migrations do Cosmos.', `
      <h2>Por que a migration falha</h2><p>O Cosmos armazena embeddings com a extensão <code>vector</code>. O erro em <code>CREATE EXTENSION vector</code> indica que o pacote não existe no servidor PostgreSQL ou que o usuário da aplicação não pode habilitá-lo.</p>
      <h2>Instalar o pgvector</h2><p>Use o pacote compatível com a versão principal do PostgreSQL. Em Ubuntu/Debian com repositório PGDG, por exemplo:</p>
      <pre><code>sudo apt update
sudo apt install postgresql-16-pgvector</code></pre>
      <p>Troque <code>16</code> pela versão instalada. Em imagem Docker, use uma imagem que inclua pgvector ou construa a extensão durante o build. Em serviços gerenciados, habilite a extensão no painel ou consulte a lista de extensões permitidas.</p>
      <h2>Habilitar no banco</h2><pre><code>sudo -u postgres psql -d starchats -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d starchats -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"</code></pre>
      <p>Substitua <code>starchats</code> pelo banco real. Normalmente a criação exige superusuário ou uma função privilegiada; o usuário da aplicação não precisa permanecer superusuário depois que a extensão existe.</p>
      <h2>Retomar</h2><p>Reexecute a migration ou o instalador. Se ainda falhar, confirme que pacote e servidor usam a mesma versão do PostgreSQL e que a extensão foi criada no banco correto.</p>`),

    'whatsapp-token': article('Token de gerenciamento do WhatsApp Business', 'WhatsApp', 'Gere uma credencial com as permissões necessárias para sincronizar modelos e consultar a saúde da conta.', `
      <h2>Para que o token é usado</h2><p>O Starchats usa essa credencial para acessar ativos autorizados da conta do WhatsApp Business, sincronizar modelos de mensagem e consultar informações operacionais do número e da conta.</p>
      <h2>Obter o token</h2><ol class="steps"><li>No Meta Business Manager, confirme que você administra a empresa, o app e a WABA corretos.</li><li>Crie ou selecione um usuário do sistema dedicado à integração.</li><li>Atribua ao usuário os ativos do app e da conta do WhatsApp Business.</li><li>Gere um token para o app com <code>whatsapp_business_management</code>; inclua <code>whatsapp_business_messaging</code> quando o fluxo também enviar mensagens.</li><li>Cole a credencial no campo indicado pelo Starchats e teste a sincronização.</li></ol>
      <div class="callout warning"><p>Trate o token como senha: não envie em chat, não salve em repositório e revogue imediatamente se houver exposição. Use uma credencial dedicada em vez do token pessoal de um funcionário.</p></div>
      <h2>Problemas comuns</h2><p>Se nenhuma WABA aparecer, revise ativos atribuídos e empresa selecionada. Se modelos não sincronizarem, confira a permissão de gerenciamento e o papel do usuário do sistema. Em erro de expiração, gere uma nova credencial e substitua a anterior.</p>`),

    'campaigns': article('Campanhas', 'Engajamento', 'Envie mensagens proativas a um público definido e acompanhe a execução.', `
      <h2>Antes de enviar</h2><p>Escolha uma caixa compatível, use destinatários com base legal e consentimento aplicável e, no WhatsApp, selecione um modelo aprovado quando a janela de atendimento exigir.</p>
      <h2>Criar uma campanha</h2><ol class="steps"><li>Defina nome e canal.</li><li>Selecione o público ou lista de contatos.</li><li>Escreva a mensagem e revise variáveis.</li><li>Agende ou envie após um teste interno.</li></ol>
      <p>Acompanhe enviados, entregues, lidos e falhas. Remova destinatários inválidos e respeite solicitações de descadastro para proteger reputação e entregabilidade.</p>`),

    'reports': article('Relatórios', 'Gestão', 'Acompanhe volume, tempos, desempenho e satisfação com filtros consistentes.', `
      <h2>Escolher o relatório</h2><p>Use relatórios de conversas para volume e tempo, de agentes para desempenho individual, de caixas e times para capacidade operacional e de CSAT para satisfação.</p>
      <h2>Filtrar corretamente</h2><p>Defina período e fuso, depois aplique caixas, times, agentes ou etiquetas. Ao comparar períodos, mantenha os mesmos filtros e considere mudanças em horário comercial, equipe e volume.</p>
      <div class="callout"><p>Médias isoladas escondem extremos. Leia tempo de primeira resposta, resolução, violações de SLA, reaberturas e satisfação em conjunto.</p></div>`),

    'help-center': article('Central de ajuda e portais', 'Autoatendimento', 'Publique artigos organizados e ofereça respostas antes que o cliente abra uma conversa.', `
      <h2>Estrutura</h2><p>Um portal reúne categorias; categorias agrupam artigos; artigos entregam a resposta. Use títulos que reproduzam a pergunta do cliente e mantenha um assunto principal por página.</p>
      <h2>Publicar</h2><ol class="steps"><li>Crie o portal e configure nome, idioma e identidade.</li><li>Crie categorias por tarefa ou etapa da jornada.</li><li>Escreva, revise e publique artigos.</li><li>Teste navegação, pesquisa e links em janela anônima.</li></ol>
      <p>Revise conteúdo depois de mudanças no produto. Arquive páginas obsoletas e redirecione URLs que já tenham sido compartilhadas.</p>`),

    'email-channel': article('Canal de e-mail', 'Canais', 'Receba e envie e-mails por IMAP/SMTP ou OAuth Google e Microsoft.', `
      <h2>Escolher a conexão</h2><p>Prefira OAuth para Google e Microsoft. Para outros provedores, informe servidores IMAP e SMTP, portas e modo TLS conforme a documentação do serviço.</p>
      <h2>Configurar</h2><ol class="steps"><li>Informe o endereço que será atendido.</li><li>Autentique por OAuth ou forneça a credencial de aplicativo.</li><li>Teste IMAP para recebimento e SMTP para envio.</li><li>Adicione membros e envie uma mensagem externa de ponta a ponta.</li></ol>
      <div class="callout warning"><p>Não use a senha principal quando o provedor oferece senha de aplicativo. Mantenha SPF, DKIM e DMARC corretos para reduzir falhas e spam.</p></div>`),

    'facebook-channel': article('Canal do Facebook', 'Canais', 'Conecte uma Página do Facebook e centralize mensagens no Starchats.', `
      <h2>Pré-requisitos</h2><p>Entre com uma conta que administre a Página e permita ao Starchats listar páginas, gerenciar a conversa e receber webhooks necessários.</p>
      <h2>Conectar</h2><ol class="steps"><li>Crie uma caixa de entrada Facebook.</li><li>Autorize a Meta e selecione a empresa e Página corretas.</li><li>Adicione membros à caixa.</li><li>Envie uma mensagem à Página por outro perfil e responda pelo Starchats.</li></ol>
      <p>Se as mensagens pararem após mudança de senha, papel ou política da Meta, reautorize o canal com um administrador atual.</p>`)
  };

  const groups = [
    { title: 'Configuração e equipe', items: [
      ['inboxes','/docs/inboxes/'], ['agents','/docs/agents/'], ['teams','/docs/teams/'],
      ['labels','/docs/labels/'], ['canned','/docs/canned-responses/'], ['custom-roles','/docs/custom-roles/'],
      ['custom-attributes','/docs/custom-attributes/'], ['macros','/docs/macros/'], ['sla','/docs/sla/'], ['audit-logs','/docs/audit-logs/']
    ]},
    { title: 'Integrações e desenvolvimento', items: [
      ['integrations','/docs/integrations/'], ['agent-bots','/docs/agent-bots/'], ['dashboard-apps','/docs/dashboard-apps/'],
      ['webhooks','/docs/webhooks/'], ['saml','/docs/saml/'], ['whatsapp-token','/docs/whatsapp-business-management-token/']
    ]},
    { title: 'Cosmos IA', items: [
      ['cosmos','/docs/cosmos/'], ['cosmos-assistants','/docs/cosmos-assistants/'], ['cosmos-documents','/docs/cosmos-documents/'],
      ['cosmos-faqs','/docs/cosmos-faqs/'], ['cosmos-tools','/docs/cosmos-tools/']
    ]},
    { title: 'Canais e comunicação', items: [
      ['whatsapp-migration','/docs/whatsapp-migration/'], ['email-channel','/docs/email/'], ['facebook-channel','/docs/facebook/'],
      ['campaigns','/docs/campaigns/'], ['help-center','/docs/help-center/']
    ]},
    { title: 'Gestão e instalação', items: [
      ['reports','/docs/reports/'], ['microsoft-email','/docs/microsoft-email/'], ['pgvector','/docs/pgvector/']
    ]}
  ];

  const header = () => `<nav class="help-nav"><div class="help-nav-inner">
    <a class="help-brand" href="/"><img src="/logo2.png" alt="Starchats"><span class="help-badge">Documentação</span></a>
    <div class="help-nav-links"><a href="/docs/">Todos os guias</a><a href="/">Site</a><a class="help-cta" href="https://wa.me/5521966621486" target="_blank" rel="noopener">Falar com suporte</a></div>
  </div></nav>`;

  const footer = () => `<footer class="help-footer"><div class="help-footer-inner"><span>© 2026 Stardev · Starchats</span><div class="help-footer-links"><a href="/politica-de-privacidade">Privacidade</a><a href="/termos-de-servico">Termos</a><a href="mailto:stardev.sistemas@gmail.com">Contato</a></div></div></footer>`;

  const slugify = (text) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

  function renderHome(root) {
    const cards = groups.map(group => `<section class="doc-section"><h2>${group.title}</h2><div class="doc-grid">${group.items.map(([key, url]) => {
      const item = docs[key];
      return `<a class="doc-card" href="${url}" data-search="${item.title} ${item.eyebrow} ${item.description}"><small>${item.eyebrow}</small><strong>${item.title}</strong><p>${item.description}</p></a>`;
    }).join('')}</div></section>`).join('');

    root.innerHTML = `${header()}<header class="help-hero"><div class="help-hero-inner"><span class="eyebrow">Central de ajuda</span><h1>Como podemos ajudar?</h1><p class="help-lead">Guias práticos para configurar canais, organizar a equipe, integrar sistemas e colocar o Cosmos em operação.</p><div class="search-box"><input id="doc-search" type="search" placeholder="Buscar na documentação" aria-label="Buscar na documentação"><span aria-hidden="true">⌕</span></div></div></header><main class="help-home">${cards}<div class="no-results">Nenhum guia encontrado. Tente outro termo ou <a href="https://wa.me/5521966621486">fale com o suporte</a>.</div></main>${footer()}`;

    const input = document.querySelector('#doc-search');
    input.addEventListener('input', () => {
      const query = input.value.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      let visible = 0;
      document.querySelectorAll('.doc-card').forEach(card => {
        const haystack = card.dataset.search.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
        card.hidden = query !== '' && !haystack.includes(query);
        if (!card.hidden) visible += 1;
      });
      document.querySelectorAll('.doc-section').forEach(section => {
        section.hidden = !section.querySelector('.doc-card:not([hidden])');
      });
      document.querySelector('.no-results').style.display = visible ? 'none' : 'block';
    });
  }

  function renderArticle(root, key) {
    const item = docs[key];
    if (!item) {
      window.location.replace('/docs/');
      return;
    }

    const holder = document.createElement('div');
    holder.innerHTML = item.body;
    const headings = [...holder.querySelectorAll('h2')];
    headings.forEach((heading, index) => {
      heading.id = heading.id || `${slugify(heading.textContent)}-${index + 1}`;
    });
    const toc = headings.map(heading => `<a href="#${heading.id}">${heading.textContent}</a>`).join('');

    root.innerHTML = `${header()}<header class="help-hero"><div class="help-hero-inner"><div class="breadcrumb"><a href="/docs/">Documentação</a><span>›</span><span>${item.eyebrow}</span></div><span class="eyebrow">${item.eyebrow}</span><h1>${item.title}</h1><p class="help-lead">${item.description}</p></div></header><main class="help-shell"><article class="help-article">${holder.innerHTML}${end}</article><aside class="toc"><strong>Neste guia</strong>${toc}</aside></main>${footer()}`;

    document.title = `${item.title} | Documentação Starchats`;
    const description = document.querySelector('meta[name="description"]');
    if (description) description.content = item.description;
    const schema = document.createElement('script');
    schema.type = 'application/ld+json';
    schema.textContent = JSON.stringify({ '@context':'https://schema.org', '@type':'TechArticle', headline:item.title, description:item.description, inLanguage:'pt-BR', publisher:{ '@type':'Organization', name:'Starchats', url:'https://starchats.com.br' } });
    document.head.appendChild(schema);
  }

  const root = document.querySelector('#help-app');
  if (!root) return;
  const key = document.body.dataset.doc;
  if (key === 'home') renderHome(root);
  else renderArticle(root, key);
})();
