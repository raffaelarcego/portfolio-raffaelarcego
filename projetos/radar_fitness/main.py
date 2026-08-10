"""
Radar do mercado fitness brasileiro.

Le a base de CNPJ da Receita Federal, isola as academias pelo CNAE
9313-1/00 e responde quatro perguntas: quanto o mercado cresce, quanto
tempo uma academia vive, quando elas abrem e onde ainda ha espaco.

Rodar tudo:

    python main.py

A primeira rodada baixa uns 5 GB da Receita e leva um tempo. As
rodadas seguintes reaproveitam o dataset filtrado e terminam em
segundos.
"""

import os

from radar import analise, coleta, exportacao, ibge, relatorio

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_DATASET = os.path.join(PASTA_PROJETO, "dataset")
PASTA_RESULTADOS = os.path.join(PASTA_PROJETO, "resultados")


def principal():
    academias_csv = os.path.join(PASTA_DATASET, "academias.csv")
    if not os.path.exists(academias_csv):
        print("dataset filtrado nao encontrado, comecando a coleta", flush=True)
        coleta.coletar(PASTA_DATASET)

    print("carregando dataset filtrado", flush=True)
    dados = analise.carregar(PASTA_DATASET)
    populacao = ibge.carregar_populacao(PASTA_DATASET)

    print("calculando as respostas", flush=True)
    resultados = {
        "referencia": coleta.PASTA_REFERENCIA,
        "cnae": "9313-1/00 atividades de condicionamento fisico",
        "visao_geral": analise.visao_geral(dados),
        "serie_anual": analise.serie_anual(dados),
        "sobrevivencia": analise.sobrevivencia_por_coorte(dados),
        "vida_mediana": analise.vida_mediana(dados),
        "sazonalidade": analise.sazonalidade(dados),
        "por_uf": analise.por_uf(dados, populacao),
        "por_municipio": analise.por_municipio(
            dados, os.path.join(PASTA_DATASET, "municipios.csv"), populacao),
    }

    relatorio.gerar(resultados, PASTA_RESULTADOS)
    exportacao.gerar(resultados, PASTA_PROJETO)
    print("pronto", flush=True)


if __name__ == "__main__":
    principal()
