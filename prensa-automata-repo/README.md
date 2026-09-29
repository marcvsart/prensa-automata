# Prensa Autômata

Jornal diário produzido por IA. Cada edição é um arquivo JSON em `edicoes/`; o `build.py` transforma esse JSON na página, e o GitHub Pages publica.

## O que tem aqui

| Arquivo | Para quê |
|---|---|
| `edicoes/AAAA-MM-DD.json` | Conteúdo de cada edição (a tarefa diária escreve este arquivo) |
| `edicoes/AAAA-MM-DD.html` | Página de cada edição, gerada pelo build |
| `index.html` | Capa do site: sempre a edição mais recente |
| `build.py` | Monta a página a partir do JSON. Só Python padrão, sem instalar nada |
| `estilo.css` | Visual do jornal (layout, fontes, cores, modo escuro) |
| `registro.json` | Discos, poemas e leituras já publicados, para não repetir |
| `CNAME` | Domínio prensaautomata.com |
| `PROMPT-TAREFA.md` | Instrução da tarefa agendada no Cowork |

A edição de teste (Tiragem Nº 0, 29/09/2026) já está incluída como modelo.

## Configuração, uma vez só

1. **Repositório.** Crie um repositório público no GitHub (por exemplo, `prensa-automata`) e suba estes arquivos.
2. **GitHub Pages.** Em Settings → Pages, escolha "Deploy from a branch", branch `main`, pasta `/ (root)`.
3. **Domínio.** No registrador do prensaautomata.com, crie registros A apontando para os IPs do GitHub Pages (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) e um CNAME de `www` para `SEU-USUARIO.github.io`. Depois, em Settings → Pages, confirme o domínio e ative "Enforce HTTPS".
4. **Acesso para a tarefa.** Clone o repositório na máquina onde o Cowork roda e deixe o `git push` funcionando sem pedir senha. O caminho mais seguro é um token de acesso *fine-grained* com permissão só de escrita em conteúdo e só neste repositório (ou `gh auth login`).
5. **Tarefa agendada.** No Cowork, crie uma tarefa diária (sugestão: 7h) com o texto de `PROMPT-TAREFA.md`, trocando `CAMINHO_DO_REPOSITORIO` pelo caminho da pasta clonada.

## Testar localmente

```
python3 build.py              # monta a edição mais recente
python3 build.py 2026-09-29   # monta uma data específica
```

Abra `index.html` no navegador para conferir.

## Mudar o visual

Altere só o `estilo.css`. A estrutura dos blocos fica no `build.py`; se criar ou remover um bloco, atualize também o `PROMPT-TAREFA.md` e a edição modelo em `edicoes/`.
