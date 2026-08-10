"""
Deteccao dos jogadores e da bola com deep learning.

Usamos o YOLO, uma rede neural treinada para reconhecer objetos em
imagens. Ela ja sabe identificar pessoas e bolas de esporte, entao
nao precisamos treinar nada, so carregar o modelo e passar os
quadros do video. Na primeira execucao o arquivo do modelo é
baixado automaticamente pela biblioteca ultralytics.

Escolhi a versao nano do modelo porque ela é a mais leve e permite
rodar a analise em tempo real mesmo sem placa de video.
"""

import os

from ultralytics import YOLO

# numeros das classes que interessam dentro do modelo.
# no vocabulario do YOLO a classe 0 é pessoa e a 32 é bola de esporte
CLASSE_PESSOA = 0
CLASSE_BOLA = 32

# se o arquivo do modelo ja estiver na pasta do projeto, usamos ele
# direto e evitamos o download, senao a ultralytics baixa sozinha
PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_LOCAL = os.path.join(PASTA_PROJETO, "yolov8n.pt")


class DetectorYolo:
    """Roda a rede neural em cada quadro e organiza o que ela encontrou."""

    def __init__(self, arquivo_modelo=None):
        if arquivo_modelo is None:
            arquivo_modelo = MODELO_LOCAL if os.path.isfile(MODELO_LOCAL) else "yolov8n.pt"

        # o carregamento do modelo é demorado, por isso acontece uma
        # vez so aqui no construtor e nunca dentro do loop do video
        self.modelo = YOLO(arquivo_modelo)

    def detectar(self, quadro):
        """
        Recebe um quadro e devolve duas listas: pessoas e bolas.

        Cada pessoa vem como um dicionario com a caixa (x1, y1, x2, y2),
        o ponto dos pes (base da caixa, que é o que toca o chao) e a
        confianca da rede. As bolas vem com o centro e a confianca.
        """
        # o predict roda a rede no quadro. filtramos direto pelas duas
        # classes que interessam para nao perder tempo com o resto
        resultado = self.modelo.predict(
            quadro,
            classes=[CLASSE_PESSOA, CLASSE_BOLA],
            conf=0.30,
            verbose=False,
        )[0]

        pessoas = []
        bolas = []

        for caixa in resultado.boxes:
            x1, y1, x2, y2 = caixa.xyxy[0].tolist()
            classe = int(caixa.cls[0])
            confianca = float(caixa.conf[0])

            if classe == CLASSE_PESSOA:
                pessoas.append({
                    "caixa": (int(x1), int(y1), int(x2), int(y2)),
                    # o pe do jogador é o meio da borda de baixo da caixa,
                    # é esse ponto que projeta certo no chao da quadra
                    "pe": ((x1 + x2) / 2.0, y2),
                    "confianca": confianca,
                })
            elif classe == CLASSE_BOLA:
                bolas.append({
                    "centro": ((x1 + x2) / 2.0, (y1 + y2) / 2.0),
                    "confianca": confianca,
                })

        return pessoas, bolas


def escolher_jogadores(pessoas, quadra):
    """
    Decide quais das pessoas detectadas sao os dois jogadores.

    Um video de partida tem juiz, gandulas e plateia, entao nao da
    para pegar qualquer pessoa. A regra é: so vale quem esta pisando
    dentro da quadra (com uma pequena margem) e, em cada metade,
    ficamos com a deteccao de maior confianca.

    Devolve uma tupla (jogador_fundo, jogador_frente), cada um sendo
    o dicionario da deteccao ou None quando nao encontrado. O fundo é
    o lado de cima da tela, mais longe da camera.
    """
    fundo = None
    frente = None

    for pessoa in pessoas:
        posicao = quadra.imagem_para_quadra(pessoa["pe"])
        if posicao is None:
            continue
        if not quadra.dentro_da_quadra(posicao, margem_metros=2.0):
            continue

        # a rede da quadra fica na metade do comprimento, quem esta
        # antes dela joga no fundo e quem esta depois joga na frente
        if posicao[1] < quadra.COMPRIMENTO / 2.0:
            if fundo is None or pessoa["confianca"] > fundo["confianca"]:
                fundo = pessoa
        else:
            if frente is None or pessoa["confianca"] > frente["confianca"]:
                frente = pessoa

    return fundo, frente
