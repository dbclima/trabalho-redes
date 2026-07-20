import json
from sys import argv
from typing import Dict
from pathlib import Path


def criar_conversor_asn_to_pais(arquivo: Path) -> Dict:
    org_id_to_pais = dict()
    asn_to_org_id = dict()
    asn_to_pais = dict()

    with open(arquivo, "r", encoding="utf-8-sig", errors="replace") as fp:
        while (line := fp.readline()):
            line = line.strip()
            if not line or not line.startswith("{"):
                continue

            entry = json.loads(line)
            if entry["type"] == "Organization":
                try:
                    org_id_to_pais[entry["organizationId"]] = entry["country"]
                except KeyError:
                    # Caso não haja entrada de país retorna Unknown
                    org_id_to_pais[entry["organizationId"]] = "Unknown"

            elif entry["type"] == "ASN":
                asn_to_org_id[entry["asn"]] = entry["organizationId"]

    for asn, org_id in asn_to_org_id.items():
        asn_to_pais[asn] = org_id_to_pais[org_id]

    return asn_to_pais

def salvar_conversor_asn_pais(arquivo_destino: Path, dicionario: Dict) -> None:
    with open(arquivo_destino, "w") as fp:
        json.dump(dicionario, fp)

    return None

def main():
    assert len(argv) == 2, f"Uso: <{argv[0]}> <pasta-arquivos-jsonl-caida>"
    # arquivo = Path("../data/20160104.as-org2info.jsonl")
    pasta = Path(argv[1])
    assert pasta.exists() and pasta.is_dir(), "Pasta passada não existe"

    for arquivo in pasta.iterdir():
        if not arquivo.name.endswith("jsonl"):
            continue
        print("Convertendo arquivo: ", arquivo)
        arquivo_destino = Path("../data/") / (arquivo.name.split(".")[0] + ".json")
        conversor = criar_conversor_asn_to_pais(arquivo)
        salvar_conversor_asn_pais(arquivo_destino, conversor)

    return None


if __name__ == "__main__":
    main()
