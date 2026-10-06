# Classificador baseado em SVM — Classificação da Família Amadey

Classificador binário treinado com Support Vector Machine (SVM) para detectar a família de malware **Amadey** a partir de características extraídas por **análise estática** (engenharia reversa) de executáveis PE.

Projeto de finalização da cadeira de Criação de Antivírus, pós-graduação em Defesa Cibernética e Resposta a Incidentes (Blue Team) — CEIC/UFPE.

## Resultado Final

**Acurácia de teste: 96,56% ± 1,71%** (validação cruzada 10-fold)

- Kernel: Polinomial (C=1000, γ=1)
- Features: 10 características extraídas por análise estática
- Dataset: 349 amostras (177 Amadey + 172 benignas)
- Sem overfitting (gap mínimo entre treino e teste)

## Pipeline do Projeto

1. **Coleta de amostras** — 200 Amadey (MalwareBazaar) + 200 benignas (DikeDataset)
2. **Extração de características** — análise estática via PE_Analyzer
3. **Consolidação em CSV** — 10 features rotuladas (malware=1, benigno=-1)
4. **Normalização Min-Max** — correção de escala (turning point do projeto: 70% → 96%)
5. **Treinamento e validação** — comparação de kernels, refinamento de parâmetros
6. **Validação cruzada 10-fold** — resultado final confiável

## Estrutura do Repositório

```
classificador-svm-amadey/
├── README.md                          # Este arquivo
├── QUICKSTART.md                      # Guia rápido de como rodar
├── LICENSE                            # MIT License
├── requirements.txt                   # Dependências Python
├── .gitignore                         # Arquivos ignorados pelo Git
│
├── scripts/                           # Scripts de automação
│   ├── download_amostras.py           # Coleta automatizada via API
│   ├── montar_csv.py                  # Consolidação de features em CSV
│   ├── normalizar_dataset.py          # Normalização Min-Max
│   └── checar_falhas_pescanner.sh     # Diagnóstico de falhas
│
├── dataset/                           # Dados finais (sem binários)
│   ├── dataset_amadey.csv             # Features brutas (349 amostras)
│   └── dataset_normalizado.csv        # Dataset pronto para treino
│
└── docs/                              # Documentação
    ├── documentacao_processo.pdf      # Processo completo (detalhado)
    ├── hashes_excluidos_do_csv.txt    # Amostras que falharam
    ├── amadey_metadata.csv            # Metadados das amostras
    └── relatorios_html/               # Relatórios de validação
        ├── svm_report_SEM_normalizacao.html
        └── svm_report_COM_normalizacao.html
```

## Quickstart

### Pré-requisitos
- Python 3.8+
- Conta gratuita em [abuse.ch](https://auth.abuse.ch/) (para coletar Amadey)
- ~2GB de espaço em disco

### Instalação (5 minutos)

```bash
git clone https://github.com/jfonsecaedu/classificador-svm-amadey.git
cd classificador-svm-amadey

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Reproduzir o Pipeline Completo

Para instruções detalhadas, veja `QUICKSTART.md`. Em resumo:

```bash
# 1. Coletar amostras de Amadey
# (requer Auth-Key do abuse.ch no script)
python3 scripts/download_amostras.py

# 2. Extrair features (requer PE_Analyzer clonado)
# Veja docs/documentacao_processo.pdf para detalhes

# 3. Consolidar dados
python3 scripts/montar_csv.py

# 4. Normalizar
python3 scripts/normalizar_dataset.py

# 5. Treinar (requer SVM repository clonado)
# Veja QUICKSTART.md para comandos exatos
```

## O Aprendizado Principal

A **normalização Min-Max** foi o turning point do projeto:

- **Antes:** 70-81% de acurácia de teste (instabilidade numérica)
- **Depois:** 96,56% de acurácia (otimização estável, generalização forte)

O kernel Polinomial é sensível à diferença de escala entre features (tamanho de arquivo em milhões vs. entropia entre 0-8). A normalização [0,1] elimina essa discrepância e melhora o resultado em ~26 pontos percentuais.

**Lição prática:** Sempre normalize dados antes de usar kernels não-lineares em SVM.

## Detalhes Técnicos

### Features Extraídas
- Tamanho do arquivo
- Arquitetura (32/64 bits)
- Número de seções PE
- Entropia (média, máxima, mínima)
- Timestamp suspeito (sim/não)
- Entry point suspeito (sim/não)
- Divergência de CRC
- Número de DLLs importadas

### Validação
- Método: 10-fold cross-validation
- Kernel: Polinomial (C=1000, γ=1)
- Treino: 100,00% ± 0,00%
- Teste: **96,56% ± 1,71%**

### Aviso Importante

**Este repositório não contém nenhuma amostra de malware, arquivo binário, ou executável.** Apenas scripts de automação, datasets de características numéricas (sem código executável) e documentação. As amostras foram coletadas e processadas em ambiente virtualizado isolado, exclusivamente para fins educacionais.

## Referências

- [MalwareBazaar](https://bazaar.abuse.ch) — abuse.ch
- [DikeDataset](https://github.com/iosifache/DikeDataset) — Iosifache
- [SVM Template](https://github.com/DejavuForensics/SVM) — DejavuForensics
- [PE_Analyzer](https://github.com/serrastusbear/PE_Analyzer) — Serrastusbear

## Licença

MIT License
