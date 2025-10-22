import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.facecolor": "#f5f7fb",
})

fig, ax = plt.subplots(figsize=(15, 9), dpi=160)
ax.set_xlim(0, 15)
ax.set_ylim(0, 9)
ax.axis("off")

# Card background
def add_card(x, y, width, height, radius=0.25, **kwargs):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle=f"round,pad=0.3,rounding_size={radius}",
            linewidth=0,
            **kwargs,
        )
    )

add_card(0.4, 0.6, 14.2, 7.9, facecolor="#eef2f9")
add_card(0.5, 0.7, 14.0, 7.7, facecolor="#ffffff")

# Title section
ax.text(
    7.5,
    8.7,
    "PLATAFORMA UGC",
    ha="center",
    va="center",
    fontsize=30,
    fontweight="bold",
    color="#1f3b73",
)
ax.text(
    7.5,
    8.2,
    "Hoja de ruta para gestionar innovaciones desde la I+D hasta la comercialización",
    ha="center",
    va="center",
    fontsize=16,
    color="#3f5c94",
)

# Phases configuration
phases = [
    {
        "title": "FASE 0",
        "subtitle": "Portafolio & Filtro",
        "bullet": "Registra iniciativas, normaliza datos críticos y asigna responsables",
    },
    {
        "title": "FASE 1",
        "subtitle": "Evaluación TRL",
        "bullet": "Califica madurez en 6 dimensiones y documenta evidencias",
    },
    {
        "title": "FASE 2",
        "subtitle": "Evaluación EBCT",
        "bullet": "Analiza la trayectoria del proyecto y define brechas estratégicas",
    },
    {
        "title": "FASE 3",
        "subtitle": "Diagnóstico",
        "bullet": "Convierte resultados en requerimientos de recursos y acciones",
    },
    {
        "title": "FASE 4",
        "subtitle": "Paneles e Indicadores",
        "bullet": "Monitorea portafolio, compromisos y desempeño en tiempo real",
    },
]

palette = ["#1f78b4", "#33a0c7", "#53b3cb", "#80d0d9", "#a5e0dd"]
center_y = 5.65
radius = 0.95

for idx, (phase, color) in enumerate(zip(phases, palette)):
    cx = 2 + idx * 2.75
    circle = Circle((cx, center_y), radius, color=color, alpha=0.95)
    ax.add_patch(circle)
    ax.text(cx, center_y + 0.55, phase["title"], ha="center", va="center", fontsize=13, fontweight="bold", color="#ffffff")
    ax.text(cx, center_y + 0.15, phase["subtitle"], ha="center", va="center", fontsize=11, color="#e8f4fb")
    ax.text(
        cx,
        center_y - 0.75,
        phase["bullet"],
        ha="center",
        va="center",
        fontsize=10.5,
        color="#1f3b73",
        wrap=True,
    )
    if idx < len(phases) - 1:
        ax.annotate(
            "",
            xy=(cx + radius + 0.3, center_y),
            xytext=(cx + radius + 0.9, center_y),
            arrowprops=dict(arrowstyle="->", color="#7088b9", linewidth=2.0),
        )

# Bottom narrative
add_card(1.0, 1.45, 13.0, 1.7, facecolor="#1f3b73", radius=0.35)
ax.text(
    7.5,
    2.75,
    "Cómo funciona",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold",
    color="#ffffff",
)

steps = [
    ("Configura el portafolio maestro con datos trazables."),
    ("Prioriza proyectos de alto potencial con criterios objetivos."),
    ("Evalúa TRL y otras métricas para identificar brechas."),
    ("Planifica recursos, hitos y responsables."),
    ("Visualiza indicadores y comparte avances con aliados."),
]

for idx, text in enumerate(steps):
    x = 1.6 + idx * 2.7
    ax.text(x, 2.1, f"{idx + 1}.", ha="center", va="center", fontsize=12, fontweight="bold", color="#f7f9ff")
    ax.text(x + 0.8, 2.1, text, ha="left", va="center", fontsize=11, color="#f7f9ff")

ax.text(
    7.5,
    1.1,
    "Resultados: flujo único de trabajo, decisión ágil sobre inversión y visibilidad integral del portafolio.",
    ha="center",
    va="center",
    fontsize=12,
    color="#354668",
)

fig.savefig("assets/infografia_fases_ugc.png", dpi=180, bbox_inches="tight", facecolor="#f5f7fb")
plt.close(fig)
