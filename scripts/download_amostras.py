#!/usr/bin/env python3

"""
Baixa automaticamente amostras da familia de malware Amadey via API do
MalwareBazaar (abuse.ch), para uso no projeto de antivirus SVM.
"""

import csv
import os
import time
import requests
import pyzipper

AUTH_KEY = "SUA-CHAVE-AQUI"              # Cole sua chave de API do MalwareBazaar aqui

if AUTH_KEY == "SUA-CHAVE-AQUI":
    print("Configure seu AUTH_KEY antes de rodar o script.")
    return

SIGNATURE = "Amadey"
LIMIT = 200

OUTPUT_DIR = "amadey_samples"            # pasta onde os binarios vao ficar
METADATA_CSV = "amadey_metadata.csv"     # csv com hash/data/tags de cada amostra
ZIP_PASSWORD = b"infected"               # senha padrao usada pelo MalwareBazaar

API_URL = "https://mb-api.abuse.ch/api/v1/"
SLEEP_BETWEEN_DOWNLOADS = 2


def listar_amostras(signature: str, limit: int) -> list[dict]:
    """Consulta a API e retorna a lista de amostras da familia informada."""
    headers = {"Auth-Key": AUTH_KEY}
    data = {"query": "get_siginfo", "signature": signature, "limit": limit}

    resp = requests.post(API_URL, headers=headers, data=data, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    if result.get("query_status") != "ok":
        raise RuntimeError(f"Erro na consulta: {result.get('query_status')}")

    return result["data"]


def baixar_amostra(sha256_hash: str, destino_dir: str) -> str | None:
    """Baixa uma amostra pelo hash, descompacta e salva sem extensao .exe."""
    headers = {"Auth-Key": AUTH_KEY}
    data = {"query": "get_file", "sha256_hash": sha256_hash}

    resp = requests.post(API_URL, headers=headers, data=data, timeout=60)

    # Se der erro, a API retorna JSON em vez do arquivo zip
    content_type = resp.headers.get("Content-Type", "")
    if "json" in content_type:
        print(f"  [!] Falha ao baixar {sha256_hash}: {resp.json()}")
        return None

    zip_path = os.path.join(destino_dir, f"{sha256_hash}.zip")
    with open(zip_path, "wb") as f:
        f.write(resp.content)

    # Descompacta o zip protegido por senha (AES) e salva o binario puro
    try:
        with pyzipper.AESZipFile(zip_path) as zf:
            zf.pwd = ZIP_PASSWORD
            nomes = zf.namelist()
            if not nomes:
                print(f"  [!] Zip vazio: {sha256_hash}")
                return None
            nome_interno = nomes[0]
            conteudo = zf.read(nome_interno, pwd=ZIP_PASSWORD)
    except Exception as e:
        print(f"  [!] Erro ao descompactar {sha256_hash}: {e}")
        return None
    finally:
        os.remove(zip_path)  # remove o zip, mantem so o binario extraido

    # Salva SEM extensao .exe, so com o hash como nome (evita clique acidental)
    bin_path = os.path.join(destino_dir, sha256_hash)
    with open(bin_path, "wb") as f:
        f.write(conteudo)

    return bin_path


def main():
    if AUTH_KEY == "COLE_SEU_AUTH_KEY_AQUI":
        print("Configure seu AUTH_KEY antes de rodar o script.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Consultando amostras da familia '{SIGNATURE}' (limite: {LIMIT})...")
    amostras = listar_amostras(SIGNATURE, LIMIT)
    print(f"{len(amostras)} amostras encontradas.\n")

    linhas_csv = []
    baixadas = 0

    for i, amostra in enumerate(amostras, start=1):
        sha256 = amostra["sha256_hash"]
        ja_existe = os.path.exists(os.path.join(OUTPUT_DIR, sha256))

        if ja_existe:
            print(f"[{i}/{len(amostras)}] ja existe: {sha256}")
        else:
            print(f"[{i}/{len(amostras)}] baixando: {sha256}")
            caminho = baixar_amostra(sha256, OUTPUT_DIR)
            if caminho:
                baixadas += 1
            time.sleep(SLEEP_BETWEEN_DOWNLOADS)

        linhas_csv.append({
            "sha256_hash": sha256,
            "file_type": amostra.get("file_type", ""),
            "file_size": amostra.get("file_size", ""),
            "first_seen": amostra.get("first_seen", ""),
            "signature": amostra.get("signature", ""),
            "tags": ",".join(amostra.get("tags", []) or []),
        })

    # Salva metadados de todas as amostras listadas (baixadas ou nao)
    with open(METADATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas_csv[0].keys()))
        writer.writeheader()
        writer.writerows(linhas_csv)

    print(f"\nConcluido. {baixadas} amostras novas baixadas em '{OUTPUT_DIR}/'.")
    print(f"Metadados salvos em '{METADATA_CSV}'.")


if __name__ == "__main__":
    main()
