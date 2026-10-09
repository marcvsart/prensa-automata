# Animação 9:16 de cada edição para as redes (fase de testes, publicação manual).
# Uso: python3 scripts/gerar_animacao.py /tmp/animacao.json   (rode na raiz do repositório)
# Formato do JSON: veja scripts/exemplo-animacao.json (Noturna Nº 10, 8 out 2026).
# Gera saida-animacao/<slug>.mp4 (1080x1920, 9:16, 30 fps, H.264) e <slug>-quadros.jpg (folha de conferência).
# Tema escuro se o slug terminar em "-noite"; claro nos demais.
import json, html, sys, pathlib, subprocess, shutil, re
from playwright.sync_api import sync_playwright

W, H, FPS = 1080, 1920, 30
c = json.load(open(sys.argv[1]))
noturna = c["slug"].endswith("-noite")
e = html.escape
svg = pathlib.Path("icone.svg").read_text()
svg_claro = svg.replace('fill="#0f1a2c"', 'fill="#e4e9f2"')
ICONE = svg_claro if noturna else svg            # ícone sobre o fundo
ICONE_PLACA = svg if noturna else svg_claro       # ícone sobre a placa azul
CORES = ("--bg:#0b111c;--ink:#e4e9f2;--azul:#8fa9f2;--cinza:#95a1b7;--filete:#243149;--papel:#121a2a;--sombra:rgba(5,8,14,.85)" if noturna
         else "--bg:#f6f8fb;--ink:#0f1a2c;--azul:#1e3a9e;--cinza:#56627a;--filete:#d7deea;--papel:#ffffff;--sombra:rgba(15,26,44,.10)")

def nwords(s): return len(re.sub(r"<[^>]+>", " ", s).split())

def titulo_html(txt, d):
    ws = txt.split(" ")
    return "".join(f'<span class="w"><span class="wi" data-d="{d+i*0.065:.2f}">{e(w)}</span></span> ' for i, w in enumerate(ws)), d + len(ws)*0.065

def cnt(v, d, dur=1.1, de=0, dec=0):
    fmt = "int" if dec == 0 and abs(v) >= 1000 else str(dec)
    return f'<span class="count" data-d="{d:.2f}" data-dur="{dur}" data-from="{de}" data-to="{v}" data-fmt="{fmt}"></span>'

# ---- módulos: cada um devolve (html, tempo em que termina de entrar, palavras visíveis) ----
def m_texto(m, d): return f'<div class="in texto" data-d="{d:.2f}">{e(m["texto"])}</div>', d+0.7, nwords(m["texto"])
def m_nota(m, d): return f'<div class="in nota" data-d="{d:.2f}">{e(m["texto"])}</div>', d+0.7, nwords(m["texto"])
def m_colunas(m, d):
    cols = ""
    for i, it in enumerate(m["itens"]):
        di = d + i*0.15
        cols += (f'<div class="col"><div class="col-num">{cnt(it["valor"], di, 1.3, 0, it.get("decimais",0))}<small>{e(it.get("sufixo","%"))}</small></div>'
                 f'<div class="col-trilho"><div class="col-fill grow-h" data-d="{di:.2f}" data-dur="1.3" data-v="{it["valor"]/m.get("escala_max",100)*100:.2f}"></div></div>'
                 f'<div class="in col-nome" data-d="{di+0.2:.2f}">{e(it["nome"])}</div></div>')
    lado = "".join(f'<div class="lado-k">{e(x["k"])}</div><div class="lado-v">{e(x["v"])}</div>' for x in m.get("lado", []))
    if lado: cols += f'<div class="in col-lado" data-d="{d+0.9:.2f}">{lado}</div>'
    w = sum(nwords(x["nome"]) for x in m["itens"]) + sum(nwords(x["k"]+" "+x["v"]) for x in m.get("lado", []))
    return f'<div class="colunas">{cols}</div>', d+1.6, w
def m_barras(m, d):
    out = f'<div class="in mod-k" data-d="{d:.2f}">{e(m["titulo"])}</div>' if m.get("titulo") else ""
    mx = m.get("escala_max") or max(x["valor"] for x in m["itens"])
    for i, it in enumerate(m["itens"]):
        di = d + 0.1 + i*0.3
        out += (f'<div class="bar-l"><span class="in" data-d="{di:.2f}">{e(it["nome"])}</span><div class="bar-t"><div class="bar-f {"fraco" if it.get("tracejado") else ""} grow-w" data-d="{di+0.1:.2f}" data-dur="0.9" data-v="{it["valor"]/mx*100:.2f}"></div></div>'
                f'<b class="in" data-d="{di+0.5:.2f}">{e(it["rotulo"])}</b></div>')
    w = nwords(m.get("titulo","")) + sum(nwords(x["nome"]+" "+x["rotulo"]) for x in m["itens"])
    return f'<div class="barras">{out}</div>', d+0.6+0.3*len(m["itens"]), w
def m_numeros(m, d):
    out = ""
    for i, it in enumerate(m["itens"]):
        di = d + i*0.25
        out += (f'<div class="in num" data-d="{di:.2f}"><span class="num-k">{e(it.get("antes",""))}</span><b>{e(it.get("prefixo",""))}{cnt(it["valor"], di, 1.1, it.get("de",0), it.get("decimais",0))}{e(it.get("sufixo",""))}</b>'
                f'<span class="num-v">{e(it.get("rotulo",""))}</span></div>')
    cls = "numeros duo" if m.get("lado_a_lado") else "numeros"
    return f'<div class="{cls}">{out}</div>', d+0.4+0.25*len(m["itens"]), sum(nwords(x.get("antes","")+" "+x.get("rotulo",""))+1 for x in m["itens"])
def m_placar(m, d):
    pts = "".join(f'<i class="ponto {"cheio" if i < m["cheios"] else ""}" data-d="{d+0.1+i*0.09:.2f}"></i>' for i in range(m["total"]))
    fim = d + 0.2 + m["total"]*0.09
    return (f'<div class="placar"><div class="in mod-k" data-d="{d:.2f}">{e(m["titulo"])}</div><div class="pontos">{pts}</div>'
            f'<div class="in placar-v" data-d="{fim:.2f}">{e(m["legenda"])}</div></div>'), fim+0.6, nwords(m["titulo"]+" "+m["legenda"])
def m_limiar(m, d):
    mn, mx = m["min"], m["max"]; p = lambda v: (v-mn)/(mx-mn)*100
    return (f'<div class="in limiar" data-d="{d:.2f}"><div class="mod-k">{e(m["titulo"])}</div><div class="eixo">'
            f'<div class="eixo-fill grow-w" data-d="{d+0.2:.2f}" data-dur="0.9" data-v="{p(m["de"]):.2f}" data-v2="{p(m["para"]):.2f}" data-d2="{d+1.3:.2f}"></div>'
            f'<div class="marco" style="left:{p(m["marco"]):.2f}%"><span>{e(m["marco_rotulo"])}</span></div></div>'
            f'<div class="eixo-esc"><span>{e(m.get("min_rotulo", str(mn)))}</span><span>{e(m.get("max_rotulo", str(mx)))}</span></div>'
            f'<div class="in texto menor" data-d="{d+2.0:.2f}">{e(m["legenda"])}</div></div>'), d+2.6, nwords(m["titulo"]+" "+m["legenda"])
def m_distancia(m, d):
    return (f'<div class="in esquema" data-d="{d:.2f}"><div class="esq-linha draw" data-d="{d+0.1:.2f}"></div><div class="esq-ponto"></div><div class="esq-front"></div>'
            f'<div class="esq-lab1">{e(m["origem"])}</div><div class="esq-lab2">{e(m["destino"])}</div><div class="esq-med">{e(m["rotulo"])}</div></div>'), d+1.0, nwords(m["origem"]+" "+m["destino"]+" "+m["rotulo"])
def m_fita(m, d): return f'<div class="fita in" data-d="{d:.2f}"><div class="fita-i">{e(m["texto"]+"   /   ")*5}</div></div>', d+0.5, 0
def m_livros(m, d):
    out = "".join(f'<div class="livro" data-d="{d+i*0.5:.2f}" data-k="{i%2}"><i class="lombada"></i><div class="lv-t">{e(it["titulo"])}</div><div class="lv-a">{e(it["autor"])}</div></div>' for i, it in enumerate(m["itens"]))
    return f'<div class="livros">{out}</div>', d+1.4+0.5*len(m["itens"]), sum(nwords(x["titulo"]+" "+x["autor"]) for x in m["itens"])
def m_lista(m, d):
    out = f'<div class="in mod-k" data-d="{d:.2f}">{e(m["titulo"])}</div>' if m.get("titulo") else ""
    out += "".join(f'<div class="in tb" data-d="{d+0.2+i*0.2:.2f}">{e(x)}</div>' for i, x in enumerate(m["itens"]))
    return f'<div class="lista">{out}</div>', d+0.5+0.2*len(m["itens"]), sum(nwords(x) for x in m["itens"])
MODULOS = dict(texto=m_texto, nota=m_nota, colunas=m_colunas, barras=m_barras, numeros=m_numeros, placar=m_placar,
               limiar=m_limiar, distancia=m_distancia, fita=m_fita, livros=m_livros, lista=m_lista)

# ---- cenas ----
ab = c["abertura"]
marca = "".join(f'<span class="letra" data-d="{0.45+i*0.035:.3f}">{ch if ch != " " else "&nbsp;"}</span>' for i, ch in enumerate("Prensa Autômata"))
cenas = [dict(placa="", fantasma="PRENSA", dur=3.6, html=f'''<div class="abre"><div class="in icone-g" data-d="0.1" data-k="pop">{ICONE}</div><div class="marca">{marca}</div>
 <div class="linha draw" data-d="1.1"></div><div class="in sub" data-d="1.3">{e(ab["edicao"])} Nº {cnt(ab["numero"], 1.3, 0.9)}</div>
 <div class="typ meta2" data-d="1.5" data-txt="{e(ab["data"])}" data-vel="1.7"></div></div>''')]
for s in c["cenas"] + [dict(c["fecho"], fecho=True)]:
    d = 0.45; h = f'<div class="rotulo typ" data-d="0.35" data-txt="{e(s["rotulo"])}"></div>'
    palavras = nwords(s["rotulo"])
    if s.get("fecho"):
        th, d = titulo_html("Leia em", d)
        h += f'<h1 class="h1 fecho">{th}</h1><div class="url-l"><span class="typ url" data-d="{d+0.2:.2f}" data-txt="prensaautomata.com" data-vel="0.9"></span></div>'
        d += 1.2; palavras += 3
        s = dict(s, modulos=[dict(tipo="lista", titulo="Também nesta edição", itens=s["itens"]), dict(tipo="nota", texto="Escrita por IA, com as fontes de cada notícia")])
    elif s.get("titulo"):
        th, d = titulo_html(s["titulo"], d)
        h += f'<h1 class="h1">{th}</h1>'; palavras += nwords(s["titulo"]); d += 0.3
    for m in s.get("modulos", []):
        mh, fim, w = MODULOS[m["tipo"]](m, d)
        h += mh; palavras += w; d = fim + 0.2
    dur = s.get("dur") or round(min(8.5, max(4.4, d + 1.8, 1.6 + 0.10*palavras)), 1)
    cenas.append(dict(placa=s["rotulo"] if not s.get("fecho") else "A edição completa", fantasma=s.get("fantasma", ""), dur=dur, html=h))

t = 0.0; secs = []; segs = []; finais = []
for i, s in enumerate(cenas):
    a, b = round(t, 2), round(t + s["dur"], 2); t += s["dur"]; finais.append(round(b - 0.5, 2))
    secs.append(f'<section class="cena" data-a="{a}" data-b="{b}" data-placa="{e(s["placa"])}"><div class="fantasma">{e(s["fantasma"])}</div><div class="miolo">{s["html"]}</div></section>')
    if i: segs.append(f'<div class="seg" data-a="{a}" data-b="{b}"><i></i></div>')
DUR = round(t, 2)

CSS = ":root{" + CORES + "}" + """*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:var(--bg);color:var(--ink);overflow:hidden}body{position:relative;font-family:'Newsreader',serif}
#retic{position:absolute;inset:-40px;background-image:radial-gradient(var(--filete) 1.6px,transparent 1.8px);background-size:18px 18px;opacity:.55}
#vinheta{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 40%,var(--sombra) 100%)}
.topo{position:absolute;left:88px;right:88px;top:150px;display:flex;align-items:center;gap:28px;padding-bottom:32px;border-bottom:2px solid var(--ink);z-index:3}
.topo svg{width:96px;height:96px;flex:none}.nome{font-weight:500;font-size:44px;line-height:1.1}
.meta{font-family:'Geist Mono',monospace;font-size:21px;text-transform:uppercase;color:var(--cinza);margin-top:10px;letter-spacing:.02em}
.cena{position:absolute;inset:0;display:none}
.fantasma{position:absolute;left:0;bottom:520px;font-weight:500;font-size:360px;line-height:1;white-space:nowrap;color:transparent;-webkit-text-stroke:2px var(--filete);letter-spacing:-.02em}
.miolo{position:absolute;left:88px;right:88px;top:360px;bottom:520px;display:flex;flex-direction:column;justify-content:center}
.rotulo{font-family:'Geist Mono',monospace;font-weight:500;font-size:28px;text-transform:uppercase;color:var(--azul);letter-spacing:.06em;margin-bottom:32px;min-height:34px}
.typ.cur::after{content:'▍';margin-left:4px}
.h1{font-weight:500;font-size:100px;line-height:1.04;letter-spacing:-.015em;margin-bottom:52px}.h1.fecho{font-size:104px;margin-bottom:0}
.w{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.14em;margin-bottom:-.14em}.wi{display:inline-block}
.texto{font-size:46px;line-height:1.3;margin-bottom:8px}.texto.menor{font-size:38px;margin-top:26px}
.nota{font-family:'Geist Mono',monospace;font-size:23px;color:var(--cinza);margin-top:44px;padding-top:24px;border-top:1px solid var(--filete);line-height:1.5}
.mod-k{font-family:'Geist Mono',monospace;font-size:24px;text-transform:uppercase;color:var(--azul);letter-spacing:.05em;margin-bottom:18px}
b{font-weight:500}
.abre{display:flex;flex-direction:column;align-items:flex-start}.icone-g svg{width:280px;height:280px}
.marca{font-weight:500;font-size:116px;line-height:1;letter-spacing:-.02em;margin-top:48px;white-space:nowrap}.letra{display:inline-block}
.linha{height:3px;background:var(--azul);width:100%;margin-top:52px;transform-origin:left}
.sub{font-family:'Geist Mono',monospace;font-size:38px;text-transform:uppercase;color:var(--azul);letter-spacing:.06em;margin-top:40px}
.meta2{font-size:46px;margin-top:14px;white-space:nowrap}
.colunas{display:grid;grid-template-columns:240px 240px 1fr;gap:36px;align-items:end;margin-bottom:10px}
.col{display:flex;flex-direction:column;align-items:flex-start}
.col-num{font-weight:500;font-size:116px;line-height:1;letter-spacing:-.03em;margin-bottom:18px;white-space:nowrap}.col-num small{font-size:58px;margin-left:4px;color:var(--cinza)}
.col-trilho{width:200px;height:330px;background:var(--filete);position:relative}.col-fill{position:absolute;left:0;right:0;bottom:0;height:0;background:var(--azul)}
.col-nome{font-family:'Geist Mono',monospace;font-size:23px;text-transform:uppercase;letter-spacing:.03em;margin-top:18px}
.col-lado{align-self:center;padding-left:28px;border-left:1px solid var(--filete)}
.lado-k{font-family:'Geist Mono',monospace;font-size:21px;text-transform:uppercase;color:var(--azul);letter-spacing:.05em;margin-top:26px}.lado-k:first-child{margin-top:0}
.lado-v{font-size:32px;line-height:1.25;margin-top:8px}
.pontos{display:flex;gap:20px;margin:6px 0 20px}.ponto{width:50px;height:50px;border-radius:50%;border:3px solid var(--azul);display:block}.ponto.cheio{background:var(--azul)}
.placar{margin-bottom:40px}.placar-v{font-size:42px}
.limiar{margin-top:10px}.eixo{position:relative;height:50px;background:var(--filete);margin-top:58px}
.eixo-fill{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--azul)}
.marco{position:absolute;top:-16px;bottom:-16px;width:4px;margin-left:-2px;background:var(--ink)}
.marco span{position:absolute;top:-38px;left:50%;transform:translateX(-50%);font-family:'Geist Mono',monospace;font-size:22px;white-space:nowrap}
.eixo-esc{display:flex;justify-content:space-between;font-family:'Geist Mono',monospace;font-size:20px;color:var(--cinza);margin-top:12px}
.numeros{display:grid;gap:44px}.numeros.duo{grid-template-columns:1fr 1fr;gap:40px}
.num-k{display:block;font-family:'Geist Mono',monospace;font-size:26px;text-transform:uppercase;color:var(--azul);letter-spacing:.06em}
.num b{display:block;font-size:180px;line-height:1;letter-spacing:-.03em;white-space:nowrap;font-variant-numeric:tabular-nums}
.numeros.duo .num b{font-size:200px}
.num-v{display:block;font-family:'Geist Mono',monospace;font-size:26px;text-transform:uppercase;color:var(--cinza);letter-spacing:.04em;margin-top:12px;line-height:1.4}
.esquema{position:relative;height:180px;margin-top:60px}
.esq-linha{position:absolute;left:20px;right:12px;top:74px;height:3px;background:repeating-linear-gradient(90deg,var(--cinza) 0 14px,transparent 14px 26px);transform-origin:left}
.esq-ponto{position:absolute;left:0;top:56px;width:42px;height:42px;border-radius:50%;background:var(--azul);box-shadow:0 0 0 12px color-mix(in srgb,var(--azul) 20%,transparent)}
.esq-front{position:absolute;right:0;top:22px;width:8px;height:108px;background:repeating-linear-gradient(180deg,var(--ink) 0 12px,transparent 12px 20px)}
.esq-lab1,.esq-lab2{position:absolute;top:130px;font-family:'Geist Mono',monospace;font-size:23px;text-transform:uppercase;letter-spacing:.04em}
.esq-lab1{left:0;color:var(--azul)}.esq-lab2{right:0}.esq-med{position:absolute;left:0;right:0;top:18px;text-align:center;font-size:36px}
.barras{margin-bottom:10px}.bar-l{display:grid;grid-template-columns:1fr 280px;column-gap:24px;align-items:center;margin-bottom:26px}
.bar-l>span{grid-column:1/3;font-size:32px;color:var(--cinza);margin-bottom:10px}.bar-t{height:50px;position:relative}
.bar-f{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--azul)}.bar-f.fraco{background:transparent;border:2px dashed var(--cinza)}
.bar-l b{font-size:44px;text-align:right;white-space:nowrap}
.fita{margin:56px -88px 0;height:74px;border-top:2px solid var(--ink);border-bottom:2px solid var(--ink);overflow:hidden}
.fita-i{white-space:pre;font-family:'Geist Mono',monospace;font-size:27px;line-height:70px;letter-spacing:.04em}
.livros{display:flex;flex-direction:column;gap:44px}
.livro{position:relative;width:100%;padding:56px 60px 56px 88px;background:var(--papel);border:1px solid var(--filete);box-shadow:0 30px 60px var(--sombra)}
.livro:nth-child(even){margin-left:44px;width:calc(100% - 44px)}.lombada{position:absolute;left:0;top:0;bottom:0;width:28px;background:var(--azul);display:block}
.lv-t{font-size:72px;line-height:1.05;font-weight:500;letter-spacing:-.01em}
.lv-a{font-family:'Geist Mono',monospace;font-size:23px;color:var(--cinza);margin-top:26px;text-transform:uppercase;letter-spacing:.03em}
.url-l{font-size:92px;font-weight:500;line-height:1.1;letter-spacing:-.02em;min-height:104px;white-space:nowrap}.url{color:var(--azul)}
.lista{margin-top:56px}.tb{font-size:40px;line-height:1.3;padding:14px 0 14px 36px;position:relative;border-bottom:1px solid var(--filete)}
.tb::before{content:'';position:absolute;left:4px;top:34px;width:13px;height:13px;background:var(--azul)}
.pe{position:absolute;left:88px;right:88px;bottom:400px;z-index:3}.segs{display:flex;gap:10px;margin-bottom:26px}
.seg{flex:1;height:5px;background:var(--filete);position:relative;overflow:hidden}.seg i{position:absolute;left:0;top:0;bottom:0;background:var(--azul);width:0}
.rod{display:flex;justify-content:space-between;font-family:'Geist Mono',monospace;font-size:22px;color:var(--cinza)}
.placa{position:absolute;inset:0;z-index:10;transform:translateY(100%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px}
#placa2{background:var(--ink)}#placa{background:var(--azul);color:var(--bg)}#placa svg{width:170px;height:170px}
#placa-txt{font-family:'Geist Mono',monospace;font-weight:500;font-size:68px;text-transform:uppercase;letter-spacing:.08em;text-align:center;padding:0 80px}"""

JS = """const DUR=@DUR@,T=0.42,cl=x=>Math.max(0,Math.min(1,x)),eo=x=>1-Math.pow(1-x,3),
eio=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,eback=x=>1+2.5*Math.pow(x-1,3)+1.5*Math.pow(x-1,2),
fmt=(v,f)=>f==='int'?Math.round(v).toLocaleString('pt-BR'):(+f>0?v.toLocaleString('pt-BR',{minimumFractionDigits:+f,maximumFractionDigits:+f}):String(Math.round(v))),
D=el=>+(el.dataset.d||0),cenas=[...document.querySelectorAll('.cena')],lim=cenas.slice(0,-1).map(c=>+c.dataset.b);
function render(t){
 let pl=null;lim.forEach((b,i)=>{if(t>=b-T&&t<=b+T)pl={b,i};});
 const P=document.getElementById('placa'),P2=document.getElementById('placa2');
 if(pl){const u=(t-(pl.b-T))/(2*T);P2.style.transform=`translateY(${100-200*eio(cl(u*1.12))}%)`;P.style.transform=`translateY(${100-200*eio(cl(u*1.12-.12))}%)`;
  document.getElementById('placa-txt').textContent=cenas[pl.i+1].dataset.placa;}else P.style.transform=P2.style.transform='translateY(100%)';
 ['topo','pe'].forEach(id=>document.getElementById(id).style.opacity=t>=lim[0]?1:0);
 document.getElementById('retic').style.transform=`translate(${(t*6)%18}px,${(t*4)%18}px)`;
 cenas.forEach((c,ci)=>{const a=+c.dataset.a,b=+c.dataset.b,lt=t-a,on=t>=a&&(t<b||ci==cenas.length-1);
  c.style.display=on?'block':'none';if(!on)return;
  const sai=ci<cenas.length-1?cl((t-(b-T))/T):0;c.querySelector('.miolo').style.transform=`scale(${1-.04*eio(sai)}) translateY(${-40*eio(sai)}px)`;
  const f=c.querySelector('.fantasma');f.style.transform=`translateX(${80-lt*38}px)`;f.style.opacity=eo(cl(lt/.8));
  const q=s=>c.querySelectorAll(s);
  q('.in').forEach(el=>{const p=cl((lt-D(el))/.7);if(el.dataset.k==='pop'){el.style.transform=`scale(${.5+.5*eback(p)})`;el.style.opacity=cl(p*2);}
   else{const e=eo(p);el.style.opacity=e;el.style.transform=`translateY(${(1-e)*40}px)`;}});
  q('.wi').forEach(el=>{el.style.transform=`translateY(${(1-eo(cl((lt-D(el))/.6)))*110}%)`;});
  q('.letra').forEach(el=>{const p=cl((lt-D(el))/.55),e=eback(p);el.style.opacity=cl(p*2.5);el.style.transform=`translateY(${(1-e)*90}px) rotate(${(1-e)*8}deg)`;});
  q('.typ').forEach(el=>{const s=el.dataset.txt,dur=s.length*.045/+(el.dataset.vel||1),p=cl((lt-D(el))/dur);el.textContent=s.slice(0,Math.round(s.length*p));
   el.classList.toggle('cur',lt>D(el)&&(lt-D(el)-dur)<1.2&&Math.floor(lt*3)%2==0);});
  q('.count').forEach(el=>{const p=eo(cl((lt-D(el))/+el.dataset.dur)),fr=+el.dataset.from,to=+el.dataset.to;el.textContent=fmt(fr+(to-fr)*p,el.dataset.fmt);});
  q('.grow-h').forEach(el=>{el.style.height=(+el.dataset.v*eo(cl((lt-D(el))/+el.dataset.dur)))+'%';});
  q('.grow-w').forEach(el=>{let w=+el.dataset.v*eo(cl((lt-D(el))/+el.dataset.dur));if(el.dataset.v2)w+=(+el.dataset.v2-+el.dataset.v)*eio(cl((lt-+el.dataset.d2)/.9));el.style.width=w+'%';});
  q('.draw').forEach(el=>{el.style.transform=`scaleX(${eio(cl((lt-D(el))/.9))})`;});
  q('.ponto').forEach(el=>{const p=cl((lt-D(el))/.45);el.style.transform=`scale(${eback(p)})`;el.style.opacity=cl(p*3);});
  q('.livro').forEach(el=>{const p=cl((lt-D(el))/.9),k=+el.dataset.k,r=k?2:-2.5;el.style.opacity=cl(p*2.2);
   el.style.transform=`translateX(${(1-eo(p))*(k?260:-260)}px) rotate(${r+(1-eback(p))*(k?10:-10)}deg)`;});
  q('.fita-i').forEach(el=>{el.style.transform=`translateX(${-lt*110}px)`;});});
 document.querySelectorAll('.seg').forEach(s=>{const a=+s.dataset.a,b=+s.dataset.b;s.querySelector('i').style.width=(cl((t-a)/(b-a))*100)+'%';});}
function confere(){const m=[...document.querySelectorAll('.cena')].find(c=>c.style.display!='none');if(!m)return false;
 const mi=m.querySelector('.miolo'),r=mi.getBoundingClientRect();if(mi.scrollHeight>mi.clientHeight+2)return true;
 return [...mi.querySelectorAll('*')].some(el=>{const b=el.getBoundingClientRect();return b.width&&(b.right>1080-40||b.left<40)&&!el.closest('.fita')&&!el.closest('.livro');});}
render(0);""".replace("@DUR@", str(DUR))

FONTES = '<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Geist+Mono:wght@400;500&display=block" rel="stylesheet">'
PAGE = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">{FONTES}<style>{CSS}</style></head><body><div id="retic"></div><div id="vinheta"></div>'
        f'<div class="topo" id="topo">{ICONE}<div><div class="nome">Prensa Autômata</div><div class="meta">{e(c["meta"])}</div></div></div>{"".join(secs)}'
        f'<div class="pe" id="pe"><div class="segs">{"".join(segs)}</div><div class="rod"><span>prensaautomata.com</span><span>{"Edição da noite" if noturna else "Edição da manhã"}</span></div></div>'
        f'<div class="placa" id="placa2"></div><div class="placa" id="placa">{ICONE_PLACA}<div id="placa-txt"></div></div><script>{JS}</script></body></html>')

saida = pathlib.Path("saida-animacao"); saida.mkdir(exist_ok=True)
quadros = pathlib.Path("/tmp/quadros-" + c["slug"]); shutil.rmtree(quadros, ignore_errors=True); quadros.mkdir()
pagina = quadros / "animacao.html"; pagina.write_text(PAGE)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
    pg.goto(pagina.as_uri(), wait_until="networkidle"); pg.evaluate("document.fonts.ready")
    ok = pg.evaluate("document.fonts.check('500 44px Newsreader') && document.fonts.check('21px \"Geist Mono\"')")
    print("fontes ok" if ok else "FONTES NÃO CARREGARAM")
    for i, tf in enumerate(finais):   # conferência no fim de cada cena, quando tudo já entrou
        pg.evaluate(f"render({tf})"); est = pg.evaluate("confere()")
        print(f"cena {i}: {cenas[i]['placa'] or 'abertura'} ({cenas[i]['dur']} s)", "ESTOURO" if est else "ok")
        pg.screenshot(path=str(quadros / f"conf{i}.png"))
    for i in range(int(DUR * FPS)):
        pg.evaluate(f"render({i / FPS})"); pg.screenshot(path=str(quadros / f"f{i:05d}.jpg"), type="jpeg", quality=94)
    b.close()
ff = shutil.which("ffmpeg")
if not ff:
    import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()   # pip install imageio-ffmpeg, se não houver ffmpeg
subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(quadros / "f%05d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18", "-preset", "slow", "-movflags", "+faststart", str(saida / f'{c["slug"]}.mp4')], check=True)
n = len(finais); entradas = sum((["-i", str(quadros / f"conf{i}.png")] for i in range(n)), [])
subprocess.run([ff, "-loglevel", "error", "-y", *entradas, "-filter_complex", f"hstack=inputs={n},scale=2400:-1", str(saida / f'{c["slug"]}-quadros.jpg')], check=True)
print(f"duração {DUR} s · {saida / (c['slug'] + '.mp4')} · {saida / (c['slug'] + '-quadros.jpg')}")
