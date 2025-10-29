import pandas as pd
import streamlit as st
import io
import plotly.graph_objects as go
import plotly.express as px
from html import escape
from pathlib import Path

from core import db, utils
from core.config import DIMENSIONES_TRL
from core.data_table import render_table
from core.db_trl import get_trl_history
from core.db_ebct import (
    get_ebct_history,
    init_db_ebct,
    save_ebct_evaluation,
)
from core.ebct import (
    EBCT_CHARACTERISTICS,
    EBCT_PHASES,
    get_characteristics_by_phase,
)
from core.ebct_panel import build_phase_summary, format_weight, prepare_panel_data
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


def render_phase_overview(panel_map: dict[int, bool]) -> None:
    """Render a simplified EBCT phase overview without custom HTML."""

    phase_summary = build_phase_summary(panel_map)
    if phase_summary:
        summary_records = []
        for entry in phase_summary:
            total_value = entry["total_value"]
            if total_value:
                completed_label = f"{entry['achieved_label']}/{entry['total_label']}"
            else:
                completed_label = "Sin características registradas"
            summary_records.append(
                {
                    "Fase": entry["name"],
                    "Descripción": entry["subtitle"] or "—",
                    "Cumplimiento": entry["percentage_label"],
                    "Características cumplidas": completed_label,
                }
            )
        summary_df = pd.DataFrame(summary_records)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    panel_data = prepare_panel_data(panel_map)
    for data in panel_data:
        phase = data["phase"]
        phase_name = phase.get("name", "Fase")
        phase_subtitle = phase.get("subtitle", "")
        total = data["total"] or 0.0
        achieved = data["achieved"] or 0.0
        percentage = data["percentage"]
        progress_value = max(0.0, min(1.0, percentage / 100 if total else 0.0))

        with st.expander(phase_name, expanded=False):
            if phase_subtitle:
                st.caption(phase_subtitle)
            st.progress(progress_value)
            if total:
                st.write(
                    f"Cumplimiento: {percentage:.0f}% | Características logradas: "
                    f"{format_weight(achieved)} de {format_weight(total)}"
                )
            else:
                st.info("Sin características registradas para esta fase.")

            if data["items"]:
                items_df = pd.DataFrame(
                    [
                        {
                            "ID": item["id"],
                            "Característica": item["name"],
                            "Cumple": "Sí" if item["status"] else "No",
                            "Peso": format_weight(item["weight"]),
                        }
                        for item in data["items"]
                    ]
                )
                st.dataframe(
                    items_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No hay características asociadas a esta fase.")


OPTION_NO = "⚫ No cumple"
OPTION_PARTIAL = "🟡 En desarrollo"
OPTION_YES = "🟢 Sí cumple"

# Mapeo de opciones a valores numéricos para scoring y ayuda
OPTION_INFO = {
    OPTION_NO: {
        "score": 0.0,
        "color": "#ff4d4d",  # Rojo
        "help": "La característica no está implementada o no cumple los criterios mínimos.",
        "icon": "🔴",
    },
    OPTION_PARTIAL: {
        "score": 0.5,
        "color": "#ffd700",  # Amarillo
        "help": "La característica está en proceso de implementación o cumple parcialmente.",
        "icon": "🟡",
    },
    OPTION_YES: {
        "score": 1.0,
        "color": "#1f6b36",  # Verde
        "help": "La característica cumple completamente con los criterios establecidos.",
        "icon": "🟢",
    }
}

# Shortcuts para scoring
OPTION_SCORES = {opt: info["score"] for opt, info in OPTION_INFO.items()}

SUMMARY_SECTIONS = [
    {
        "title": "Objetivos de la Plataforma",
        "items": [
            "Guiar a Emprendimientos de Base Científico-Tecnológica (EBCT) desde la ideación hasta la internacionalización.",
            "Mostrar de forma visual e interactiva la hoja de ruta con etapas, capacidades necesarias y próximos pasos según el nivel de madurez.",
            "Facilitar la identificación de fuentes de financiamiento, programas de apoyo y actores clave del ecosistema nacional.",
            "Reducir la incertidumbre en la toma de decisiones y mejorar la gestión estratégica de las EBCT.",
            "Detectar brechas y saturación en programas de apoyo para orientar políticas públicas y coordinación interinstitucional.",
        ],
    },
    {
        "title": "Funcionalidades",
        "items": [
            "Mapa base de actores para ubicar universidades, OTLs, incubadoras, fondos y otros aliados estratégicos por región.",
            "Rutas personalizadas según la etapa tecnológica y comercial del emprendimiento a partir de un autodiagnóstico detallado.",
            "Directorio actualizado de programas y financiamiento con filtros por región y sector.",
            "Canal único de vinculación para contactar múltiples instituciones desde un mismo punto.",
            "Seguimiento y trazabilidad del avance, actores vinculados y resultados obtenidos.",
            "Visualización clara de la hoja de ruta desde la investigación hasta la exportación o escalamiento.",
        ],
    },
    {
        "title": "Público objetivo",
        "items": [
            "Equipos científicos que inician procesos de valorización tecnológica.",
            "Spin-offs universitarios en etapa de validación técnica o comercial.",
            "Startups tecnológicas que buscan clientes o inversión.",
            "EBCT consolidadas que requieren apoyo para escalar o internacionalizarse.",
            "Actores de apoyo (universidades, incubadoras, agencias públicas, inversionistas) que buscan coordinarse y acceder a información consolidada.",
        ],
    },
]

SUMMARY_FOOTER = "Agosto, 2025"


st.set_page_config(page_title="Fase 2 - Trayectoria EBCT", page_icon="🌲", layout="wide")
load_theme()
init_db_ebct()

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

    .ebct-summary {
        background: #ffffff;
        border-radius: 26px;
        padding: 1.8rem 2rem;
        border: 1px solid rgba(var(--shadow-color), 0.12);
        box-shadow: 0 24px 48px rgba(var(--shadow-color), 0.14);
        margin-bottom: 2.3rem;
    }

    .ebct-summary__grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.4rem;
    }

    .ebct-summary__column h4 {
        margin: 0 0 0.65rem;
        font-size: 1rem;
        color: var(--forest-900);
    }

    .ebct-summary__column ul {
        margin: 0;
        padding-left: 1.1rem;
        display: grid;
        gap: 0.55rem;
        color: var(--text-700);
    }

    .ebct-summary__column li {
        line-height: 1.45;
    }

    .ebct-summary__footer {
        margin-top: 1.4rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.45rem 1.1rem;
        border-radius: 999px;
        background: rgba(var(--shadow-color), 0.08);
        color: var(--forest-700);
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }

    .ebct-roadmap {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 1.6rem;
        margin-top: 1.4rem;
    }

    .ebct-phase {
        border-radius: 24px;
        border: 1px solid rgba(var(--shadow-color), 0.12);
        box-shadow: 0 24px 48px rgba(var(--shadow-color), 0.12);
        background: #ffffff;
        overflow: hidden;
        border-top: 4px solid var(--phase-accent, var(--forest-500));
        display: flex;
        flex-direction: column;
    }

    .ebct-phase__header {
        padding: 1.2rem 1.4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(135deg, rgba(var(--shadow-color), 0.06), rgba(var(--shadow-color), 0.03));
    }

    .ebct-phase__header h4 {
        margin: 0;
        font-size: 1.05rem;
        color: var(--forest-900);
    }

    .ebct-phase__header span {
        display: block;
        font-size: 0.85rem;
        color: var(--text-500);
    }

    .ebct-phase__score {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.18rem;
    }

    .ebct-phase__score strong {
        font-size: 1.35rem;
        color: var(--phase-accent, var(--forest-700));
    }

    .ebct-phase__score span {
        font-size: 0.78rem;
        color: var(--text-500);
        letter-spacing: 0.2px;
    }

    .ebct-phase__items {
        padding: 1.2rem 1.4rem 1.6rem;
        display: grid;
        gap: 0.9rem;
    }

    .ebct-chip {
        border-radius: 18px;
        padding: 0.85rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        background: rgba(255, 255, 255, 0.94);
        border: 1px dashed rgba(var(--shadow-color), 0.22);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .ebct-chip--yes {
        background: linear-gradient(135deg, var(--chip-color-start), var(--chip-color-end));
        border: none;
        color: var(--forest-950);
        box-shadow: 0 18px 32px rgba(var(--shadow-color), 0.18);
    }

    .ebct-chip--no {
        color: var(--text-700);
    }

    .ebct-chip__title {
        font-weight: 600;
        font-size: 0.95rem;
    }

    .ebct-chip small {
        font-size: 0.75rem;
        color: rgba(var(--shadow-color), 0.65);
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }

    .ebct-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 34px rgba(var(--shadow-color), 0.2);
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

previous_project = st.session_state.get("fase2_active_project_id")
if previous_project is not None and previous_project != project_id:
    for item in EBCT_CHARACTERISTICS:
        st.session_state.pop(f"ebct_resp_{item['id']}", None)
    st.session_state.pop("ebct_panel_map", None)
    st.session_state.pop("ebct_last_eval_timestamp", None)
st.session_state["fase2_active_project_id"] = project_id

history_df = get_ebct_history(project_id)
last_eval_map: dict[int, bool] | None = None
last_eval_timestamp: str | None = None
if not history_df.empty:
    last_eval_timestamp = history_df["fecha_eval"].iloc[0]
    latest_eval_df = history_df[history_df["fecha_eval"] == last_eval_timestamp]
    last_eval_map = {
        int(row["caracteristica_id"]): bool(row["cumple"])
        for _, row in latest_eval_df.iterrows()
    }
    st.session_state["ebct_last_eval_timestamp"] = last_eval_timestamp

panel_map = st.session_state.get("ebct_panel_map")
if panel_map is None and last_eval_map:
    panel_map = last_eval_map.copy()
    st.session_state["ebct_panel_map"] = panel_map

for item in EBCT_CHARACTERISTICS:
    key = f"ebct_resp_{item['id']}"
    if key not in st.session_state:
        default_value = OPTION_YES if last_eval_map and last_eval_map.get(item["id"]) else OPTION_NO
        st.session_state[key] = default_value

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

summary_html_parts = ["<div class='ebct-summary'>", "<div class='ebct-summary__grid'>"]
for section in SUMMARY_SECTIONS:
    summary_html_parts.append("<div class='ebct-summary__column'>")
    summary_html_parts.append(f"<h4>{escape(section['title'])}</h4>")
    summary_html_parts.append("<ul>")
    for item in section["items"]:
        summary_html_parts.append(f"<li>{escape(item)}</li>")
    summary_html_parts.append("</ul></div>")
summary_html_parts.append("</div>")
summary_html_parts.append(f"<div class='ebct-summary__footer'>{escape(SUMMARY_FOOTER)}</div>")
summary_html_parts.append("</div>")
st.markdown("".join(summary_html_parts), unsafe_allow_html=True)

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
    st.markdown("""
        <style>
        .ebct-legend {
            background: white;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(0,0,0,0.1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .ebct-legend-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 0.8rem;
        }
        
        .ebct-legend-items {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }
        
        .ebct-legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .ebct-legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .ebct-legend-text {
            font-size: 0.9rem;
            color: #666;
        }
        
        .ebct-characteristic {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        .ebct-characteristic:hover {
            background: #f8f9fa;
        }
        
        .ebct-characteristic-title {
            font-size: 0.95rem;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .ebct-radio-group {
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("Evaluación EBCT por características")
    
    # Leyenda al inicio de la sección
    st.markdown("""
        <div class="ebct-legend">
            <div class="ebct-legend-title">Estados de evaluación:</div>
            <div class="ebct-legend-items">
                <div class="ebct-legend-item">
                    <span class="ebct-legend-dot" style="background: #ff4d4d;"></span>
                    <span class="ebct-legend-text">No cumple - La característica no está implementada o no cumple los criterios mínimos</span>
                </div>
                <div class="ebct-legend-item">
                    <span class="ebct-legend-dot" style="background: #ffd700;"></span>
                    <span class="ebct-legend-text">En desarrollo - La característica está en proceso de implementación o cumple parcialmente</span>
                </div>
                <div class="ebct-legend-item">
                    <span class="ebct-legend-dot" style="background: #1f6b36;"></span>
                    <span class="ebct-legend-text">Sí cumple - La característica cumple completamente con los criterios establecidos</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption(
        "Las 34 características comienzan marcadas como 'No cumple'. Actualiza cada respuesta según corresponda y guarda la evaluación para generar el panel por fase."
    )

    grouped_characteristics = get_characteristics_by_phase()
    
    # Definir colores y porcentajes de dimensiones
    DIMENSION_COLORS = {
        1: {"color": "#673AB7", "name": "Investigación y Validación Técnica"},  # Purpura
        2: {"color": "#4CAF50", "name": "Estrategia de Propiedad Intelectual"},  # Verde
        3: {"color": "#2196F3", "name": "Estrategia de Desarrollo de Negocio", "pct": 0.30},  # Azul
        4: {"color": "#2196F3", "name": "Modelo de Negocio", "pct": 0.30},  # Azul
        5: {"color": "#2196F3", "name": "Estrategia Comercial", "pct": 0.40},  # Azul
        6: {"color": "#FFC107", "name": "Estrategia y Gestión para Exportación"}  # Amarillo
    }

    # Mapeo de características a dimensiones
    CARACTERISTICA_DIMENSIONES = {
        1: [3,4,5], 2: [1], 3: [1], 4: [1], 5: [1], 6: [1], 7: [6,3,4,5], 8: [6,3,4,5],
        9: [3,4,5], 10: [1], 11: [1], 12: [6,2], 13: [2], 14: [2], 15: [6], 16: [6,3,4,5],
        17: [6], 18: [3,4,5], 19: [6,3,4,5], 20: [6], 21: [6,3,4,5], 22: [6], 23: [3,4,5],
        24: [3,4,5], 25: [3,4,5], 26: [3,4,5], 27: [3,4,5], 28: [6,3,4,5], 29: [6,3,4,5],
        30: [6], 31: [6], 32: [6], 33: [6], 34: [6]
    }

    st.markdown("""
        <style>
        .ebct-map-container {
            display: flex;
            flex-direction: column;
            gap: 2rem;
            padding: 1rem;
        }
        
        .phase-section {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding: 1.5rem;
            border-radius: 15px;
            position: relative;
        }
        
        .phase-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .phase-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .characteristic-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            position: relative;
        }
        
        .dimension-indicators {
            display: flex;
            gap: 0.3rem;
            align-items: center;
        }
        
        .dimension-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .characteristic-title {
            font-size: 0.9rem;
            color: #333;
            line-height: 1.3;
        }
        
        .characteristic-options {
            padding: 0.5rem 0;
        }
        
        .dimension-tooltip {
            display: none;
            position: absolute;
            bottom: 100%;
            left: 0;
            background: white;
            padding: 0.5rem;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 1000;
            min-width: 200px;
        }
        
        .dimension-dot-container:hover .dimension-tooltip {
            display: block;
        }

        /* Colores específicos para cada fase */
        .phase-incipiente {
            background: rgba(103, 58, 183, 0.1);
            border: 1px solid rgba(103, 58, 183, 0.3);
        }
        .phase-incipiente .phase-title {
            background: #673AB7;
        }
        
        .phase-validacion {
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid rgba(76, 175, 80, 0.3);
        }
        .phase-validacion .phase-title {
            background: #4CAF50;
        }
        
        .phase-preparacion {
            background: rgba(33, 150, 243, 0.1);
            border: 1px solid rgba(33, 150, 243, 0.3);
        }
        .phase-preparacion .phase-title {
            background: #2196F3;
        }
        
        .phase-internacionalizacion {
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.3);
        }
        .phase-internacionalizacion .phase-title {
            background: #FFC107;
            color: #333;
        }

        /* Estilo para los radio buttons */
        .characteristic-radio {
            display: flex;
            gap: 1rem;
            padding: 0.5rem;
            background: rgba(0,0,0,0.03);
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.form("fase2_ebct_form"):
        # Leyenda de dimensiones al inicio
        with st.expander("ℹ️ Leyenda de Dimensiones", expanded=False):
            st.markdown("### Dimensiones y sus indicadores:")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("🟣 Investigación y Validación Técnica")
            with col2:
                st.markdown("🟢 Estrategia de Propiedad Intelectual")
            with col3:
                st.markdown("🔵 Preparación para Mercado")
            with col4:
                st.markdown("🟡 Estrategia y Gestión para Exportación")
        
        st.markdown("#### Preparación para Mercado:")
        st.markdown("- Estrategia de Desarrollo de Negocio (30%)")
        st.markdown("- Modelo de Negocio (30%)")
        st.markdown("- Estrategia Comercial (40%)")
        
        st.markdown("---")
        
        # Fases del EBCT
        phase_colors = {
            "Fase Incipiente": "🟣",
            "Fase Validación y PI": "🟢",
            "Fase Preparación para Mercado": "🔵",
            "Fase Internacionalización": "🟡"
        }

        for idx, phase in enumerate(EBCT_PHASES):
            # Determinar si esta fase debería estar expandida inicialmente
            # Por defecto, solo la primera fase estará expandida
            is_expanded = idx == 0
            
            # Crear el expander para la fase
            with st.expander(
                f"{phase_colors[phase['name']]} {phase['name']} - {phase.get('subtitle', '')}",
                expanded=is_expanded
            ):
                # Obtener características de la fase
                characteristics = grouped_characteristics.get(phase["id"], [])
                if not characteristics:
                    st.info("No hay características definidas para esta fase.")
                    continue
                
                # Mostrar todas las características de la fase
                for item in characteristics:
                    with st.container():
                        # Columnas para dimensiones y características
                        col1, col2 = st.columns([0.2, 0.8])
                        
                        with col1:
                            # Mostrar dimensiones como emojis
                            dims = CARACTERISTICA_DIMENSIONES.get(item['id'], [])
                            for dim_id in dims:
                                if dim_id in [3,4,5]:  # Dimensiones azules
                                    st.markdown(f"🔵 {DIMENSION_COLORS[dim_id]['pct']*100:.0f}%")
                                elif dim_id == 1:
                                    st.markdown("🟣")
                                elif dim_id == 2:
                                    st.markdown("🟢")
                                elif dim_id == 6:
                                    st.markdown("🟡")
                        
                        with col2:
                            # Nombre y evaluación
                            st.markdown(f"**{item['name']}**")
                            key = f"ebct_resp_{item['id']}"
                            option = st.radio(
                                item['name'],
                                (OPTION_NO, OPTION_PARTIAL, OPTION_YES),
                                key=key,
                                horizontal=True,
                                label_visibility="collapsed"
                            )
                        
                        st.markdown("---")
                # Características de la fase
                for item in grouped_characteristics.get(phase["id"], []):
                    # Obtener dimensiones de la característica
                    dims = CARACTERISTICA_DIMENSIONES.get(item['id'], [])
                    
                    # Crear indicadores de dimensión
                    dimension_dots = ""
                    for dim_id in dims:
                        dim_info = DIMENSION_COLORS[dim_id]
                        if dim_id in [3,4,5]:  # Dimensiones azules
                            tooltip_text = f"{dim_info['name']} ({dim_info['pct']*100:.0f}%)"
                        else:
                            tooltip_text = dim_info['name']
                    
                    dimension_dots += f"""
                        <div class="dimension-dot-container">
                            <span class="dimension-dot" style="background-color: {dim_info['color']}"></span>
                            <span class="dimension-tooltip">{tooltip_text}</span>
                        </div>
                    """
                # Contenedor para la característica ya implementado arriba: omitido (redundante)
                # Agregar separador visual al final de la fase
            st.markdown("---")  # Separador entre fases

        # Botones de submit y reset - dentro del formulario, fuera del bucle de fases
        col_submit, col_reset = st.columns([1, 1])
        submit_clicked = col_submit.form_submit_button("Guardar evaluación EBCT")
        reset_clicked = col_reset.form_submit_button("Restablecer a 'No cumple'")
        
    if reset_clicked:
        for item in EBCT_CHARACTERISTICS:
            st.session_state[f"ebct_resp_{item['id']}"] = OPTION_NO
        st.info("Se restablecieron las respuestas a 'No cumple'.")

    if submit_clicked:
        responses_map: dict[int, float] = {}
        evaluation_rows = []
        for item in EBCT_CHARACTERISTICS:
            key = f"ebct_resp_{item['id']}"
            option = st.session_state.get(key, OPTION_NO)
            score = OPTION_SCORES[option]
            responses_map[item["id"]] = score
            evaluation_rows.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "phase_id": item["phase_id"],
                    "phase_name": item["phase_name"],
                    "weight": item["weight"],
                    "value": value,
                }
            )
        try:
            timestamp = save_ebct_evaluation(project_id, evaluation_rows)
            st.session_state["ebct_panel_map"] = responses_map
            st.session_state["ebct_last_eval_timestamp"] = timestamp
            panel_map = responses_map
            last_eval_timestamp = timestamp
            history_df = get_ebct_history(project_id)
            last_eval_map = responses_map
            st.success(f"Evaluación EBCT guardada el {timestamp}.")
        except Exception as error:
            st.error(f"Error al guardar la evaluación EBCT: {error}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ==== Integración Semáforo (versión integrada, sin dependencia externa) ====
    def compute_semaforo(responses_map: dict[int, float]) -> pd.DataFrame:
        """Genera una tabla tipo semáforo a partir del mapa de respuestas.

        Lógica integrada:
        - Sí cumple (1.0) -> Verde
        - En proceso (0.5) -> Amarillo
        - No cumple (0.0) -> Rojo
        """
        rows = []
        for item in EBCT_CHARACTERISTICS:
            cid = item["id"]
            name = item["name"]
            phase = item.get("phase_name") or item.get("phase_id")
            weight = item.get("weight", 1)
            if cid in responses_map:
                score = responses_map[cid]
                if score >= 0.9:
                    estado = "🟢 Verde"
                elif score >= 0.4:
                    estado = "🟡 Amarillo"
                else:
                    estado = "🔴 Rojo"
            else:
                estado = "🟡 Amarillo"
                score = 0.5
            # Obtener dimensiones de la característica
            dims = CARACTERISTICA_DIMENSIONES.get(cid, [])
            dimension_labels = []
            for dim_id in dims:
                if dim_id == 1:
                    dimension_labels.append("🟣 Investigación y Validación Técnica")
                elif dim_id == 2:
                    dimension_labels.append("🟢 Estrategia de Propiedad Intelectual")
                elif dim_id in [3, 4, 5]:
                    dimension_labels.append(f"🔵 {DIMENSION_COLORS[dim_id]['name']} ({DIMENSION_COLORS[dim_id]['pct']*100:.0f}%)")
                elif dim_id == 6:
                    dimension_labels.append("🟡 Estrategia y Gestión para Exportación")
            
            rows.append({
                "id": cid,
                "Característica": name,
                "Fase": phase,
                "Dimensiones": " | ".join(dimension_labels),
                "Peso": weight,
                "Cumple": "Sí" if responses_map.get(cid) else "No",
                "EstadoSemaforo": estado,
                "Score": score,
            })
        return pd.DataFrame(rows)

    # UI para semáforo: import, generar y exportar
    with st.container():
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.subheader("Visor Semáforo integrado")
        st.caption(
            "Genera una vista rápida tipo semáforo a partir de las respuestas registradas en la evaluación EBCT."
        )

        col_imp, col_gen, col_exp = st.columns([1, 1, 1])

        # Importador simple: CSV con columnas 'id' y 'cumple' (1/0 o True/False)
        uploaded = col_imp.file_uploader(
            "Importar respuestas (CSV) opcional",
            type=("csv",),
            help="CSV con columnas: id, cumple (1/0 o True/False). Las respuestas importadas sobrescriben las actuales en sesión.",
            key="fase2_semaforo_import",
        )
        if uploaded is not None:
            try:
                imp_df = pd.read_csv(uploaded)
                if "id" in imp_df.columns and "estado" in imp_df.columns:
                    for _, r in imp_df.iterrows():
                        try:
                            cid = int(r["id"])
                        except Exception:
                            continue
                        val = str(r["estado"]).strip().lower()
                        if val in ("1", "true", "sí", "si", "cumple"):
                            st.session_state[f"ebct_resp_{cid}"] = OPTION_YES
                        elif val in ("0.5", "parcial", "en proceso", "proceso"):
                            st.session_state[f"ebct_resp_{cid}"] = OPTION_PARTIAL
                        else:
                            st.session_state[f"ebct_resp_{cid}"] = OPTION_NO
                    st.success("Respuestas importadas y aplicadas en la sesión.")
                else:
                    st.error("Archivo inválido: se requieren columnas 'id' y 'cumple'.")
            except Exception as e:
                st.error(f"Error leyendo el CSV: {e}")

        generate = col_gen.button("Generar semáforo (vista)", key="fase2_gen_semaforo")
        if generate:
            # Construir mapa de respuestas desde st.session_state
            current_map = {}
            for item in EBCT_CHARACTERISTICS:
                key = f"ebct_resp_{item['id']}"
                val = st.session_state.get(key, OPTION_NO) == OPTION_YES
                current_map[item["id"]] = val

            sem_df = compute_semaforo(current_map)

            # KPIs básicos
            total_items = len(sem_df)
            achieved = (sem_df["Score"] * sem_df["Peso"]).sum()
            total_weight = sem_df["Peso"].sum() if total_items else 0.0
            pct = (achieved / total_weight * 100) if total_weight else 0.0

            st.metric("Características evaluadas", total_items)
            st.metric("Peso logrado (sum)", format_weight(achieved))
            st.metric("Cumplimiento (peso)", f"{pct:.1f}%")

            # Definir orden de fases (se usa para todas las visualizaciones)
            phase_order = {
                "Fase Incipiente": 1,
                "Fase Validación y PI": 2,
                "Fase Preparación para Mercado": 3,
                "Fase Internacionalización": 4,
            }
            ordered_phases = sorted(sem_df["Fase"].unique(), key=lambda x: phase_order.get(x, 999))

            # Mostrar tabla semáforo con dimensiones (ordenada por la secuencia de fases definida)
            display_df = sem_df.drop(columns=["id"]).copy()
            display_df["Fase"] = pd.Categorical(display_df["Fase"], categories=ordered_phases, ordered=True)
            # Reordenar las columnas para mostrar las dimensiones después de la característica
            display_df = display_df[["Fase", "Característica", "Dimensiones", "EstadoSemaforo", "Score", "Peso", "Cumple"]]
            display_df = display_df.sort_values(["Fase", "Score"], ascending=[True, False])
            st.dataframe(display_df, use_container_width=True)

            # Panel de Estado EBCT por Fases
            st.write("### Panel de Estado EBCT")
            
            # CSS para el panel de fases
            st.markdown("""
                <style>
                .fase-container {
                    margin: 2rem 0;
                    border-radius: 15px;
                    padding: 1.5rem;
                    background: rgba(255,255,255,0.05);
                }
                
                .fase-titulo {
                    font-size: 1.2rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    display: inline-block;
                }
                
                .fase-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 1.5rem;
                    align-items: start;
                }
                
                .caracteristica-item {
                    background: white;
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                    cursor: pointer;
                    position: relative;
                    border-left: 4px solid;
                }
                
                .caracteristica-item:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 8px 16px rgba(0,0,0,0.15);
                }
                
                .caracteristica-nombre {
                    font-size: 0.9rem;
                    margin-bottom: 0.5rem;
                    color: #2c3e50;
                }
                
                .caracteristica-estado {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                
                .estado-emoji {
                    font-size: 1.2rem;
                }
                
                .estado-score {
                    font-size: 0.8rem;
                    color: #666;
                }
                
                .caracteristica-tooltip {
                    display: none;
                    position: absolute;
                    bottom: 110%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: white;
                    padding: 0.8rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    width: max-content;
                    max-width: 300px;
                    z-index: 1000;
                    text-align: left;
                }
                
                .caracteristica-item:hover .caracteristica-tooltip {
                    display: block;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Colores por fase
            fase_colors = {
                "Fase Incipiente": "#673AB7",  # Morado
                "Fase Validación y PI": "#4CAF50",  # Verde
                "Fase Preparación para Mercado": "#2196F3",  # Azul
                "Fase Internacionalización": "#FFC107"  # Amarillo
            }
            
            # Generar paneles por fase en el orden definido (ordered_phases)
            for fase in ordered_phases:
                grupo = sem_df[sem_df["Fase"] == fase]
                # Sólo renderizar si hay elementos en la fase
                if grupo.empty:
                    continue
                st.markdown(f"""
                    <div class="fase-container">
                        <div class="fase-titulo" style="background: {fase_colors.get(fase, '#666')}20; color: {fase_colors.get(fase, '#666')}">
                            {fase}
                        </div>
                        <div class="fase-grid">
                """, unsafe_allow_html=True)

                for _, row in grupo.iterrows():
                    estado_color = {
                        "🔴 Rojo": "#ff4d4d",
                        "🟡 Amarillo": "#ffd700",
                        "🟢 Verde": "#1f6b36"
                    }.get(row["EstadoSemaforo"], "#666")

                    st.markdown(f"""
                        <div class="caracteristica-item" style="border-left-color: {estado_color}">
                            <div class="caracteristica-nombre">{row['Característica']}</div>
                            <div class="caracteristica-dimensiones" style="margin: 0.5rem 0; font-size: 0.85rem; color: #666;">
                                {row['Dimensiones']}
                            </div>
                            <div class="caracteristica-estado">
                                <span class="estado-emoji">{row['EstadoSemaforo'].split()[0]}</span>
                                <span class="estado-score">Score: {row['Score']:.1f}</span>
                            </div>
                            <div class="caracteristica-tooltip">
                                <strong>ID:</strong> #{row['id']}<br>
                                <strong>Característica:</strong> {row['Característica']}<br>
                                <strong>Dimensiones:</strong><br>{row['Dimensiones'].replace(' | ', '<br>')}<br>
                                <strong>Estado:</strong> {row['EstadoSemaforo']}<br>
                                <strong>Score:</strong> {row['Score']:.1f}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div></div>", unsafe_allow_html=True)

            # Visualizaciones: Radar y Heatmap
            col_radar, col_heat = st.columns(2)

            with col_radar:
                st.write("### Radar por Fase")
                # Preparar datos por fase para el radar (y ordenar según ordered_phases)
                radar_df = sem_df.groupby("Fase").agg({
                    "Score": lambda x: (x * sem_df.loc[x.index, "Peso"]).sum() / sem_df.loc[x.index, "Peso"].sum()
                }).reset_index()
                # Reordenar radar_df según ordered_phases
                radar_df = radar_df.set_index("Fase").reindex(ordered_phases).reset_index()
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_df["Score"] * 100,
                    theta=radar_df["Fase"],
                    fill="toself",
                    name="Cumplimiento",
                    fillcolor="rgba(31, 107, 54, 0.35)",
                    line=dict(color="rgb(31, 107, 54)"),
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100],
                            ticksuffix="%",
                            gridcolor="rgba(0,0,0,0.1)",
                            showline=False,
                        ),
                        bgcolor="rgba(255,255,255,0.95)",
                    ),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=20, b=20),
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_heat:
                st.write("### Heatmap de Cumplimiento")
                # Preparar matriz para heatmap y reordenar filas según ordered_phases
                heat_df = sem_df.pivot_table(
                    values="Score",
                    index="Fase",
                    columns="Característica",
                    aggfunc="first",
                    fill_value=0
                )
                heat_df = heat_df.reindex(ordered_phases)
                
                # Preparar datos para el heatmap con información de dimensiones
                hover_text = []
                for idx, row in sem_df.iterrows():
                    hover_text.append(
                        f"Característica: {row['Característica']}<br>" +
                        f"Fase: {row['Fase']}<br>" +
                        f"Dimensiones: {row['Dimensiones']}<br>" +
                        f"Estado: {row['EstadoSemaforo']}<br>" +
                        f"Score: {row['Score']:.1f}"
                    )

                fig_heat = go.Figure(data=go.Heatmap(
                    z=heat_df.values,
                    x=heat_df.columns,
                    y=heat_df.index,
                    colorscale=[
                        [0, "rgb(255, 77, 77)"],     # Rojo para 0
                        [0.5, "rgb(255, 215, 0)"],   # Amarillo para 0.5
                        [1, "rgb(31, 107, 54)"]      # Verde para 1
                    ],
                    hoverongaps=False,
                    showscale=True,
                    text=hover_text,
                    hoverinfo='text',
                    colorbar=dict(
                        title="Score",
                        tickmode="array",
                        ticktext=["No cumple", "Parcial", "Cumple"],
                        tickvals=[0, 0.5, 1],
                        ticks="outside"
                    )
                ))
                fig_heat.update_layout(
                    margin=dict(l=40, r=40, t=20, b=60),
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        tickangle=45,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        showgrid=False,
                    )
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            # Exportar CSV
            csv_buf = io.StringIO()
            sem_df.to_csv(csv_buf, index=False)
            csv_data = csv_buf.getvalue()
            col_exp.download_button("Exportar semáforo CSV", csv_data, file_name=f"semaforo_proyecto_{project_id}.csv")

        st.markdown("</div>", unsafe_allow_html=True)

panel_timestamp = st.session_state.get("ebct_last_eval_timestamp")
panel_map = st.session_state.get("ebct_panel_map", panel_map)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Panel de trayectoria EBCT")
    if panel_timestamp:
        st.caption(f"Última evaluación EBCT guardada el {panel_timestamp}.")
    if panel_map:
        render_phase_overview(panel_map)
    else:
        st.info("Guarda la evaluación para visualizar el panel segmentado por fase.")

    if not history_df.empty:
        history_augmented = history_df.copy()
        history_augmented["peso_logrado"] = history_augmented["peso"] * history_augmented["cumple"]
        resumen_ebct = (
            history_augmented.groupby("fecha_eval", as_index=False)
            .agg({"peso": "sum", "peso_logrado": "sum"})
            .sort_values("fecha_eval", ascending=False)
        )
        resumen_ebct["porcentaje"] = (
            resumen_ebct.apply(
                lambda row: (row["peso_logrado"] / row["peso"] * 100) if row["peso"] else 0.0,
                axis=1,
            ).round(1)
        )
        resumen_display = pd.DataFrame(
            {
                "Fecha de evaluación": resumen_ebct["fecha_eval"],
                "Características cumplidas": resumen_ebct["peso_logrado"].apply(format_weight),
                "Total características": resumen_ebct["peso"].apply(format_weight),
                "Porcentaje de cumplimiento": resumen_ebct["porcentaje"].map(lambda value: f"{value:.1f}%"),
            }
        )
        with st.expander("Historial de evaluaciones EBCT", expanded=False):
            render_table(
                resumen_display,
                key="fase2_historial_ebct",
                include_actions=False,
                hide_index=True,
                default_page_size=5,
                page_size_options=(5, 10, 20),
            )
    else:
        st.caption("Aún no existen evaluaciones EBCT guardadas para este proyecto.")
    st.markdown("</div>", unsafe_allow_html=True)
