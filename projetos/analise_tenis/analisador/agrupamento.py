"""
Parte de machine learning do projeto.

Aqui ficam os dois usos do algoritmo KMeans:

1. Descobrir as zonas da quadra onde cada jogador passa mais tempo.
   O KMeans recebe todas as posicoes registradas do jogador e agrupa
   os pontos parecidos, revelando as regioes preferidas dele sem que
   a gente precise definir essas regioes na mao.

2. Separar os momentos de ponto ativo dos momentos de pausa. Durante
   um ponto os jogadores se mexem muito, entre pontos quase nada.
   Medimos a intensidade de movimento ao longo do tempo e deixamos o
   KMeans dividir esses valores em dois grupos, um de movimento alto
   e um de movimento baixo. Assim o programa aprende sozinho o que é
   ponto e o que é descanso, sem precisar de nenhum valor fixo.
"""

import numpy as np
from sklearn.cluster import KMeans


def zonas_preferidas(posicoes, n_zonas=3):
    """
    Agrupa as posicoes de um jogador em zonas usando KMeans.

    Recebe a lista de posicoes (x, y) do jogador ao longo da partida e
    devolve uma lista de zonas, cada uma com o centro e a porcentagem
    do tempo que o jogador passou nela, ordenada da mais ocupada para
    a menos ocupada.
    """
    # tiramos os quadros em que o jogador nao foi detectado
    pontos = np.array([p for p in posicoes if p is not None])

    # sem pontos suficientes nao da para agrupar nada
    if len(pontos) < n_zonas * 5:
        return []

    modelo = KMeans(n_clusters=n_zonas, n_init=10, random_state=42)
    rotulos = modelo.fit_predict(pontos)

    zonas = []
    for i in range(n_zonas):
        quantidade = int(np.sum(rotulos == i))
        porcentagem = 100.0 * quantidade / len(pontos)
        centro = modelo.cluster_centers_[i]
        zonas.append({
            "centro": (float(centro[0]), float(centro[1])),
            "porcentagem": porcentagem,
        })

    # a zona mais frequentada vem primeiro
    zonas.sort(key=lambda z: z["porcentagem"], reverse=True)
    return zonas


def separar_pontos_e_pausas(intensidades, fps_efetivo):
    """
    Usa KMeans para descobrir quais trechos do video sao ponto ativo.

    Recebe a lista com a intensidade de movimento de cada quadro
    analisado e devolve uma lista de trechos ativos, cada um como uma
    tupla (inicio_segundos, fim_segundos).
    """
    valores = np.array(intensidades, dtype=float).reshape(-1, 1)

    # com pouquissimos dados nao tem o que separar
    if len(valores) < 20:
        return []

    # se o movimento quase nao variou, tipo um video sem deteccoes ou
    # com os jogadores parados o tempo todo, nao existe o que agrupar
    if float(valores.std()) < 1e-6:
        return []

    # dois grupos, um vai representar movimento alto e o outro baixo
    modelo = KMeans(n_clusters=2, n_init=10, random_state=42)
    rotulos = modelo.fit_predict(valores)

    # descobrimos qual dos dois grupos é o de movimento alto olhando
    # a media de intensidade de cada um
    media_grupo_0 = valores[rotulos == 0].mean()
    media_grupo_1 = valores[rotulos == 1].mean()
    grupo_ativo = 0 if media_grupo_0 > media_grupo_1 else 1

    # se os dois grupos ficaram praticamente iguais, o video
    # provavelmente nao tem variacao de movimento suficiente
    if abs(media_grupo_0 - media_grupo_1) < 1e-6:
        return []

    ativo = rotulos == grupo_ativo

    # agora transformamos a sequencia de quadros ativos em trechos de
    # tempo continuos, juntando os quadros vizinhos
    trechos = []
    inicio = None
    for i, esta_ativo in enumerate(ativo):
        if esta_ativo and inicio is None:
            inicio = i
        elif not esta_ativo and inicio is not None:
            trechos.append((inicio, i))
            inicio = None
    if inicio is not None:
        trechos.append((inicio, len(ativo)))

    # trechos muito curtos costumam ser ruido, tipo alguem passando na
    # frente da camera, entao exigimos pelo menos um segundo de duracao
    minimo_quadros = max(2, int(fps_efetivo))
    trechos = [t for t in trechos if (t[1] - t[0]) >= minimo_quadros]

    # convertendo de indice de quadro para segundos
    em_segundos = []
    for inicio, fim in trechos:
        em_segundos.append((inicio / fps_efetivo, fim / fps_efetivo))

    return em_segundos
