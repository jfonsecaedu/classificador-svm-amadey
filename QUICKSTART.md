# Guia Rápido — Como Reproduzir o Projeto

## Pré-requisitos

- Python 3.8+
- Git
- Conta gratuita em [abuse.ch](https://auth.abuse.ch/) (para coletar amostras de Amadey)
- ~2-3 GB de espaço em disco (para amostras + repositórios de terceiros)

## Instalação (10 minutos)

```bash
# Clone o repositório
git clone https://github.com/jfonsecaedu/classificador-svm-amadey.git
cd classificador-svm-amadey

# Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Clone os repositórios de terceiros (necessários para rodar os scripts)
git clone https://github.com/DejavuForensics/SVM.git
git clone https://github.com/iosifache/DikeDataset.git
git clone https://github.com/serrastusbear/PE_Analyzer.git
```

## Reproduzir o Pipeline Completo (1-2 horas)

### Etapa 1: Coletar amostras de Amadey

```bash
# Gere seu Auth-Key em https://auth.abuse.ch/
# Edite scripts/download_amostras.py e adicione seu AUTH_KEY

python3 scripts/download_amostras.py
# Resultado: pasta 'amadey_samples/' com 200 amostras
```

### Etapa 2: Preparar amostras benignas

```bash
# As amostras benignas já estão em dataset/
# Se quiser regenerar do DikeDataset:
# Veja docs/documentacao_processo.pdf, Etapa 2
```

### Etapa 3: Extrair características

```bash
# Rode o PE_Analyzer em loop (pode levar 30-60 minutos)
# Instruções detalhadas em docs/documentacao_processo.pdf, Etapa 3

mkdir outputs_pescanner
for f in amadey_samples/* benign_samples/*; do
  hash=$(basename "$f")
  python3 PE_Analyzer/pescanner.py "$f" > "outputs_pescanner/${hash}.txt" 2>&1
done
```

### Etapa 4: Montar CSV

```bash
python3 scripts/montar_csv.py
# Resultado: dataset_amadey.csv (349 amostras, 10 features)
```

### Etapa 5: Normalizar dados

```bash
python3 scripts/normalizar_dataset.py
# Resultado: dataset_normalizado.csv (pronto para treinamento)
```

### Etapa 6: Converter para LIBSVM e treinar

```bash
# Converta o CSV
python3 SVM/converter_libsvm.py dataset_normalizado.csv \
  dataset_amadey_normalizado.libsvm --label label

# Treinar e validar
cd SVM/PT-BR/classificacao
python3 svmKfold.py -dataset ../../docx_odt_oneclass_system/dataset_amadey_normalizado.libsvm
```

## Resultado Esperado

```
Acurácia Média de Treino: 100.00% ± 0.00%
Acurácia Média de Teste: 96.56% ± 1.71%
```

---

## Progressão de Acurácia — Antes vs. Depois (Cada Etapa)

### Fase 1: Kernel RBF + Dados sem normalização
**Status:** Overfitting severo

| Métrica | Valor |
|---------|-------|
| **Treino** | 100,00% → ❌ |
| **Teste** | 70,20% ± 8,09% ← **RUIM** |
| **Diagnóstico** | Modelo decorando os dados; ~90% das amostras viraram vetores de suporte |

**Problema identificado:** RBF não generalizava bem + escala de features disparada (`obj = -nan`)

---

### Fase 2: Kernel Polinomial + Dados sem normalização
**Status:** Melhor que RBF, mas instável

| Métrica | Valor |
|---------|-------|
| **Treino** | 81,28% ± 1,01% |
| **Teste** | 81,38% ± 6,15% ← **INSTÁVEL** |
| **Diagnóstico** | Sem overfitting; generaliza melhor que RBF, mas otimização numericamente instável |

**Problema identificado:** `obj = -nan` durante otimização; diferença de escala entre features (tamanho em milhões vs. entropia entre 0-8)

---

### Fase 3: Kernel Polinomial + Normalização Min-Max (C=1, γ=1)
**Status:** Estável, bom resultado

| Métrica | Valor |
|---------|-------|
| **Treino** | 96,85% ± 0,42% ← **↑ +15,57%** |
| **Teste** | 95,09% ± 4,58% ← **↑ +13,71%** (vs. Fase 1: +24,89%) |
| **Diagnóstico** | Otimização numericamente estável; gap treino/teste mínimo |

**Problema resolvido:** Normalização eliminou instabilidade; `obj` voltou a valores normais (~-25)

---

### Fase 4: Refinamento — Nova busca de kernels após normalização
**Status:** Descuberta de melhor configuração

Comparação dos kernels com dados normalizados:

| Kernel | Config (C, γ) | Treino | Teste | Status |
|--------|---|---|---|---|
| **Polinomial** | C=1000, γ=1 | 100,00% ± 0,00% | **96,27% ± 1,48%** | ✅ Escolhido |
| RBF | C=1000, γ=1 | 99,93% ± 0,14% | 96,27% ± 1,96% | Empate técnico |
| Linear | C=1000, γ=0 | 95,41% ± 0,83% | 94,25% ± 3,06% | Bom, não melhor |
| Sigmoide | C=1, γ=1 | 55,01% ± 7,49% | 52,17% ± 10,04% | ❌ Underfitting |

**Achado:** RBF deixou de ter overfitting (antes: 100%/70%; agora: 99,93%/96,27%) — normalização ajudou todas as configurações

---

### Fase 5: Resultado Final — Validação Cruzada 10-Fold
**Status:** Modelo pronto para produção

| Métrica | Valor |
|---------|-------|
| **Kernel** | Polinomial |
| **Config** | C=1000, γ=1 |
| **Treino** | 100,00% ± 0,00% |
| **Teste** | **96,56% ± 1,71%** ← **FINAL** |
| **Vetores de Suporte** | 21-27 de 314 (~7-8%), nBSV ≈ 0 |
| **Diagnóstico** | Classes bem separadas; sem overfitting real |

**Comparação desde o início:** Treino: 100% → 100% (estável) | Teste: 70,20% → **96,56%** (↑ +26,36%)

---

## Resumo da Jornada

```
Fase 1: RBF, sem norm.    → 100%/70%   (❌ Overfitting)
Fase 2: Polin., sem norm. → 81%/81%    (⚠️ Instável)
Fase 3: Polin., com norm. → 96%/95%    (✅ Bom)
Fase 4: Refinamento       → 100%/96%   (✅ Excelente)
Fase 5: k-fold final      → 100%/96,56% (✅ MODELO FINAL)
```

**Aprendizado chave:** A normalização Min-Max foi o turning point. Mudou a acurácia de teste de ~70% para ~96% — uma melhora de **+26 pontos percentuais**.

---

## Próximos Passos

- Consulte `docs/documentacao_processo.pdf` para detalhes técnicos de cada etapa
- Consulte `docs/roteiro_slides.md` para a apresentação (20 slides)
- Consulte `docs/relatorios_html/` para os relatórios interativos do svmParameters.py (antes vs. depois da normalização)

## Suporte

Se encontrar problemas:
1. Veja `docs/documentacao_processo.pdf`, seção "Problemas Encontrados"
2. Abra uma issue no GitHub
3. Verifique que o venv está ativado (`(venv)` no prompt)
4. Confirme que o `.gitignore` está bloqueando binários (`git status`)

---

**Última atualização:** setembro 2026  
**Status:** Projeto finalizado e testado  
**Código-fonte:** Disponível em `scripts/`  
**Dataset:** Disponível em `dataset/` (features já extraídas, sem binários)
