"""
Trabalho de Redes - Bloqueios/geopolítica refletidos no BGP
Estudo de caso: rivalidade tecnológica EUA-China

Fonte de dados: RIPEstat API (https://stat.ripe.net/docs/data_api)
Não requer pybgpstream nem libbgpstream, só 'requests'.

Ideia geral do script:
1. Escolher um ASN alvo (ex: ligado a Huawei, China Telecom, etc)
2. Escolher uma data de evento geopolítico (ex: entity list, sanção, hijack)
3. Puxar o histórico de prefixos anunciados por esse ASN numa janela
   de tempo em torno do evento
4. Puxar o histórico de "visibility" (quantos coletores RIS enxergam o AS)
5. Salvar tudo em CSV e plotar um gráfico simples com uma linha vertical
   marcando a data do evento

Casos sugeridos (troque ASN_ALVO e DATA_EVENTO conforme o grupo escolher):

  Huawei entity list (15/05/2019):
    ASN_ALVO = "AS4837"   # China Unicom (exemplo, ajustar para AS real ligado à Huawei/operadora afetada)
    DATA_EVENTO = "2019-05-15"

  China Telecom hijacks (relatados por Oracle/Internet Intelligence, 2019):
    ASN_ALVO = "AS4134"   # China Telecom (Chinanet)
    DATA_EVENTO = "2019-06-06"   # ajustar para data específica do incidente estudado

  TikTok / restrição a cloud chinesa nos EUA:
    ASN_ALVO = "AS37963"  # Alibaba Cloud (exemplo)
    DATA_EVENTO = "2020-08-06"   # ordem executiva dos EUA sobre TikTok/WeChat
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

BASE_URL = "https://stat.ripe.net/data"

# ------------------- PARÂMETROS DO ESTUDO DE CASO -------------------
ASN_ALVO = "AS4837"          # troque pelo ASN que o grupo vai investigar
DATA_EVENTO = "2019-05-15"   # troque pela data do evento geopolítico
JANELA_DIAS = 60             # quantos dias antes/depois do evento observar
# ----------------------------------------------------------------------


def get_json(endpoint, params):
    """Faz uma chamada genérica à RIPEstat API e devolve o JSON de 'data'."""
    resp = requests.get(f"{BASE_URL}/{endpoint}/data.json", params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"RIPEstat retornou status={payload.get('status')} para {endpoint}")
    return payload["data"]


def prefixos_anunciados(asn, data_referencia):
    """
    Retorna a lista de prefixos anunciados por um ASN numa data específica
    (endpoint 'announced-prefixes' aceita starttime/endtime).
    """
    data = get_json("announced-prefixes", {
        "resource": asn,
        "starttime": data_referencia,
        "endtime": data_referencia,
    })
    prefixos = data.get("prefixes", [])
    return [p["prefix"] for p in prefixos]


def serie_temporal_prefixos(asn, data_evento_str, janela_dias):
    """
    Monta uma série temporal (uma amostra por semana) do número de
    prefixos anunciados pelo ASN, cobrindo [evento - janela, evento + janela].
    Uma amostra por semana é suficiente para ver tendência sem estourar
    o rate limit da API.
    """
    evento = datetime.strptime(data_evento_str, "%Y-%m-%d")
    inicio = evento - timedelta(days=janela_dias)
    fim = evento + timedelta(days=janela_dias)

    linhas = []
    data_atual = inicio
    while data_atual <= fim:
        data_str = data_atual.strftime("%Y-%m-%d")
        try:
            prefixos = prefixos_anunciados(asn, data_str)
            linhas.append({
                "asn": asn,
                "data": data_str,
                "n_prefixos": len(prefixos),
                "dias_relativos_ao_evento": (data_atual - evento).days,
            })
            print(f"{data_str}: {len(prefixos)} prefixos anunciados por {asn}")
        except Exception as e:
            print(f"Falha em {data_str}: {e}")
        data_atual += timedelta(days=7)

    return pd.DataFrame(linhas)


def visibilidade_as(asn, data_evento_str, janela_dias):
    """
    Usa o endpoint 'as-routing-consistency' / 'visibility' para checar
    quantos RIS route collectors enxergam o AS numa data.
    Serve como sinal complementar: queda de visibilidade pode indicar
    isolamento de rota sem necessariamente zerar prefixos anunciados.
    """
    evento = datetime.strptime(data_evento_str, "%Y-%m-%d")
    inicio = evento - timedelta(days=janela_dias)
    fim = evento + timedelta(days=janela_dias)

    data = get_json("visibility", {
        "resource": asn,
        "starttime": inicio.strftime("%Y-%m-%d"),
        "endtime": fim.strftime("%Y-%m-%d"),
    })
    return data


def plot_serie(df, asn, data_evento_str, caminho_saida="serie_prefixos.png"):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["dias_relativos_ao_evento"], df["n_prefixos"], marker="o")
    ax.axvline(0, color="red", linestyle="--", label="Data do evento")
    ax.set_xlabel("Dias em relação ao evento geopolítico")
    ax.set_ylabel("Número de prefixos anunciados")
    ax.set_title(f"Prefixos anunciados por {asn} ao redor de {data_evento_str}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150)
    print(f"Gráfico salvo em {caminho_saida}")


if __name__ == "__main__":
    print(f"Coletando série temporal de prefixos para {ASN_ALVO} em torno de {DATA_EVENTO}...")
    df = serie_temporal_prefixos(ASN_ALVO, DATA_EVENTO, JANELA_DIAS)
    df.to_csv("serie_prefixos.csv", index=False)
    print("Dados salvos em serie_prefixos.csv")

    if not df.empty:
        plot_serie(df, ASN_ALVO, DATA_EVENTO)
    else:
        print("Nenhum dado coletado - verifique conexão ou parâmetros.")