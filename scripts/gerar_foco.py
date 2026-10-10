# Vídeo "Em foco": uma notícia só, 9:16, derivado da animação diária (fase de testes, publicação manual).
# Uso: python3 scripts/gerar_foco.py /tmp/foco.json   (rode na raiz do repositório)
# Reaproveita scripts/gerar_animacao.py sem alterá-lo: lê o código, troca a paleta, a abertura,
# o rodapé e o fecho, e executa. Se uma troca deixar de casar com o original, o script para com erro.
# JSON: veja scripts/exemplo-foco.json; instruções em scripts/EM-FOCO.md.
# Gera saida-animacao/<slug>.mp4 e <slug>-quadros.jpg.
import pathlib, sys

src = pathlib.Path(__file__).with_name("gerar_animacao.py").read_text()

def troca(velho, novo):
    global src
    assert src.count(velho) == 1, f"trecho não encontrado em gerar_animacao.py: {velho[:60]!r}"
    src = src.replace(velho, novo)

# paleta: fundo no azul da Prensa, texto claro, destaques no azul-claro da edição da noite
troca('ICONE = svg_claro if noturna else svg', 'ICONE = svg_claro')
troca('ICONE_PLACA = svg if noturna else svg_claro', 'ICONE_PLACA = svg')
troca('CORES = (', 'CORES = "--bg:#1e3a9e;--ink:#f6f8fb;--azul:#b9c8f5;--cinza:#c9d3ee;--filete:rgba(246,248,251,.20);--papel:#22409f;--sombra:rgba(8,16,48,.45)"\n_CORES_DIARIA = (')

# abertura: a notícia em si; a marca e a tiragem ficam discretas no pé
troca('ab = c["abertura"]', 'ab = dict(dict(edicao="", numero=0, data=""), **c["abertura"])')
troca('cenas = [dict(placa="", fantasma="", dur=3.6, html=f', 'cenas = [dict(placa="", fantasma="", dur=0, html=f')
troca("for s in c[\"cenas\"] + [dict(c[\"fecho\"], fecho=True)]:", '''_tt, _fim = titulo_html(ab["titulo"], 0.9)
cenas[0] = dict(placa="", fantasma=ab.get("fantasma", ""), dur=ab.get("dur") or round(max(5.6, _fim + 3.4), 1), html=f\'\'\'<div class="abre foco">
 <div class="rotulo typ" data-d="0.3" data-txt="{e(ab["chapeu"])}"></div><h1 class="h1 abre-h">{_tt}</h1>
 <div class="linha draw" data-d="{_fim+0.1:.2f}"></div><div class="in local" data-d="{_fim+0.3:.2f}">{e(ab["local"])}</div></div>
 <div class="in assin" data-d="{_fim+0.6:.2f}">{ICONE}<span>{e(ab["tiragem"])}</span></div>\'\'\')
for s in c["cenas"] + [dict(c["fecho"], fecho=True)]:''')

# leitura: o vídeo de uma notícia só é mais denso; cada cena ganha 1 s além da folga da diária
troca('1.6 + 0.10*palavras)) + 1.0, 1)', '1.6 + 0.10*palavras)) + 2.0, 1)')

# fecho: fontes da notícia no lugar de "Também nesta edição"
troca('dict(tipo="lista", titulo="Também nesta edição", itens=s["itens"])', 'dict(tipo="lista", titulo="Fontes", itens=s["fontes"])')
troca('else "A edição completa"', 'else s["rotulo"]')
troca('{"Edição da noite" if noturna else "Edição da manhã"}', 'Em foco')

# ajustes de estilo: título da abertura menor, assinatura discreta, topo mais leve
troca('#placa-txt{', '''.abre.foco{width:100%}.abre-h{font-size:92px;margin-bottom:0}.local{font-family:'Geist Mono',monospace;font-size:30px;text-transform:uppercase;letter-spacing:.06em;color:var(--azul);margin-top:34px}
.assin{position:absolute;left:0;right:0;bottom:-330px;display:flex;align-items:center;gap:18px;font-family:'Geist Mono',monospace;font-size:22px;text-transform:uppercase;letter-spacing:.05em;color:var(--cinza)}
.assin svg{width:54px;height:54px}.topo svg{width:72px;height:72px}.nome{font-size:36px}
#placa-txt{''')

# a assinatura da abertura fica fora da área útil de propósito; a conferência de altura ignora essa cena
troca('if(mi.scrollHeight>mi.clientHeight+2)return true;', 'if(mi.scrollHeight>mi.clientHeight+2&&!mi.querySelector(\'.assin\'))return true;')

exec(compile(src, "gerar_animacao.py (Em foco)", "exec"))
