"""
Avaliacao do previsor no conjunto de teste.

O teste e tocado uma unica vez, aqui. Todas as decisoes de treino,
parada antecipada, limiar de decisao e ablacao, acontecem antes,
usando so treino e validacao.

Duas leituras do erro de regressao saem juntas. A composta usa todos
os minutos do teste, e o numero comparavel com os baselines do
dataset. A condicional usa so os minutos com chuva de verdade, e o
numero honesto, porque a maioria seca zera o erro global e faz o
resultado parecer melhor do que e.
"""

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from .dados import preparar_matriz
from .modelo import PrevisorDeChuva


def avaliar(previsor, X_teste, y_evento, y_taxa):
    """Roda o previsor no teste e devolve um dicionario de metricas."""
    evento_previsto, taxa_prevista, probabilidade = previsor.prever(X_teste)

    y_evento = y_evento.to_numpy()
    y_taxa = y_taxa.to_numpy()

    # matriz de confusao com contagens cruas, na ordem
    # [[seco certo, alarme falso], [chuva perdida, chuva certa]]
    matriz = confusion_matrix(y_evento, evento_previsto)

    metricas = {
        "limiar": previsor.limiar,
        "f1": f1_score(y_evento, evento_previsto),
        "precisao": precision_score(y_evento, evento_previsto),
        "revocacao": recall_score(y_evento, evento_previsto),
        "matriz_confusao": matriz,
        "rmse": float(np.sqrt(mean_squared_error(y_taxa, taxa_prevista))),
        "mae": float(mean_absolute_error(y_taxa, taxa_prevista)),
        "r2": float(r2_score(y_taxa, taxa_prevista)),
    }

    # a leitura condicional: erro so onde choveu de verdade
    chuva = y_evento == 1
    metricas["rmse_na_chuva"] = float(np.sqrt(mean_squared_error(y_taxa[chuva], taxa_prevista[chuva])))
    metricas["mae_na_chuva"] = float(mean_absolute_error(y_taxa[chuva], taxa_prevista[chuva]))

    # os vetores completos seguem junto porque o grafico de dispersao
    # do relatorio precisa deles
    metricas["taxa_real_teste"] = y_taxa
    metricas["taxa_prevista_teste"] = taxa_prevista

    return metricas, evento_previsto, taxa_prevista, probabilidade


def comparar_estagios(conjuntos):
    """
    Treina tres versoes reduzidas do previsor e mede na validacao
    quanto cada estagio de features acrescenta.

    Versoes mais leves, com menos arvores, porque aqui interessa a
    comparacao entre estagios e nao o melhor numero absoluto.
    """
    combinacoes = [
        ("so fisica do enlace (A)", ("A",)),
        ("fisica e dinamica do sinal (A+B)", ("A", "B")),
        ("completo com coeficientes ITU (A+B+C)", ("A", "B", "C")),
    ]

    resultados = []
    for nome, estagios in combinacoes:
        X_treino, ev_treino, tx_treino = preparar_matriz(conjuntos["treino"], estagios)
        X_val, ev_val, tx_val = preparar_matriz(conjuntos["validacao"], estagios)

        versao = PrevisorDeChuva(n_estimators=200)
        versao.treinar(X_treino, ev_treino, tx_treino, X_val, ev_val, tx_val)

        _, taxa_prevista, probabilidade = versao.prever(X_val)
        evento_previsto = (probabilidade >= versao.limiar).astype(int)

        resultados.append({
            "nome": nome,
            "f1": f1_score(ev_val.to_numpy(), evento_previsto),
            "rmse": float(np.sqrt(mean_squared_error(tx_val.to_numpy(), taxa_prevista))),
        })

    return resultados


def tabela_comparativa(metricas, baselines):
    """Linhas de texto prontas comparando o pipeline com os baselines."""
    analitico = baselines["analytical_inverse"]
    xgb_cls = baselines["xgboost_classifier"]
    xgb_reg = baselines["xgboost_regressor"]

    linhas = []
    linhas.append("  %-34s %8s %8s %8s" % ("", "F1", "RMSE", "MAE"))
    linhas.append("  %-34s %8.4f %8.2f %8s" % ("Inversao analitica ITU-R", analitico["f1"], analitico["rmse"], "-"))
    linhas.append("  %-34s %8.4f %8.2f %8.2f" % ("Baseline XGBoost do dataset", xgb_cls["f1"], xgb_reg["rmse"], xgb_reg["mae"]))
    linhas.append("  %-34s %8.4f %8.2f %8.2f" % ("Este pipeline", metricas["f1"], metricas["rmse"], metricas["mae"]))
    return linhas
