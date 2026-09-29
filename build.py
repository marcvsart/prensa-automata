#!/usr/bin/env python3
"""Prensa Autômata — monta a edição a partir de edicoes/AAAA-MM-DD.json.

Uso:  python3 build.py            (monta a edição mais recente)
      python3 build.py 2026-09-29 (monta uma data específica)

Gera edicoes/AAAA-MM-DD.html, copia a mais recente para index.html
e refaz edicoes/index.html (arquivo com todas as edições).
Só usa a biblioteca padrão do Python.
"""
import glob, html, json, os, sys
from datetime import date

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIAS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

e = html.escape

def data_extenso(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month-1]} de {d.year}"

def data_curta(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS_CURTOS[d.weekday()]} · {d.day:02d}/{d.month:02d}/{d.year}"

def paragrafos(texto, classe=""):
    if isinstance(texto, str):
        texto = [texto]
    c = f' class="{classe}"' if classe else ""
    return "\n".join(f"<p{c}>{e(p)}</p>" for p in texto if p)

def fontes(lista, prefixo=""):
    if not lista and not prefixo:
        return ""
    links = " · ".join(f'<a href="{e(f["url"], quote=True)}">{e(f["nome"])}</a>' for f in (lista or []))
    miolo = " · ".join(x for x in [e(prefixo) if prefixo else "", links] if x)
    return f'<p class="src">{miolo}</p>'

def noticia(n):
    return f"<h3>{e(n['titulo'])}</h3>\n{paragrafos(n['texto'])}\n{fontes(n.get('fontes'))}"

def secao(id_, rotulo, corpo, classe=""):
    c = f' class="{classe}"' if classe else ""
    h2 = f"<h2>{e(rotulo)}</h2>\n" if rotulo else ""
    return f'<section id="{id_}"{c}>\n{h2}{corpo}\n</section>'

def leitura(l):
    return (f'<div class="leitura">\n<h3>{e(l["titulo"])}</h3>\n'
            f'<p class="autor">{e(l["autor"])}</p>\n{paragrafos(l["texto"])}\n{fontes(l.get("fontes"))}\n</div>')

def ticker(painel):
    celulas = "\n".join(f"<div><span>{e(k)}</span><b>{e(v)}</b></div>" for k, v in painel)
    return f'<div class="ticker">\n{celulas}\n</div>'

def mercado(nome, m):
    return (f'<div class="mercado">\n<h3>{e(nome)}</h3>\n{ticker(m["painel"])}\n'
            f'{paragrafos(m["texto"])}\n{fontes(m.get("fontes"))}\n</div>')

REG = ('<svg class="reg {lado}" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="5.5" '
       'fill="none" stroke="currentColor"/><path d="M10 0v20M0 10h20" stroke="currentColor"/></svg>')

def navegacao(atual, arquivo):
    """Links fixos no fim da edição: a anterior (que nunca muda) e o arquivo completo."""
    anteriores = [a for a in arquivo if a < atual]
    itens = []
    if anteriores:
        ant = max(anteriores)
        if (date.fromisoformat(atual) - date.fromisoformat(ant)).days == 1:
            rotulo = "← Edição de ontem"
        else:
            d = date.fromisoformat(ant)
            rotulo = f"← Edição anterior · {d.day:02d}/{d.month:02d}"
        itens.append(f'<a href="edicoes/{ant}.html">{e(rotulo)}</a>')
    itens.append('<a href="edicoes/index.html">Todas as edições →</a>')
    return f'<nav class="nav-ed" aria-label="Outras edições">\n' + "\n".join(itens) + "\n</nav>"

def cabeca(titulo, descricao, css):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E%3Ctext y=%22.9em%22 font-size=%2290%22%3E🗞️%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Geist+Mono:wght@400;500&display=swap">
<style>
{css}
</style>
<script data-goatcounter="https://prensaautomata.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</head>"""

RODAPE = """<footer>
  Prensa Autômata · jornal diário produzido por IA · os textos são resumos com link para as fontes originais; erros podem acontecer, confira sempre a fonte.
</footer>"""

def pagina_arquivo(pasta, datas, css):
    """edicoes/index.html: todas as edições, da mais recente para a mais antiga, agrupadas por mês."""
    grupos = []
    for iso in datas:
        with open(os.path.join(pasta, f"{iso}.json"), encoding="utf-8") as f:
            ed = json.load(f)
        d = date.fromisoformat(iso)
        mes = f"{MESES[d.month-1].capitalize()} de {d.year}"
        if not grupos or grupos[-1][0] != mes:
            grupos.append((mes, []))
        grupos[-1][1].append(
            f'<li><a href="{iso}.html"><span class="d">{data_curta(iso)}</span>'
            f'<span class="n">Nº {e(str(ed.get("numero", "")))}</span>'
            f'<span class="t">{e(ed["manchete"]["titulo"])}</span></a></li>')
    corpo = "\n".join(f'<section>\n<h2>{e(mes)}</h2>\n<ol>\n' + "\n".join(itens) + "\n</ol>\n</section>"
                      for mes, itens in grupos)
    return f"""{cabeca("Prensa Autômata · Todas as edições", "Arquivo de todas as edições da Prensa Autômata.", css)}
<body>
<main>
<header>
  {REG.format(lado='l')}
  {REG.format(lado='r')}
  <h1 class="mast"><a href="../">Prensa Autômata</a></h1>
  <p class="sub">jornal diário produzido por IA</p>
  <p class="meta"><span>Todas as edições</span><span>{len(datas)} {"tiragem" if len(datas) == 1 else "tiragens"}</span></p>
</header>

<div class="arq">
{corpo}
</div>

<nav class="nav-ed" aria-label="Capa"><a href="../">← Edição de hoje</a></nav>

{RODAPE}
</main>
</body>
</html>
"""

def montar(ed, arquivo):
    css = open(os.path.join(RAIZ, "estilo.css"), encoding="utf-8").read()
    partes = []

    aviso = ed.get("aviso")
    if aviso:
        partes.append(f'<p class="teste">{e(aviso)}</p>')

    m = ed["manchete"]
    partes.append(secao("manchete", "",
        f"<h3>{e(m['titulo'])}</h3>\n{paragrafos(m['texto'], 'lede')}\n{fontes(m.get('fontes'), m.get('nota', ''))}",
        "manchete"))

    partes.append(secao("brasil", "Brasil", "\n\n".join(noticia(n) for n in ed["brasil"])))
    partes.append(secao("leitura", "Para entender o momento", leitura(ed["momento"])))
    partes.append(secao("mundo", "Mundo", noticia(ed["mundo"])))
    partes.append(secao("ia", "Inteligência artificial", noticia(ed["ia"])))

    blocos = []
    for r in ed["giro"]:
        itens = "\n".join(f'<li><a href="{e(i["url"], quote=True)}">{e(i["titulo"])}</a></li>' for i in r["itens"])
        blocos.append(f"<div>\n<h4>{e(r['regiao'])}</h4>\n<ul>\n{itens}\n</ul>\n</div>")
    partes.append(secao("giro", "Giro pelo mundo", '<div class="giro">\n' + "\n".join(blocos) + "\n</div>"))

    partes.append(secao("ciencia", "Ciência", noticia(ed["ciencia"])))

    d = ed["disco"]
    partes.append(secao("disco", "Um disco",
        f'<div class="album">\n<h3>{e(d["artista"])} — {e(d["titulo"])}</h3>\n'
        f'<p class="y">{e(d["ficha"])}</p>\n{paragrafos(d["texto"])}\n{fontes(d.get("fontes"))}\n</div>'))

    p = ed["poema"]
    partes.append(secao("poema", "Poema",
        f'<h3>{e(p["autor"])}, "{e(p["titulo"])}"</h3>\n<p class="y src">{e(p["ficha"])}</p>\n'
        f'<p class="poem">{e(p["texto"])}</p>\n{paragrafos(p["comentario"])}\n{fontes(p.get("fontes"))}'))

    partes.append(secao("brasil-fundo", "Para entender o Brasil", leitura(ed["entender_brasil"])))

    if "ibovespa" in ed:
        blocos_m = [mercado(nome, ed[chave]) for chave, nome in
                    [("ibovespa", "Ibovespa"), ("dolar", "Dólar"), ("bitcoin", "Bitcoin")] if chave in ed]
        resumo = ed.get("mercado")
        topo = (f'<div class="resumo">\n{paragrafos(resumo["texto"])}\n{fontes(resumo.get("fontes"))}\n</div>\n'
                if resumo else "")
        partes.append(secao("mercados", "Mercados",
            topo + '<div class="mercados">\n' + "\n".join(blocos_m) + '\n</div>\n'
            '<p class="src aviso">Informativo, não é recomendação.</p>'))
    else:
        b = ed["bitcoin"]
        partes.append(secao("bitcoin", "Bitcoin",
            f'{ticker(b["painel"])}\n{paragrafos(b["texto"])}\n{fontes(b.get("fontes"))}'))

    partes.append(secao("esporte", "Esporte", noticia(ed["esporte"])))

    t = ed["tempo"]
    regs = "\n".join(f"<div><dt>{e(r['regiao'])}</dt><dd>{e(r['texto'])}</dd></div>" for r in t["regioes"])
    partes.append(secao("tempo", f"Tempo no Brasil · {t['dia']}",
        f'<dl class="regioes">\n{regs}\n</dl>\n{fontes(t.get("fontes"))}'))

    partes.append(navegacao(ed["data"], arquivo))

    numero = ed.get("numero", "")
    return f"""{cabeca(f"Prensa Autômata · {data_extenso(ed['data'])}", m['titulo'], css)}
<body>
<main>
<header>
  {REG.format(lado='l')}
  {REG.format(lado='r')}
  <h1 class="mast">Prensa Autômata</h1>
  <p class="sub">jornal diário produzido por IA</p>
  <p class="meta"><span>{e(data_extenso(ed['data']))}</span><span>Tiragem Nº {e(str(numero))}</span></p>
</header>

{chr(10).join(chr(10) + x for x in partes)}

{RODAPE}
</main>
</body>
</html>
"""

def main():
    pasta = os.path.join(RAIZ, "edicoes")
    datas = sorted((os.path.basename(f)[:-5] for f in glob.glob(os.path.join(pasta, "*.json"))), reverse=True)
    if not datas:
        sys.exit("Nenhuma edição em edicoes/*.json")
    alvo = sys.argv[1] if len(sys.argv) > 1 else datas[0]
    with open(os.path.join(pasta, f"{alvo}.json"), encoding="utf-8") as f:
        ed = json.load(f)
    ed.setdefault("data", alvo)
    pagina = montar(ed, datas)
    # links do arquivo apontam para edicoes/…; dentro de edicoes/ o caminho relativo muda
    with open(os.path.join(pasta, f"{alvo}.html"), "w", encoding="utf-8") as f:
        f.write(pagina.replace('href="edicoes/', 'href="'))
    if alvo == datas[0]:
        with open(os.path.join(RAIZ, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina)
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina_arquivo(pasta, datas, open(os.path.join(RAIZ, "estilo.css"), encoding="utf-8").read()))
    print(f"ok: edição {alvo} montada" + (" (capa atualizada)" if alvo == datas[0] else "") + "; arquivo atualizado")

if __name__ == "__main__":
    main()
