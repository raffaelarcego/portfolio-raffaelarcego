# Radar do Mercado Fitness Brasileiro

A Receita Federal publica todo mês o cadastro completo de CNPJ do país, com mais de 60 milhões de estabelecimentos. Este projeto filtra dessa base as academias, pelo CNAE principal 9313-1/00 (atividades de condicionamento físico), cruza com a população estimada pelo IBGE e responde quatro perguntas de negócio: quanto o mercado cresce, quanto tempo uma academia vive, quando elas abrem e onde ainda há espaço.

## Como funciona por dentro

1. A coleta baixa os dez arquivos de estabelecimentos de uma foto fixa da base (junho de 2026, via espelho da Casa dos Dados), um por vez. Cada zip é lido em streaming e só as linhas com CNAE de academia são guardadas; o zip é apagado em seguida, então o pico de disco fica em um arquivo, não nos 5 GB da base
2. Dos 60 milhões de estabelecimentos sobram as academias, com situação cadastral, datas de abertura e baixa, UF e município. A tabela de municípios da Receita e a estimativa de população 2025 do IBGE (agregado 6579) entram como apoio, com junção por nome de município normalizado mais UF, porque a Receita usa código próprio de município
3. A análise responde as quatro perguntas em pandas: série anual de aberturas e fechamentos, sobrevivência por coorte anual, vida mediana das que fecharam, sazonalidade mensal das aberturas e ranking de academias por 100 mil habitantes por UF e por cidade grande
4. O relatório final sai em texto e gráficos na pasta `resultados`, e os mesmos números alimentam a demonstração interativa em `demo.html` via `dados_demo.js`
5. Por cima da mesma base, um dashboard em Power BI entrega a visão de gestão para acompanhamento contínuo: KPIs dos últimos 12 meses, aberturas contra fechamentos mês a mês, saldo líquido, ranking de estados e cidades e recortes por região, porte e natureza jurídica. O print do painel está em `dashboard_powerbi.jpg` e aparece em destaque na demonstração

## Como usar

1. Instale as dependências:

```
pip install -r requirements.txt
```

2. Rode o programa:

```
python main.py
```

3. A primeira rodada baixa uns 5 GB da Receita e leva de 15 a 40 minutos, dependendo da conexão. As rodadas seguintes reaproveitam o dataset filtrado em `dataset/academias.csv` e terminam em segundos

## Observações

A decisão mais importante do projeto foi medir o que o dado consegue medir. CNPJ ativo não garante academia funcionando: estúdios pequenos operam como MEI em outros CNAEs, e a data de baixa é a da situação cadastral, que pode chegar bem depois da porta fechar. Os mutirões de baixa da Receita criam picos artificiais de fechamento em anos específicos, e o relatório aponta isso em vez de esconder. O cadastro é o melhor espelho público do mercado, mas ainda é um espelho, e as conclusões do estudo são escritas com esse limite à vista.

A pasta de referência da base fica fixada no código de propósito: o estudo cita números de uma foto específica do cadastro, e rodar de novo sobre a mesma foto reproduz os mesmos números.

## Sobre os dados

Dados abertos de CNPJ da Receita Federal, servidos pelo espelho público da Casa dos Dados, que mantém cópia mensal dos arquivos oficiais atrás de CDN. População municipal da estimativa 2025 do IBGE, consultada na API de agregados. Ambas as fontes são públicas e gratuitas.

## Estrutura do projeto

```
radar_fitness/
    main.py                  ponto de entrada, roda o pipeline completo
    radar/
        coleta.py            download em streaming e filtro por CNAE
        ibge.py              populacao por municipio, com cache local
        analise.py           as quatro perguntas, respondidas em pandas
        relatorio.py         resumo em texto e graficos em png
        exportacao.py        janela da demonstracao interativa
    dataset/                 academias filtradas e tabelas de apoio
    resultados/              relatorios gerados, com data e hora no nome
    demo.html                demonstracao interativa, em SVG puro
    dados_demo.js            numeros exportados para a demonstracao
    dashboard_powerbi.jpg    print do painel de acompanhamento em Power BI
```
