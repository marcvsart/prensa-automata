# Lista as notícias publicadas nos últimos dias, para a pauta não repetir assunto.
# Uso: python3 scripts/publicadas.py            (últimos 14 dias; giros, só os últimos 7)
#      python3 scripts/publicadas.py --dias 30 --dias-giro 14
# Lê só os JSON de edicoes/; não grava nada. Janela móvel: não precisa de reset.
import argparse, glob, json, os
from datetime import date, datetime, timedelta, timezone

GIROS = {"giro_brasil", "giro"}   # muitas manchetes por edição: janela menor para a lista não pesar
SECOES = [("manchete", "Manchete"), ("brasil", "Brasil"), ("giro_brasil", "Giro pelo Brasil"),
          ("mundo", "Mundo"), ("ia", "IA"), ("giro", "Giro pelo mundo"),
          ("ciencia", "Ciência"), ("esporte", "Esporte")]

def titulos(chave, valor):
    """Títulos de uma seção, seja ela um item, uma lista de itens ou o giro por região."""
    if isinstance(valor, dict):
        return [valor["titulo"]] if valor.get("titulo") else []
    saida = []
    for item in valor or []:
        if isinstance(item, dict) and "itens" in item:          # giro: [{"regiao", "itens": [...]}]
            saida += [f'{item.get("regiao", "")}: {x["titulo"]}' for x in item["itens"] if x.get("titulo")]
        elif isinstance(item, dict) and item.get("titulo"):
            saida.append(f'{item["lugar"]}: {item["titulo"]}' if item.get("lugar") else item["titulo"])
    return saida

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=14)
    ap.add_argument("--dias-giro", type=int, default=7)
    a = ap.parse_args()
    hoje = (datetime.now(timezone.utc) - timedelta(hours=3)).date()   # São Paulo (UTC−3, sem horário de verão)
    inicio = hoje - timedelta(days=a.dias)
    inicio_giro = hoje - timedelta(days=a.dias_giro)
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "edicoes")
    arquivos = sorted(glob.glob(os.path.join(raiz, "*.json")), reverse=True)
    print(f"Notícias publicadas de {inicio:%d/%m} a {hoje:%d/%m}; giros desde {inicio_giro:%d/%m} (mais recentes primeiro)")
    for arq in arquivos:
        slug = os.path.basename(arq)[:-5]
        try:
            dia = date.fromisoformat(slug[:10])
        except ValueError:
            continue
        if not (inicio <= dia <= hoje):
            continue
        ed = json.load(open(arq, encoding="utf-8"))
        print(f"\n## {dia:%d/%m} · {'noite' if slug.endswith('-noite') else 'manhã'}")
        for chave, nome in SECOES:
            if chave in GIROS and dia < inicio_giro:
                continue
            for t in titulos(chave, ed.get(chave)):
                print(f"- {nome}: {t}")

if __name__ == "__main__":
    main()
