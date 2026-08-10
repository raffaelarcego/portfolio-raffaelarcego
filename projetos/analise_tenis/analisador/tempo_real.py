"""
Loop principal da analise em tempo real.

Aqui é onde tudo se encontra. Para cada quadro do video a rede
neural detecta pessoas e bola, a quadra converte as posicoes para
metros, as estatisticas sao atualizadas e o painel desenha o
resultado na tela, tudo dentro do mesmo ciclo.

Durante a exibicao funcionam estas teclas:
    espaco  pausa e continua
    q       encerra a analise e gera o relatorio com o que ja foi visto
"""

import os
import time

import cv2

from .deteccao import DetectorYolo, escolher_jogadores
from .quadra import Quadra, calibrar_com_cliques, calibracao_automatica
from .estatisticas import EstatisticasDoJogador, MedidorDeMovimento
from .painel import montar_tela, desenhar_video
from .relatorio import gerar_relatorio

# quantos circulos do rastro da bola ficam na tela
TAMANHO_RASTRO = 8

# largura maxima da janela na tela, videos maiores sao reduzidos
LARGURA_MAXIMA_TELA = 1500


class AnalisadorTempoReal:
    """Roda a analise completa de um video, com ou sem janela."""

    def __init__(self, caminho_video, pasta_resultados,
                 cantos=None, mostrar=True, max_quadros=None):
        """
        O parametro cantos permite passar a calibracao pronta, util
        para testes. O mostrar desliga a janela, e o max_quadros
        limita o processamento, os dois tambem pensados para testes.
        """
        self.caminho_video = caminho_video
        self.pasta_resultados = pasta_resultados
        self.cantos = cantos
        self.mostrar = mostrar
        self.max_quadros = max_quadros

    def executar(self):
        """Processa o video inteiro e devolve os caminhos do relatorio."""
        captura = cv2.VideoCapture(self.caminho_video)
        if not captura.isOpened():
            raise ValueError("Nao consegui abrir o video: " + self.caminho_video)

        fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
        intervalo = 1.0 / fps

        ok, primeiro_quadro = captura.read()
        if not ok:
            captura.release()
            raise ValueError("O video nao tem quadros para analisar.")

        # calibracao da quadra: usa a que veio pronta, ou pede os
        # cliques do usuario, ou cai na estimativa automatica
        cantos = self.cantos
        if cantos is None:
            if self.mostrar:
                cantos = calibrar_com_cliques(primeiro_quadro)
                if cantos is None:
                    captura.release()
                    raise ValueError("Calibracao cancelada pelo usuario.")
            else:
                altura, largura = primeiro_quadro.shape[:2]
                cantos = calibracao_automatica(largura, altura)

        quadra = Quadra(cantos)

        # o carregamento do modelo YOLO acontece aqui e demora alguns
        # segundos na primeira vez, depois fica em cache
        detector = DetectorYolo()

        estat_frente = EstatisticasDoJogador("Jogador 1 (frente)")
        estat_fundo = EstatisticasDoJogador("Jogador 2 (fundo)")
        medidor = MedidorDeMovimento(fps)
        rastro_bola = []

        quadro = primeiro_quadro
        indice = 0
        janela = "Analise de Tenis"

        try:
            while True:
                # a rede neural encontra as pessoas e a bola no quadro
                pessoas, bolas = detector.detectar(quadro)
                jogador_fundo, jogador_frente = escolher_jogadores(pessoas, quadra)

                # posicoes dos pes convertidas para metros na quadra
                posicao_fundo = None
                posicao_frente = None
                if jogador_fundo is not None:
                    posicao_fundo = quadra.imagem_para_quadra(jogador_fundo["pe"])
                if jogador_frente is not None:
                    posicao_frente = quadra.imagem_para_quadra(jogador_frente["pe"])

                estat_fundo.atualizar(posicao_fundo, intervalo)
                estat_frente.atualizar(posicao_frente, intervalo)
                medidor.atualizar(estat_frente, estat_fundo)

                # da bola guardamos o centro para desenhar o rastro.
                # quando a rede acha mais de uma, vale a mais confiavel
                posicao_bola = None
                if bolas:
                    melhor = max(bolas, key=lambda b: b["confianca"])
                    rastro_bola.insert(0, melhor["centro"])
                    if len(rastro_bola) > TAMANHO_RASTRO:
                        rastro_bola.pop()
                    posicao_bola = quadra.imagem_para_quadra(melhor["centro"])

                if self.mostrar:
                    tempo_s = indice / fps
                    anotado = quadro.copy()
                    desenhar_video(anotado, quadra, jogador_fundo,
                                   jogador_frente, rastro_bola)
                    tela = montar_tela(anotado, quadra, estat_frente, estat_fundo,
                                       medidor, posicao_fundo, posicao_frente,
                                       posicao_bola, tempo_s)

                    # reduz a tela se nao couber no monitor
                    if tela.shape[1] > LARGURA_MAXIMA_TELA:
                        fator = LARGURA_MAXIMA_TELA / tela.shape[1]
                        tela = cv2.resize(tela, None, fx=fator, fy=fator)

                    cv2.imshow(janela, tela)
                    tecla = cv2.waitKey(1) & 0xFF
                    if tecla == ord("q"):
                        break
                    if tecla == ord(" "):
                        # pausado, espera outra tecla de espaco ou q
                        while True:
                            tecla = cv2.waitKey(100) & 0xFF
                            if tecla in (ord(" "), ord("q")):
                                break
                        if tecla == ord("q"):
                            break

                indice += 1
                if self.max_quadros is not None and indice >= self.max_quadros:
                    break

                ok, quadro = captura.read()
                if not ok:
                    break
        finally:
            captura.release()
            if self.mostrar:
                cv2.destroyAllWindows()

        # com a partida percorrida, geramos o relatorio final
        duracao = indice / fps
        nome_video = os.path.splitext(os.path.basename(self.caminho_video))[0]

        return gerar_relatorio(
            self.pasta_resultados,
            nome_video,
            duracao_segundos=duracao,
            estat_frente=estat_frente,
            estat_fundo=estat_fundo,
            medidor=medidor,
            fps=fps,
        )
