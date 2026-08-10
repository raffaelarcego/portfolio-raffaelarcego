# Predição de Chuva pela Telemetria de um Enlace de Satélite

Quando chove, o sinal do satélite enfraquece. Todo link de comunicação por satélite sofre com isso, e a telemetria registra a queda minuto a minuto. Este projeto vira o problema ao contrário: em vez de tratar a atenuação como defeito, um pipeline de machine learning lê a telemetria do enlace (SNR, atenuação, geometria) e transforma a própria antena num pluviômetro, detectando o evento de chuva e estimando a intensidade em mm/h.

## Como funciona por dentro

1. O dataset traz a telemetria simulada de 4 estações terrestres (Delhi, São Paulo, Tóquio e Berlim) em 5 frequências de portadora, com resolução de 1 minuto e 600 mil linhas
2. Antes de qualquer modelo, uma auditoria dos dados: as colunas de atenuação do dataset são a fórmula ITU-R P.838 aplicada na própria taxa de chuva, quase sem ruído. Inverter a fórmula em uma linha recupera o alvo com RMSE de 0.03 mm/h, sem machine learning nenhum. Essas colunas ficam fora das features, de propósito: o pipeline lê apenas o SNR ruidoso e a geometria do enlace
3. Um classificador XGBoost responde a primeira pergunta: está chovendo agora, sim ou não
4. Um regressor XGBoost, treinado só nos minutos com chuva, responde a segunda: chovendo, quantos mm/h. Na predição, minuto seco recebe zero direto e minuto chuvoso passa pelo regressor
5. O limiar de decisão do classificador e a parada antecipada do treino vêm do conjunto de validação. O conjunto de teste é tocado uma única vez, na avaliação final
6. O resultado é comparado com os baselines que acompanham o dataset, como referência: eles usam o conjunto completo de features, incluindo as colunas vazadas. Um relatório com resumo em texto e gráficos é salvo na pasta `resultados`

## Como usar

1. Instale as dependências:

```
pip install -r requirements.txt
```

2. Rode o programa:

```
python main.py
```

3. O treino leva alguns minutos em CPU. Ao final, o relatório aparece em `resultados` e a janela da demonstração interativa é atualizada em `dados_demo.js`

## Observações

A decisão mais importante do projeto foi jogar features fora. Na primeira versão, com o conjunto completo do dataset, o modelo cravava F1 de 0.9999 e R² de 0.998, números bons demais para serem verdade. A investigação mostrou o porquê: `specific_attenuation_db_per_km` e `excess_attenuation_db` vêm do simulador praticamente sem ruído e revelam o alvo por fórmula, então o modelo não previa nada, só desfazia uma conta. Sem essas colunas a tarefa vira previsão de verdade: inferir a chuva a partir de um SNR que mistura a queda causada pela chuva com o ruído de cintilação do próprio sinal. O relatório inclui uma ablação mostrando quanto cada grupo de features acrescenta, e também o erro medido só nos minutos com chuva de verdade, que é a leitura honesta quando metade dos minutos é seca.

Vale dizer também que o dataset é sintético e generoso: metade das séries chove o tempo todo e a outra metade quase nunca, o que deixa a base com 53% de minutos chuvosos, bem mais do que qualquer clima real.

## Sobre os dados

O dataset é sintético, gerado com o RainCast, um simulador físico de enlaces de satélite criado por Satyansh Gaur que combina propagação orbital com os modelos de atenuação das recomendações ITU-R. Os dados estão na pasta `dataset`, com dicionário de colunas, descrição das features e métricas de baseline geradas junto. Crédito e licença acompanham os arquivos do próprio dataset.

## Estrutura do projeto

```
predicao_chuva/
    main.py                  ponto de entrada, roda o pipeline completo
    previsor/
        dados.py             carga dos parquets e preparo das features
        modelo.py            classificador e regressor XGBoost encadeados
        avaliacao.py         metricas no teste, ablacao e baselines
        relatorio.py         relatorio final em texto e graficos
        exportacao.py        janela da demonstracao interativa
    dataset/                 dados do benchmark (terceiros)
    resultados/              relatorios e graficos gerados
    demo.html                demonstracao interativa usada no portfolio
    dados_demo.js            fatia real do teste com as predicoes do modelo
```
