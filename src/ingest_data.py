"""Ingestão bruta de vagas da API Adzuna (endpoint Brasil)."""

import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
import os

# ---------------------------------------------------------------------------
# Configurações ajustáveis
# ---------------------------------------------------------------------------
MAX_PAGES_PER_TERM = 20
RESULTS_PER_PAGE = 50
REQUEST_DELAY_SECONDS = 1  # pausa entre requisições para respeitar rate limit

SEARCH_TERMS = [
    "dados",
    "analista de dados",
    "cientista de dados",
    "data analyst",
    "data engineer",
    "data scientist",
    "business intelligence",
]

BASE_URL = "https://api.adzuna.com/v1/api/jobs/br/search/{page}"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_page(app_id: str, app_key: str, term: str, page: int) -> dict | None:
    """Busca uma página de resultados para um termo. Retorna None em caso de erro."""
    url = BASE_URL.format(page=page)
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": term,
        "results_per_page": RESULTS_PER_PAGE,
        "content-type": "application/json",
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            print(f"  [RATE LIMIT] Página {page} do termo '{term}'. Aguardando 60s...")
            time.sleep(60)
            resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO] Página {page} do termo '{term}': {e}")
        return None


def flatten_job(job: dict) -> dict:
    """Achata um registro de vaga do JSON da Adzuna em um dict plano."""
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "location_areas": " > ".join(job.get("location", {}).get("area", [])),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "salary_is_predicted": job.get("salary_is_predicted"),
        "contract_type": job.get("contract_type"),
        "contract_time": job.get("contract_time"),
        "category_label": job.get("category", {}).get("label"),
        "category_tag": job.get("category", {}).get("tag"),
        "description": job.get("description"),
        "created": job.get("created"),
        "redirect_url": job.get("redirect_url"),
        "latitude": job.get("latitude"),
        "longitude": job.get("longitude"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        print("ERRO: Defina ADZUNA_APP_ID e ADZUNA_APP_KEY no arquivo .env")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    all_jobs = []

    for term in SEARCH_TERMS:
        slug = term.replace(" ", "_")
        print(f"\n>>> Buscando: '{term}'")
        term_results = []

        for page in range(1, MAX_PAGES_PER_TERM + 1):
            data = fetch_page(app_id, app_key, term, page)
            if data is None:
                continue

            results = data.get("results", [])
            if not results:
                print(f"  Página {page}: sem resultados. Fim deste termo.")
                break

            term_results.extend(results)
            print(f"  Página {page}: {len(results)} vagas coletadas.")

            if len(results) < RESULTS_PER_PAGE:
                break

            time.sleep(REQUEST_DELAY_SECONDS)

        json_path = RAW_DIR / f"adzuna_{slug}_{today}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(term_results, f, ensure_ascii=False, indent=2)
        print(f"  Salvo: {json_path.name} ({len(term_results)} vagas)")

        all_jobs.extend(term_results)

    if all_jobs:
        flat = [flatten_job(job) for job in all_jobs]
        df = pd.DataFrame(flat)
        csv_path = RAW_DIR / f"adzuna_consolidado_{today}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n>>> Consolidado: {csv_path.name} ({len(df)} registros)")
    else:
        print("\nNenhuma vaga coletada.")


if __name__ == "__main__":
    main()
