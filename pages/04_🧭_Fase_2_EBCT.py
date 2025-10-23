import pandas as pd
import streamlit as st

from html import escape
from pathlib import Path

from core import db, utils
from core.config import DIMENSIONES_TRL
from core.data_table import render_table
from core.db_trl import get_trl_history
from core.theme import load_theme


def _display_text(value, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    if pd.isna(value):
        return default
    return str(value)


st.set_page_config(page_title="Fase 2 - Trayectoria EBCT", page_icon="🌲", layout="wide")
load_theme()

st.markdown(
    """
    <style>
    .page-intro {
        display: grid;
        grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr);
        gap: 2.4rem;
        padding: 2.3rem 2.6rem;
        border-radius: 30px;
        background: linear-gradient(145deg, rgba(18, 48, 29, 0.9), rgba(111, 75, 44, 0.86));
        color: #fdf9f2;
        box-shadow: 0 36px 60px rgba(12, 32, 20, 0.35);
        margin-bottom: 2.6rem;
    }

    .page-intro h1 {
        font-size: 2.2rem;
        margin-bottom: 1rem;
        color: #fffdf8;
    }

    .page-intro p {
        font-size: 1.02rem;
        line-height: 1.6;
        color: rgba(253, 249, 242, 0.86);
    }

    .page-intro__aside {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .page-intro__aside .intro-stat {
        background: rgba(255, 255, 255, 0.14);
        border-radius: 20px;
        padding: 1.1rem 1.3rem;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
    }

    .page-intro__aside .intro-stat strong {
        display: block;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
        color: #fefcf9;
    }

    .page-intro__aside .intro-stat p {
        margin: 0;
        color: rgba(253, 249, 242, 0.86);
        font-size: 0.96rem;
        line-height: 1.5;
    }

    .back-band {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1.6rem;
    }

    .section-shell {
        background: #ffffff;
        border-radius: 24px;
        padding: 1.6rem 1.8rem;
        border: 1px solid rgba(var(--shadow-color), 0.12);
        box-shadow: 0 24px 48px rgba(var(--shadow-color), 0.16);
        margin-bottom: 2.3rem;
    }

    .section-shell h3, .section-shell h4 {
        margin-top: 0;
    }

    .selection-card {
        position: relative;
        padding: 1.8rem 2rem;
        border-radius: 26px;
        background: linear-gradient(140deg, rgba(49, 106, 67, 0.16), rgba(32, 73, 46, 0.22));
        border: 1px solid rgba(41, 96, 59, 0.45);
        box-shadow: 0 26px 48px rgba(21, 56, 35, 0.28);
        overflow: hidden;
    }

    .selection-card::after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        border-radius: 50%;
        background: rgba(103, 164, 123, 0.18);
        top: -80px;
        right: -70px;
        filter: blur(0.5px);
    }

    .selection-card__badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 1.1rem;
        border-radius: 999px;
        background: #1f6b36;
        color: #f4fff2;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        font-size: 0.78rem;
        font-weight: 600;
        box-shadow: 0 12px 24px rgba(31, 107, 54, 0.35);
        position: relative;
        z-index: 1;
    }

    .selection-card__title {
        margin: 1.1rem 0 0.6rem;
        font-size: 1.65rem;
        color: #10371d;
        position: relative;
        z-index: 1;
    }

    .selection-card__subtitle {
        margin: 0;
        color: rgba(16, 55, 29, 0.78);
        font-size: 1rem;
        position: relative;
        z-index: 1;
    }

    .selection-card__meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.1rem;
        margin-top: 1.5rem;
        position: relative;
        z-index: 1;
    }

    .selection-card__meta-item {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(41, 96, 59, 0.18);
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
    }

    .selection-card__meta-label {
        display: block;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.6px;
        color: rgba(16, 55, 29, 0.64);
        margin-bottom: 0.35rem;
    }

    .selection-card__meta-value {
        display: block;
        font-size: 1.05rem;
        font-weight: 600;
        color: #10371d;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

fase1_page = next(Path("pages").glob("03_*_Fase_1_*.py"), None)
if fase1_page:
    st.markdown("<div class='back-band'>", unsafe_allow_html=True)
    if st.button("Volver a Fase 1", type="primary"):
        st.switch_page(str(fase1_page))
    st.markdown("</div>", unsafe_allow_html=True)

payload = st.session_state.get("fase2_payload")
fase2_ready = st.session_state.get("fase2_ready", False)

if not payload or not fase2_ready:
    st.warning("Finaliza una evaluación en Fase 1 para acceder a esta etapa.")
    if fase1_page:
        if st.button("Ir a Fase 1", key="fase2_btn_ir_fase1"):
            st.switch_page(str(fase1_page))
    st.stop()

project_id = payload.get("project_id")
if project_id is None:
    st.error("No se pudo determinar el proyecto seleccionado desde Fase 1.")
    st.stop()

responses_records = payload.get("responses", [])
irl_score = payload.get("irl_score")
fecha_eval = payload.get("fecha_eval")

order_map = {item["id"]: idx for idx, item in enumerate(DIMENSIONES_TRL)}
label_map = {item["id"]: item.get("label", item["id"]) for item in DIMENSIONES_TRL}

responses_df = pd.DataFrame(responses_records)
if not responses_df.empty:
    responses_df["__order"] = responses_df["dimension"].map(order_map)
    responses_df = responses_df.sort_values(["__order", "nivel"], ascending=[True, False])
    responses_df = responses_df.drop(columns="__order")
    responses_df["dimension_label"] = responses_df["dimension"].map(label_map)
    responses_df["dimension_label"] = responses_df["dimension_label"].fillna(responses_df["dimension"])
    responses_df = responses_df.drop(columns="dimension")
    responses_df = responses_df.rename(
        columns={
            "dimension_label": "Dimensión",
            "nivel": "Nivel acreditado",
            "evidencia": "Evidencia",
        }
    )
    responses_df["Nivel acreditado"] = pd.to_numeric(
        responses_df["Nivel acreditado"], errors="coerce"
    ).astype("Int64")
    responses_df = responses_df[["Dimensión", "Nivel acreditado", "Evidencia"]]


snapshot = payload.get("project_snapshot", {}).copy()
df_port = utils.normalize_df(db.fetch_df())
project_row = df_port.loc[df_port["id_innovacion"] == project_id]
if not project_row.empty:
    row = project_row.iloc[0]
    for field in (
        "nombre_innovacion",
        "potencial_transferencia",
        "impacto",
        "estatus",
        "responsable_innovacion",
    ):
        value = row.get(field)
        if isinstance(value, str):
            value = value.strip()
        if value not in (None, "") and not (isinstance(value, float) and pd.isna(value)):
            snapshot[field] = value
    eval_value = row.get("evaluacion_numerica")
    if eval_value not in (None, "") and not pd.isna(eval_value):
        snapshot["evaluacion_numerica"] = float(eval_value)

nombre_txt = _display_text(snapshot.get("nombre_innovacion"), "Proyecto seleccionado")
transferencia_txt = _display_text(snapshot.get("potencial_transferencia"), "Sin potencial declarado")
impacto_txt = _display_text(snapshot.get("impacto"), "No informado")
estado_txt = _display_text(snapshot.get("estatus"), "Sin estado")
responsable_txt = _display_text(snapshot.get("responsable_innovacion"), "Sin responsable asignado")
evaluacion_val = snapshot.get("evaluacion_numerica")
evaluacion_txt = (
    f"{float(evaluacion_val):.1f}" if evaluacion_val is not None and not pd.isna(evaluacion_val) else "—"
)

selection_meta = [
    ("Impacto estratégico", impacto_txt),
    ("Estado actual", estado_txt),
    ("Responsable de innovación", responsable_txt),
    ("Evaluación Fase 0", evaluacion_txt),
]

meta_items_html = "".join(
    f"<div class='selection-card__meta-item'>"
    f"<span class='selection-card__meta-label'>{escape(label)}</span>"
    f"<span class='selection-card__meta-value'>{escape(str(value))}</span>"
    "</div>"
    for label, value in selection_meta
)

selection_card_html = f"""
<div class='selection-card'>
    <span class='selection-card__badge'>Proyecto seleccionado</span>
    <h3 class='selection-card__title'>{escape(nombre_txt)}</h3>
    <p class='selection-card__subtitle'>{escape(str(transferencia_txt))}</p>
    <div class='selection-card__meta'>
        {meta_items_html}
    </div>
</div>
"""

st.markdown(
    """
    <div class="page-intro">
        <div>
            <h1>Planifica la trayectoria EBCT</h1>
            <p>
                Usa la evaluación IRL más reciente para definir el foco de trabajo, identificar brechas
                y preparar la hoja de ruta hacia las fases de mercado y comercialización.
            </p>
        </div>
        <div class="page-intro__aside">
            <div class="intro-stat">
                <strong>Próximo paso</strong>
                <p>Confirma el proyecto seleccionado y registra sus prioridades estratégicas.</p>
            </div>
            <div class="intro-stat">
                <strong>Referencia</strong>
                <p>El nivel IRL acreditado será el punto de partida para la hoja EBCT.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.markdown(selection_card_html, unsafe_allow_html=True)
    if fecha_eval:
        st.caption(f"Evaluación IRL registrada el {fecha_eval}.")
    st.markdown("</div>", unsafe_allow_html=True)

irl_display = f"{float(irl_score):.1f}" if irl_score is not None else "—"

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Resumen de evidencias IRL")
    if fecha_eval:
        st.caption(f"Última evaluación registrada: {fecha_eval}.")
    st.metric("Nivel IRL acreditado", irl_display)
    if responses_df.empty:
        st.info("No se encontraron niveles guardados para esta evaluación.")
    else:
        render_table(
            responses_df,
            key="fase2_respuestas_guardadas",
            include_actions=False,
            hide_index=True,
            default_page_size=6,
            page_size_options=(6, 12, 18),
        )
    st.markdown("</div>", unsafe_allow_html=True)

historial = get_trl_history(project_id)
with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Historial IRL del proyecto")
    if historial.empty:
        st.info("Aún no existe historial IRL para este proyecto.")
    else:
        resumen_historial = (
            historial.groupby("fecha_eval", as_index=False)
            .agg({"trl_global": "max"})
            .rename(columns={"fecha_eval": "Fecha de evaluación", "trl_global": "IRL global"})
        )
        resumen_historial["IRL global"] = pd.to_numeric(
            resumen_historial["IRL global"], errors="coerce"
        ).round(1)
        resumen_historial = resumen_historial.sort_values(
            "Fecha de evaluación", ascending=False
        ).reset_index(drop=True)
        render_table(
            resumen_historial,
            key="fase2_historial_global",
            include_actions=False,
            hide_index=True,
            default_page_size=5,
            page_size_options=(5, 10, 20),
        )
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Hoja EBCT en construcción")
    st.info(
        "Pronto podrás registrar hitos, capacidades requeridas y apoyos disponibles para la trayectoria EBCT de este proyecto."
    )
    st.markdown("</div>", unsafe_allow_html=True)
