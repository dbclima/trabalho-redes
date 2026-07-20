from typing import Dict, List, Tuple
from pathlib import Path
from sys import argv
import json

import networkx as nx
import pickle as pkl


def load_grafo(caminho_grafo: Path) -> nx.Graph:
    "Função que carrega o grafo em memória"
    with open(caminho_grafo, "rb") as fp:
        return pkl.load(fp)


def load_conversor(caminho_arquivo: Path) -> dict:
    "Função que carrega o Dicionário de conversão Número AS -> País em memória"
    with open(caminho_arquivo, "r") as fp:
        return json.load(fp)


def embutir_pais_grafo(grafo: nx.Graph, conversores: List[Dict]) -> None:
    "Função que atribui a cada vétrice (ASN) o país de origem"
    for asn in grafo.nodes:
        grafo.nodes[asn]["country"] = "Unknown"

    for conversor in conversores[::-1]:
        for asn in grafo.nodes:
            if grafo.nodes[asn]["country"] != "Unknown":
                continue

            grafo.nodes[asn]["country"] = conversor.get(str(asn), "Unknown")

    return None


def is_pais_valido(codigo_pais: str, conversor: Dict) -> bool:
    "Função que verifica se o codigo do país inputado tem registro"
    return codigo_pais in conversor.values()


def contar_arestas_pais(
    grafo: nx.Graph,
    pais: str
) -> int:

    arestas = 0
    for (u, v) in grafo.edges:
        pais_u = grafo.nodes[u].get("country", "unknown")
        pais_v = grafo.nodes[v].get("country", "unknown")

        if (pais_u == pais or pais_v == pais):
            arestas += 1

    return arestas


def contar_ligacoes_diretas(
        grafo: nx.Graph,
        pais_1: str,
        pais_2: str
) -> Tuple[int, int, int]:

    ligacoes_diretas = set()
    as_sem_pais = set()
    as_fronteira_pais_1 = set()
    as_fronteira_pais_2 = set()

    for u, v in grafo.edges():
        pais_u = grafo.nodes[u].get("country", "Unknown")
        pais_v = grafo.nodes[v].get("country", "Unknown")

        if pais_u == "Unknown":
            as_sem_pais.add(u)

        if pais_v == "Unknown":
            as_sem_pais.add(v)

        if sorted([pais_u, pais_v]) == sorted([pais_1, pais_2]):
            ligacoes_diretas.add((min(u, v), max(u, v)))
            if grafo.nodes[u]["country"] == pais_1:
                as_fronteira_pais_1.add(u)
                as_fronteira_pais_2.add(v)
            else:
                as_fronteira_pais_1.add(v)
                as_fronteira_pais_2.add(u)

    print("Encontrados", len(as_sem_pais), "AS's sem país")
    return len(ligacoes_diretas), len(as_fronteira_pais_1), len(as_fronteira_pais_2)


def contar_qtd_as_por_pais(
    grafo: nx.Graph,
    pais: str
) -> int:

    contador = 0
    for asn in grafo.nodes:
        if grafo.nodes[asn]["country"] == pais:
            contador += 1

    return contador


def calcular_betweenness(
    grafo: nx.Graph,
    k: int = 50
) -> Dict:

    bet = nx.betweenness_centrality(grafo, k=k, seed=42)

    return bet


def somar_betweenness_pais(
    grafo: nx.Graph,
    bet: Dict[int, float],
    pais: str
) -> float:

    betweenness_acumulado = 0
    for asn in grafo.nodes:
        if grafo.nodes[asn]["country"] == pais:
            betweenness_acumulado += bet[asn]

    return betweenness_acumulado

def contar_componentes_conexas_sem_pais(
    grafo: nx.Graph,
    pais: str
) -> int:

    grafo_reduzido = grafo.copy()
    for asn in grafo.nodes:
        if grafo_reduzido.nodes[asn]["country"] == pais:
            grafo_reduzido.remove_node(asn)

    return nx.number_connected_components(grafo_reduzido)


def contar_componentes_conexas_desconectando_paises(
    grafo: nx.Graph,
    pais_1: str,
    pais_2: str
) -> int:

    grafo_reduzido = grafo.copy()
    for (u, v) in grafo.edges:
        pais_u = grafo.nodes[u].get("country", "unknown")
        pais_v = grafo.nodes[v].get("country", "unknown")

        if sorted([pais_u, pais_v]) == sorted([pais_1, pais_2]):
            grafo_reduzido.remove_edge(u, v)

    return nx.number_connected_components(grafo_reduzido)


def extrair_parametros_grafo(
        grafo: nx.Graph,
        pais_1: str,
        pais_2: str,
) -> Dict:
    "Função que extrai os parâmetros do grafo"

    # bet = calcular_betweenness(grafo, 100)

    parametros = dict()
    parametros["#arestas"] = grafo.number_of_edges()
    parametros[f"#arestas_{pais_1}"] = contar_arestas_pais(grafo, pais_1)
    parametros[f"#arestas_{pais_2}"] = contar_arestas_pais(grafo, pais_2)
    parametros["#asn"] = grafo.number_of_nodes()
    parametros[f"#asn_{pais_1}"] = contar_qtd_as_por_pais(grafo, pais_1)
    parametros[f"#asn_{pais_2}"] = contar_qtd_as_por_pais(grafo, pais_2)
    ligacoes_diretas, fronteira_pais_1, fronteira_pais_2 = contar_ligacoes_diretas(grafo, pais_1, pais_2)
    parametros[f"#as_fronteira_{pais_1}"] = fronteira_pais_1
    parametros[f"#as_fronteira_{pais_2}"] = fronteira_pais_2
    parametros["#direct_connections"] = ligacoes_diretas
    parametros["#componentes_conexas"] = nx.number_connected_components(grafo)
    parametros[f"#componentes_conexas_sem_{pais_1}-{pais_2}"] = contar_componentes_conexas_desconectando_paises(grafo, pais_1, pais_2)
    parametros[f"#componentes_conexas_sem_{pais_1}"] = contar_componentes_conexas_sem_pais(grafo, pais_1)
    parametros[f"#componentes_conexas_sem_{pais_2}"] = contar_componentes_conexas_sem_pais(grafo, pais_2)
    # parametros[f"betweenness_{pais_1}"] = somar_betweenness_pais(grafo, bet, pais_1)
    # parametros[f"betweenness_{pais_2}"] = somar_betweenness_pais(grafo, bet, pais_2)

    return parametros

def salvar_dados(dict_parametros: Dict, output_file: Path) -> None:
    with open(output_file, "w") as fp:
        json.dump(dict_parametros, fp)

    return None


def main():
    pasta_grafos = Path("../grafos/")
    pasta_conversores = Path("../data/")

    if not pasta_grafos.is_dir() or not pasta_conversores.is_dir():
        print("[ERRO] Dependências não encontradas.\n")
        print(
            "Antes de executar esse arquivo se certifique que as rotinas",
            "e tem seus outputs salvos nas pastas corretas."
            "./bgp_to_graph.py e ./conversor_asn_pais.py foram executadas",
        )

    conversores = dict()
    for arquivo in sorted(pasta_conversores.iterdir()):
        if not arquivo.name.endswith("json"):
            continue

        conversores[arquivo.name] = load_conversor(arquivo)

    assert len(argv) == 3, f"Uso: python {argv[0]} <pais-1> <pais-2>"

    pais_1 = argv[1]
    for conversor in conversores.values():
        assert is_pais_valido(pais_1, conversor), "Codigo pais 1 invalido"

    pais_2 = argv[2]
    for conversor in conversores.values():
        assert is_pais_valido(pais_2, conversor), "Codigo pais 2 invalido"


    dict_grafos = dict()
    for arquivo_grafo in sorted(pasta_grafos.iterdir()):
        if not arquivo_grafo.name.endswith(".pkl"):
            continue

        grafo = load_grafo(arquivo_grafo)
        embutir_pais_grafo(grafo, list(conversores.values()))
        params = extrair_parametros_grafo(grafo, pais_1, pais_2)
        dict_grafos[arquivo_grafo.name] = params

    for key, value in dict_grafos.items():
        print(key, value)

    salvar_dados(dict_grafos, Path(f"../output/analise-{pais_1}-{pais_2}.json"))


if __name__ == "__main__":
    main()
