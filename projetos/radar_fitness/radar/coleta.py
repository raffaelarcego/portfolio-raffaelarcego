"""
Coleta dos dados abertos de CNPJ da Receita Federal.

A base completa de estabelecimentos tem uns 5 GB zipados e passa de
60 milhoes de linhas. Este modulo baixa um arquivo por vez, le o CSV
de dentro do zip em streaming e guarda somente as linhas cujo CNAE
principal e o de academia (9313-1/00, atividades de condicionamento
fisico). O zip e apagado logo depois de filtrado, entao o pico de uso
de disco fica no tamanho do maior arquivo, e nao no da base inteira.

A fonte e o espelho da Casa dos Dados, que serve os mesmos arquivos
da Receita por tras de CDN. A pasta de referencia esta fixada no
codigo de proposito: o estudo cita numeros de uma foto da base, e
rodar de novo sobre a mesma foto reproduz os mesmos numeros.
"""

import csv
import io
import os
import sys
import time
import zipfile

import requests

ESPELHO = "https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos"
PASTA_REFERENCIA = "2026-06-14"

# atividades de condicionamento fisico, o CNAE das academias
CNAE_ACADEMIA = "9313100"

# posicoes das colunas no CSV de estabelecimentos, que vem sem cabecalho
# (layout descrito no PDF de metadados da Receita)
COL_CNPJ_BASICO = 0
COL_CNPJ_ORDEM = 1
COL_MATRIZ_FILIAL = 3
COL_NOME_FANTASIA = 4
COL_SITUACAO = 5
COL_DATA_SITUACAO = 6
COL_DATA_INICIO = 10
COL_CNAE_PRINCIPAL = 11
COL_UF = 19
COL_MUNICIPIO = 20

CABECALHO_SAIDA = [
    "cnpj_basico",
    "cnpj_ordem",
    "matriz_filial",
    "nome_fantasia",
    "situacao",
    "data_situacao",
    "data_inicio",
    "uf",
    "municipio_codigo",
]


def baixar(nome_arquivo, destino):
    """Baixa um arquivo do espelho com tres tentativas e retomada simples."""
    url = f"{ESPELHO}/{PASTA_REFERENCIA}/{nome_arquivo}"
    for tentativa in range(1, 4):
        try:
            ja_tem = os.path.getsize(destino) if os.path.exists(destino) else 0
            cabecalhos = {"Range": f"bytes={ja_tem}-"} if ja_tem else {}
            with requests.get(url, stream=True, timeout=120, headers=cabecalhos) as resposta:
                if resposta.status_code == 416:
                    return  # o arquivo ja veio inteiro numa tentativa anterior
                resposta.raise_for_status()
                modo = "ab" if ja_tem and resposta.status_code == 206 else "wb"
                with open(destino, modo) as saida:
                    for pedaco in resposta.iter_content(chunk_size=1024 * 1024):
                        saida.write(pedaco)
            return
        except requests.RequestException as erro:
            print(f"    tentativa {tentativa} falhou: {erro}", flush=True)
            time.sleep(10 * tentativa)
    raise RuntimeError(f"nao consegui baixar {nome_arquivo}")


def filtrar_academias(caminho_zip, destino_csv):
    """Le o CSV de dentro do zip linha a linha e guarda so as academias."""
    guardadas = 0
    lidas = 0
    with zipfile.ZipFile(caminho_zip) as pacote, \
            open(destino_csv, "w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(CABECALHO_SAIDA)
        for interno in pacote.namelist():
            fluxo = io.TextIOWrapper(pacote.open(interno), encoding="latin-1", newline="")
            for linha in csv.reader(fluxo, delimiter=";"):
                lidas += 1
                # linha truncada nao tem nem como ser classificada, descarta
                if len(linha) <= COL_MUNICIPIO:
                    continue
                if linha[COL_CNAE_PRINCIPAL] != CNAE_ACADEMIA:
                    continue
                escritor.writerow([
                    linha[COL_CNPJ_BASICO],
                    linha[COL_CNPJ_ORDEM],
                    linha[COL_MATRIZ_FILIAL],
                    linha[COL_NOME_FANTASIA].strip(),
                    linha[COL_SITUACAO],
                    linha[COL_DATA_SITUACAO],
                    linha[COL_DATA_INICIO],
                    linha[COL_UF],
                    linha[COL_MUNICIPIO],
                ])
                guardadas += 1
    return lidas, guardadas


def extrair_tabela_pequena(caminho_zip, destino_csv, cabecalho):
    """Extrai por inteiro as tabelas auxiliares, que tem poucos KB."""
    with zipfile.ZipFile(caminho_zip) as pacote, \
            open(destino_csv, "w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(cabecalho)
        for interno in pacote.namelist():
            fluxo = io.TextIOWrapper(pacote.open(interno), encoding="latin-1", newline="")
            for linha in csv.reader(fluxo, delimiter=";"):
                escritor.writerow(linha)


def coletar(pasta_dataset):
    """Roda a coleta completa. Partes ja filtradas nao sao baixadas de novo."""
    os.makedirs(pasta_dataset, exist_ok=True)

    # tabela de municipios, para trocar o codigo interno da Receita pelo nome
    municipios_csv = os.path.join(pasta_dataset, "municipios.csv")
    if not os.path.exists(municipios_csv):
        print("baixando tabela de municipios", flush=True)
        zip_temporario = os.path.join(pasta_dataset, "Municipios.zip")
        baixar("Municipios.zip", zip_temporario)
        extrair_tabela_pequena(zip_temporario, municipios_csv, ["codigo", "nome"])
        os.remove(zip_temporario)

    # os dez arquivos de estabelecimentos, um por vez
    for indice in range(10):
        parte_csv = os.path.join(pasta_dataset, f"academias_parte{indice}.csv")
        if os.path.exists(parte_csv):
            print(f"parte {indice} ja filtrada, pulando", flush=True)
            continue
        nome = f"Estabelecimentos{indice}.zip"
        zip_temporario = os.path.join(pasta_dataset, nome)
        print(f"baixando {nome}", flush=True)
        inicio = time.time()
        baixar(nome, zip_temporario)
        print(f"  baixado em {time.time() - inicio:.0f}s, filtrando", flush=True)
        parcial = parte_csv + ".tmp"
        lidas, guardadas = filtrar_academias(zip_temporario, parcial)
        os.replace(parcial, parte_csv)
        os.remove(zip_temporario)
        print(f"  {lidas} linhas lidas, {guardadas} academias guardadas", flush=True)

    # junta as dez partes num arquivo so
    final_csv = os.path.join(pasta_dataset, "academias.csv")
    with open(final_csv, "w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(CABECALHO_SAIDA)
        for indice in range(10):
            parte_csv = os.path.join(pasta_dataset, f"academias_parte{indice}.csv")
            with open(parte_csv, newline="", encoding="utf-8") as parte:
                leitor = csv.reader(parte)
                next(leitor)
                escritor.writerows(leitor)
    print("coleta concluida", flush=True)


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")
    coletar(pasta)
