"""
Carregamento do dataset e preparo das matrizes de features.

Todo o conhecimento sobre o esquema das colunas mora aqui. Os outros
modulos nunca citam nome de coluna cru: pedem a matriz pronta e
recebem junto os dois alvos, o evento de chuva e a taxa em mm/h.

As features vem em tres estagios, na mesma divisao que o dataset
documenta, so que depuradas do vazamento descrito abaixo:

    A  fisica do enlace que um receptor conhece sem medir a chuva
       (SNR, perdas de espaco livre e de gases, geometria)
    B  janelas moveis e deltas do SNR, mais estacao e clima
    C  coeficientes das recomendacoes ITU-R, cientes da frequencia

Colunas deixadas de fora, e o porque:

    rain_rate_mm_per_hr, rain_event   sao os alvos

    specific_attenuation_db_per_km,
    excess_attenuation_db,
    attenuation_roll_mean,
    attenuation_roll_std,
    attenuation_delta                 vazamento de alvo. O simulador
                                      entrega a atenuacao de chuva
                                      quase sem ruido, e ela e a
                                      formula da ITU-R P.838 aplicada
                                      na propria taxa: inverter a
                                      formula em uma linha recupera a
                                      chuva com RMSE de 0.03 mm/h.
                                      Com essas colunas o modelo nao
                                      preve nada, so desfaz uma conta.
                                      Sem elas a tarefa vira real:
                                      inferir a chuva do SNR ruidoso.

    simulation_id                     identificador da rodada do
                                      simulador, decoraria o regime
    timestamp                         so serve para ordenar e plotar
    itu_R001, itu_P_rain, gs_*,
    season_sin, season_cos            climatologia estatica da
                                      estacao, quase constante por
                                      serie, decoraria a estacao em
                                      vez de ler o sinal
"""

import json
import os

import pandas as pd

ALVO_REGRESSAO = "rain_rate_mm_per_hr"
ALVO_CLASSIFICACAO = "rain_event"

# colunas presentes em todos os estagios
FEATURES_BASE = [
    "received_snr_db",
    "carrier_frequency_ghz",
    "elevation_angle_deg",
    "slant_range_km",
]

# estagio A: fisica que o receptor conhece de antemao, perdas de
# espaco livre e de gases vem de modelo, nao da medicao da chuva
FEATURES_ESTAGIO_A = [
    "fspl_db",
    "gaseous_attenuation_db",
    "effective_path_length_km",
    "rain_height_km",
]

# estagio B: janelas moveis e deltas do SNR, o modelo enxerga a
# dinamica do sinal e consegue separar chuva de ruido de cintilacao
FEATURES_ESTAGIO_B = [
    "snr_roll_mean_5min",
    "snr_roll_std_5min",
    "snr_roll_max_5min",
    "snr_roll_min_5min",
    "snr_roll_mean_30min",
    "snr_roll_std_30min",
    "snr_delta",
]

# estagio C: coeficientes k e alpha da ITU-R P.838, que dependem
# da frequencia da portadora
FEATURES_ESTAGIO_C = [
    "frequency_ghz",
    "itu_k",
    "itu_alpha",
]

# categoricas entram junto com os estagios B e C, como no benchmark
CATEGORICAS = ["station", "climate"]


def carregar_conjuntos(pasta_dataset):
    """
    Le os tres parquets e devolve {"treino", "validacao", "teste"}.

    As colunas categoricas viram dtype category com o mesmo conjunto
    de categorias nos tres splits. Sem essa unificacao o XGBoost
    embaralha os codigos entre treino e teste em silencio.
    """
    nomes = {"treino": "train", "validacao": "validation", "teste": "test"}
    conjuntos = {}
    for apelido, arquivo in nomes.items():
        caminho = os.path.join(pasta_dataset, arquivo + ".parquet")
        conjuntos[apelido] = pd.read_parquet(caminho)

    for coluna in CATEGORICAS:
        # o conjunto de categorias vem da uniao dos tres splits
        valores = sorted(set().union(*(set(df[coluna].unique()) for df in conjuntos.values())))
        tipo = pd.CategoricalDtype(categories=valores)
        for df in conjuntos.values():
            df[coluna] = df[coluna].astype(tipo)

    return conjuntos


def preparar_matriz(df, estagios=("A", "B", "C")):
    """
    Monta a matriz de features e devolve (X, y_evento, y_taxa).

    O parametro estagios permite treinar versoes reduzidas, usadas
    na ablacao do relatorio: so A, A com B, e o conjunto completo.
    """
    colunas = list(FEATURES_BASE)
    if "A" in estagios:
        colunas += FEATURES_ESTAGIO_A
    if "B" in estagios:
        colunas += FEATURES_ESTAGIO_B
    if "C" in estagios:
        colunas += FEATURES_ESTAGIO_C
    if "B" in estagios or "C" in estagios:
        colunas += CATEGORICAS

    X = df[colunas]
    y_evento = df[ALVO_CLASSIFICACAO]
    y_taxa = df[ALVO_REGRESSAO]
    return X, y_evento, y_taxa


def carregar_baselines(pasta_dataset):
    """Le as metricas de referencia publicadas junto do dataset."""
    caminho = os.path.join(pasta_dataset, "baseline_metrics.json")
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)
