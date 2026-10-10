# Em foco — vídeo dedicado a uma notícia

Formato derivado da animação diária, para notícias de impacto escolhidas pelo Marcus. Só é feito quando ele pede; não faz parte das rotinas da manhã e da noite. Fase de testes, publicação manual: o vídeo e os textos ficam na sessão para aprovação, sem commit.

## Formato
- 9:16, 1080 × 1920, fundo no azul da Prensa (`#1e3a9e`), texto claro, destaques em azul-claro.
- **Abertura:** a notícia em si — chapéu ("Em foco · <tema>"), título e uma linha com local e momento. A marca e a tiragem ficam discretas no pé ("Prensa Autômata · Matutina Nº <n>").
- **Miolo:** 3 ou 4 cenas que contam a notícia em partes (ex.: o estudo, o risco, a aprovação, quem apoia), com os mesmos módulos da diária.
- **Fecho:** "Leia em prensaautomata.com" e a lista de fontes.
- **Duração:** de 40 a 45 s. Cada cena tem 2 s de folga (a diária tem 1 s) e a abertura dura pelo menos 5,6 s.

## Apuração
- Se a notícia tem texto na edição, use os fatos e números da edição.
- Se ela saiu só como manchete (por exemplo, no Giro), apure: cada fato em duas fontes abertas; o que só uma fonte traz vai atribuído ("segundo o Guardian").
- Mesma voz da diária: interpretar e conectar, sem opinar; os lados envolvidos com espaço, inclusive quem não respondeu; nada cita o Claude, só "IA".

## JSON
Escreva `/tmp/foco.json` com um script python (exemplo completo em `scripts/exemplo-foco.json`):
```
{"slug": "AAAA-MM-DD-foco-<assunto>",
 "meta": "Em foco · Matutina Nº <n> · <d> <mês abreviado> <ano>",
 "abertura": {"chapeu": "Em foco · <tema>", "titulo": "...", "local": "<lugar> · <momento>", "tiragem": "Prensa Autômata · Matutina Nº <n>"},
 "cenas": [{"rotulo": "...", "fantasma": "...", "titulo": "até 60 caracteres", "modulos": [...]}],
 "fecho": {"rotulo": "Fontes", "fantasma": "PRENSA", "fontes": ["Veículo, data", "..."]}}
```
Os módulos são os da diária (`texto`, `numeros`, `barras`, `colunas`, `placar`, `limiar`, `distancia`, `nota`), com as mesmas regras: números iguais aos das fontes, escala real, contagens que partem de 0 ou de um ponto neutro. Evite `numeros` com `lado_a_lado` para números de mais de 4 dígitos (ex.: 14.000 e 7.000 se cortam); use `barras`.

## Gerar
Na raiz do repositório: `python3 scripts/gerar_foco.py /tmp/foco.json` (mesmos requisitos da diária: playwright e ffmpeg). Ele grava `saida-animacao/<slug>.mp4` e `<slug>-quadros.jpg`. Se aparecer "ESTOURO", encurte a cena; confira a folha de quadros com os próprios olhos. O `gerar_foco.py` reaproveita o `gerar_animacao.py` sem alterá-lo e para com erro se o original mudar a ponto de quebrar o derivado.

## Textos que acompanham
- **Instagram** (até 1.000 caracteres): o título na primeira linha; 3 a 5 frases com os fatos principais, incluindo o outro lado; "Mais notícias do dia: link na bio."; "Produzido por IA, com fontes em cada notícia."; hashtags #prensaautomata #jornalismo #noticias e uma do tema (ex.: #saudeglobal; #brasil quando a notícia for brasileira).
- **X** (até 260 caracteres, contando o link): o título, mais um fato curto, e o link da edição do dia.
Conte os caracteres com python antes de entregar.
