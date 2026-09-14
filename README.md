# Starchats Landing Page

Landing page estatica da Starchats, preparada para publicacao no GitHub Pages.

## Visualizar localmente

Na raiz do projeto, execute:

```powershell
python -m http.server 8000
```

Depois acesse `http://localhost:8000`.

## Publicar no GitHub Pages

1. Crie um repositorio vazio no GitHub.
2. Conecte este projeto ao repositorio e envie a branch `main`:

```powershell
git add .
git commit -m "Prepare landing page for GitHub Pages"
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
git push -u origin main
```

3. No GitHub, abra **Settings > Pages**.
4. Em **Build and deployment**, escolha **Deploy from a branch**.
5. Selecione a branch `main`, a pasta `/ (root)` e salve.

O site sera publicado em:

```text
https://SEU-USUARIO.github.io/SEU-REPOSITORIO/
```

## Estrutura

- `index.html`: estrutura e conteudo da landing page.
- `style.css`: estilos e responsividade.
- `script.js`: menu mobile e ano automatico do rodape.
- `docs/`: rotas canonicas da central de documentacao.
- `help.js`: conteudo e renderizacao dos artigos.
- `help.css`: identidade visual e responsividade da documentacao.
- `api.js` e `api.css`: navegacao, sidebar e estilos da referencia da API.
- `hc/` e demais aliases: redirecionamentos das URLs legadas do produto para `/docs/...`.
- `logo2.png` e `favicon.png`: identidade visual.
- `.nojekyll`: impede processamento desnecessario pelo Jekyll.

## Documentacao

A pagina principal fica em `https://starchats.com.br/docs/`. Cada artigo possui uma rota
canonica propria. Os enderecos antigos usados pelo aplicativo continuam funcionando por meio
de redirecionamentos estaticos com fallback em `404.html`.
