"""
Populacao por municipio, direto da API de agregados do IBGE.

O agregado 6579 traz a populacao residente estimada. A serie de 2025
e a mais recente e cobre os 5570 municipios. O resultado fica em
cache num CSV dentro da pasta dataset, entao a API so e consultada
na primeira rodada.

O cruzamento com a base da Receita e por nome de municipio mais UF,
porque o codigo de municipio da Receita e o da tabela TOM do Serpro,
nao o do IBGE. Nome com acento, cedilha e apostrofo vira uma chave
normalizada antes da juncao, e os poucos casos que nao casam sao
descartados com aviso no relatorio.
"""

import csv
import os
import unicodedata

import requests

URL_POPULACAO = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
    "periodos/2025/variaveis/9324?localidades=N6[all]"
)


def normalizar(nome):
    """Reduz um nome de municipio a uma chave estavel de comparacao."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().replace("'", " ").split())


def carregar_populacao(pasta_dataset):
    """Devolve um dicionario (nome normalizado, uf) para populacao."""
    cache = os.path.join(pasta_dataset, "populacao.csv")
    if not os.path.exists(cache):
        print("consultando populacao no IBGE", flush=True)
        resposta = requests.get(URL_POPULACAO, timeout=120)
        resposta.raise_for_status()
        series = resposta.json()[0]["resultados"][0]["series"]
        with open(cache, "w", newline="", encoding="utf-8") as saida:
            escritor = csv.writer(saida)
            escritor.writerow(["nome", "uf", "populacao"])
            for item in series:
                # o nome vem no formato "Cidade - UF"
                rotulo = item["localidade"]["nome"]
                nome, uf = rotulo.rsplit(" - ", 1)
                populacao = int(item["serie"]["2025"])
                escritor.writerow([nome, uf, populacao])

    populacao = {}
    with open(cache, newline="", encoding="utf-8") as entrada:
        for linha in csv.DictReader(entrada):
            chave = (normalizar(linha["nome"]), linha["uf"])
            populacao[chave] = int(linha["populacao"])
    return populacao
