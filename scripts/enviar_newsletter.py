#!/usr/bin/env python3
"""Prensa Autômata — manda a edição mais recente por email via Buttondown.

Uso:  python3 scripts/enviar_newsletter.py [--saida ARQUIVO.html] [--sem-api]

Lê ultima.json, transforma edicoes/<edição>.html numa versão para email
(estilos inline, largura máxima de 640px, links absolutos) e cria o email
no Buttondown com o slug prensa-<edição>. Se o slug já existir, encerra sem erro.

Ambiente:
  BUTTONDOWN_API_KEY   chave da API (secret do repositório; nunca em arquivo)
  NEWSLETTER_MODO      "rascunho" (padrão, cria draft) ou "envio" (manda para os assinantes)

--saida grava o HTML gerado (a Action guarda esse arquivo como artifact).
--sem-api só gera o HTML, sem falar com o Buttondown (para testar localmente).
Depende de beautifulsoup4 e css-inline (scripts/requirements-newsletter.txt).
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

import css_inline
from bs4 import BeautifulSoup

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://prensaautomata.com/"
API = "https://api.buttondown.com/v1/emails"
VERSAO_API = "2026-04-01"
LIMITE_ASSUNTO = 90

# paleta do :root do site, com valores fixos (clientes de email não entendem variáveis CSS)
BG, PAPEL, TINTA, SECUNDARIO, LINHA, DESTAQUE = "#f6f8fb", "#ffffff", "#0f1a2c", "#56627a", "#d7deea", "#1e3a9e"
SERIF = 'Georgia,"Times New Roman",serif'
MONO = "ui-monospace,Menlo,monospace"

# Mesmo desenho do estilo.css, reduzido ao que os clientes de email aceitam (sem grid,
# flex, contadores nem variáveis). O css-inline copia tudo para atributos style.
CSS = f"""
body{{margin:0;padding:0;background:{BG}}}
.fundo{{background:{BG}}}
.fundo-td{{padding:24px 12px}}
.folha{{width:100%;max-width:640px;background:{PAPEL};border-top:1px solid {DESTAQUE};border-bottom:1px solid {LINHA}}}
.cabeca{{padding:28px 28px 18px;text-align:center;border-bottom:1px solid {LINHA}}}
.mast{{margin:0;font:normal 40px/1 {SERIF};letter-spacing:-.02em;color:{TINTA}}}
.mast a{{color:{TINTA};text-decoration:none}}
.sub{{margin:10px 0 10px;font:400 11px/1.4 {MONO};letter-spacing:.2em;text-transform:uppercase;color:{DESTAQUE}}}
.meta{{margin:0;font:11.5px/1.5 {MONO};color:{SECUNDARIO}}}
.miolo{{padding:8px 28px 12px;font:17px/1.6 {SERIF};color:{TINTA}}}
.pe{{padding:14px 28px 22px;border-top:1px solid {DESTAQUE};font:11.5px/1.65 {MONO};color:{SECUNDARIO}}}
.pe a{{color:{SECUNDARIO}}}
a{{color:{TINTA};text-decoration:underline}}
p{{margin:0 0 12px}}
h2{{margin:36px 0 14px;padding-bottom:6px;border-bottom:1px solid {LINHA};font:500 11px/1.4 {MONO};letter-spacing:.16em;text-transform:uppercase;color:{DESTAQUE}}}
h3{{margin:24px 0 6px;font:normal 23px/1.2 {SERIF};letter-spacing:-.01em;color:{TINTA}}}
h4{{margin:18px 0 6px;padding-bottom:6px;border-bottom:1px solid {DESTAQUE};font:500 11px/1.4 {MONO};letter-spacing:.08em;text-transform:uppercase;color:{TINTA}}}
.manchete h3{{margin:20px 0 14px;font-size:31px;line-height:1.1;letter-spacing:-.02em}}
.lede{{font-size:18px;line-height:1.55}}
.src{{font:12px/1.55 {MONO};color:{SECUNDARIO}}}
.src a{{color:{SECUNDARIO}}}
.teste{{margin:18px 0 8px;padding:8px 12px;border:1px solid {LINHA};background:{BG};font:11.5px/1.5 {MONO};color:{DESTAQUE};text-align:center}}
.leitura{{padding:16px 18px 6px;border:1px solid {LINHA};background:{BG}}}
.leitura h3{{margin-top:0}}
.autor{{margin:0 0 12px;font:12px/1.5 {MONO};color:{SECUNDARIO}}}
ul{{margin:0;padding:0;list-style:none}}
li{{padding:7px 0;border-bottom:1px solid {LINHA};font-size:15px;line-height:1.4}}
.y{{margin:0 0 8px;font:12px/1.5 {MONO};color:{SECUNDARIO}}}
.poem{{margin:10px 0 14px;padding-left:16px;border-left:1px solid {DESTAQUE};font-style:italic}}
.resumo{{margin:0 0 18px}}
.mercado{{margin:0 0 20px}}
.mercado h3{{font-size:20px}}
.ticker{{margin:0 0 12px}}
.ticker{{width:100%;border-collapse:collapse}}
.ticker td{{padding:6px 0;border-top:1px solid {LINHA};vertical-align:baseline}}
.ticker .k{{font:10.5px/1.4 {MONO};letter-spacing:.08em;text-transform:uppercase;color:{SECUNDARIO}}}
.ticker .v{{text-align:right;font:500 15px/1.4 {MONO};color:{TINTA}}}
.regioes{{margin:0 0 12px}}
.regioes div{{padding:8px 0;border-bottom:1px solid {LINHA}}}
.regioes dt{{font:500 12px/1.8 {MONO};letter-spacing:.04em;color:{DESTAQUE}}}
.regioes dd{{margin:0;font-size:16px;line-height:1.5}}
.nav-ed{{margin:32px 0 8px;padding:10px 0;border-top:1px solid {LINHA};border-bottom:1px solid {LINHA};font:500 12px/1.8 {MONO}}}
.nav-ed a{{color:{DESTAQUE};text-decoration:none}}
"""


def erro(msg):
    """Mensagem que aparece destacada no resumo da Action, e saída com falha."""
    print(f"::error::{msg}")
    sys.exit(1)


def ler_edicao():
    with open(os.path.join(RAIZ, "ultima.json"), encoding="utf-8") as f:
        slug = json.load(f)["edicao"]
    caminho = os.path.join(RAIZ, "edicoes", f"{slug}.html")
    if not os.path.exists(caminho):
        erro(f"ultima.json aponta para {slug}, mas edicoes/{slug}.html não existe")
    with open(caminho, encoding="utf-8") as f:
        pagina = f.read()
    with open(os.path.join(RAIZ, "edicoes", f"{slug}.json"), encoding="utf-8") as f:
        ed = json.load(f)
    return slug, pagina, ed


def assunto(slug, ed):
    """'Prensa Autômata · Manchete…', com até ~90 caracteres."""
    prefixo = "Prensa Autômata · "
    manchete = " ".join(ed["manchete"]["titulo"].split())
    cabe = LIMITE_ASSUNTO - len(prefixo)
    if len(manchete) > cabe:
        corte = manchete[:cabe - 1]
        if " " in corte:
            corte = corte.rsplit(" ", 1)[0]
        manchete = corte.rstrip(" ,;:—-·") + "…"
    return prefixo + manchete


def versao_email(pagina, slug, titulo):
    """HTML da edição -> HTML para email: só o conteúdo, estilos inline, links absolutos."""
    url = f"{SITE}edicoes/{slug}.html"
    sopa = BeautifulSoup(pagina, "html.parser")
    main = sopa.find("main")

    # cabeçalho: só a data e a tiragem do <p class="meta">, sem o link de assinatura
    meta = " · ".join(s.get_text(" ", strip=True) for s in main.select("header .meta > span")
                      if not s.find(class_="assinar-link"))
    for el in main.select("header, footer, .assinar-pe, script, style, noscript, form, input, button, "
                          "select, textarea, iframe, svg, details, .recente"):
        el.decompose()
    # o poema usa white-space:pre-line no site; no email as quebras viram <br>
    for poema in main.select(".poem"):
        linhas = poema.get_text().split("\n")
        poema.clear()
        for i, linha in enumerate(linhas):
            if i:
                poema.append(sopa.new_tag("br"))
            poema.append(linha)
    # painel de números (grid no site) vira tabela de duas colunas: rótulo à esquerda, valor à direita
    for painel in main.select(".ticker"):
        tabela = sopa.new_tag("table", attrs={"class": "ticker", "role": "presentation", "width": "100%",
                                              "cellpadding": "0", "cellspacing": "0", "border": "0"})
        for celula in painel.find_all("div", recursive=False):
            tr = sopa.new_tag("tr")
            for classe, el in (("k", celula.find("span")), ("v", celula.find("b"))):
                td = sopa.new_tag("td", attrs={"class": classe})
                td.string = el.get_text(strip=True) if el else ""
                tr.append(td)
            tabela.append(tr)
        painel.replace_with(tabela)
    # no site os links da navegação ficam lado a lado (flex); no email, separados por " · "
    for nav in main.select(".nav-ed"):
        links = nav.find_all("a")
        nav.clear()
        for i, a in enumerate(links):
            if i:
                nav.append(" · ")
            nav.append(a)
    # tags do HTML5 que alguns clientes de email ignoram viram <div>
    for el in main.find_all(["section", "nav", "article", "aside"]):
        el.name = "div"
    for el in main.find_all(attrs={"aria-label": True}):
        del el["aria-label"]
    for a in main.find_all("a", href=True):
        a["href"] = urllib.parse.urljoin(url, a["href"])
    conteudo = main.decode_contents().strip()

    e = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<style>{CSS}</style>
</head>
<body>
<table role="presentation" class="fundo" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{BG}">
<tr><td class="fundo-td" align="center">
<table role="presentation" class="folha" width="640" cellpadding="0" cellspacing="0" border="0" bgcolor="{PAPEL}" align="center">
<tr><td class="cabeca" align="center">
<h1 class="mast"><a href="{url}">Prensa Autômata</a></h1>
<p class="sub">jornal diário produzido por IA</p>
<p class="meta">{e(meta)}</p>
</td></tr>
<tr><td class="miolo">
{conteudo}
</td></tr>
<tr><td class="pe">
Prensa Autômata · jornal diário produzido por IA · os textos são resumos com link para as fontes originais; erros podem acontecer, confira sempre a fonte.<br>
<a href="{url}">Ler no site</a> · <a href="{SITE}sobre.html">Sobre a Prensa</a> · <a href="{{{{ unsubscribe_url }}}}">Cancelar assinatura</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
    # o link de descadastro é variável do Buttondown; o inliner não pode reescrevê-lo
    return css_inline.CSSInliner(keep_style_tags=False, load_remote_stylesheets=False).inline(doc)


def corpo_buttondown(doc):
    """O Buttondown recebe só o conteúdo do <body>, marcado como HTML (modo 'fancy')."""
    corpo = BeautifulSoup(doc, "html.parser").body.decode_contents().strip()
    return "<!-- buttondown-editor-mode: fancy -->\n" + corpo


def chamar(metodo, url, chave, dados=None, extra=None):
    cab = {"Authorization": f"Token {chave}", "X-API-Version": VERSAO_API,
           "Content-Type": "application/json", "Accept": "application/json"}
    cab.update(extra or {})
    req = urllib.request.Request(url, method=metodo, headers=cab,
                                 data=json.dumps(dados).encode() if dados is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as ex:
        detalhe = ex.read().decode("utf-8", "replace")[:2000]
        erro(f"Buttondown respondeu {ex.code} em {metodo} {url}: {detalhe}")
    except urllib.error.URLError as ex:
        erro(f"Não foi possível falar com o Buttondown ({metodo} {url}): {ex.reason}")


def ja_existe(slug, chave):
    """Percorre a lista de emails (a API não filtra por slug) procurando o slug."""
    url = API + "?" + urllib.parse.urlencode({"ordering": "-creation_date", "excluded_fields": "body"})
    while url:
        pagina = chamar("GET", url, chave)
        for email in pagina.get("results", []):
            if email.get("slug") == slug and email.get("status") != "deleted":
                return email
        url = pagina.get("next")
    return None


def esperar_site(url, minutos=5):
    """Espera o GitHub Pages publicar a edição, para o 'Ler no site' não cair num 404."""
    fim = time.time() + minutos * 60
    while time.time() < fim:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20):
                return True
        except Exception:
            time.sleep(20)
    print(f"::warning::{url} ainda não respondeu após {minutos} min; seguindo assim mesmo")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", help="grava aqui o HTML gerado para o email")
    ap.add_argument("--sem-api", action="store_true", help="só gera o HTML, sem chamar o Buttondown")
    args = ap.parse_args()

    slug, pagina, ed = ler_edicao()
    titulo = assunto(slug, ed)
    doc = versao_email(pagina, slug, titulo)
    print(f"edição: {slug}\nassunto ({len(titulo)} caracteres): {titulo}")
    if args.saida:
        os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"HTML gravado em {args.saida}")
    if args.sem_api:
        return

    chave = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not chave:
        erro("BUTTONDOWN_API_KEY não definida (Settings → Secrets and variables → Actions → Secrets)")
    modo = (os.environ.get("NEWSLETTER_MODO") or "rascunho").strip().lower()
    if modo not in ("rascunho", "envio"):
        erro(f'NEWSLETTER_MODO="{modo}" inválido; use "rascunho" ou "envio"')

    slug_email = f"prensa-{slug}"
    existente = ja_existe(slug_email, chave)
    if existente:
        print(f"slug {slug_email} já existe no Buttondown (id {existente.get('id')}, "
              f"status {existente.get('status')}); nada a fazer")
        return

    esperar_site(f"{SITE}edicoes/{slug}.html")
    dados = {"subject": titulo, "body": corpo_buttondown(doc), "slug": slug_email, "template": "naked",
             "status": "about_to_send" if modo == "envio" else "draft"}
    extra = {"X-Buttondown-Live-Dangerously": "true"} if modo == "envio" else None
    print(f"modo: {modo} → status {dados['status']}")
    r = chamar("POST", API, chave, dados, extra)
    print(f"criado: id {r.get('id')} · status {r.get('status')} · slug {r.get('slug')}")
    if r.get("id"):
        print(f"conferir: https://buttondown.com/emails/{r['id']}")


if __name__ == "__main__":
    main()
