const ACCENT = "#7C3AED";
const WEBHOOK_URL = "https://n8n.starchats.com.br/webhook-test/d7fd4fbf-a39e-4972-b80a-5c859a455bab";

const scenarios = {
  atraso: {
    msg: "Faz 8 dias que comprei e o pedido ainda não chegou. Tô esperando notícias.",
    sentiment: 18,
    sentimentTag: "frustrado · urgente",
    tags: ["atraso", "logística", "vip"],
    summary: "Cliente VIP (3ª compra). Pedido #43219 em atraso há 8 dias. Já entrou em contato 2x esta semana.",
    intent: "Reclamação · Logística",
    nextStep: "Priorizar entrega · Oferecer cupom",
  },
  frete: {
    msg: "Oi! Vocês entregam pra Curitiba? Qual o prazo e o valor do frete?",
    sentiment: 72,
    sentimentTag: "curioso · neutro",
    tags: ["pré-venda", "frete", "novo"],
    summary: "Lead novo, primeira interação. Demonstra interesse claro de compra. CEP da capital paranaense.",
    intent: "Pré-venda · Informações",
    nextStep: "Enviar tabela de frete · Oferecer cupom de 1ª compra",
  },
  upsell: {
    msg: "Adorei o último pedido! Vocês têm o conjunto completo da mesma coleção?",
    sentiment: 92,
    sentimentTag: "satisfeito · pronto pra comprar",
    tags: ["vip", "upsell", "fidelizado"],
    summary: "Cliente VIP com 8 compras no último ano. Ticket médio R$ 1.890. Comprou recentemente.",
    intent: "Upsell · Recompra",
    nextStep: "Sugerir conjunto · Aplicar desconto VIP",
  },
  reclamacao: {
    msg: "Vocês me venderam um produto com defeito e ninguém me responde há 2 dias!!",
    sentiment: 8,
    sentimentTag: "irritado · risco de churn",
    tags: ["defeito", "urgente", "churn-risk"],
    summary: "Cliente desde 2024. Reportou defeito há 2 dias sem retorno. Risco alto de cancelamento.",
    intent: "Reclamação · Pós-venda",
    nextStep: "Pedir desculpa · Trocar produto · Escalar pro gestor",
  },
};

const responses = {
  atraso: {
    Profissional: "Olá! Sinto muito pelo atraso. Vou verificar o status do seu pedido agora mesmo e te retorno com o código de rastreio em até 5 minutos.",
    Amigável: "Oi! Lamento o atraso 🙏 Vou priorizar seu pedido agora e te mando o rastreio em alguns minutinhos, tá?",
    Casual: "Poxa, lamento muito! Bora resolver agora - já tô puxando o rastreio do seu pedido, te aviso em 5min.",
  },
  frete: {
    Profissional: "Olá! Sim, entregamos em Curitiba. Prazo de 3 a 5 dias úteis, frete a partir de R$ 14,90. Posso aplicar um cupom de 1ª compra?",
    Amigável: "Oi! Sim, entregamos em Curitiba 💜 Prazo é 3-5 dias úteis e o frete sai a partir de R$ 14,90. Quer um cupom de primeira compra?",
    Casual: "Oi! Entregamos sim em Curitiba 👍 3-5 dias úteis, frete começa em R$ 14,90. Te mando um cupom de 1ª compra?",
  },
  upsell: {
    Profissional: "Que ótimo! Sim, temos o conjunto completo. Posso enviar as fotos com 10% de desconto VIP exclusivo pra você?",
    Amigável: "Adorei saber! 💜 Temos sim, e como cliente VIP você ganha 10% de desconto no conjunto completo. Te envio as fotos?",
    Casual: "Que legal!! 🥰 Tenho sim o conjunto, e como você é VIP, libero 10% off. Manda eu te enviar as fotos?",
  },
  reclamacao: {
    Profissional: "Peço sinceras desculpas pela demora. Vou priorizar seu caso agora e providenciar a troca do produto. Em 1 hora você terá resposta.",
    Amigável: "Sinto muito mesmo pela demora 🙏 Vou priorizar seu caso agora e providenciar a troca. Te retorno em 1h, ok?",
    Casual: "Cara, peço mil desculpas pela demora 😔 Tô priorizando seu caso agora, vou trocar o produto e te aviso em 1h.",
  },
};

const faqAnswers = [
  "Você tem 7 dias para testar todos os recursos da plataforma, sem cartão de crédito. Ao final, escolhe se quer continuar no Pacote Pequeno ou no Pacote Médio.",
  "Todos os planos incluem os canais disponíveis — WhatsApp, Instagram, Messenger, Telegram, e-mail, chat do site, TikTok e mais. A diferença está no número de inboxes e usuários incluídos.",
  "Sim. A IA Cosmos está disponível em todos os planos, com sugestões de resposta, análise de sentimento, resumo automático e tradução.",
  "Sim. Todo cliente novo tem um processo de implantação guiada com nossa equipe — setup gratuito incluído em ambos os planos. O Pacote Médio inclui onboarding prioritário.",
  "Sim. Temos integrações nativas com os principais CRMs e ERPs, além de API REST completa e webhooks para qualquer sistema.",
  "Suporte por chat e e-mail com SLA de 24h úteis no Pacote Pequeno. O Pacote Médio tem suporte prioritário com SLA de 8h. Enterprise conta com gerente dedicado e SLA de 4h.",
  "Sim. Infraestrutura em nuvem com criptografia em trânsito e em repouso, backups diários e conformidade com a LGPD.",
];

function setActive(buttons, active) {
  buttons.forEach((button) => {
    const on = button === active;
    button.classList.toggle("on", on);
    button.style.background = on ? ACCENT : "";
    button.style.color = on ? "white" : "";
    button.style.borderColor = on ? ACCENT : "";
  });
}

function initNav() {
  const nav = document.querySelector(".nav");
  const burger = document.querySelector(".nav-burger");
  if (!nav || !burger) return;

  // Build structured fullscreen mobile menu
  const mobile = document.createElement("div");
  mobile.className = "nav-mobile";
  mobile.hidden = true;
  mobile.setAttribute("role", "dialog");
  mobile.setAttribute("aria-modal", "true");
  mobile.setAttribute("aria-label", "Menu de navegação");

  // Head: brand clone + close button
  const mHead = document.createElement("div");
  mHead.className = "nav-mobile-head";
  const brandClone = nav.querySelector(".brand")?.cloneNode(true);
  if (brandClone) { brandClone.href = "#top"; mHead.append(brandClone); }
  const closeBtn = document.createElement("button");
  closeBtn.className = "nav-mobile-close";
  closeBtn.setAttribute("aria-label", "Fechar menu");
  closeBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
  mHead.append(closeBtn);
  mobile.append(mHead);

  // Links section
  const mLinks = document.createElement("nav");
  mLinks.className = "nav-mobile-links";
  document.querySelectorAll(".nav-links a").forEach((link) => mLinks.append(link.cloneNode(true)));
  mobile.append(mLinks);

  // CTA section
  const mCta = document.createElement("div");
  mCta.className = "nav-mobile-cta";
  mCta.innerHTML = `<a class="btn btn-ghost" href="#contact">Falar com especialista</a><a class="btn btn-primary" href="#pricing">Testar agora</a>`;
  mobile.append(mCta);

  // Append to body so it escapes nav's stacking context
  document.body.append(mobile);

  function openMenu() {
    mobile.hidden = false;
    burger.setAttribute("aria-expanded", "true");
    document.body.classList.add("menu-open");
  }

  function closeMenu() {
    mobile.hidden = true;
    burger.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
  }

  window.addEventListener("scroll", () => nav.classList.toggle("scrolled", window.scrollY > 12), { passive: true });
  burger.setAttribute("aria-expanded", "false");
  burger.addEventListener("click", () => mobile.hidden ? openMenu() : closeMenu());
  closeBtn.addEventListener("click", closeMenu);
  mobile.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !mobile.hidden) closeMenu();
  });
}

function initHeroChat() {
  const body = document.querySelector(".mock-chat .mc-body");
  const suggestion = body?.querySelector(".ai-suggest");
  if (!body || !suggestion) return;

  const messages = [
    ["them", "Oi, o sofá retrátil tá disponível?"],
    ["me", "Olá Maria! Sim, em pronta entrega 🛋️"],
    ["them", "Quanto fica à vista?"],
    ["me", "R$ 2.490 com 5% off via Pix 💜"],
  ];

  body.querySelectorAll(":scope > .bbl").forEach((bubble) => bubble.remove());
  let step = 0;
  let completed = [];

  function typeMessage() {
    if (step === 0) completed = [];
    body.querySelectorAll(":scope > .bbl").forEach((bubble) => bubble.remove());
    completed.forEach(([from, text]) => insertBubble(from, text));

    const [from, text] = messages[step];
    const bubble = insertBubble(from, "");
    let index = 0;
    const timer = setInterval(() => {
      bubble.textContent = text.slice(0, index);
      index += 1;
      if (index > text.length) {
        clearInterval(timer);
        completed.push(messages[step]);
        step = (step + 1) % messages.length;
        setTimeout(typeMessage, 1200);
      }
    }, 42);
  }

  function insertBubble(from, text) {
    const bubble = document.createElement("div");
    bubble.className = `bbl ${from}`;
    bubble.textContent = text;
    if (from === "me") bubble.style.background = ACCENT;
    body.insertBefore(bubble, suggestion);
    return bubble;
  }

  typeMessage();
}

function initAIPlayground() {
  const section = document.querySelector(".aip");
  if (!section) return;

  const blocks = section.querySelectorAll(".aip-controls .aip-block");
  const scenarioButtons = [...blocks[0].querySelectorAll("button")];
  const toneButtons = [...blocks[1].querySelectorAll("button")];
  const languageButtons = [...blocks[2].querySelectorAll("button")];
  const slider = blocks[3].querySelector("input");
  const toggleButtons = [...blocks[4].querySelectorAll(".tgl")];
  const keys = ["atraso", "frete", "upsell", "reclamacao"];
  let scenario = "atraso";
  let tone = "Amigável";
  let language = "Português";
  let translateOn = false;

  const sentimentSection = section.querySelector(".aip-sent-tag")?.closest(".aip-section");
  const summarySection = section.querySelector(".aip-summary")?.closest(".aip-section");
  const aiReply = section.querySelector(".aip-ai-reply");

  function update() {
    const data = scenarios[scenario];
    const color = data.sentiment < 30 ? "#DC2626" : data.sentiment < 60 ? "#F59E0B" : "#10B981";
    const label = data.sentiment < 30 ? "Negativo" : data.sentiment < 60 ? "Neutro" : "Positivo";

    section.querySelector(".aip-lang").textContent = `· ${language === "Português" ? "pt-BR" : language === "English" ? "en-US" : "es-AR"}`;
    section.querySelector(".aip-bbls .bbl.them").textContent = data.msg;
    section.querySelector(".aip-ai-h").lastChild.textContent = ` Cosmos sugere · tom ${tone.toLowerCase()}`;
    section.querySelector(".aip-ai-body").textContent = `"${responses[scenario][tone]}"`;
    section.querySelector(".aip-sent-tag").textContent = `${label} · ${data.sentimentTag}`;
    section.querySelector(".aip-sent-tag").style.cssText = `background:${color}1f;color:${color}`;
    section.querySelector(".aip-sent-fill").style.width = `${data.sentiment}%`;
    section.querySelector(".aip-sent-marker").style.cssText = `left:${data.sentiment}%;background:${color}`;
    section.querySelector(".aip-intent").textContent = `🎯 ${data.intent}`;
    section.querySelector(".aip-summary").textContent = data.summary;
    section.querySelector(".aip-next").lastChild.textContent = data.nextStep;

    const tagBox = section.querySelector(".aip-tags");
    tagBox.innerHTML = data.tags.map((tag) => `<span class="tag-pill" style="background:var(--accent-soft);color:var(--accent-ink)">${tag}</span>`).join("") +
      '<span class="tag-pill tag-add" style="border-style:dashed">+ adicionar</span>';
    updateTranslation();
  }

  function updateTranslation() {
    const bubbles = section.querySelector(".aip-bbls");
    const message = bubbles.querySelector(".bbl.them");
    const actions = section.querySelector(".aip-ai-actions");
    bubbles.querySelector(".aip-translate")?.remove();
    actions.querySelector(".aip-translate-action")?.remove();
    if (!translateOn || language === "Português") return;

    const translated = document.createElement("div");
    translated.className = "aip-translate";
    translated.innerHTML = `↻ Traduzido para o atendente: <em>"${scenarios[scenario].msg}"</em>`;
    message.insertAdjacentElement("afterend", translated);

    const action = document.createElement("button");
    action.className = "aip-translate-action";
    action.textContent = "Traduzir";
    actions.append(action);
  }

  scenarioButtons.forEach((button, index) => button.addEventListener("click", () => {
    scenario = keys[index];
    setActive(scenarioButtons, button);
    update();
  }));
  toneButtons.forEach((button) => button.addEventListener("click", () => {
    tone = button.textContent.trim();
    setActive(toneButtons, button);
    update();
  }));
  languageButtons.forEach((button) => button.addEventListener("click", () => {
    language = button.textContent.trim();
    setActive(languageButtons, button);
    update();
  }));
  slider?.addEventListener("input", () => {
    slider.style.setProperty("--p", `${slider.value}%`);
    blocks[3].querySelector(".aip-temp-val").textContent = `${slider.value}%`;
  });

  const toggleTargets = [aiReply, sentimentSection, summarySection, null];
  toggleButtons.forEach((button, index) => button.addEventListener("click", () => {
    const on = !button.classList.contains("on");
    button.classList.toggle("on", on);
    button.style.background = on ? ACCENT : "";
    button.setAttribute("aria-pressed", String(on));
    if (toggleTargets[index]) toggleTargets[index].hidden = !on;
    if (index === 3) {
      translateOn = on;
      updateTranslation();
    }
  }));

  const useButton = section.querySelector(".aip-ai-actions .btn-pri");
  useButton?.addEventListener("click", () => {
    const original = useButton.textContent;
    useButton.textContent = "✓ enviado";
    setTimeout(() => { useButton.textContent = original; }, 1400);
  });
}

function initPricing() {
  const buttons = [...document.querySelectorAll(".pricing-toggle button")];
  const prices = [...document.querySelectorAll(".plan .price-num")];
  const notes = [...document.querySelectorAll(".plan .price-note")];
  if (buttons.length < 2 || prices.length < 3) return;

  function update(annual) {
    setActive(buttons, annual ? buttons[0] : buttons[1]);
    prices[0].textContent = annual ? "R$ 499" : "R$ 699";
    prices[1].textContent = annual ? "R$ 999" : "R$ 1.199";
    prices[2].textContent = "Sob consulta";
    if (notes[0]) notes[0].textContent = annual ? "R$ 5.988 cobrado anualmente" : "ou R$ 5.988/ano no plano anual";
    if (notes[1]) notes[1].textContent = annual ? "R$ 11.988 cobrado anualmente" : "ou R$ 11.988/ano no plano anual";
  }
  buttons[0].addEventListener("click", () => update(true));
  buttons[1].addEventListener("click", () => update(false));
  update(true);
  document.querySelectorAll(".plan > .btn").forEach((button) => button.addEventListener("click", () => {
    document.querySelector("#contact")?.scrollIntoView({ behavior: "smooth" });
  }));
}

function initFAQ() {
  const items = [...document.querySelectorAll(".faq-item")];
  items.forEach((item, index) => {
    const button = item.querySelector(".faq-q");
    const toggle = item.querySelector(".faq-toggle");
    button.addEventListener("click", () => {
      const opening = !item.classList.contains("open");
      items.forEach((other) => {
        other.classList.remove("open");
        other.querySelector(".faq-a")?.remove();
        other.querySelector(".faq-toggle").innerHTML = '<i class="fas fa-plus"></i>';
      });
      if (!opening) return;
      item.classList.add("open");
      toggle.innerHTML = '<i class="fas fa-minus"></i>';
      const answer = document.createElement("div");
      answer.className = "faq-a";
      answer.textContent = faqAnswers[index];
      item.append(answer);
    });
  });
}

function initCopyButton() {
  const button = document.querySelector(".ic-copy");
  const code = document.querySelector(".ic-code");
  button?.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(code?.innerText || ""); } catch {}
    button.textContent = "✓ copiado";
    setTimeout(() => { button.textContent = "copiar payload"; }, 1600);
  });
}

function initContactForm() {
  const form = document.querySelector(".contact-form");
  if (!form || form.dataset.ready) return;
  form.dataset.ready = "true";
  const initialMarkup = form.innerHTML;
  const inputs = [...form.querySelectorAll("input")];
  const names = ["nome", "email", "empresa", "telefone"];
  inputs.forEach((input, index) => { input.name = names[index]; });
  const textarea = form.querySelector("textarea");
  if (textarea) textarea.name = "mensagem";

  form.querySelectorAll(".cf-seg button").forEach((button) => button.addEventListener("click", () => {
    setActive([...button.parentElement.children], button);
  }));
  form.querySelectorAll(".cf-chip").forEach((button) => button.addEventListener("click", () => button.classList.toggle("on")));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    form.querySelectorAll(".cf-err, .cf-send-err").forEach((el) => el.remove());
    const values = Object.fromEntries(new FormData(form));
    const checks = [
      [inputs[0], values.nome?.trim() ? "" : "Como podemos te chamar?"],
      [inputs[1], /.+@.+\..+/.test(values.email || "") ? "" : "E-mail inválido"],
      [inputs[2], values.empresa?.trim() ? "" : "Qual sua empresa?"],
    ];
    const invalid = checks.filter(([, message]) => message);
    invalid.forEach(([input, message]) => {
      const error = document.createElement("span");
      error.className = "cf-err";
      error.textContent = ` · ${message}`;
      input.closest(".cf-field").querySelector(".cf-label").append(error);
    });
    if (invalid.length) {
      invalid[0][0].focus();
      return;
    }

    const equipe = form.querySelector(".cf-seg button.on")?.textContent?.trim() || "";
    const canais = [...form.querySelectorAll(".cf-chip.on")].map((b) => b.textContent.trim()).join(", ");
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Enviando…"; }

    try {
      await fetch(WEBHOOK_URL, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          nome: values.nome?.trim() ?? "",
          email: values.email?.trim() ?? "",
          empresa: values.empresa?.trim() ?? "",
          telefone: values.telefone?.trim() ?? "",
          equipe,
          canais,
          mensagem: values.mensagem?.trim() ?? "",
        }).toString(),
      });
    } catch (_) {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Solicitar demo gratuita"; }
      const errEl = document.createElement("p");
      errEl.className = "cf-send-err";
      errEl.textContent = "Erro de rede. Tente novamente ou fale pelo WhatsApp: +55 21 96662-1486.";
      submitBtn?.insertAdjacentElement("beforebegin", errEl);
      return;
    }

    form.classList.add("is-success");
    form.innerHTML = `<div class="cf-success">
      <div class="cf-success-ico" style="background:var(--accent-soft);color:var(--accent)">✓</div>
      <h3>Recebemos seu pedido!</h3>
      <p>Em até 1 dia útil, um especialista da Stardev vai entrar em contato pra agendar sua demo personalizada.</p>
      <p class="cf-success-meta">Conferindo enquanto isso: <a href="#features">funcionalidades</a> · <a href="#pricing">planos</a></p>
      <button type="button" class="btn btn-ghost">Enviar outro</button>
    </div>`;
    form.querySelector("button").addEventListener("click", () => {
      form.classList.remove("is-success");
      form.innerHTML = initialMarkup;
      delete form.dataset.ready;
      initContactForm();
    });
  });
}

function initCtas() {
  const ctaLinks = document.querySelectorAll(".cta-actions a");
  if (ctaLinks[0]) ctaLinks[0].href = "#pricing";
  if (ctaLinks[1]) ctaLinks[1].href = "#contact";
}

document.addEventListener("DOMContentLoaded", () => {
  initNav();
  initHeroChat();
  initAIPlayground();
  initPricing();
  initFAQ();
  initCopyButton();
  initContactForm();
  initCtas();
});
