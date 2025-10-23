import pandas as pd
import streamlit as st

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


OPTION_NO = "No cumple"
OPTION_YES = "Sí cumple"

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


def _format_weight(value: float) -> str:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value_float.is_integer():
        return str(int(value_float))
    return f"{value_float:.2f}"


def _prepare_panel_data(responses_map: dict[int, bool]) -> list[dict[str, object]]:
    grouped = get_characteristics_by_phase()
    panel_rows: list[dict[str, object]] = []
    for phase in sorted(EBCT_PHASES, key=lambda info: int(info.get("order", 0))):
        items = []
        total = 0.0
        achieved = 0.0
        for item in grouped.get(phase["id"], []):
            weight = float(item.get("weight", 1.0))
            status = bool(responses_map.get(item["id"], False))
            total += weight
            if status:
                achieved += weight
            items.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "status": status,
                    "weight": weight,
                    "color_primary": item["color_primary"],
                    "color_secondary": item["color_secondary"],
                }
            )
        percentage = (achieved / total * 100) if total else 0.0
        panel_rows.append(
            {
                "phase": phase,
                "items": items,
                "total": total,
                "achieved": achieved,
                "percentage": percentage,
            }
        )
    return panel_rows


def _render_panel_html(responses_map: dict[int, bool]) -> str:
    panel_data = _prepare_panel_data(responses_map)
    html_chunks = ["<div class='ebct-roadmap'>"]
    for data in panel_data:
        phase = data["phase"]
        total = data["total"] or 0.0
        achieved = data["achieved"] or 0.0
        percentage = data["percentage"]
        percentage_label = f"{percentage:.0f}%"
        tooltip = (
            f"{percentage:.0f}% de cumplimiento · {achieved:.0f}/{total:.0f} características"
            if total
            else "Sin características registradas"
        )
        items_html = "".join(
            (
                "<div class='ebct-chip "
                + ("ebct-chip--yes'" if item["status"] else "ebct-chip--no'")
                + f" style='--chip-color-start: {item['color_primary']}; --chip-color-end: {item['color_secondary']}';"
                + f" title='{escape(('Sí cumple' if item['status'] else 'No cumple') + ' · Peso ' + _format_weight(item['weight']))}'>"
                + f"<span class='ebct-chip__title'>{item['id']}. {escape(item['name'])}</span>"
                + f"<small>Peso {_format_weight(item['weight'])}</small>"
                + "</div>"
            )
            for item in data["items"]
        )
        html_chunks.append(
            """
            <div class='ebct-phase' style='--phase-accent: {accent}'>
                <div class='ebct-phase__header' title='{tooltip}'>
                    <div>
                        <h4>{title}</h4>
                        <span>{subtitle}</span>
                    </div>
                    <strong>{percentage}</strong>
                </div>
                <div class='ebct-phase__items'>
                    {items}
                </div>
            </div>
            """.format(
                accent=escape(str(phase.get("accent", "#3f8144"))),
                tooltip=escape(tooltip),
                title=escape(str(phase.get("name", "Fase"))),
                subtitle=escape(str(phase.get("subtitle", ""))),
                percentage=escape(percentage_label),
                items=items_html,
            )
        )
    html_chunks.append("</div>")
    return "".join(html_chunks)


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

    .ebct-phase__header strong {
        font-size: 1.35rem;
        color: var(--phase-accent, var(--forest-700));
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
    st.subheader("Evaluación EBCT por características")
    st.caption(
        "Las 34 características comienzan marcadas como 'No cumple'. Actualiza cada respuesta y guarda la evaluación para generar el panel por fase."
    )
    grouped_characteristics = get_characteristics_by_phase()
    with st.form("fase2_ebct_form"):
        for phase in EBCT_PHASES:
            expanded = phase["id"] == EBCT_PHASES[0]["id"]
            with st.expander(f"{phase['name']} · {phase['subtitle']}", expanded=expanded):
                for item in grouped_characteristics.get(phase["id"], []):
                    key = f"ebct_resp_{item['id']}"
                    st.radio(
                        f"{item['id']}. {item['name']}",
                        (OPTION_NO, OPTION_YES),
                        key=key,
                        horizontal=True,
                    )
        col_submit, col_reset = st.columns([1, 1])
        submit_clicked = col_submit.form_submit_button("Guardar evaluación EBCT")
        reset_clicked = col_reset.form_submit_button("Restablecer a 'No cumple'")

    if reset_clicked:
        for item in EBCT_CHARACTERISTICS:
            st.session_state[f"ebct_resp_{item['id']}"] = OPTION_NO
        st.info("Se restablecieron las respuestas a 'No cumple'.")

    if submit_clicked:
        responses_map: dict[int, bool] = {}
        evaluation_rows = []
        for item in EBCT_CHARACTERISTICS:
            key = f"ebct_resp_{item['id']}"
            value = st.session_state.get(key, OPTION_NO) == OPTION_YES
            responses_map[item["id"]] = value
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

panel_timestamp = st.session_state.get("ebct_last_eval_timestamp")
panel_map = st.session_state.get("ebct_panel_map", panel_map)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Panel de trayectoria EBCT")
    if panel_timestamp:
        st.caption(f"Última evaluación EBCT guardada el {panel_timestamp}.")
    if panel_map:
        st.markdown(_render_panel_html(panel_map), unsafe_allow_html=True)
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
                "Características cumplidas": resumen_ebct["peso_logrado"].apply(_format_weight),
                "Total características": resumen_ebct["peso"].apply(_format_weight),
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
