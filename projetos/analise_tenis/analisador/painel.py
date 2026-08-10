"""
Parte visual da analise em tempo real.

Este modulo desenha tudo que aparece na tela: as caixas azuis nos
jogadores, os pontos vermelhos de referencia da quadra, o rastro
verde da bola, o mini-mapa com a quadra vista de cima e o painel
lateral com as estatisticas e os mapas de calor ao vivo.

So tem desenho aqui, nenhum calculo de analise. Isso deixa o loop
principal limpo e facilita mexer no visual sem medo de quebrar as
contas.
"""

import cv2
import numpy as np

from .quadra import Quadra

# cores em BGR, que é a ordem que o OpenCV usa
COR_CAIXA = (255, 80, 30)        # azul das caixas dos jogadores
COR_PONTO_QUADRA = (0, 0, 255)   # vermelho dos pontos de referencia
COR_RASTRO = (80, 220, 80)       # verde do rastro da bola
COR_BOLA = (0, 230, 255)         # amarelo da bola no mini-mapa
COR_TEXTO = (235, 235, 235)
COR_FUNDO_PAINEL = (24, 22, 20)

# dimensoes do painel lateral e do mini-mapa
LARGURA_PAINEL = 340
MAPA_LARGURA = 150
MAPA_ALTURA = 300


def desenhar_video(quadro, quadra, jogador_fundo, jogador_frente, rastro_bola):
    """Desenha as marcacoes por cima do quadro do video."""

    # pontos de referencia da quadra, projetados de volta na imagem
    for ponto in quadra.pontos_de_referencia():
        px, py = quadra.quadra_para_imagem(ponto)
        cv2.circle(quadro, (int(px), int(py)), 5, COR_PONTO_QUADRA, -1)

    # caixas dos jogadores com o rotulo em cima
    for deteccao, rotulo in ((jogador_fundo, "Jogador 2"), (jogador_frente, "Jogador 1")):
        if deteccao is None:
            continue
        x1, y1, x2, y2 = deteccao["caixa"]
        cv2.rectangle(quadro, (x1, y1), (x2, y2), COR_CAIXA, 2)
        cv2.putText(quadro, rotulo, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, COR_CAIXA, 2, cv2.LINE_AA)

    # rastro da bola, circulos que vao encolhendo conforme envelhecem
    for idade, centro in enumerate(rastro_bola):
        raio = max(2, 7 - idade)
        cv2.circle(quadro, (int(centro[0]), int(centro[1])), raio, COR_RASTRO, 2)

    return quadro


def desenhar_minimapa(quadra, posicao_fundo, posicao_frente, posicao_bola):
    """
    Monta a imagem do mini-mapa, a quadra vista de cima com os
    jogadores em azul e a bola em amarelo, igual as transmissoes.
    """
    # borda de 20 pixels em volta da quadra desenhada
    borda = 20
    mapa = np.zeros((MAPA_ALTURA + 2 * borda, MAPA_LARGURA + 2 * borda, 3), dtype=np.uint8)

    def para_mapa(posicao):
        """Converte metros da quadra para pixels do mini-mapa."""
        x = borda + posicao[0] / Quadra.LARGURA * MAPA_LARGURA
        y = borda + posicao[1] / Quadra.COMPRIMENTO * MAPA_ALTURA
        return (int(x), int(y))

    # linhas da quadra em branco
    for inicio, fim in quadra.segmentos_das_linhas():
        cv2.line(mapa, para_mapa(inicio), para_mapa(fim), (255, 255, 255), 1)

    # jogadores e bola por cima das linhas
    for posicao in (posicao_fundo, posicao_frente):
        if posicao is not None:
            cv2.circle(mapa, para_mapa(posicao), 5, (255, 120, 40), -1)
    if posicao_bola is not None and quadra.dentro_da_quadra(posicao_bola, margem_metros=3.0):
        cv2.circle(mapa, para_mapa(posicao_bola), 4, COR_BOLA, -1)

    return mapa


def desenhar_calor(grade):
    """
    Transforma a grade de contagem do jogador num mapa de calor
    colorido pequeno, para caber no painel lateral.
    """
    if grade.max() > 0:
        normalizada = (grade / grade.max() * 255).astype(np.uint8)
    else:
        normalizada = grade.astype(np.uint8)

    # o desfoque espalha os pontos e deixa o mapa continuo,
    # sem ele o resultado fica quadriculado
    normalizada = cv2.GaussianBlur(normalizada, (5, 5), 0)
    colorido = cv2.applyColorMap(normalizada, cv2.COLORMAP_JET)

    # celulas nunca visitadas ficam escuras em vez de azul forte,
    # o mapa fica mais limpo de ler
    colorido[grade < 0.5] = (30, 30, 30)

    return cv2.resize(colorido, (110, 220), interpolation=cv2.INTER_NEAREST)


def montar_tela(quadro, quadra, estat_frente, estat_fundo, medidor,
                posicao_fundo, posicao_frente, posicao_bola, tempo_s):
    """
    Junta tudo numa imagem so: o video anotado a esquerda e o painel
    com mini-mapa, estatisticas e mapas de calor a direita.
    """
    altura = quadro.shape[0]
    painel = np.full((altura, LARGURA_PAINEL, 3), COR_FUNDO_PAINEL, dtype=np.uint8)

    def texto(mensagem, x, y, escala=0.5, cor=COR_TEXTO, grossura=1):
        cv2.putText(painel, mensagem, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    escala, cor, grossura, cv2.LINE_AA)

    # cabecalho do painel com o relogio da analise
    texto("ANALISE EM TEMPO REAL", 16, 30, 0.55, (120, 220, 160), 2)
    minutos = int(tempo_s // 60)
    segundos = int(tempo_s % 60)
    texto("tempo %02d:%02d" % (minutos, segundos), 16, 54)

    # situacao do ponto, verde quando em disputa
    if medidor.ponto_ativo:
        texto("PONTO EM DISPUTA", 160, 54, 0.5, (80, 220, 80), 2)
    texto("pontos: %d" % medidor.total_pontos, 16, 78)

    # mini-mapa centralizado na parte de cima do painel
    mapa = desenhar_minimapa(quadra, posicao_fundo, posicao_frente, posicao_bola)
    mh, mw = mapa.shape[:2]
    mx = (LARGURA_PAINEL - mw) // 2
    my = 92
    if my + mh < altura:
        painel[my:my + mh, mx:mx + mw] = mapa

    # bloco de numeros de cada jogador
    y = my + mh + 30
    for estat in (estat_frente, estat_fundo):
        if y + 70 > altura:
            break
        texto(estat.nome, 16, y, 0.55, (255, 170, 90), 2)
        texto("dist %.0f m" % estat.distancia_m, 16, y + 22)
        texto("vel %.1f km/h" % estat.velocidade_kmh, 120, y + 22)
        texto("max %.1f km/h" % estat.velocidade_maxima_kmh, 225, y + 22)
        y += 52

    # mapas de calor lado a lado na parte de baixo, se houver espaco
    calor_frente = desenhar_calor(estat_frente.grade_calor)
    calor_fundo = desenhar_calor(estat_fundo.grade_calor)
    ch, cw = calor_frente.shape[:2]
    if y + ch + 30 < altura:
        texto("mapa de calor  J1 / J2", 16, y + 6, 0.45)
        painel[y + 16:y + 16 + ch, 40:40 + cw] = calor_frente
        painel[y + 16:y + 16 + ch, 60 + cw:60 + 2 * cw] = calor_fundo

    return np.hstack([quadro, painel])
