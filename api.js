(() => {
  'use strict';
  const sidebar = document.querySelector('.api-sidebar');
  const overlay = document.querySelector('.api-overlay');
  const openButton = document.querySelector('.api-menu-button');
  const closeButton = document.querySelector('.api-sidebar-close');
  const links = [...document.querySelectorAll('.api-sidebar a[href^="#"]')];
  const sections = links.map(link => document.querySelector(link.getAttribute('href'))).filter(Boolean);

  const close = () => {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('open');
    openButton?.setAttribute('aria-expanded', 'false');
  };
  const open = () => {
    sidebar?.classList.add('open');
    overlay?.classList.add('open');
    openButton?.setAttribute('aria-expanded', 'true');
  };
  openButton?.addEventListener('click', open);
  closeButton?.addEventListener('click', close);
  overlay?.addEventListener('click', close);
  links.forEach(link => link.addEventListener('click', close));

  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    links.forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${visible.target.id}`));
  }, { rootMargin:'-18% 0px -70% 0px', threshold:[0, .2, .5] });
  sections.forEach(section => observer.observe(section));

  document.querySelectorAll('pre').forEach(block => {
    const button = document.createElement('button');
    button.className = 'copy-code';
    button.type = 'button';
    button.textContent = 'Copiar';
    button.addEventListener('click', async () => {
      await navigator.clipboard.writeText(block.querySelector('code')?.innerText || block.innerText);
      button.textContent = 'Copiado';
      window.setTimeout(() => { button.textContent = 'Copiar'; }, 1600);
    });
    block.appendChild(button);
  });
})();
