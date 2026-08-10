"""
Relatorio final da avaliacao.

Quando o pipeline termina, este modulo pega as metricas do teste, a
ablacao de estagios e as importancias dos modelos e salva tudo na
pasta de resultados: um resumo em texto, a matriz de confusao, a
dispersao do previsto contra o real, a serie temporal da janela da
demo e as importancias em barras.

As cores dos graficos repetem o par usado no resto do portfolio,
azul para o previsto e laranja para o real, escolhido por ser
legivel tambem para quem tem daltonismo.
"""

import os
from datetime import datetime

import numpy as np
import matplotlib

# modo sem janela do matplotlib, os graficos so precisam ir para o disco
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .avaliacao import tabela_comparativa
from .dados import ALVO_CLASSIFICACAO, ALVO_REGRESSAO

COR_PREVISTO = "#0072B2"
COR_REAL = "#D55E00"


def gerar_relatorio(pasta_resultados, conjuntos, metricas, ablacao,
                    baselines, importancias, janela):
    """Salva todos os arquivos do relatorio e devolve os caminhos."""
    os.makedirs(pasta_resultados, exist_ok=True)

    # prefixo com a data para nunca sobrescrever avaliacoes anteriores
    momento = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(pasta_resultados, momento + "_predicao_chuva")

    arquivos = [
        _salvar_texto(base, conjuntos, metricas, ablacao, baselines, importancias),
        _salvar_matriz_confusao(base, metricas["matriz_confusao"]),
        _salvar_dispersao(base, metricas),
        _salvar_serie_temporal(base, janela),
        _salvar_importancias(base, importancias),
    ]
    return arquivos


def _salvar_texto(base, conjuntos, metricas, ablacao, baselines, importancias):
    """Escreve o resumo da avaliacao num arquivo de texto simples."""
    caminho = base + "_resumo.txt"

    treino = conjuntos["treino"]
    validacao = conjuntos["validacao"]
    teste = conjuntos["teste"]

    linhas = []
    linhas.append("RELATORIO DO PREVISOR DE CHUVA POR TELEMETRIA DE SATELITE")
    linhas.append("Data da avaliacao: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    linhas.append("")
    linhas.append("Dados")
    linhas.append("  Treino: %d minutos, %.0f%% com chuva" % (len(treino), 100 * treino[ALVO_CLASSIFICACAO].mean()))
    linhas.append("  Validacao: %d minutos, %.0f%% com chuva" % (len(validacao), 100 * validacao[ALVO_CLASSIFICACAO].mean()))
    linhas.append("  Teste: %d minutos, %.0f%% com chuva" % (len(teste), 100 * teste[ALVO_CLASSIFICACAO].mean()))
    linhas.append("")

    linhas.append("Deteccao do evento de chuva (teste)")
    linhas.append("  F1: %.4f" % metricas["f1"])
    linhas.append("  Precisao: %.4f" % metricas["precisao"])
    linhas.append("  Revocacao: %.4f" % metricas["revocacao"])
    linhas.append("  Limiar de decisao escolhido na validacao: %.2f" % metricas["limiar"])
    linhas.append("")

    linhas.append("Intensidade da chuva em mm/h (teste)")
    linhas.append("  Em todos os minutos, comparavel aos baselines:")
    linhas.append("    RMSE: %.3f   MAE: %.3f   R2: %.4f" % (metricas["rmse"], metricas["mae"], metricas["r2"]))
    linhas.append("  So nos minutos com chuva de verdade, a leitura honesta:")
    linhas.append("    RMSE: %.3f   MAE: %.3f" % (metricas["rmse_na_chuva"], metricas["mae_na_chuva"]))
    linhas.append("")

    linhas.append("Comparacao com os baselines que acompanham o dataset")
    linhas += tabela_comparativa(metricas, baselines)
    linhas.append("  Os baselines usam o conjunto completo de features, que inclui")
    linhas.append("  as colunas de atenuacao vazadas. A tabela fica como referencia,")
    linhas.append("  nao como disputa justa: este pipeline joga sem elas.")
    linhas.append("")

    linhas.append("Quanto cada estagio de features acrescenta (validacao)")
    linhas.append("  %-40s %8s %8s" % ("", "F1", "RMSE"))
    for versao in ablacao:
        linhas.append("  %-40s %8.4f %8.2f" % (versao["nome"], versao["f1"], versao["rmse"]))
    linhas.append("")

    for nome, titulo in (("classificador", "Deteccao"), ("regressor", "Intensidade")):
        linhas.append("Features mais importantes por ganho, modelo de " + titulo.lower())
        for feature, ganho in importancias[nome][:10]:
            linhas.append("  %-32s %10.1f" % (feature, ganho))
        linhas.append("")

    linhas.append("As colunas de atenuacao do dataset sao a formula ITU-R P.838")
    linhas.append("aplicada na propria taxa de chuva, quase sem ruido: inverter a")
    linhas.append("formula em uma linha recupera o alvo com RMSE de 0.03 mm/h.")
    linhas.append("Este pipeline exclui essas colunas de proposito e le apenas o")
    linhas.append("SNR ruidoso e a geometria do enlace. Os numeros acima medem")
    linhas.append("previsao de verdade: separar a queda causada pela chuva do")
    linhas.append("ruido de cintilacao do proprio sinal.")
    linhas.append("")
    linhas.append("Dados: Rain Narrowcasting Benchmark (RainCast), de Satyansh Gaur.")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

    return caminho


def _salvar_matriz_confusao(base, matriz):
    """Matriz de confusao 2x2 anotada com contagens e percentuais."""
    caminho = base + "_matriz_confusao.png"

    fig, eixo = plt.subplots(figsize=(5, 4.2))
    eixo.imshow(matriz, cmap="Greens")

    total = matriz.sum()
    rotulos = ["Seco", "Chuva"]
    for linha in range(2):
        for coluna in range(2):
            valor = matriz[linha, coluna]
            # texto escuro nas celulas claras e claro nas escuras
            cor = "white" if valor > matriz.max() / 2 else "#191c1a"
            eixo.text(coluna, linha, "%d\n%.2f%%" % (valor, 100 * valor / total),
                      ha="center", va="center", color=cor, fontsize=11)

    eixo.set_xticks([0, 1], rotulos)
    eixo.set_yticks([0, 1], rotulos)
    eixo.set_xlabel("Previsto")
    eixo.set_ylabel("Real")
    eixo.set_title("Deteccao do evento de chuva no teste")

    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho


def _salvar_dispersao(base, metricas):
    """Previsto contra real em mm/h, so onde houve ou foi prevista chuva."""
    caminho = base + "_dispersao.png"

    y_real = metricas["taxa_real_teste"]
    y_previsto = metricas["taxa_prevista_teste"]

    # o grosso dos minutos e seco dos dois lados e viraria um borrao
    # em cima do zero, entao ficam so os minutos com chuva de um lado
    # ou do outro
    interessa = (y_real > 0) | (y_previsto > 0)
    y_real = y_real[interessa]
    y_previsto = y_previsto[interessa]

    fig, eixo = plt.subplots(figsize=(5.5, 5.5))
    eixo.scatter(y_real, y_previsto, s=3, alpha=0.08, color=COR_PREVISTO,
                 edgecolors="none", rasterized=True)

    maximo = float(max(y_real.max(), y_previsto.max()))
    eixo.plot([0, maximo], [0, maximo], linestyle="--", linewidth=1,
              color="#191c1a", label="Previsao perfeita")

    eixo.set_xlabel("Chuva real (mm/h)")
    eixo.set_ylabel("Chuva prevista (mm/h)")
    eixo.set_title("Previsto contra real, minutos com chuva")
    eixo.legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho


def _salvar_serie_temporal(base, janela):
    """A janela da demo em dois paineis: sinal em cima, chuva embaixo."""
    caminho = base + "_serie_temporal.png"

    horas = np.arange(len(janela)) / 60.0

    fig, (eixo_sinal, eixo_chuva) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)

    eixo_sinal.plot(horas, janela["received_snr_db"], linewidth=0.7,
                    color="#191c1a", label="SNR recebido (dB)")
    eixo_sinal.plot(horas, janela["excess_attenuation_db"], linewidth=0.9,
                    color="#98a09b", label="Atenuacao em excesso (dB)")
    eixo_sinal.set_ylabel("dB")
    eixo_sinal.legend(loc="upper right", fontsize=8)
    eixo_sinal.set_title("Enlace %s, %.0f GHz: o sinal cai quando a chuva chega"
                         % (janela["station"].iloc[0], janela["carrier_frequency_ghz"].iloc[0]))

    # a chuva real leva area preenchida e tambem uma linha propria:
    # so com a area, um pico de poucos minutos vira um fiapo invisivel
    # e a previsao parece alarme falso mesmo quando acertou
    eixo_chuva.fill_between(horas, janela[ALVO_REGRESSAO], color=COR_REAL,
                            alpha=0.35, linewidth=0)
    eixo_chuva.plot(horas, janela[ALVO_REGRESSAO], linewidth=0.9,
                    color=COR_REAL, label="Chuva real")
    eixo_chuva.plot(horas, janela["taxa_prevista"], linewidth=0.9,
                    color=COR_PREVISTO, label="Chuva prevista")
    eixo_chuva.set_ylabel("mm/h")
    eixo_chuva.set_xlabel("Horas desde o inicio da janela")
    eixo_chuva.legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho


def _salvar_importancias(base, importancias):
    """Barras horizontais de ganho, um painel por modelo."""
    caminho = base + "_importancias.png"

    fig, eixos = plt.subplots(1, 2, figsize=(10, 4.5))
    titulos = {"classificador": "Deteccao do evento", "regressor": "Intensidade da chuva"}

    for eixo, (nome, titulo) in zip(eixos, titulos.items()):
        pares = importancias[nome][:12]
        features = [par[0] for par in pares][::-1]
        ganhos = [par[1] for par in pares][::-1]

        eixo.barh(features, ganhos, color="#0a6847")
        eixo.set_title(titulo, fontsize=10)
        eixo.set_xlabel("Ganho")
        eixo.tick_params(axis="y", labelsize=8)

    fig.suptitle("Features mais importantes de cada modelo")
    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho
