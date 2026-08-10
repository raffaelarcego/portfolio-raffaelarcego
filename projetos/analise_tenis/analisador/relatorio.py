"""
Relatorio final da analise.

Quando o video termina, ou quando o usuario encerra com a tecla q,
este modulo pega tudo que foi acumulado durante a exibicao e salva
na pasta de resultados: um resumo em texto, o mapa de calor de cada
jogador e a linha do tempo dos pontos.

O KMeans entra aqui de novo para duas coisas: encontrar as zonas
preferidas de cada jogador e refinar a separacao entre pontos e
pausas usando o historico completo de movimento.
"""

import os
from datetime import datetime

import numpy as np
import matplotlib

# modo sem janela do matplotlib, os graficos so precisam ir para o disco
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .quadra import Quadra
from .agrupamento import zonas_preferidas, separar_pontos_e_pausas


def gerar_relatorio(pasta_resultados, nome_video, duracao_segundos,
                    estat_frente, estat_fundo, medidor, fps):
    """Salva todos os arquivos do relatorio e devolve os caminhos."""
    os.makedirs(pasta_resultados, exist_ok=True)

    # prefixo com a data para nunca sobrescrever analises anteriores
    momento = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(pasta_resultados, momento + "_" + nome_video)

    # o KMeans refina a contagem de pontos feita ao vivo, agora
    # olhando o historico de movimento da partida inteira
    trechos = separar_pontos_e_pausas(medidor.historico, fps)

    arquivos = [
        _salvar_texto(base, nome_video, duracao_segundos,
                      estat_frente, estat_fundo, trechos),
        _salvar_calor(base, estat_frente, estat_fundo),
    ]

    caminho_tempo = _salvar_linha_do_tempo(base, trechos, duracao_segundos)
    if caminho_tempo:
        arquivos.append(caminho_tempo)

    return arquivos


def _salvar_texto(base, nome_video, duracao, estat_frente, estat_fundo, trechos):
    """Escreve o resumo da partida num arquivo de texto simples."""
    caminho = base + "_resumo.txt"

    linhas = []
    linhas.append("RELATORIO DE ANALISE DA PARTIDA")
    linhas.append("Video analisado: " + nome_video)
    linhas.append("Data da analise: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    linhas.append("Duracao analisada: %.1f segundos" % duracao)
    linhas.append("")

    for estat in (estat_frente, estat_fundo):
        linhas.append(estat.nome)
        linhas.append("  Distancia percorrida: %.1f metros" % estat.distancia_m)
        linhas.append("  Velocidade media: %.1f km/h" % estat.velocidade_media_kmh())
        linhas.append("  Velocidade maxima: %.1f km/h" % estat.velocidade_maxima_kmh)
        linhas.append("  Presenca na deteccao: %.0f%% dos quadros" % estat.taxa_de_deteccao())

        # zonas preferidas encontradas por agrupamento das posicoes
        zonas = zonas_preferidas(estat.posicoes)
        if zonas:
            linhas.append("  Zonas preferidas na quadra:")
            for i, zona in enumerate(zonas, start=1):
                cx, cy = zona["centro"]
                linhas.append("    Zona %d: %.0f%% do tempo, centro em x %.1f m e y %.1f m"
                              % (i, zona["porcentagem"], cx, cy))
        linhas.append("")

    if trechos:
        duracoes = [fim - inicio for inicio, fim in trechos]
        linhas.append("Pontos disputados (separados por machine learning)")
        linhas.append("  Quantidade de pontos: %d" % len(trechos))
        linhas.append("  Duracao media dos pontos: %.1f segundos" % float(np.mean(duracoes)))
        linhas.append("  Ponto mais longo: %.1f segundos" % float(np.max(duracoes)))
    else:
        linhas.append("Nao foi possivel separar pontos e pausas neste video.")

    linhas.append("")
    linhas.append("As distancias e velocidades estao em unidades reais, calculadas")
    linhas.append("pela projecao da quadra feita na calibracao.")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

    return caminho


def _salvar_calor(base, estat_frente, estat_fundo):
    """Mapa de calor dos dois jogadores lado a lado, visto de cima."""
    caminho = base + "_mapa_de_calor.png"

    fig, eixos = plt.subplots(1, 2, figsize=(8, 6))

    for eixo, estat in zip(eixos, (estat_frente, estat_fundo)):
        # o extent coloca os eixos em metros de quadra de verdade
        eixo.imshow(estat.grade_calor, cmap="hot", aspect="auto",
                    extent=[0, Quadra.LARGURA, Quadra.COMPRIMENTO, 0])
        eixo.set_title(estat.nome, fontsize=10)
        eixo.set_xlabel("Largura (m)")
        eixo.set_ylabel("Comprimento (m)")

        # a linha da rede ajuda a ler o mapa
        eixo.axhline(Quadra.COMPRIMENTO / 2.0, color="white", linewidth=1)

    fig.suptitle("Ocupacao da quadra durante a partida")
    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho


def _salvar_linha_do_tempo(base, trechos, duracao):
    """Faixas verdes mostrando quando havia ponto em disputa."""
    if not trechos:
        return None

    caminho = base + "_linha_do_tempo.png"

    fig, eixo = plt.subplots(figsize=(9, 2.5))
    for inicio, fim in trechos:
        eixo.axvspan(inicio, fim, color="#4a9", alpha=0.8)

    eixo.set_xlim(0, duracao)
    eixo.set_yticks([])
    eixo.set_xlabel("Tempo (segundos)")
    eixo.set_title("Linha do tempo: faixas verdes sao pontos em disputa")

    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)

    return caminho
