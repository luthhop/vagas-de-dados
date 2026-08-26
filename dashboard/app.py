"""Dashboard interativo — Vagas de Dados v1.0"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Vagas de Dados v1.0", page_icon=":bar_chart:", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "vagas_tratado.csv"

SKILLS = [
    "Python", "SQL", "R", "Excel", "VBA", "Power BI", "Tableau", "Looker",
    "Qlik", "AWS", "Azure", "GCP", "Google Cloud", "Spark", "Hadoop",
    "Airflow", "Kafka", "dbt", "Databricks", "PostgreSQL", "MySQL",
    "Oracle", "MongoDB", "SQL Server", "BigQuery", "Redshift", "Snowflake",
    "Machine Learning", "Scikit-learn", "TensorFlow", "PyTorch", "Git",
    "Docker", "Linux", "ETL", "API",
]

SKILL_COLS = [f"skill_{s}" for s in SKILLS]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, encoding="utf-8-sig")

df_full = load_data()

# ---------------------------------------------------------------------------
# Sidebar — filtros
# ---------------------------------------------------------------------------

st.sidebar.header("Filtros")

senioridades = sorted(df_full["senioridade"].unique())
sel_senioridade = st.sidebar.multiselect("Senioridade", senioridades, default=senioridades)

modalidades = sorted(df_full["modalidade"].unique())
sel_modalidade = st.sidebar.multiselect("Modalidade", modalidades, default=modalidades)

sel_skills = st.sidebar.multiselect("Skills (vagas que mencionam TODAS as selecionadas)", SKILLS)

estados_top = df_full["estado"].value_counts().head(15).index.tolist()
sel_estado = st.sidebar.multiselect("Estado / Localização", estados_top)

# ---------------------------------------------------------------------------
# Aplicar filtros
# ---------------------------------------------------------------------------

df = df_full.copy()
df = df[df["senioridade"].isin(sel_senioridade)]
df = df[df["modalidade"].isin(sel_modalidade)]

if sel_skills:
    for skill in sel_skills:
        df = df[df[f"skill_{skill}"] == 1]

if sel_estado:
    df = df[df["estado"].isin(sel_estado)]

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------

st.title("Vagas de Dados v1.0")
st.caption("Análise de vagas de Dados/Analytics no mercado brasileiro — fonte: API Adzuna, coleta em 26/08/2026")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

total_vagas = len(df)
com_salario = df["salary_avg"].notna().sum()
pct_salario = (com_salario / total_vagas * 100) if total_vagas > 0 else 0
salario_medio = df["salary_avg"].mean() if com_salario > 0 else None

skill_counts = df[SKILL_COLS].sum()
skill_counts.index = SKILLS
skill_top = skill_counts.idxmax() if skill_counts.max() > 0 else "—"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de vagas", f"{total_vagas:,}")
col2.metric("Com salário informado", f"{pct_salario:.1f}%")

if salario_medio is not None:
    label_sal = f"R$ {salario_medio:,.0f}/ano"
    if com_salario < 30:
        label_sal += " *"
    col3.metric("Salário médio anual", label_sal)
    if com_salario < 30:
        col3.caption(f"* Baseado em apenas {com_salario} vagas — amostra pequena.")
else:
    col3.metric("Salário médio anual", "—")

col4.metric("Skill mais mencionada", skill_top)

st.divider()

# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

tab_skills, tab_salario, tab_geo = st.tabs(
    ["Skills Mais Demandadas", "Salário por Senioridade", "Modalidade e Localização"]
)

# --- Tab 1: Skills ---
with tab_skills:
    st.subheader("Top 20 Skills Mais Mencionadas")

    top_skills = skill_counts.sort_values(ascending=False).head(20)
    top_skills_pct = (top_skills / total_vagas * 100).round(1) if total_vagas > 0 else top_skills * 0

    fig_skills = go.Figure(go.Bar(
        x=top_skills.values[::-1],
        y=top_skills.index[::-1],
        orientation="h",
        text=[f"{v} ({p}%)" for v, p in zip(top_skills.values[::-1], top_skills_pct.values[::-1])],
        textposition="outside",
        marker_color="#4c72b0",
    ))
    fig_skills.update_layout(
        xaxis_title="Número de vagas",
        height=600,
        margin=dict(l=0, r=80),
        xaxis=dict(range=[0, top_skills.max() * 1.25]) if top_skills.max() > 0 else {},
    )
    st.plotly_chart(fig_skills, use_container_width=True)

# --- Tab 2: Salário por senioridade ---
with tab_salario:
    st.subheader("Distribuição Salarial por Senioridade (R$/ano)")
    st.caption("Valores anuais em reais. Apenas vagas com salário informado.")

    df_sal = df[df["salary_avg"].notna()]

    if len(df_sal) > 0:
        order = ["estágio", "júnior", "pleno", "sênior", "não especificado"]
        order_present = [s for s in order if s in df_sal["senioridade"].unique()]

        fig_sal = px.box(
            df_sal, x="senioridade", y="salary_avg",
            category_orders={"senioridade": order_present},
            labels={"salary_avg": "Salário médio anual (R$/ano)", "senioridade": "Senioridade"},
        )
        fig_sal.update_layout(height=500)
        st.plotly_chart(fig_sal, use_container_width=True)

        stats = df_sal.groupby("senioridade")["salary_avg"].agg(
            ["count", "median"]
        ).reindex(order_present)
        stats.columns = ["n", "Mediana (R$/ano)"]
        stats["Mediana (R$/ano)"] = stats["Mediana (R$/ano)"].map(lambda x: f"R$ {x:,.0f}")
        st.dataframe(stats, use_container_width=True)

        small_samples = stats[stats["n"] < 15]
        if not small_samples.empty:
            st.info(
                f"Categorias com amostra pequena (n < 15): "
                f"{', '.join(small_samples.index)}. Resultados indicativos, não definitivos."
            )
    else:
        st.warning("Nenhuma vaga com salário informado nos filtros atuais.")

# --- Tab 3: Modalidade e localização ---
with tab_geo:
    col_mod, col_loc = st.columns(2)

    with col_mod:
        st.subheader("Modalidade de Trabalho")
        mod_counts = df["modalidade"].value_counts().reset_index()
        mod_counts.columns = ["Modalidade", "Vagas"]

        color_map = {
            "remoto": "#4c72b0", "híbrido": "#55a868",
            "presencial": "#c44e52", "não especificado": "#cccccc",
        }
        fig_mod = px.bar(
            mod_counts, x="Modalidade", y="Vagas",
            color="Modalidade", color_discrete_map=color_map,
            text="Vagas",
        )
        fig_mod.update_layout(showlegend=False, height=400)
        fig_mod.update_traces(textposition="outside")
        st.plotly_chart(fig_mod, use_container_width=True)

    with col_loc:
        st.subheader("Top 10 Estados")
        estado_counts = df["estado"].value_counts().head(10).reset_index()
        estado_counts.columns = ["Estado", "Vagas"]

        fig_loc = go.Figure(go.Bar(
            x=estado_counts["Vagas"].values[::-1],
            y=estado_counts["Estado"].values[::-1],
            orientation="h",
            text=estado_counts["Vagas"].values[::-1],
            textposition="outside",
            marker_color="#4c72b0",
        ))
        fig_loc.update_layout(
            xaxis_title="Número de vagas", height=400,
            margin=dict(l=0, r=40),
        )
        st.plotly_chart(fig_loc, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Tabela de vagas
# ---------------------------------------------------------------------------

st.subheader("Vagas Filtradas")

display_cols = ["title", "company", "location", "senioridade", "modalidade", "salary_avg", "redirect_url"]
df_display = df[display_cols].copy()
df_display.columns = ["Título", "Empresa", "Localização", "Senioridade", "Modalidade", "Salário (R$/ano)", "Link"]
df_display["Salário (R$/ano)"] = df_display["Salário (R$/ano)"].apply(
    lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "—"
)
df_display["Link"] = df_display["Link"].apply(lambda x: x if pd.notna(x) else "—")

st.dataframe(
    df_display,
    use_container_width=True,
    height=400,
    column_config={
        "Link": st.column_config.LinkColumn("Link", display_text="Ver vaga"),
    },
)

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "**Fonte:** API Adzuna (endpoint Brasil) · **Data da coleta:** 26/08/2026 · "
    "**Nota metodológica:** apenas 5,2% das vagas informam salário e 11,5% indicam "
    'modalidade de trabalho explicitamente — os demais campos ficaram como "não especificado". '
    "Nenhum valor foi assumido sem evidência textual."
)
