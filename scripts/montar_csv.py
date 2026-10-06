#!/usr/bin/env python3

"""
Consolida as saidas de texto do pescanner.py (outputs_pescanner/*.txt) em
um unico CSV rotulado: uma linha por amostra, uma coluna por caracteristica
extraida da analise estatica, e uma coluna final "label" (1 = Amadey,
-1 = benigno).

Amostras cujo .txt nao contem o marcador "Meta-data" (ou seja, que
falharam no pescanner) sao automaticamente ignoradas e listadas ao final.
"""

import csv
import os
import re

OUTPUTS_DIR = "outputs_pescanner"
AMADEY_DIR = "amadey_samples"
BENIGN_DIR = "benign_samples"
CSV_SAIDA = "dataset_amadey.csv"

# Regex de extração

RE_SIZE = re.compile(r"^Size\s*:\s*(\d+)\s*bytes", re.MULTILINE)
RE_ARCH = re.compile(r"^Architecture\s*:\s*(\d+)\s*Bits", re.MULTILINE)
RE_DATE_SUSPICIOUS = re.compile(r"^Date\s*:.*\[SUSPICIOUS\]", re.MULTILINE)
RE_EP_SUSPICIOUS = re.compile(r"^Entry Point\s*:.*\[SUSPICIOUS\]", re.MULTILINE)
RE_CRC = re.compile(
    r"^CRC:\s*\(Claimed\)\s*:\s*(0x[0-9a-fA-F]+),\s*\(Actual\)\s*:\s*(0x[0-9a-fA-F]+)",
    re.MULTILINE,
)
# linha de uma secao na tabela "Sections": nome ... entropia no final
RE_SECTION_ROW = re.compile(
    r"^\S+\s+0x[0-9a-fA-F]+\s+0x[0-9a-fA-F]+\s+0x[0-9a-fA-F]+\s+[0-9a-fA-F]{32}\s+([\d.]+)",
    re.MULTILINE,
)
# entradas de DLL na secao Imports, ex: [1] b'kernel32.dll'
RE_IMPORT_DLL = re.compile(r"^\[\d+\]\s*b?['\"]?([\w\.]+)", re.MULTILINE)


def extrair_features(texto: str) -> dict | None:
    """Extrai as features de um relatorio do pescanner. Retorna None se
    o relatorio nao tiver o marcador 'Meta-data' (ou seja, falhou)."""
    if "Meta-data" not in texto:
        return None

    size_match = RE_SIZE.search(texto)
    arch_match = RE_ARCH.search(texto)
    crc_match = RE_CRC.search(texto)

    entropias = [float(x) for x in RE_SECTION_ROW.findall(texto)]
    dlls = RE_IMPORT_DLL.findall(texto)

    features = {
        "file_size": int(size_match.group(1)) if size_match else 0,
        "is_64bit": 1 if (arch_match and arch_match.group(1) == "64") else 0,
        "num_sections": len(entropias),
        "entropy_avg": round(sum(entropias) / len(entropias), 4) if entropias else 0,
        "entropy_max": round(max(entropias), 4) if entropias else 0,
        "entropy_min": round(min(entropias), 4) if entropias else 0,
        "date_suspicious": 1 if RE_DATE_SUSPICIOUS.search(texto) else 0,
        "entrypoint_suspicious": 1 if RE_EP_SUSPICIOUS.search(texto) else 0,
        "crc_mismatch": (
            1
            if (crc_match and crc_match.group(1).lower() != crc_match.group(2).lower())
            else 0
        ),
        "num_imported_dlls": len(set(dlls)),
    }
    return features


def construir_mapa_de_labels() -> dict:
    """Mapeia cada hash de arquivo para seu rotulo (1=Amadey, -1=benigno),
    olhando em qual pasta de origem ele esta."""
    mapa = {}
    for nome in os.listdir(AMADEY_DIR):
        mapa[nome] = 1
    for nome in os.listdir(BENIGN_DIR):
        mapa[nome] = -1
    return mapa


def main():
    mapa_labels = construir_mapa_de_labels()

    linhas = []
    falhas = []

    for arquivo_txt in sorted(os.listdir(OUTPUTS_DIR)):
        if not arquivo_txt.endswith(".txt"):
            continue

        hash_amostra = arquivo_txt[:-4]  # remove ".txt"
        label = mapa_labels.get(hash_amostra)

        if label is None:
            print(f"[!] Hash sem correspondencia em amadey/benign: {hash_amostra}")
            continue

        with open(os.path.join(OUTPUTS_DIR, arquivo_txt), "r", errors="ignore") as f:
            texto = f.read()

        features = extrair_features(texto)

        if features is None:
            falhas.append(hash_amostra)
            continue

        features["label"] = label
        features["sha256"] = hash_amostra
        linhas.append(features)

    if not linhas:
        print("Nenhuma amostra valida encontrada.")
        return

    colunas = [c for c in linhas[0].keys() if c not in ("label", "sha256")]
    colunas_finais = ["sha256"] + colunas + ["label"]

    with open(CSV_SAIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas_finais)
        writer.writeheader()
        writer.writerows(linhas)

    qtd_malware = sum(1 for l in linhas if l["label"] == 1)
    qtd_benigno = sum(1 for l in linhas if l["label"] == -1)

    print(f"CSV gerado: {CSV_SAIDA}")
    print(f"Amostras incluidas: {len(linhas)} (Amadey: {qtd_malware} | Benignas: {qtd_benigno})")
    print(f"Amostras ignoradas (falha no pescanner): {len(falhas)}")
    if falhas:
        with open("hashes_excluidos_do_csv.txt", "w") as f:
            f.write("\n".join(falhas))
        print("Lista de hashes excluidos salva em hashes_excluidos_do_csv.txt")


if __name__ == "__main__":
    main()
