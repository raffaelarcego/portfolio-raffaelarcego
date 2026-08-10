"""
Exportacao dos resultados para a demonstracao interativa.

O site do portfolio e estatico, entao a demo nao roda Python: ela le
um arquivo dados_demo.js com tudo ja calculado. Este modulo escreve
esse arquivo. Quem desenha os graficos e o proprio demo.html, em SVG.
"""

import json
import os


def gerar(resultados, pasta_projeto):
    caminho = os.path.join(pasta_projeto, "dados_demo.js")
    conteudo = json.dumps(resultados, ensure_ascii=False, indent=1)
    with open(caminho, "w", encoding="utf-8") as saida:
        saida.write("// gerado por main.py, nao editar na mao\n")
        saida.write("window.DADOS_RADAR = ")
        saida.write(conteudo)
        saida.write(";\n")
    print(f"janela da demonstracao atualizada em {caminho}", flush=True)
