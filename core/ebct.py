"""Definitions and helpers for the EBCT trajectory assessment."""

from __future__ import annotations

from typing import Final

# Paleta de colores utilizada en la visualización del panel EBCT.
COLOR_PALETTE: Final[dict[str, str]] = {
    "azul": "#4a7fb5",
    "purpura": "#a67ce0",
    "amarillo": "#f6d27a",
    "verde": "#66b48a",
}


EBCT_PHASES: Final[list[dict[str, object]]] = [
    {
        "id": "incipiente",
        "name": "Fase Incipiente",
        "subtitle": "Investigación y validación técnica",
        "accent": COLOR_PALETTE["azul"],
        "order": 1,
    },
    {
        "id": "validacion_pi",
        "name": "Fase Validación y PI",
        "subtitle": "Estrategia y protección de la I+D",
        "accent": COLOR_PALETTE["purpura"],
        "order": 2,
    },
    {
        "id": "preparacion_mercado",
        "name": "Fase Preparación para Mercado",
        "subtitle": "Desarrollo comercial y escalamiento",
        "accent": COLOR_PALETTE["amarillo"],
        "order": 3,
    },
    {
        "id": "internacionalizacion",
        "name": "Fase Internacionalización",
        "subtitle": "Expansión a mercados internacionales",
        "accent": COLOR_PALETTE["verde"],
        "order": 4,
    },
]


_PHASE_LABELS = {phase["id"]: phase["name"] for phase in EBCT_PHASES}


# (id, nombre, phase_id, orden_visual, color1, color2)
_CHARACTERISTICS_RAW: Final[list[tuple[int, str, str, int, str, str | None]]] = [
    (1, "Conocimiento de los actores del Ecosistema EBCT", "incipiente", 1, "azul", None),
    (2, "Conocimiento de frontera", "incipiente", 2, "purpura", None),
    (3, "Equipos técnicos y multidisciplinarios", "incipiente", 3, "purpura", None),
    (4, "Capacidad de realizar pruebas de concepto", "incipiente", 4, "purpura", None),
    (5, "Acceso a infraestructura", "incipiente", 5, "purpura", None),
    (6, "Recursos financieros", "incipiente", 6, "purpura", None),
    (7, "Conocimiento de negocios", "incipiente", 7, "amarillo", "azul"),
    (8, "Conocimientos de mercados de interés", "incipiente", 8, "amarillo", "azul"),
    (
        9,
        "Conocimientos legales que permitan una adecuada estrategia legal de la empresa",
        "validacion_pi",
        1,
        "azul",
        None,
    ),
    (10, "Capacidad de realizar pruebas de laboratorio", "validacion_pi", 2, "purpura", None),
    (11, "Función experimental", "validacion_pi", 3, "purpura", None),
    (12, "Conocimiento de mecanismos posibles de PI", "validacion_pi", 4, "amarillo", "verde"),
    (
        13,
        "Conocimientos legales que habiliten negociación de PI con instituciones que albergan la investigación",
        "validacion_pi",
        5,
        "verde",
        None,
    ),
    (
        14,
        "Evaluación estratégica de posibilidades de desarrollo científico, modelo de negocio y PI intramuros (Academia)",
        "validacion_pi",
        6,
        "verde",
        None,
    ),
    (15, "Conocimiento de potencial exportador del desarrollo/solución", "validacion_pi", 7, "amarillo", None),
    (
        16,
        "Conocimientos de normativas/regulaciones vigentes en mercados de interés",
        "validacion_pi",
        8,
        "amarillo",
        "azul",
    ),
    (
        17,
        "Conocimientos de acuerdos comerciales y aranceles vigentes con mercados internacionales de interés",
        "validacion_pi",
        9,
        "amarillo",
        None,
    ),
    (18, "Capacidad de realizar pilotaje comercial", "preparacion_mercado", 1, "azul", None),
    (
        19,
        "Capacidad de ejecución de estrategia de marketing y desarrollo de canales de venta",
        "preparacion_mercado",
        2,
        "amarillo",
        "azul",
    ),
    (20, "Validación técnica en países de interés", "preparacion_mercado", 3, "amarillo", None),
    (
        21,
        "Conocimientos sobre mecanismos de venta y estrategias de marketing",
        "preparacion_mercado",
        4,
        "amarillo",
        "azul",
    ),
    (22, "Conocimiento de potencial exportador de la empresa", "preparacion_mercado", 5, "amarillo", None),
    (23, "Conocimiento de distintos mecanismos de financiamiento", "preparacion_mercado", 6, "azul", None),
    (24, "Capacidades técnicas (marketing y producción)", "preparacion_mercado", 7, "azul", None),
    (25, "Capacidad de levantar capital para iniciar producción", "preparacion_mercado", 8, "azul", None),
    (26, "Conocimiento de métodos de valoración de una EBCT", "preparacion_mercado", 9, "azul", None),
    (
        27,
        "Capacidad de concretar venta nacional que responda a la demanda",
        "preparacion_mercado",
        10,
        "azul",
        None,
    ),
    (
        28,
        "Conocimiento de cómo operan los distintos canales de venta",
        "preparacion_mercado",
        11,
        "amarillo",
        "azul",
    ),
    (
        29,
        "Equipo o persona con conocimientos comerciales",
        "preparacion_mercado",
        12,
        "amarillo",
        "azul",
    ),
    (30, "Validación comercial en países de interés", "internacionalizacion", 1, "amarillo", None),
    (
        31,
        "Conocimiento acabado de los mercados internacionales posibles de acceder",
        "internacionalizacion",
        2,
        "amarillo",
        None,
    ),
    (
        32,
        "Definir estrategia de comercialización exportadora",
        "internacionalizacion",
        3,
        "amarillo",
        None,
    ),
    (
        33,
        "Definición de condiciones de exportación",
        "internacionalizacion",
        4,
        "amarillo",
        None,
    ),
    (
        34,
        "Capacidad de concretar venta internacional que responda a la demanda",
        "internacionalizacion",
        5,
        "amarillo",
        None,
    ),
]


EBCT_CHARACTERISTICS: Final[list[dict[str, object]]] = []
for characteristic_id, name, phase_id, order, color1, color2 in _CHARACTERISTICS_RAW:
    color_primary = COLOR_PALETTE[color1.lower()]
    if color2:
        color_secondary = COLOR_PALETTE[color2.lower()]
    else:
        color_secondary = color_primary
    EBCT_CHARACTERISTICS.append(
        {
            "id": characteristic_id,
            "name": name,
            "phase_id": phase_id,
            "phase_name": _PHASE_LABELS[phase_id],
            "order": order,
            "weight": 1.0,
            "color_primary": color_primary,
            "color_secondary": color_secondary,
        }
    )


EBCT_CHARACTERISTICS_BY_ID: Final[dict[int, dict[str, object]]] = {
    item["id"]: item for item in EBCT_CHARACTERISTICS
}


def get_characteristics_by_phase() -> dict[str, list[dict[str, object]]]:
    """Return the EBCT characteristics grouped (and ordered) by phase."""

    grouped: dict[str, list[dict[str, object]]] = {phase["id"]: [] for phase in EBCT_PHASES}
    for item in EBCT_CHARACTERISTICS:
        grouped[item["phase_id"]].append(item)
    for phase_id, rows in grouped.items():
        rows.sort(key=lambda data: int(data["order"]))
    return grouped


__all__ = [
    "COLOR_PALETTE",
    "EBCT_PHASES",
    "EBCT_CHARACTERISTICS",
    "EBCT_CHARACTERISTICS_BY_ID",
    "get_characteristics_by_phase",
]
