"""
Estatisticas de desempenho calculadas ao vivo, quadro a quadro.

Como a homografia da quadra converte as posicoes para metros de
verdade, tudo aqui ja sai em unidades reais: distancia em metros e
velocidade em km/h, sem estimativa por pixel.

Cada jogador tem o seu proprio acumulador. A cada quadro novo o loop
principal chama o atualizar com a posicao detectada e o acumulador
vai somando distancia, guardando velocidades e alimentando a grade
do mapa de calor.
"""

import numpy as np

from .quadra import Quadra

# tamanho da grade do mapa de calor, em celulas.
# cada celula cobre mais ou menos meio metro de quadra
GRADE_LARGURA = 24
GRADE_COMPRIMENTO = 52


class EstatisticasDoJogador:
    """Acumula os numeros de um jogador ao longo da partida."""

    def __init__(self, nome):
        self.nome = nome
        self.distancia_m = 0.0
        self.velocidade_kmh = 0.0          # velocidade atual, suavizada
        self.velocidade_maxima_kmh = 0.0
        self.velocidades = []              # historico para a media
        self.posicoes = []                 # trajetoria completa em metros
        self.ultima_posicao = None
        self.quadros_detectado = 0
        self.quadros_totais = 0

        # grade do mapa de calor, cada celula conta quantas vezes o
        # jogador esteve naquela regiao da quadra
        self.grade_calor = np.zeros((GRADE_COMPRIMENTO, GRADE_LARGURA), dtype=np.float32)

    def atualizar(self, posicao, intervalo_s):
        """
        Recebe a posicao do jogador em metros neste quadro, ou None
        quando a deteccao falhou, e o tempo desde o quadro anterior.
        """
        self.quadros_totais += 1
        self.posicoes.append(posicao)

        if posicao is None:
            # sem deteccao zeramos a referencia para nao medir um
            # salto falso quando o jogador reaparecer
            self.ultima_posicao = None
            self.velocidade_kmh = 0.0
            return

        self.quadros_detectado += 1
        self._marcar_no_calor(posicao)

        if self.ultima_posicao is not None and intervalo_s > 0:
            passo = float(np.hypot(posicao[0] - self.ultima_posicao[0],
                                   posicao[1] - self.ultima_posicao[1]))

            # um humano nao se desloca 2 metros entre dois quadros
            # seguidos, se aconteceu foi erro de deteccao e ignoramos
            if passo < 2.0:
                self.distancia_m += passo
                velocidade = (passo / intervalo_s) * 3.6

                # suavizamos a velocidade mostrada na tela para o numero
                # nao ficar pulando, misturando o valor novo com o antigo
                self.velocidade_kmh = 0.7 * self.velocidade_kmh + 0.3 * velocidade
                self.velocidades.append(velocidade)

                if len(self.velocidades) > 10:
                    # para a maxima usamos a velocidade suavizada, o pico
                    # cru quase sempre é ruido da deteccao
                    self.velocidade_maxima_kmh = max(self.velocidade_maxima_kmh,
                                                     self.velocidade_kmh)

        self.ultima_posicao = posicao

    def _marcar_no_calor(self, posicao):
        """Soma um ponto na celula da grade onde o jogador esta."""
        coluna = int(posicao[0] / Quadra.LARGURA * GRADE_LARGURA)
        linha = int(posicao[1] / Quadra.COMPRIMENTO * GRADE_COMPRIMENTO)

        # jogadores saem um pouco da quadra, prendemos na borda da grade
        coluna = min(max(coluna, 0), GRADE_LARGURA - 1)
        linha = min(max(linha, 0), GRADE_COMPRIMENTO - 1)

        self.grade_calor[linha, coluna] += 1.0

    def velocidade_media_kmh(self):
        if not self.velocidades:
            return 0.0
        return float(np.mean(self.velocidades))

    def taxa_de_deteccao(self):
        if self.quadros_totais == 0:
            return 0.0
        return 100.0 * self.quadros_detectado / self.quadros_totais


class MedidorDeMovimento:
    """
    Acompanha a intensidade de movimento da partida para separar,
    ao vivo, os momentos de ponto em disputa dos momentos de pausa.

    A regra é simples: somamos a velocidade dos dois jogadores e
    mantemos uma media dos ultimos segundos. Quando essa media passa
    do limiar, consideramos que ha ponto em andamento. O historico
    completo fica guardado para o KMeans refinar essa separacao no
    relatorio final.
    """

    # media de velocidade somada, em km/h, acima da qual
    # consideramos que existe um ponto em disputa
    LIMIAR_KMH = 5.0

    def __init__(self, fps):
        self.historico = []
        self.janela = []
        # a janela cobre mais ou menos um segundo de video
        self.tamanho_janela = max(3, int(fps))
        self.ponto_ativo = False
        self.total_pontos = 0

    def atualizar(self, jogador_a, jogador_b):
        """Recebe os dois acumuladores e atualiza o estado do ponto."""
        intensidade = jogador_a.velocidade_kmh + jogador_b.velocidade_kmh
        self.historico.append(intensidade)

        self.janela.append(intensidade)
        if len(self.janela) > self.tamanho_janela:
            self.janela.pop(0)

        media = float(np.mean(self.janela))
        ativo_agora = media > self.LIMIAR_KMH

        # contamos um ponto novo na transicao de pausa para ativo
        if ativo_agora and not self.ponto_ativo:
            self.total_pontos += 1
        self.ponto_ativo = ativo_agora
