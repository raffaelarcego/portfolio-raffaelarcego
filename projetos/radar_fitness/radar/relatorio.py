"""
Relatorio final em texto e graficos, salvo na pasta resultados.

Os graficos seguem o vocabulario visual do portfolio: fundo claro,
uma cor por serie e o par azul e laranja quando duas series dividem
o mesmo eixo, que e um par seguro para daltonismo. Rotulos e titulos
em portugues, sem firula.
"""

import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COR_ABERTURA = "#0072B2"
COR_FECHAMENTO = "#D55E00"
COR_UNICA = "#0a6847"
COR_TEXTO = "#191c1a"
COR_SUAVE = "#5d6360"
COR_GRADE = "#d4d9d4"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]


def _preparar_eixo(eixo):
    """Grade discreta e sem moldura, para o dado ficar na frente."""
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.spines[["left", "bottom"]].set_color(COR_GRADE)
    eixo.tick_params(colors=COR_SUAVE, labelsize=9)
    eixo.yaxis.grid(True, color=COR_GRADE, linewidth=0.6)
    eixo.set_axisbelow(True)


def _salvar(figura, pasta, prefixo, nome):
    caminho = os.path.join(pasta, f"{prefixo}_{nome}.png")
    figura.savefig(caminho, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return caminho


def grafico_serie_anual(serie, pasta, prefixo):
    anos = [item["ano"] for item in serie]
    figura, eixo = plt.subplots(figsize=(9, 4.2))
    _preparar_eixo(eixo)
    eixo.plot(anos, [item["aberturas"] for item in serie],
              color=COR_ABERTURA, linewidth=2, label="aberturas")
    eixo.plot(anos, [item["fechamentos"] for item in serie],
              color=COR_FECHAMENTO, linewidth=2, label="fechamentos")
    eixo.set_title("Academias abertas e fechadas por ano no Brasil",
                   color=COR_TEXTO, fontsize=11, loc="left")
    eixo.legend(frameon=False, labelcolor=COR_SUAVE)
    return _salvar(figura, pasta, prefixo, "serie_anual")


def grafico_sobrevivencia(coortes, pasta, prefixo):
    anos = [item["ano"] for item in coortes]
    valores = [100 * (item["sobrevivencia"] or 0) for item in coortes]
    figura, eixo = plt.subplots(figsize=(9, 4.2))
    _preparar_eixo(eixo)
    eixo.bar(anos, valores, color=COR_UNICA, width=0.72)
    eixo.set_ylim(0, 100)
    eixo.set_title("Da turma aberta em cada ano, quantas seguem ativas hoje (%)",
                   color=COR_TEXTO, fontsize=11, loc="left")
    for ano, valor in zip(anos, valores):
        eixo.text(ano, valor + 2, f"{valor:.0f}", ha="center",
                  fontsize=8, color=COR_SUAVE)
    return _salvar(figura, pasta, prefixo, "sobrevivencia")


def grafico_sazonalidade(meses, pasta, prefixo):
    valores = [100 * (item["fracao"] or 0) for item in meses]
    figura, eixo = plt.subplots(figsize=(9, 4.2))
    _preparar_eixo(eixo)
    eixo.bar(range(1, 13), valores, color=COR_UNICA, width=0.72)
    eixo.set_xticks(range(1, 13), MESES)
    eixo.set_title("Fatia das aberturas por mes do ano, 2016 a 2025 (%)",
                   color=COR_TEXTO, fontsize=11, loc="left")
    maior = max(valores)
    for posicao, valor in enumerate(valores, start=1):
        if valor == maior:
            eixo.text(posicao, valor + 0.25, f"{valor:.1f}", ha="center",
                      fontsize=9, color=COR_TEXTO, fontweight="bold")
    return _salvar(figura, pasta, prefixo, "sazonalidade")


def grafico_por_uf(ufs, pasta, prefixo):
    ordenado = sorted(ufs, key=lambda item: item["por_100k"])
    nomes = [item["uf"] for item in ordenado]
    valores = [item["por_100k"] for item in ordenado]
    figura, eixo = plt.subplots(figsize=(7, 8))
    _preparar_eixo(eixo)
    eixo.xaxis.grid(True, color=COR_GRADE, linewidth=0.6)
    eixo.yaxis.grid(False)
    eixo.barh(nomes, valores, color=COR_UNICA, height=0.68)
    eixo.set_title("Academias ativas por 100 mil habitantes, por UF",
                   color=COR_TEXTO, fontsize=11, loc="left")
    return _salvar(figura, pasta, prefixo, "por_uf")


def escrever_resumo(resultados, pasta, prefixo):
    geral = resultados["visao_geral"]
    vida = resultados["vida_mediana"]
    serie = resultados["serie_anual"]
    coortes = resultados["sobrevivencia"]
    sazonal = resultados["sazonalidade"]
    ufs = resultados["por_uf"]
    cidades = resultados["por_municipio"]

    pico = max(serie, key=lambda item: item["aberturas"])
    janeiro = sazonal[0]
    pico_mes = max(sazonal, key=lambda item: item["aberturas"])
    media_mensal = sum(item["aberturas"] for item in sazonal) / 12

    linhas = [
        "RADAR DO MERCADO FITNESS BRASILEIRO",
        f"foto da base de CNPJ da Receita Federal de {resultados['referencia']}",
        "",
        "VISAO GERAL",
        f"  registros com CNAE de academia:  {geral['total_registros']:,}",
        f"  ativas hoje:                     {geral['ativas']:,}",
        f"  baixadas:                        {geral['baixadas']:,}",
        f"  outras situacoes:                {geral['outras_situacoes']:,}",
        "",
        "RITMO",
        f"  ano com mais aberturas: {pico['ano']} ({pico['aberturas']:,})",
        f"  vida mediana das que fecharam: {vida['mediana_anos']} anos"
        f" (quartis {vida['quartil_inferior']} e {vida['quartil_superior']})",
        f"  mes de pico das aberturas: {MESES[pico_mes['mes'] - 1]}"
        f" ({100 * pico_mes['fracao']:.1f}% do ano)",
        f"  janeiro fica em {janeiro['aberturas'] / media_mensal:.2f}x a media mensal,"
        " o mito da promessa de ano novo nao aparece do lado dos donos",
        "",
        "SOBREVIVENCIA POR COORTE (% ainda ativa hoje)",
    ]
    for item in coortes:
        linhas.append(f"  {item['ano']}  {100 * item['sobrevivencia']:5.1f}%"
                      f"  ({item['ativas_hoje']:,} de {item['abertas']:,})")

    linhas += ["", "UF COM MAIS ACADEMIAS POR 100 MIL HABITANTES"]
    for item in ufs[:5]:
        linhas.append(f"  {item['uf']}  {item['por_100k']:6.1f}  ({item['ativas']:,} ativas)")
    linhas += ["", "UF COM MENOS ACADEMIAS POR 100 MIL HABITANTES"]
    for item in ufs[-5:]:
        linhas.append(f"  {item['uf']}  {item['por_100k']:6.1f}  ({item['ativas']:,} ativas)")

    linhas += ["", "CIDADES GRANDES MAIS SERVIDAS (100 mil+ habitantes)"]
    for item in cidades["mais_servidas"][:5]:
        linhas.append(f"  {item['cidade']} {item['uf']}  {item['por_100k']:6.1f} por 100k")
    linhas += ["", "CIDADES GRANDES MENOS SERVIDAS"]
    for item in cidades["menos_servidas"][:5]:
        linhas.append(f"  {item['cidade']} {item['uf']}  {item['por_100k']:6.1f} por 100k")

    linhas += [
        "",
        f"juncao com populacao do IBGE cobriu"
        f" {100 * cidades['cobertura_juncao']:.1f}% das academias ativas",
    ]

    caminho = os.path.join(pasta, f"{prefixo}_resumo.txt")
    with open(caminho, "w", encoding="utf-8") as saida:
        saida.write("\n".join(linhas) + "\n")
    return caminho


def gerar(resultados, pasta_resultados):
    """Escreve o resumo e os quatro graficos, com prefixo de data e hora."""
    os.makedirs(pasta_resultados, exist_ok=True)
    prefixo = time.strftime("%Y%m%d_%H%M%S") + "_radar_fitness"
    escrever_resumo(resultados, pasta_resultados, prefixo)
    grafico_serie_anual(resultados["serie_anual"], pasta_resultados, prefixo)
    grafico_sobrevivencia(resultados["sobrevivencia"], pasta_resultados, prefixo)
    grafico_sazonalidade(resultados["sazonalidade"], pasta_resultados, prefixo)
    grafico_por_uf(resultados["por_uf"], pasta_resultados, prefixo)
    print(f"relatorio salvo em {pasta_resultados} com prefixo {prefixo}", flush=True)
