"""Limpeza e tratamento dos dados brutos coletados da Adzuna."""

import re
from datetime import date
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

INPUT_FILE = RAW_DIR / "adzuna_consolidado_2026-08-26.csv"
OUTPUT_FILE = PROCESSED_DIR / "vagas_tratado.csv"

# ---------------------------------------------------------------------------
# Inferência de modalidade de trabalho
# ---------------------------------------------------------------------------
# Lógica: busca palavras-chave no título e na descrição da vaga.
# - "remoto", "remote", "home office", "trabalho remoto", "vaga remota" → remoto
# - "híbrido", "hibrido", "hybrid" → híbrido
# - "presencial", "in loco", "in-loco", "no local" → presencial
# - Se nenhum termo for encontrado → "não especificado" (ausência de
#   indicação não confirma modalidade — não assumimos presencial).
# Ordem de prioridade: se aparecem termos de remoto E híbrido, prevalece
# híbrido — pois indica que não é 100% remoto.

REMOTE_PATTERN = re.compile(
    r"\b(remoto|remote|home\s*office|trabalho\s+remoto|vaga\s+remota)\b",
    re.IGNORECASE,
)
HYBRID_PATTERN = re.compile(
    r"\b(h[ií]brido|hybrid)\b",
    re.IGNORECASE,
)
ONSITE_PATTERN = re.compile(
    r"\b(presencial|in[- ]loco|no\s+local)\b",
    re.IGNORECASE,
)


def infer_modalidade(title: str, description: str) -> str:
    text = f"{title} {description}"
    has_hybrid = bool(HYBRID_PATTERN.search(text))
    has_remote = bool(REMOTE_PATTERN.search(text))
    has_onsite = bool(ONSITE_PATTERN.search(text))

    if has_hybrid:
        return "híbrido"
    if has_remote:
        return "remoto"
    if has_onsite:
        return "presencial"
    return "não especificado"


# ---------------------------------------------------------------------------
# Inferência de nível de senioridade
# ---------------------------------------------------------------------------
# Lógica: busca palavras-chave APENAS no título da vaga (descrições costumam
# mencionar múltiplos níveis em frases como "de júnior a sênior").
# - "estágio", "estagiário", "estagiária", "intern" → estágio
# - "júnior", "junior", "jr" (como palavra isolada) → júnior
# - "pleno", "pl" (como palavra isolada) → pleno
# - "sênior", "senior", "sr" (como palavra isolada) → sênior
# - Se nenhum termo for encontrado → "não especificado".
# Ordem de checagem: estágio → sênior → pleno → júnior (do mais restritivo
# ao menos restritivo, para evitar que "sr" dentro de outra palavra gere
# falso positivo — por isso usamos \b word boundaries).

INTERNSHIP_PATTERN = re.compile(
    r"\b(est[aá]gio|estagi[aá]ri[oa]|intern)\b", re.IGNORECASE
)
SENIOR_PATTERN = re.compile(
    r"\b(s[eê]nior|sr\.?)\b", re.IGNORECASE
)
MID_PATTERN = re.compile(
    r"\b(pleno|pl\.?)\b", re.IGNORECASE
)
JUNIOR_PATTERN = re.compile(
    r"\b(j[uú]nior|jr\.?)\b", re.IGNORECASE
)


def infer_senioridade(title: str) -> str:
    if INTERNSHIP_PATTERN.search(title):
        return "estágio"
    if SENIOR_PATTERN.search(title):
        return "sênior"
    if MID_PATTERN.search(title):
        return "pleno"
    if JUNIOR_PATTERN.search(title):
        return "júnior"
    return "não especificado"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    total_bruto = len(df)
    print(f"Registros brutos carregados: {total_bruto}")

    # --- Deduplicação por ID ---
    df = df.drop_duplicates(subset="id", keep="first")
    total_dedup = len(df)
    removidos = total_bruto - total_dedup
    print(f"Duplicatas removidas: {removidos}")
    print(f"Registros após deduplicação: {total_dedup}")

    # --- Salário ---
    df["salary_avg"] = df.apply(
        lambda r: (r["salary_min"] + r["salary_max"]) / 2
        if pd.notna(r["salary_min"]) and pd.notna(r["salary_max"])
        else None,
        axis=1,
    )

    # --- Modalidade ---
    df["modalidade"] = df.apply(
        lambda r: infer_modalidade(str(r["title"]), str(r["description"])),
        axis=1,
    )

    # --- Senioridade ---
    df["senioridade"] = df["title"].apply(lambda t: infer_senioridade(str(t)))

    # --- Padronização de localização ---
    df["location"] = df["location"].str.strip().str.title()

    # --- Salvar ---
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\nArquivo salvo: {OUTPUT_FILE.name}")

    # --- Resumo ---
    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)

    print(f"\nRegistros brutos:          {total_bruto}")
    print(f"Duplicatas removidas:      {removidos}")
    print(f"Registros finais:          {total_dedup}")

    print("\n--- Modalidade ---")
    for modalidade, count in df["modalidade"].value_counts().items():
        print(f"  {modalidade:<15} {count:>5}")

    print("\n--- Senioridade ---")
    for nivel, count in df["senioridade"].value_counts().items():
        print(f"  {nivel:<20} {count:>5}")

    com_salario = df["salary_min"].notna().sum()
    sem_salario = df["salary_min"].isna().sum()
    print(f"\n--- Salário ---")
    print(f"  Com salário informado:   {com_salario}")
    print(f"  Sem salário (nulo):      {sem_salario}")


if __name__ == "__main__":
    main()
