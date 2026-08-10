# Análise de Desempenho em Partidas de Tênis, em Tempo Real

Software que analisa vídeos de partidas de tênis enquanto o vídeo roda, usando deep learning para detectar os jogadores e a bola. A tela mostra, ao vivo, as caixas de detecção sobre os jogadores, os pontos de referência da quadra, o rastro da bola, um mini-mapa com a quadra vista de cima e um painel de estatísticas com mapa de calor.

## O que aparece na tela durante a análise

* Caixas azuis sobre os dois jogadores, detectados pela rede neural YOLO
* Pontos vermelhos marcando as linhas e cantos da quadra
* Rastro verde acompanhando a bola
* Mini-mapa em tempo real com a posição dos jogadores e da bola vistos de cima
* Painel lateral com distância percorrida, velocidade atual, velocidade máxima, contagem de pontos disputados e o mapa de calor de cada jogador se formando ao vivo

## Como funciona por dentro

1. A rede neural YOLO detecta as pessoas e a bola em cada quadro
2. Uma calibração de quatro cliques nos cantos da quadra gera a homografia, a transformação que converte pixels da imagem em metros reais da quadra
3. Com as posições em metros, as estatísticas saem em unidades de verdade: metros percorridos e km/h
4. O algoritmo KMeans entra em duas frentes: encontrar as zonas da quadra que cada jogador mais ocupa e separar os momentos de ponto em disputa dos momentos de pausa
5. No final, um relatório com resumo em texto, mapas de calor e linha do tempo dos pontos é salvo na pasta `resultados`

## Como usar

1. Instale as dependências (a primeira instalação demora, o PyTorch é grande):

```
pip install -r requirements.txt
```

2. Coloque o vídeo da partida dentro da pasta `videos` (mp4, avi, mov ou mkv)

3. Rode o programa:

```
python main.py
```

4. Escolha o vídeo na janela que abrir
5. Na tela de calibração, clique nos quatro cantos da quadra na ordem: fundo esquerdo, fundo direito, frente direita, frente esquerda. Aperte Enter para confirmar. A tecla `a` usa uma estimativa automática e a tecla `r` recomeça os cliques
6. A análise começa. Espaço pausa e continua, `q` encerra e gera o relatório

Na primeira execução o arquivo do modelo YOLO é baixado automaticamente, então é preciso estar com internet.

## Observações

A câmera ideal é a fixa atrás da quadra, filmando a quadra inteira, como nas transmissões de TV. Sem placa de vídeo a análise roda um pouco abaixo da velocidade do vídeo, o que é normal para redes neurais em CPU.

## Estrutura do projeto

```
analise_tenis/
    main.py                  ponto de entrada, escolha do video
    analisador/
        tempo_real.py        loop principal da analise ao vivo
        deteccao.py          rede neural YOLO, jogadores e bola
        quadra.py            calibracao, homografia e geometria da quadra
        estatisticas.py      distancia, velocidade e mapa de calor ao vivo
        agrupamento.py       machine learning (KMeans) para zonas e pontos
        painel.py            desenho das marcacoes, mini-mapa e painel
        relatorio.py         relatorio final em texto e graficos
    videos/                  coloque os videos aqui
    resultados/              relatorios e graficos gerados
    demo.html                demonstracao interativa usada no portfolio
```
