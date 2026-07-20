import pickle as pkl
from pathlib import Path
from sys import argv

import mrtparse
import networkx as nx

def get_as_path(rib_entry):
    for attr in rib_entry["path_attributes"]:
        if "AS_PATH" not in attr["type"].values():
            continue

        path = []

        for segment in attr["value"]:
            path.extend(map(int, segment["value"]))

        return path

def criar_grafo(arquivo: Path, pasta_destino: Path) -> nx.Graph:
    G = nx.Graph()

    if not pasta_destino.exists():
        print(f"Pasta destino não existe, criando {pasta_destino}")
        pasta_destino.mkdir(parents=True)

    for entry in mrtparse.Reader(str(arquivo)):
        if "RIB_IPV4_UNICAST" not in entry.data["subtype"].values():
            continue

        prefixo_inteiro = entry.data["prefix"]
        mascara_prefixo = entry.data["length"]
        str_prefixo = f"{prefixo_inteiro}/{mascara_prefixo}"

        for rib_entry in entry.data["rib_entries"]:
            paths = get_as_path(rib_entry)

            if paths is None:
                continue

            path = []

            for asn in paths:
                if len(path) == 0 or path[-1] != asn:
                    path.append(asn)

            for u, v in zip(path[:-1], path[1:]):
                G.add_edge(u, v, prefixes=set())
                G[u][v]["prefixes"].add(str_prefixo)

    # print(G.number_of_nodes())
    # print(G.number_of_edges())

    return G

def salvar_grafo(arquivo_destino: Path, grafo: nx.Graph) -> None:

    with open(arquivo_destino, "wb") as fp:
        pkl.dump(grafo, fp)

    return None


def main():
    assert len(argv) == 2, f"Uso: <{argv[0]}> <pasta-arquivos-bz2>"
    pasta = Path(argv[1])
    assert pasta.is_dir(), "Pasta passada não existe"

    for arquivo in pasta.iterdir():
        if not arquivo.name.endswith(".bz2"):
            continue

        arquivo_destino = arquivo.parent / arquivo.name.replace("bz2", "pkl")

        print(
            "Convertendo",
            arquivo.name,
            "Armazenando em",
            arquivo_destino.resolve()
        )

        grafo = criar_grafo(arquivo, Path("./grafos/"))
        salvar_grafo(arquivo_destino, grafo)

    return None



if __name__ == "__main__":
    main()
