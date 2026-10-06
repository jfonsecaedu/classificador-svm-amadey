#!/bin/bash
# Identifica quais saidas do pescanner ficaram incompletas (sem o marcador
# "Meta-data", que so aparece quando a analise realmente roda ate o fim).
#
# Uso: rode este script de dentro da pasta Amadey/, com o venv ativo.

OUTPUT_DIR="outputs_pescanner"
FAILED_LIST="hashes_com_falha.txt"

echo "Verificando $(ls "$OUTPUT_DIR" | wc -l) arquivos em $OUTPUT_DIR/ ..."

> "$FAILED_LIST"  # zera o arquivo de lista

for txt in "$OUTPUT_DIR"/*.txt; do
    if ! grep -q "Meta-data" "$txt"; then
        hash=$(basename "$txt" .txt)
        echo "$hash" >> "$FAILED_LIST"
    fi
done

total_falhas=$(wc -l < "$FAILED_LIST")
echo ""
echo "Total de arquivos incompletos/com falha: $total_falhas"
echo "Lista salva em: $FAILED_LIST"
