"""
Exportacao da janela usada pela demonstracao do portfolio.

A demo abre direto do disco, sem servidor, entao ela nao pode buscar
arquivo nenhum com fetch. A saida daqui e um arquivo javascript que
declara uma variavel global com os dados, e a pagina carrega com uma
tag script comum, que funciona em file sem reclamar.

A janela vem do conjunto de teste, com as predicoes do modelo de
verdade ja calculadas. Nada na demo e simulado: a pagina so reproduz,
minuto a minuto, o que o sistema viu e o que ele respondeu.
"""

import json
import os

from .dados import ALVO_CLASSIFICACAO, ALVO_REGRESSAO

# limites da fracao de chuva para a janela ser interessante: precisa
# ter evento de chuva, mas tambem trecho seco antes e depois para a
# transicao aparecer na tela
CHUVA_MINIMA = 0.03
CHUVA_MAXIMA = 0.60

# tamanho maximo exportado, em minutos
JANELA_MAXIMA = 2880


def escolher_janela(teste):
    """
    Escolhe a serie do teste mais interessante para a demo.

    Cada simulation_id e uma serie continua de um enlace, uma estacao
    numa frequencia. Filtrar por ela primeiro e obrigatorio: sem isso
    as series ficam intercaladas e a linha do tempo vira ruido.
    """
    grupos = teste.groupby("simulation_id", observed=True)

    melhor_id = None
    melhor_acumulado = -1.0
    for sim_id, grupo in grupos:
        fracao = float(grupo[ALVO_CLASSIFICACAO].mean())
        if not (CHUVA_MINIMA <= fracao <= CHUVA_MAXIMA):
            continue
        acumulado = float(grupo[ALVO_REGRESSAO].sum())
        if acumulado > melhor_acumulado:
            melhor_acumulado = acumulado
            melhor_id = sim_id

    if melhor_id is None:
        # nenhuma serie dentro da faixa, fica a com mais chuva acumulada
        # para a demo nunca sair vazia
        melhor_id = grupos[ALVO_REGRESSAO].sum().idxmax()

    janela = teste[teste["simulation_id"] == melhor_id].sort_values("timestamp")
    return janela.head(JANELA_MAXIMA)


def exportar_dados_demo(janela, caminho_saida):
    """
    Escreve o arquivo dados_demo.js com a janela em formato colunar.

    Arrays separados por campo, valores arredondados, e so o inicio
    da serie como texto: como a resolucao e fixa em um minuto, cada
    indice ja diz que horas sao.
    """
    dados = {
        "estacao": str(janela["station"].iloc[0]),
        "clima": str(janela["climate"].iloc[0]),
        "frequencia_ghz": float(janela["carrier_frequency_ghz"].iloc[0]),
        "inicio_utc": janela["timestamp"].iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "passo_segundos": 60,
        "snr": [round(v, 2) for v in janela["received_snr_db"]],
        "atenuacao": [round(v, 2) for v in janela["excess_attenuation_db"]],
        "taxa_real": [round(v, 2) for v in janela[ALVO_REGRESSAO]],
        "taxa_prevista": [round(v, 2) for v in janela["taxa_prevista"]],
        "probabilidade": [round(v, 3) for v in janela["probabilidade"]],
        "limiar": round(float(janela["limiar"].iloc[0]), 3),
    }

    conteudo = "// gerado pelo main.py, fatia real do conjunto de teste\n"
    conteudo += "var DADOS_DEMO = " + json.dumps(dados) + ";\n"

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

    return caminho_saida
