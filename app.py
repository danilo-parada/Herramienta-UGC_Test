from pathlib import Path

import streamlit as st

from core.theme import load_theme

st.set_page_config(page_title="Plataforma EBCT", page_icon="🌲", layout="wide")

BENEFITS = [
    "Mostrar de forma visual e interactiva la hoja de ruta",
    "Facilitar la identificacion de financiamiento, programas y aliados",
    "Reducir la incertidumbre y mejorar la gestion estrategica",
]

PHASES = [
    {
        "title": "Fase 0",
        "subtitle": "Portafolio y filtro inicial",
        "summary": "Registrar iniciativas en el portafolio maestro con datos clave y filtros de madurez",
        "detail": (
            "Consolida informacion (impacto, estado, responsables, fechas) y realiza un primer filtro para definir avance."
        ),
    },
    {
        "title": "Fase 1",
        "subtitle": "IRL (Radiografia)",
        "summary": "Evaluar seis dimensiones (CRL, BRL, TRL, IPRL, TmRL, FRL) y obtener la radiografia del proyecto",
        "detail": (
            "Aplica la calculadora de madurez para cliente, negocio, tecnologia, PI, equipo y financiamiento con evidencias trazables."
        ),
    },
    {
        "title": "Fase 2",
        "subtitle": "EBCT",
        "summary": "Analizar el proyecto segun la trayectoria EBCT (Incipiente, Validacion/PI, Mercado, Comercializacion)",
        "detail": (
            "Revisa subcaracteristicas EBCT, identifica brechas y prepara recomendaciones para mercado y comercializacion."
        ),
    },
    {
        "title": "Fase 3",
        "subtitle": "Diagnostico",
        "summary": "Definir requerimientos de recursos humanos, tecnologia y financiamiento",
        "detail": (
            "Elabora carta Gantt, lista de recursos y planifica reuniones de seguimiento para cerrar brechas."
        ),
    },
    {
        "title": "Fase 4",
        "subtitle": "Panel de indicadores",
        "summary": "Monitorear el portafolio y el desempeno de cada proyecto",
        "detail": (
            "Integra datos en paneles individuales y generales para apoyar decisiones estrategicas."
        ),
    },
]

BLOQUES = [
    "La plataforma filtra proyectos que avanzaran a la evaluacion de madurez.",
    "Cada dimension tiene nueve niveles para visualizar progreso.",
    "Un experto valida evidencias y obtiene un diagnostico cualitativo.",
    "Elaboracion de cronograma, recursos y reuniones de seguimiento.",
]

ROLES = [
    {"label": "Portafolio Maestro", "subtitle": "Gerencia I+D+I INFOR", "color": "#255734"},
    {"label": "Responsable Innovacion", "subtitle": "Investigadores INFOR", "color": "#3f8144"},
    {"label": "Equipo", "subtitle": "UGC-INFOR", "color": "#6f4b2c"},
    {"label": "UGC / UdT", "subtitle": "Gerencia I+D+I INFOR", "color": "#8c6236"},
]

load_theme()

st.markdown(
    """
<style>
.hero-wrapper {
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(0, 1.1fr);
    gap: 2.4rem;
    align-items: stretch;
    margin-bottom: 2.8rem;
}

.hero-text {
    padding: 2.2rem 2.4rem;
    border-radius: 28px;
    background: linear-gradient(160deg, rgba(18, 48, 29, 0.9) 0%, rgba(63, 129, 68, 0.92) 100%);
    color: #f4f9f1;
    box-shadow: 0 34px 60px rgba(12, 32, 20, 0.35);
}

.hero-text h1 {
    font-size: 2.4rem;
    margin-top: 0.8rem;
    margin-bottom: 1rem;
    color: #fefcf8;
}

.hero-text p {
    font-size: 1.02rem;
    line-height: 1.6;
    color: rgba(248, 244, 237, 0.88);
}

.hero-benefits {
    position: relative;
    padding: 2.2rem;
    border-radius: 26px;
    background: linear-gradient(150deg, rgba(77, 51, 32, 0.95), rgba(140, 98, 54, 0.92));
    color: #fff9f0;
    box-shadow: 0 30px 55px rgba(51, 33, 19, 0.38);
    overflow: hidden;
}

.hero-benefits:after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    top: -40px;
    right: -60px;
}

.hero-benefits h3 {
    margin-bottom: 1rem;
    font-size: 1.4rem;
    color: #fffdf8;
}

.hero-benefits ul {
    margin: 0;
    padding-left: 1rem;
    display: grid;
    gap: 0.8rem;
}

.hero-benefits li {
    font-weight: 500;
    line-height: 1.5;
}

.phase-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.6rem;
    margin-top: 1.8rem;
}

.phase-card {
    position: relative;
    padding: 1.6rem 1.4rem 1.8rem;
    border-radius: 22px;
    background: #ffffff;
    border: 1px solid rgba(var(--shadow-color), 0.12);
    box-shadow: 0 26px 48px rgba(var(--shadow-color), 0.18);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    min-height: 240px;
}

.phase-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 34px 60px rgba(var(--shadow-color), 0.28);
}

.phase-index {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(63, 129, 68, 0.96), rgba(18, 48, 29, 0.95));
    color: #fefcf8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.1rem;
    box-shadow: 0 16px 24px rgba(var(--shadow-color), 0.22);
    margin-bottom: 1rem;
}

.phase-card h3 {
    font-size: 1.05rem;
    margin-bottom: 0.35rem;
    color: var(--text-900);
}

.phase-card span {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--forest-700);
}

.phase-card p {
    font-size: 0.9rem;
    line-height: 1.55;
    color: var(--text-500);
    margin-top: 0.6rem;
}

.divider-banner {
    margin: 3rem 0 2.2rem;
    position: relative;
    padding: 1rem 2.6rem;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    border-radius: 999px;
    color: #fffdf8;
    background: linear-gradient(90deg, rgba(77, 51, 32, 0.95), rgba(37, 87, 52, 0.95));
    box-shadow: 0 20px 45px rgba(39, 24, 12, 0.32);
}

.focus-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.4rem;
}

.focus-card {
    position: relative;
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    background: linear-gradient(160deg, rgba(248, 244, 237, 0.85), rgba(196, 213, 185, 0.7));
    border: 1px solid rgba(var(--shadow-color), 0.12);
    box-shadow: 0 18px 36px rgba(var(--shadow-color), 0.18);
    font-weight: 500;
    line-height: 1.5;
}

.focus-card:before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    border: 1px solid rgba(255, 255, 255, 0.6);
    pointer-events: none;
}

.roles-band {
    margin-top: 2.6rem;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1.1rem;
    background: rgba(18, 48, 29, 0.08);
    padding: 1.4rem 1.6rem;
    border-radius: 24px;
    border: 1px solid rgba(var(--shadow-color), 0.12);
}

.role-pill {
    text-align: center;
}

.role-pill strong {
    display: block;
    margin-bottom: 0.25rem;
    color: var(--text-900);
}

.role-dot {
    width: 18px;
    height: 18px;
    border-radius: 999px;
    margin: 0 auto 0.5rem;
    box-shadow: 0 6px 12px rgba(var(--shadow-color), 0.24);
}

.cta-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 1.6rem;
}

@media (max-width: 1000px) {
    .hero-wrapper {
        grid-template-columns: 1fr;
    }

    .hero-benefits {
        order: -1;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrapper">
        <div class="hero-text">
            <span class="badge-soft">INFOR · Gestion de Innovacion</span>
            <h1>Plataforma estrategica para la hoja de ruta EBCT</h1>
            <p>
                Una experiencia integral que acompana a los equipos en la maduracion de proyectos, desde la idea y los ensayos
                tempranos hasta la validacion de mercado y la comercializacion. Cada fase ha sido disenada para tomar decisiones con
                evidencias, enfocando esfuerzos y recursos clave.
            </p>
        </div>
        <div class="hero-benefits">
            <h3>Beneficios clave</h3>
            <ul>
                {benefits}
            </ul>
        </div>
    </div>
    """.format(
        benefits="".join(f"<li>{item}</li>" for item in BENEFITS)
    ),
    unsafe_allow_html=True,
)

st.markdown("### Fases de acompanamiento")

phase_cols = st.columns(len(PHASES))
for index, (col, phase) in enumerate(zip(phase_cols, PHASES), start=1):
    with col:
        st.markdown(
            f"""
            <div class=\"phase-card\">
                <div class=\"phase-index\">{index}</div>
                <h3>{phase['title']}</h3>
                <span>{phase['subtitle']}</span>
                <p>{phase['summary']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Detalle de la fase"):
            st.write(phase["detail"])

st.markdown(
    "<div class='divider-banner'>Hoja de ruta del proyecto: desde la I+D hacia la comercializacion</div>",
    unsafe_allow_html=True,
)

st.markdown("#### Enfoque en resultados tangibles")
st.markdown(
    """
    <div class="focus-grid">
        {blocks}
    </div>
    """.format(
        blocks="".join(f"<div class='focus-card'>{text}</div>" for text in BLOQUES)
    ),
    unsafe_allow_html=True,
)

st.markdown("#### Equipos protagonistas")

roles_html = "<div class='roles-band'>"
for role in ROLES:
    roles_html += (
        f"<div class='role-pill'><div class='role-dot' style='background:{role['color']}'></div>"
        f"<strong>{role['label']}</strong><span>{role['subtitle']}</span></div>"
    )
roles_html += "</div>"
st.markdown(roles_html, unsafe_allow_html=True)

fase0_page = next(Path("pages").glob("02_*_Fase_0_Portafolio.py"), None)
if fase0_page:
    st.markdown("<div class='cta-wrapper'>", unsafe_allow_html=True)
    if st.button("Ir a Fase 0", type="primary"):
        st.switch_page(str(fase0_page))
    st.markdown("</div>", unsafe_allow_html=True)
