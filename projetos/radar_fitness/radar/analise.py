"""
As perguntas do estudo, respondidas com pandas.

Cada funcao publica devolve estruturas simples (dicionarios e listas)
para o relatorio e a demonstracao nao dependerem de pandas. As regras
de recorte moram aqui e valem para todas as saidas:

    registro   cada linha e um estabelecimento com CNAE principal de
               academia (9313-1/00), matriz ou filial
    ativa      situacao cadastral 02
    fechada    situacao cadastral 08 (baixada), e a data da baixa vem
               da data da situacao cadastral
    ano valido entre 1970 e 2026, o que tiver data zerada ou fora
               disso fica de fora daquela conta especifica

O ano de 2026 esta incompleto na foto de junho e nunca entra nas
series anuais, so na contagem de ativas de hoje.
"""

import pandas as pd

from .ibge import normalizar

SITUACAO_ATIVA = "02"
SITUACAO_BAIXADA = "08"

PRIMEIRO_ANO = 1970
ULTIMO_ANO_COMPLETO = 2025


def carregar(pasta_dataset):
    """Le o CSV filtrado da coleta e prepara as colunas derivadas."""
    dados = pd.read_csv(
        f"{pasta_dataset}/academias.csv",
        dtype=str,
        keep_default_na=False,
    )
    dados["situacao"] = dados["situacao"].str.zfill(2)

    dados["ano_inicio"] = pd.to_numeric(dados["data_inicio"].str[:4], errors="coerce")
    dados["mes_inicio"] = pd.to_numeric(dados["data_inicio"].str[4:6], errors="coerce")
    dados["ano_situacao"] = pd.to_numeric(dados["data_situacao"].str[:4], errors="coerce")

    valido = dados["ano_inicio"].between(PRIMEIRO_ANO, 2026)
    dados.loc[~valido, "ano_inicio"] = pd.NA
    valido = dados["ano_situacao"].between(PRIMEIRO_ANO, 2026)
    dados.loc[~valido, "ano_situacao"] = pd.NA

    return dados


def visao_geral(dados):
    """Os numeros de capa: quantas existem, quantas ficaram no caminho."""
    contagem = dados["situacao"].value_counts()
    total = int(len(dados))
    ativas = int(contagem.get(SITUACAO_ATIVA, 0))
    baixadas = int(contagem.get(SITUACAO_BAIXADA, 0))
    return {
        "total_registros": total,
        "ativas": ativas,
        "baixadas": baixadas,
        "outras_situacoes": total - ativas - baixadas,
    }


def serie_anual(dados, primeiro_ano=2000):
    """Aberturas, fechamentos e saldo por ano, ate o ultimo ano completo."""
    anos = list(range(primeiro_ano, ULTIMO_ANO_COMPLETO + 1))

    aberturas = dados["ano_inicio"].value_counts()
    baixas = dados.loc[dados["situacao"] == SITUACAO_BAIXADA, "ano_situacao"].value_counts()

    serie = []
    for ano in anos:
        abriu = int(aberturas.get(ano, 0))
        fechou = int(baixas.get(ano, 0))
        serie.append({
            "ano": ano,
            "aberturas": abriu,
            "fechamentos": fechou,
            "saldo": abriu - fechou,
        })
    return serie


def sobrevivencia_por_coorte(dados, primeiro_ano=2010, ultimo_ano=2024):
    """De cada turma anual de academias, quantas seguem ativas hoje."""
    coortes = []
    for ano in range(primeiro_ano, ultimo_ano + 1):
        turma = dados[dados["ano_inicio"] == ano]
        abertas = int(len(turma))
        vivas = int((turma["situacao"] == SITUACAO_ATIVA).sum())
        coortes.append({
            "ano": ano,
            "abertas": abertas,
            "ativas_hoje": vivas,
            "sobrevivencia": round(vivas / abertas, 4) if abertas else None,
        })
    return coortes


def vida_mediana(dados):
    """Idade tipica das academias que fecharam, em anos."""
    fechadas = dados[
        (dados["situacao"] == SITUACAO_BAIXADA)
        & dados["ano_inicio"].notna()
        & dados["ano_situacao"].notna()
    ].copy()
    inicio = pd.to_datetime(fechadas["data_inicio"], format="%Y%m%d", errors="coerce")
    fim = pd.to_datetime(fechadas["data_situacao"], format="%Y%m%d", errors="coerce")
    duracao = (fim - inicio).dt.days / 365.25
    duracao = duracao[(duracao >= 0) & duracao.notna()]
    return {
        "quantidade": int(len(duracao)),
        "mediana_anos": round(float(duracao.median()), 2),
        "quartil_inferior": round(float(duracao.quantile(0.25)), 2),
        "quartil_superior": round(float(duracao.quantile(0.75)), 2),
    }


def sazonalidade(dados, primeiro_ano=2016):
    """Aberturas por mes do ano, somando os ultimos dez anos completos."""
    recorte = dados[
        dados["ano_inicio"].between(primeiro_ano, ULTIMO_ANO_COMPLETO)
        & dados["mes_inicio"].between(1, 12)
    ]
    contagem = recorte["mes_inicio"].value_counts()
    total = int(contagem.sum())
    meses = []
    for mes in range(1, 13):
        quantidade = int(contagem.get(mes, 0))
        meses.append({
            "mes": mes,
            "aberturas": quantidade,
            "fracao": round(quantidade / total, 4) if total else None,
        })
    return meses


def por_uf(dados, populacao):
    """Ativas, ritmo recente e academias por 100 mil habitantes em cada UF."""
    ativas = dados[dados["situacao"] == SITUACAO_ATIVA]

    populacao_uf = {}
    for (_, uf), habitantes in populacao.items():
        populacao_uf[uf] = populacao_uf.get(uf, 0) + habitantes

    tabela = []
    for uf, grupo in ativas.groupby("uf"):
        if uf not in populacao_uf:
            continue
        quantidade = int(len(grupo))
        recentes = int((grupo["ano_inicio"] >= 2021).sum())
        habitantes = populacao_uf[uf]
        tabela.append({
            "uf": uf,
            "ativas": quantidade,
            "por_100k": round(quantidade / habitantes * 100000, 1),
            "fracao_recente": round(recentes / quantidade, 4),
        })
    tabela.sort(key=lambda item: item["por_100k"], reverse=True)
    return tabela


def por_municipio(dados, municipios, populacao, populacao_minima=100000):
    """O ranking por cidade grande, dos mais servidos aos mais vazios."""
    ativas = dados[dados["situacao"] == SITUACAO_ATIVA].copy()
    ativas["municipio_codigo"] = pd.to_numeric(ativas["municipio_codigo"], errors="coerce")

    nomes = pd.read_csv(f"{municipios}", dtype={"codigo": "Int64", "nome": str})
    mapa_nomes = dict(zip(nomes["codigo"], nomes["nome"]))

    contagem = ativas.groupby(["municipio_codigo", "uf"]).size()

    cidades = []
    nao_casadas = 0
    for (codigo, uf), quantidade in contagem.items():
        nome = mapa_nomes.get(codigo)
        if nome is None:
            nao_casadas += int(quantidade)
            continue
        chave = (normalizar(nome), uf)
        habitantes = populacao.get(chave)
        if habitantes is None:
            nao_casadas += int(quantidade)
            continue
        cidades.append({
            "cidade": nome.title(),
            "uf": uf,
            "ativas": int(quantidade),
            "populacao": habitantes,
            "por_100k": round(int(quantidade) / habitantes * 100000, 1),
        })

    grandes = [cidade for cidade in cidades if cidade["populacao"] >= populacao_minima]
    grandes.sort(key=lambda item: item["por_100k"], reverse=True)

    maiores = sorted(cidades, key=lambda item: item["ativas"], reverse=True)[:15]

    total_casadas = sum(cidade["ativas"] for cidade in cidades)
    return {
        "mais_academias": maiores,
        "mais_servidas": grandes[:15],
        "menos_servidas": list(reversed(grandes[-15:])),
        "cobertura_juncao": round(total_casadas / (total_casadas + nao_casadas), 4),
    }
