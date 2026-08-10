"""
Ponto de entrada do previsor de chuva por telemetria de satelite.

A ideia do projeto: quando chove, o sinal do satelite enfraquece.
Em vez de tratar isso como defeito, o pipeline le a telemetria do
enlace, SNR e atenuacao minuto a minuto, e transforma a propria
antena num pluviometro.

O fluxo e linear de proposito:

1. Carrega os tres conjuntos do dataset, treino, validacao e teste.
2. Treina o classificador que detecta o evento de chuva e o
   regressor que estima a intensidade em mm/h, encadeados.
3. Avalia no teste, uma unica vez, e compara com os baselines
   que acompanham o dataset, como referencia.
4. Salva o relatorio completo na pasta resultados.
5. Exporta a janela da demonstracao interativa do portfolio.

Basta rodar:
    python main.py
"""

import os

# pastas do projeto, relativas a este arquivo para funcionar de
# qualquer lugar que o programa seja chamado
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_DATASET = os.path.join(PASTA_PROJETO, "dataset")
PASTA_RESULTADOS = os.path.join(PASTA_PROJETO, "resultados")
ARQUIVO_DEMO = os.path.join(PASTA_PROJETO, "dados_demo.js")


def main():
    # os imports ficam aqui dentro porque pandas e xgboost demoram
    # alguns segundos para carregar, assim a mensagem inicial aparece
    # na hora e o usuario sabe que o programa esta vivo
    print("Carregando os dados, aguarde um instante.")
    from previsor.dados import carregar_conjuntos, carregar_baselines, preparar_matriz
    from previsor.modelo import PrevisorDeChuva
    from previsor.avaliacao import avaliar, comparar_estagios
    from previsor.relatorio import gerar_relatorio
    from previsor.exportacao import escolher_janela, exportar_dados_demo

    conjuntos = carregar_conjuntos(PASTA_DATASET)
    baselines = carregar_baselines(PASTA_DATASET)

    X_treino, ev_treino, tx_treino = preparar_matriz(conjuntos["treino"])
    X_val, ev_val, tx_val = preparar_matriz(conjuntos["validacao"])
    X_teste, ev_teste, tx_teste = preparar_matriz(conjuntos["teste"])

    print("Treinando o detector de chuva e o estimador de intensidade.")
    previsor = PrevisorDeChuva()
    previsor.treinar(X_treino, ev_treino, tx_treino, X_val, ev_val, tx_val)

    print("Avaliando no conjunto de teste.")
    metricas, evento, taxa, probabilidade = avaliar(previsor, X_teste, ev_teste, tx_teste)
    print("  F1 na deteccao: %.4f" % metricas["f1"])
    print("  RMSE na intensidade: %.3f mm/h (baseline analitico: %.2f)"
          % (metricas["rmse"], baselines["analytical_inverse"]["rmse"]))

    print("Medindo quanto cada estagio de features acrescenta.")
    ablacao = comparar_estagios(conjuntos)

    # a janela da demo precisa das predicoes coladas nas linhas do teste
    teste = conjuntos["teste"].copy()
    teste["taxa_prevista"] = taxa
    teste["probabilidade"] = probabilidade
    teste["limiar"] = previsor.limiar
    janela = escolher_janela(teste)

    print("Salvando o relatorio e a janela da demonstracao.")
    arquivos = gerar_relatorio(PASTA_RESULTADOS, conjuntos, metricas, ablacao,
                               baselines, previsor.importancias(), janela)
    arquivos.append(exportar_dados_demo(janela, ARQUIVO_DEMO))

    print("Avaliacao concluida. Arquivos gerados:")
    for arquivo in arquivos:
        print("  " + arquivo)


if __name__ == "__main__":
    main()
