#!/usr/bin/env python3

import csv

ENTRADA = "dataset_amadey.csv"
SAIDA = "dataset_normalizado.csv"

COLUNAS_IGNORAR = {"sha256", "label"}


def main():
    with open(ENTRADA, "r", newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        linhas = list(leitor)
        colunas_features = [c for c in leitor.fieldnames if c not in COLUNAS_IGNORAR]

    # Descobre min e max de cada feature
    minimos = {}
    maximos = {}
    for col in colunas_features:
        valores = [float(linha[col]) for linha in linhas]
        minimos[col] = min(valores)
        maximos[col] = max(valores)

    # Aplica Min-Max scaling: (x - min) / (max - min)
    for linha in linhas:
        for col in colunas_features:
            minimo = minimos[col]
            maximo = maximos[col]
            valor = float(linha[col])
            if maximo == minimo:
                # coluna constante (sem variacao) -- evita divisao por zero
                linha[col] = 0.0
            else:
                linha[col] = round((valor - minimo) / (maximo - minimo), 6)

    # Reordena: malware (label=1) primeiro, depois benignas (label=-1)
    # Necessario para o converter_libsvm.py mapear os sinais certos
    linhas_malware = [l for l in linhas if l["label"] == "1"]
    linhas_benignas = [l for l in linhas if l["label"] == "-1"]
    linhas_ordenadas = linhas_malware + linhas_benignas

    # Salva sem a coluna sha256, com separador ';' e quebra de linha '\n'
    colunas_saida = colunas_features + ["label"]
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(
            f, fieldnames=colunas_saida, delimiter=";", lineterminator="\n"
        )
        escritor.writeheader()
        for linha in linhas_ordenadas:
            escritor.writerow({col: linha[col] for col in colunas_saida})

    print(f"CSV normalizado gerado: {SAIDA}")
    print(f"Amostras: {len(linhas_ordenadas)} (Malware: {len(linhas_malware)} | Benignas: {len(linhas_benignas)})")
    print("\nFaixas usadas na normalizacao (min -> max):")
    for col in colunas_features:
        print(f"  {col}: {minimos[col]} -> {maximos[col]}")


if __name__ == "__main__":
    main()
