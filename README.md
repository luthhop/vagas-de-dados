# Vagas de Dados v1.0

## Objetivo

Analisar vagas reais de Dados/Analytics no mercado brasileiro para identificar as skills mais exigidas, os requisitos por nível de senioridade e a distribuição geográfica (remoto x presencial), gerando um dashboard que apoie minha transição de carreira de Operações para Dados.

## Stack

- **Python** — coleta e tratamento de dados
- **Pandas** — manipulação e análise
- **SQL** — consultas e transformações
- **Streamlit** — dashboard interativo
- **Power BI** — visualizações complementares (em aprendizado)
- **Git/GitHub** — versionamento e portfólio

## Fonte de dados

[API Adzuna](https://developer.adzuna.com/) — endpoint Brasil.

## Estrutura do projeto

```
vagas-de-dados/
├── data/
│   ├── raw/          # Dados brutos coletados da API
│   └── processed/    # Dados limpos e transformados
├── notebooks/        # Notebooks exploratórios
├── src/              # Scripts Python (coleta, limpeza, análise)
├── dashboard/        # Código do dashboard Streamlit
└── docs/             # Documentação adicional
```

## Coleta de dados

- **Fonte:** [API Adzuna](https://developer.adzuna.com/) — endpoint Brasil.
- **Data da coleta:** 26/08/2026.
- **Termos de busca utilizados:**
  - dados
  - analista de dados
  - cientista de dados
  - data analyst
  - data engineer
  - data scientist
  - business intelligence
- **Total de vagas coletadas:** 4.223 (com duplicatas entre termos, a serem tratadas na etapa de limpeza).
- **Limitação conhecida:** alguns termos de busca atingiram o teto de resultados por execução (1.000 vagas), então o volume real de vagas disponíveis para esses termos pode ser maior do que o capturado. A amostra é considerada suficiente para os objetivos do projeto, mas não representa 100% das vagas publicadas.

## Status do projeto

**Em andamento** — coleta de dados concluída, próxima etapa: limpeza e deduplicação.
