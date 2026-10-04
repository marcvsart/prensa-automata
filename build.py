#!/usr/bin/env python3
"""Prensa Autômata — monta a edição a partir de edicoes/AAAA-MM-DD.json.

Uso:  python3 build.py                  (monta a edição mais recente)
      python3 build.py 2026-09-29       (monta a edição da manhã de uma data)
      python3 build.py 2026-09-29-noite (monta a edição da noite de uma data)

Gera edicoes/AAAA-MM-DD.html, copia a mais recente para index.html
e refaz edicoes/index.html (arquivo com todas as edições) e sobre.html.
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

def dia(slug):
    """'2026-09-30-noite' -> '2026-09-30'."""
    return slug[:10]

def noturna(slug):
    return slug.endswith("-noite")

RECENTE = '<a href="./" class="recente">Edição mais recente</a>'

def navegacao(atual, arquivo):
    """Links fixos no fim da edição: a anterior (que nunca muda) e o arquivo completo."""
    anteriores = [a for a in arquivo if a < atual]
    itens = []
    if anteriores:
        ant = max(anteriores)
        dias = (date.fromisoformat(dia(atual)) - date.fromisoformat(dia(ant))).days
        if dias == 0:
            rotulo = "← Edição da manhã"
        elif dias == 1:
            rotulo = "← Edição de ontem à noite" if noturna(ant) else "← Edição de ontem"
        else:
            d = date.fromisoformat(dia(ant))
            rotulo = f"← Edição anterior · {d.day:02d}/{d.month:02d}" + (" · noite" if noturna(ant) else "")
        itens.append(f'<a href="edicoes/{ant}.html">{e(rotulo)}</a>')
    # a capa sempre mostra a edição mais nova; nas páginas guardadas, este link leva de volta a ela
    itens.append(RECENTE)
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
  Prensa Autômata · jornal diário produzido por IA · os textos são resumos com link para as fontes originais; erros podem acontecer, confira sempre a fonte. · <a href="sobre.html">Sobre a Prensa</a>
</footer>"""

def lista_turno(pasta, slugs):
    """Edições de um turno, da mais recente para a mais antiga, agrupadas por mês."""
    grupos = []
    for slug in slugs:
        with open(os.path.join(pasta, f"{slug}.json"), encoding="utf-8") as f:
            ed = json.load(f)
        d = date.fromisoformat(dia(slug))
        mes = f"{MESES[d.month-1].capitalize()} de {d.year}"
        if not grupos or grupos[-1][0] != mes:
            grupos.append((mes, []))
        grupos[-1][1].append(
            f'<li><a href="{slug}.html"><span class="d">{data_curta(dia(slug))}</span>'
            f'<span class="n">Nº {e(str(ed.get("numero", "")))}</span>'
            f'<span class="t">{e(ed["manchete"]["titulo"])}</span></a></li>')
    return "\n".join(f'<section>\n<h2>{e(mes)}</h2>\n<ol>\n' + "\n".join(itens) + "\n</ol>\n</section>"
                     for mes, itens in grupos)

VISIVEIS = 7  # edições à mostra em cada turno; as demais ficam atrás de "Mais edições"

def lista_curta(pasta, slugs, rotulo):
    """As VISIVEIS mais recentes à mostra; o resto numa lista retrátil, sem JavaScript."""
    lista = lista_turno(pasta, slugs[:VISIVEIS])
    resto = slugs[VISIVEIS:]
    if resto:
        lista += (f'\n<details class="mais">\n<summary>Mais {e(rotulo.split(" ", 1)[1].lower())} '
                  f'<span>({len(resto)})</span></summary>\n{lista_turno(pasta, resto)}\n</details>')
    return lista

def pagina_arquivo(pasta, datas, css):
    """edicoes/index.html: todas as edições, separadas em manhã e noite."""
    turnos = [("manha", "☀︎ Edições da manhã", [x for x in datas if not noturna(x)]),
              ("noite", "☾ Edições da noite", [x for x in datas if noturna(x)])]
    turnos = [t for t in turnos if t[2]]
    atalhos = ""
    if len(turnos) > 1:
        atalhos = '<p class="turnos">' + "".join(f'<a href="#{id_}">{e(rot)}</a>' for id_, rot, _ in turnos) + "</p>\n"
    corpo = atalhos + "\n".join(f'<div class="turno" id="{id_}">\n<p class="turno-t">{e(rot)}</p>\n'
                                 f'{lista_curta(pasta, slugs, rot)}\n</div>' for id_, rot, slugs in turnos)
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

{RODAPE.replace('href="sobre.html"', 'href="../sobre.html"')}
</main>
</body>
</html>
"""

def montar(ed, arquivo, slug):
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
    if "momento" in ed:
        partes.append(secao("leitura", "Para entender o momento", leitura(ed["momento"])))
    if "mundo" in ed:
        partes.append(secao("mundo", "Mundo", noticia(ed["mundo"])))
    if "ia" in ed:
        partes.append(secao("ia", "Inteligência artificial", noticia(ed["ia"])))

    blocos = []
    for r in ed.get("giro", []):
        itens = "\n".join(f'<li><a href="{e(i["url"], quote=True)}">{e(i["titulo"])}</a></li>' for i in r["itens"])
        blocos.append(f"<div>\n<h4>{e(r['regiao'])}</h4>\n<ul>\n{itens}\n</ul>\n</div>")
    if blocos:
        partes.append(secao("giro", "Giro pelo mundo", '<div class="giro">\n' + "\n".join(blocos) + "\n</div>"))

    if "ciencia" in ed:
        partes.append(secao("ciencia", "Ciência", noticia(ed["ciencia"])))

    if "disco" in ed:
        d = ed["disco"]
        partes.append(secao("disco", "Um disco",
            f'<div class="album">\n<h3>{e(d["artista"])} — {e(d["titulo"])}</h3>\n'
            f'<p class="y">{e(d["ficha"])}</p>\n{paragrafos(d["texto"])}\n{fontes(d.get("fontes"))}\n</div>'))

    if "poema" in ed:
        p = ed["poema"]
        partes.append(secao("poema", "Poema",
            f'<h3>{e(p["autor"])}, "{e(p["titulo"])}"</h3>\n<p class="y src">{e(p["ficha"])}</p>\n'
            f'<p class="poem">{e(p["texto"])}</p>\n{paragrafos(p["comentario"])}\n{fontes(p.get("fontes"))}'))

    if "entender_brasil" in ed:
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
    elif "bitcoin" in ed:
        b = ed["bitcoin"]
        partes.append(secao("bitcoin", "Bitcoin",
            f'{ticker(b["painel"])}\n{paragrafos(b["texto"])}\n{fontes(b.get("fontes"))}'))

    if "esporte" in ed:
        partes.append(secao("esporte", "Esporte", noticia(ed["esporte"])))

    if "tempo" in ed:
        t = ed["tempo"]
        regs = "\n".join(f"<div><dt>{e(r['regiao'])}</dt><dd>{e(r['texto'])}</dd></div>" for r in t["regioes"])
        partes.append(secao("tempo", f"Tempo no Brasil · {t['dia']}",
            f'<dl class="regioes">\n{regs}\n</dl>\n{fontes(t.get("fontes"))}'))

    partes.append(navegacao(slug, arquivo))

    numero = e(str(ed.get("numero", "")))
    if noturna(slug):
        titulo = f"Prensa Autômata · Edição da noite · {data_extenso(ed['data'])}"
        meta = f"<span>{e(data_extenso(ed['data']))}</span><span>Edição da noite</span><span>Noturna Nº {numero}</span>"
    else:
        titulo = f"Prensa Autômata · {data_extenso(ed['data'])}"
        meta = f"<span>{e(data_extenso(ed['data']))}</span><span>Tiragem Nº {numero}</span>"
    return f"""{cabeca(titulo, m['titulo'], css)}
<body>
<main>
<header>
  {REG.format(lado='l')}
  {REG.format(lado='r')}
  <h1 class="mast"><a href="./">Prensa Autômata</a></h1>
  <p class="sub">jornal diário produzido por IA</p>
  <p class="meta">{meta}</p>
</header>

{chr(10).join(chr(10) + x for x in partes)}

{RODAPE}
</main>
</body>
</html>
"""

def pagina_sobre(css):
    """sobre.html: o que é a Prensa, como cada edição é feita e seus limites, com o arauto no topo."""
    return f"""{cabeca("Prensa Autômata · Sobre a Prensa", "O que é a Prensa Autômata, como cada edição é feita e quais são seus limites.", css)}
<body>
<main>
<header>
  {REG.format(lado='l')}
  {REG.format(lado='r')}
  <h1 class="mast"><a href="./">Prensa Autômata</a></h1>
  <p class="sub">jornal diário produzido por IA</p>
  <p class="meta"><span>Sobre a Prensa</span></p>
</header>

<div class="sobre">
<figure class="arauto"><img src="arauto.svg" width="192" height="144" alt="O arauto da Prensa Autômata: uma máquina de escrever robô de dois olhos, com chapéu fedora e uma folha saindo do rolo, em pixel art azul."></figure>

<section class="intro">
<p class="lede">A Prensa Autômata é um experimento de jornalismo e automação criado por Marcus Couto em 2026. O objetivo é testar um fluxo de produção totalmente automatizado para um jornal diário: da escolha dos assuntos à página no ar, sem que nenhuma pessoa escreva, revise ou aprove as edições.</p>
<p>Duas vezes por dia, às 6h e às 18h (horário de Brasília), o Claude, modelo de inteligência artificial da Anthropic, faz sozinho o trabalho de uma redação inteira.</p>
</section>

<section id="como">
<h2>Como uma edição é feita</h2>
<dl class="etapas">
<div><dt>Ronda</dt><dd>Percorre veículos brasileiros e estrangeiros, agências e publicações especializadas, e escolhe os assuntos do dia.</dd></div>
<div><dt>Apuração</dt><dd>Abre e lê as fontes. Só entra na edição o que foi conferido nelas, e todo texto traz os links para os originais.</dd></div>
<div><dt>Redação</dt><dd>Escreve resumos curtos, em linguagem direta, seguindo regras de imparcialidade: ouvir os lados envolvidos, não adjetivar e informar instituto, datas, amostra, margem de erro e registro de toda pesquisa eleitoral.</dd></div>
<div><dt>Publicação</dt><dd>Monta as páginas, publica o jornal e confere se a edição foi mesmo ao ar.</dd></div>
</dl>
</section>

<section id="edicoes">
<h2>Duas edições</h2>
<p>A edição da manhã traz as notícias do Brasil e do mundo, inteligência artificial, ciência, mercados, esporte, previsão do tempo, um disco, um poema e indicações de leitura para entender o país. A edição da noite é mais curta, com notícias enxutas e leituras mais aprofundadas.</p>
</section>

<section id="limites">
<h2>Limites</h2>
<p>Como tudo é feito por uma máquina, erros podem acontecer. Os textos são resumos e não substituem as reportagens originais: confira sempre a fonte. Quando um erro é encontrado, o texto é corrigido com uma nota. A Prensa também noticia a Anthropic, empresa que cria o Claude; nesses casos, o texto avisa.</p>
</section>

<p class="assina">Prensa Autômata · um experimento de Marcus Couto · 2026</p>
</div>

<nav class="nav-ed" aria-label="Edições"><a href="./">← Edição mais recente</a><a href="edicoes/index.html">Todas as edições →</a></nav>

{RODAPE}
</main>
</body>
</html>
"""

# O GitHub Pages manda o navegador guardar as páginas por 10 minutos. Na capa, este
# script pergunta (sem cache) qual é a edição mais recente e, se a página aberta for
# de uma edição anterior, recarrega com ?v=<edição>, endereço que ainda não está em cache.
VIGIA = """<script>
(function () {
  var atual = "SLUG";
  if (!window.fetch) return;
  fetch("ultima.json?t=" + Date.now(), { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.edicao || d.edicao === atual) return;
      var q = "v=" + d.edicao;
      if (location.search.indexOf(q) !== -1) return;
      location.replace(location.pathname + "?" + q);
    })
    .catch(function () {});
})();
</script>
"""

def main():
    pasta = os.path.join(RAIZ, "edicoes")
    datas = sorted((os.path.basename(f)[:-5] for f in glob.glob(os.path.join(pasta, "*.json"))), reverse=True)
    if not datas:
        sys.exit("Nenhuma edição em edicoes/*.json")
    alvo = sys.argv[1] if len(sys.argv) > 1 else datas[0]
    with open(os.path.join(pasta, f"{alvo}.json"), encoding="utf-8") as f:
        ed = json.load(f)
    ed.setdefault("data", dia(alvo))
    pagina = montar(ed, datas, alvo)
    # links do arquivo apontam para edicoes/…; dentro de edicoes/ o caminho relativo muda
    with open(os.path.join(pasta, f"{alvo}.html"), "w", encoding="utf-8") as f:
        f.write(pagina.replace('href="edicoes/', 'href="').replace('href="./"', 'href="../"')
                .replace('href="sobre.html"', 'href="../sobre.html"'))
    if alvo == datas[0]:
        with open(os.path.join(RAIZ, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina.replace(RECENTE + "\n", "").replace("</body>", VIGIA.replace("SLUG", alvo) + "</body>", 1))
    # a capa consulta este arquivo para saber se há edição mais nova que a guardada em cache
    with open(os.path.join(RAIZ, "ultima.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"edicao": datas[0]}) + "\n")
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina_arquivo(pasta, datas, open(os.path.join(RAIZ, "estilo.css"), encoding="utf-8").read()))
    with open(os.path.join(RAIZ, "sobre.html"), "w", encoding="utf-8") as f:
        f.write(pagina_sobre(open(os.path.join(RAIZ, "estilo.css"), encoding="utf-8").read()))
    print(f"ok: edição {alvo} montada" + (" (capa atualizada)" if alvo == datas[0] else "") + "; arquivo atualizado")

if __name__ == "__main__":
    main()
