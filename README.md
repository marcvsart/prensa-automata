# Prensa Autômata

Jornal diário produzido por IA. Cada edição é um arquivo JSON em `edicoes/`; o `build.py` transforma esse JSON na página, e o GitHub Pages publica.

## O que tem aqui

| Arquivo | Para quê |
|---|---|
| `edicoes/AAAA-MM-DD.json` | Conteúdo de cada edição da manhã (a tarefa das 6h escreve este arquivo) |
| `edicoes/AAAA-MM-DD-noite.json` | Conteúdo de cada edição da noite (a tarefa das 18h), mais curta nas notícias e mais funda nas leituras, sem disco, poema nem esporte |
| `edicoes/AAAA-MM-DD.html` | Página de cada edição, gerada pelo build |
| `index.html` | Capa do site: sempre a edição mais recente |
| `edicoes/index.html` | Arquivo com todas as edições, refeito a cada build |
| `sobre.html` | Página "Sobre a Prensa", refeita a cada build (o texto fica no `build.py`); link no rodapé de todas as páginas |
| `assinar.html` | Página "Receba a Prensa por email", com o formulário do Buttondown, refeita a cada build; link no cabeçalho e antes do rodapé de todas as páginas |
| `arauto.svg` | O arauto da Prensa (linotipo robô em pixel art), no topo da página Sobre |
| `build.py` | Monta a página a partir do JSON. Só Python padrão, sem instalar nada |
| `estilo.css` | Visual do jornal (layout, fontes, cores, modo escuro) |
| `registro.json` | Discos, poemas e leituras já publicados, para não repetir |
| `CNAME` | Domínio prensaautomata.com |
| `PROMPT-TAREFA.md` | Instrução da edição da manhã |
| `PROMPT-TAREFA-NOITE.md` | Cópia do prompt da edição da noite (a Routine guarda o próprio texto) |
| `.nojekyll` | Faz o GitHub Pages servir os arquivos como estão, sem passar pelo Jekyll |
| `.github/workflows/newsletter.yml` | Quando uma edição nova chega à main (muda o `ultima.json`) ou à mão, manda a edição por email via Buttondown |
| `scripts/enviar_newsletter.py` | Transforma a edição numa versão para email e cria o email no Buttondown (usado pela Action acima) |
| `.github/workflows/verificar.yml` | A cada push, confere se os JSON são válidos e se a edição mais recente monta sem erro |

A edição de teste (Tiragem Nº 0, 29/09/2026) já está incluída como modelo.

## Dependências

Nenhuma além do Python 3 (biblioteca padrão) e do git. Para criar o repositório e publicar pela linha de comando, instale o GitHub CLI: `brew install gh` e depois `gh auth login`.

## Configuração, uma vez só

1. **Repositório.** Crie um repositório público no GitHub (por exemplo, `prensa-automata`) e suba estes arquivos.
2. **GitHub Pages.** Em Settings → Pages, escolha "Deploy from a branch", branch `main`, pasta `/ (root)`.
3. **Domínio.** No registrador do prensaautomata.com, crie registros A apontando para os IPs do GitHub Pages (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) e um CNAME de `www` para `SEU-USUARIO.github.io`. Depois, em Settings → Pages, confirme o domínio e ative "Enforce HTTPS".
4. **Acesso para a tarefa.** Clone o repositório na máquina onde o Cowork roda e deixe o `git push` funcionando sem pedir senha. O caminho mais seguro é um token de acesso *fine-grained* com permissão só de escrita em conteúdo e só neste repositório (ou `gh auth login`).
5. **Tarefa agendada.** No Cowork, crie uma tarefa diária (6h30) com o texto de `PROMPT-TAREFA.md`, trocando `CAMINHO_DO_REPOSITORIO` pelo caminho da pasta clonada.

## Testar localmente

```
python3 build.py              # monta a edição mais recente
python3 build.py 2026-09-29   # monta a manhã de uma data
python3 build.py 2026-09-29-noite   # monta a noite de uma data
```

Abra `index.html` no navegador para conferir.

## Audiência

As visitas são contadas pelo GoatCounter (sem cookies, sem dados pessoais), em https://prensaautomata.goatcounter.com. O script fica no cabeçalho gerado pelo `build.py`, então entra em todas as páginas.

## Navegação entre edições

No fim de cada edição há um link para a anterior ("Edição de ontem", ou "Edição anterior · DD/MM" se algum dia ficou sem edição) e outro para `edicoes/index.html`, o arquivo com todas as edições, separadas em manhã e noite. A manhã e a noite têm numeração própria (`tiragem` e `tiragem_noite` no `registro.json`); a noite aponta para "Edição da manhã", e a manhã seguinte para "Edição de ontem à noite". Esses links não ficam defasados: a edição anterior de uma página nunca muda, e o arquivo é refeito a cada build.

## Newsletter (Buttondown)

A Action `newsletter.yml` roda separada da geração: quando um push na `main` muda o `ultima.json`, ela lê a edição, monta uma versão para email (estilos inline, até 640px, links absolutos, sem scripts nem formulário) e cria o email no Buttondown com o slug `prensa-AAAA-MM-DD` (por exemplo, `prensa-2026-10-05`). Se o slug já existe, ela para sem erro, então rodar de novo não duplica o envio. Só a Tiragem da manhã vai por email (o plano do Buttondown permite um envio por dia): numa edição noturna a Action termina sem erro e sem criar email, e o fim de cada email avisa que as noturnas estão no site.

- **Chave:** secret do repositório `BUTTONDOWN_API_KEY` (Settings → Secrets and variables → Actions → Secrets). Nunca em arquivo.
- **Modo:** variável do repositório `NEWSLETTER_MODO` (mesma tela, aba Variables). `rascunho` (padrão, se a variável não existir) cria um draft para conferir no Buttondown; `envio` manda para os assinantes.
- **Rodar à mão:** aba Actions → Newsletter → Run workflow. O campo *modo* deixa forçar `rascunho` ou `envio` só naquela execução; em branco, vale a variável.
- **Ver o email sem abrir o Buttondown:** cada execução guarda o HTML gerado como artifact `newsletter-email`, no resumo da execução.
- **Testar localmente:** `pip install -r scripts/requirements-newsletter.txt` e `python3 scripts/enviar_newsletter.py --sem-api --saida /tmp/email.html`.

## Mudar o visual

Altere só o `estilo.css`. A estrutura dos blocos fica no `build.py`; se criar ou remover um bloco, atualize também o `PROMPT-TAREFA.md` e a edição modelo em `edicoes/`.
