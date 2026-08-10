"""
Ponto de entrada do analisador de partidas de tenis.

O fluxo de uso é curto de proposito:

1. Rode este arquivo. Uma janela de escolha de arquivo abre direto
   na pasta videos.
2. Escolha o video da partida.
3. Na tela de calibracao, clique nos quatro cantos da quadra na
   ordem indicada e aperte Enter. Se preferir, a tecla a usa uma
   estimativa automatica.
4. A analise roda em tempo real: caixas nos jogadores, pontos da
   quadra, rastro da bola, mini-mapa e estatisticas ao vivo.
5. Espaco pausa, q encerra. Ao final o relatorio completo é salvo
   na pasta resultados.

Tambem da para chamar por linha de comando passando o video direto:
    python main.py caminho/do/video.mp4
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# pastas do projeto, relativas a este arquivo para funcionar de
# qualquer lugar que o programa seja chamado
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_VIDEOS = os.path.join(PASTA_PROJETO, "videos")
PASTA_RESULTADOS = os.path.join(PASTA_PROJETO, "resultados")

FORMATOS = (".mp4", ".avi", ".mov", ".mkv")


def escolher_video():
    """Abre a janela de escolha de arquivo apontando para a pasta videos."""
    raiz = tk.Tk()
    raiz.withdraw()  # so queremos o dialogo, nao a janela principal

    pasta_inicial = PASTA_VIDEOS if os.path.isdir(PASTA_VIDEOS) else PASTA_PROJETO
    caminho = filedialog.askopenfilename(
        title="Escolha o video da partida",
        initialdir=pasta_inicial,
        filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv"), ("Todos", "*.*")],
    )
    raiz.destroy()
    return caminho


def main():
    # o video pode vir como argumento na linha de comando ou ser
    # escolhido pela janela de arquivos
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = escolher_video()

    if not caminho:
        return

    if not caminho.lower().endswith(FORMATOS):
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showwarning("Formato invalido",
                               "Esse arquivo nao parece ser um video aceito.\n"
                               "Use mp4, avi, mov ou mkv.")
        raiz.destroy()
        return

    # o import fica aqui dentro porque ele carrega as bibliotecas de
    # deep learning, que demoram alguns segundos. assim a janela de
    # escolha de arquivo abre na hora
    from analisador.tempo_real import AnalisadorTempoReal

    print("Carregando o modelo de deteccao, aguarde um instante.")
    analisador = AnalisadorTempoReal(caminho, PASTA_RESULTADOS)
    arquivos = analisador.executar()

    print("Analise concluida. Arquivos gerados:")
    for arquivo in arquivos:
        print("  " + arquivo)


if __name__ == "__main__":
    main()
