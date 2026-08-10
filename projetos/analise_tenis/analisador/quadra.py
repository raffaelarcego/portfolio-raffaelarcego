"""
Tudo que envolve a geometria da quadra.

A peca central aqui é a homografia, que é a conta que transforma um
ponto da imagem do video em um ponto da quadra vista de cima, em
metros de verdade. Para calcular essa transformacao basta saber onde
os quatro cantos da quadra aparecem na imagem.

Com a homografia em maos tudo fica facil: da para desenhar os pontos
de referencia da quadra sobre o video, montar o mini-mapa visto de
cima e medir distancia e velocidade em metros reais em vez de pixels.
"""

import cv2
import numpy as np


class Quadra:
    """Guarda a calibracao e faz as conversoes entre imagem e quadra."""

    # medidas oficiais de uma quadra de duplas, em metros
    LARGURA = 10.97
    COMPRIMENTO = 23.77

    # medidas internas usadas para desenhar as linhas:
    # as laterais de simples ficam a 1.37 m das laterais de duplas e
    # as linhas de saque ficam a 6.40 m da rede
    RECUO_SIMPLES = 1.37
    DISTANCIA_SAQUE = 6.40

    def __init__(self, cantos_na_imagem):
        """
        Recebe os quatro cantos da quadra na imagem, na ordem:
        fundo esquerdo, fundo direito, frente direita, frente esquerda.
        O fundo é o lado mais distante da camera.
        """
        origem = np.array(cantos_na_imagem, dtype=np.float32)

        # os mesmos quatro cantos no mundo real, em metros.
        # a origem fica no canto esquerdo do fundo da quadra
        destino = np.array([
            [0.0, 0.0],
            [self.LARGURA, 0.0],
            [self.LARGURA, self.COMPRIMENTO],
            [0.0, self.COMPRIMENTO],
        ], dtype=np.float32)

        # matriz que leva da imagem para a quadra e a inversa,
        # que leva da quadra de volta para a imagem
        self.para_quadra = cv2.getPerspectiveTransform(origem, destino)
        self.para_imagem = cv2.getPerspectiveTransform(destino, origem)

    def imagem_para_quadra(self, ponto):
        """Converte um ponto da imagem para metros na quadra."""
        if ponto is None:
            return None
        entrada = np.array([[ponto]], dtype=np.float32)
        saida = cv2.perspectiveTransform(entrada, self.para_quadra)
        return (float(saida[0][0][0]), float(saida[0][0][1]))

    def quadra_para_imagem(self, ponto):
        """Converte um ponto em metros da quadra de volta para a imagem."""
        entrada = np.array([[ponto]], dtype=np.float32)
        saida = cv2.perspectiveTransform(entrada, self.para_imagem)
        return (float(saida[0][0][0]), float(saida[0][0][1]))

    def dentro_da_quadra(self, posicao, margem_metros=0.0):
        """
        Diz se uma posicao em metros esta dentro da quadra. A margem
        existe porque os jogadores correm um pouco para fora das
        linhas durante os pontos e isso continua sendo jogo.
        """
        x, y = posicao
        return (-margem_metros <= x <= self.LARGURA + margem_metros and
                -margem_metros <= y <= self.COMPRIMENTO + margem_metros)

    def pontos_de_referencia(self):
        """
        Lista os pontos importantes da quadra em metros: os cantos,
        os encontros das linhas de simples, de saque e a linha central.
        Sao esses pontos que aparecem como bolinhas vermelhas no video.
        """
        e = 0.0
        d = self.LARGURA
        se = self.RECUO_SIMPLES              # lateral de simples esquerda
        sd = self.LARGURA - self.RECUO_SIMPLES
        fundo = 0.0
        frente = self.COMPRIMENTO
        rede = self.COMPRIMENTO / 2.0
        saque_fundo = rede - self.DISTANCIA_SAQUE
        saque_frente = rede + self.DISTANCIA_SAQUE
        meio = self.LARGURA / 2.0

        pontos = [
            # cantos da quadra de duplas
            (e, fundo), (d, fundo), (e, frente), (d, frente),
            # encontro das laterais de simples com as linhas de fundo
            (se, fundo), (sd, fundo), (se, frente), (sd, frente),
            # linhas de saque
            (se, saque_fundo), (sd, saque_fundo),
            (se, saque_frente), (sd, saque_frente),
            # marca central das linhas de saque
            (meio, saque_fundo), (meio, saque_frente),
            # encontro da rede com as laterais
            (e, rede), (d, rede),
        ]
        return pontos

    def segmentos_das_linhas(self):
        """
        Lista as linhas da quadra como pares de pontos em metros.
        Usada para desenhar tanto o mini-mapa quanto qualquer contorno.
        """
        e = 0.0
        d = self.LARGURA
        se = self.RECUO_SIMPLES
        sd = self.LARGURA - self.RECUO_SIMPLES
        fundo = 0.0
        frente = self.COMPRIMENTO
        rede = self.COMPRIMENTO / 2.0
        saque_f = rede - self.DISTANCIA_SAQUE
        saque_fr = rede + self.DISTANCIA_SAQUE
        meio = self.LARGURA / 2.0

        return [
            # contorno externo
            ((e, fundo), (d, fundo)),
            ((e, frente), (d, frente)),
            ((e, fundo), (e, frente)),
            ((d, fundo), (d, frente)),
            # laterais de simples
            ((se, fundo), (se, frente)),
            ((sd, fundo), (sd, frente)),
            # rede
            ((e, rede), (d, rede)),
            # linhas de saque
            ((se, saque_f), (sd, saque_f)),
            ((se, saque_fr), (sd, saque_fr)),
            # linha central entre as duas linhas de saque
            ((meio, saque_f), (meio, saque_fr)),
        ]


def calibracao_automatica(largura_video, altura_video):
    """
    Estimativa dos cantos da quadra quando o usuario prefere nao
    marcar na mao. Assume o enquadramento classico de transmissao,
    com a camera atras e a quadra centralizada. Funciona razoavel
    nesses videos e sempre pode ser refeita com a marcacao manual.
    """
    w = largura_video
    h = altura_video
    return [
        (w * 0.32, h * 0.28),   # fundo esquerdo
        (w * 0.68, h * 0.28),   # fundo direito
        (w * 0.88, h * 0.92),   # frente direita
        (w * 0.12, h * 0.92),   # frente esquerda
    ]


def calibrar_com_cliques(quadro):
    """
    Abre uma janela para o usuario clicar nos quatro cantos da quadra,
    na ordem: fundo esquerdo, fundo direito, frente direita, frente
    esquerda. Enter confirma, tecla r recomeca, tecla a usa a
    estimativa automatica, Esc cancela.

    Devolve a lista de cantos ou None se o usuario cancelar.
    """
    instrucao = ("Clique nos 4 cantos: fundo esq, fundo dir, frente dir, frente esq | "
                 "Enter confirma  r recomeca  a automatico  Esc cancela")
    cliques = []

    def ao_clicar(evento, x, y, flags, params):
        if evento == cv2.EVENT_LBUTTONDOWN and len(cliques) < 4:
            cliques.append((float(x), float(y)))

    janela = "Calibracao da quadra"
    cv2.namedWindow(janela)
    cv2.setMouseCallback(janela, ao_clicar)

    while True:
        tela = quadro.copy()
        cv2.putText(tela, instrucao, (12, 26), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # desenha os cliques ja feitos e as linhas entre eles
        for i, ponto in enumerate(cliques):
            p = (int(ponto[0]), int(ponto[1]))
            cv2.circle(tela, p, 6, (0, 0, 255), -1)
            if i > 0:
                anterior = (int(cliques[i - 1][0]), int(cliques[i - 1][1]))
                cv2.line(tela, anterior, p, (0, 0, 255), 2)
        if len(cliques) == 4:
            cv2.line(tela, (int(cliques[3][0]), int(cliques[3][1])),
                     (int(cliques[0][0]), int(cliques[0][1])), (0, 0, 255), 2)

        cv2.imshow(janela, tela)
        tecla = cv2.waitKey(30) & 0xFF

        if tecla == 27:                       # Esc
            cv2.destroyWindow(janela)
            return None
        if tecla == ord("r"):                 # recomecar
            cliques.clear()
        if tecla == ord("a"):                 # estimativa automatica
            cv2.destroyWindow(janela)
            return calibracao_automatica(quadro.shape[1], quadro.shape[0])
        if tecla in (13, 10) and len(cliques) == 4:   # Enter com 4 cantos
            cv2.destroyWindow(janela)
            return list(cliques)
