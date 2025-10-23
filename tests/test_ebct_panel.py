from __future__ import annotations

from core.ebct import EBCT_CHARACTERISTICS
from core.ebct_panel import format_weight, prepare_panel_data, render_panel_html


def build_responses_map(true_ids: set[int]) -> dict[int, bool]:
    return {item["id"]: item["id"] in true_ids for item in EBCT_CHARACTERISTICS}


def test_format_weight_handles_integers_and_floats() -> None:
    assert format_weight(3) == "3"
    assert format_weight(3.0) == "3"
    assert format_weight("4") == "4"
    assert format_weight(2.5) == "2.50"



def test_prepare_panel_data_counts_by_phase() -> None:
    true_ids = {item["id"] for item in EBCT_CHARACTERISTICS if item["phase_id"] == "validacion_pi"}
    responses_map = build_responses_map(true_ids)

    panel_data = prepare_panel_data(responses_map)
    phase_map = {row["phase"]["id"]: row for row in panel_data}

    assert phase_map["incipiente"]["total"] == 8.0
    assert phase_map["incipiente"]["achieved"] == 0.0
    assert phase_map["incipiente"]["percentage"] == 0.0

    assert phase_map["validacion_pi"]["total"] == 9.0
    assert phase_map["validacion_pi"]["achieved"] == 9.0
    assert phase_map["validacion_pi"]["percentage"] == 100.0

    assert phase_map["preparacion_mercado"]["total"] == 12.0
    assert phase_map["preparacion_mercado"]["achieved"] == 0.0

    assert phase_map["internacionalizacion"]["total"] == 5.0
    assert phase_map["internacionalizacion"]["achieved"] == 0.0



def test_render_panel_html_contains_expected_sections() -> None:
    true_ids = {item["id"] for item in EBCT_CHARACTERISTICS}
    true_ids.difference_update({32, 34})
    responses_map = build_responses_map(true_ids)

    html = render_panel_html(responses_map)

    assert "<div class='ebct-roadmap'>" in html
    assert "Fase Validación y PI" in html
    assert "100% de cumplimiento · 9/9 características" in html
    assert "Fase Preparación para Mercado" in html
    assert "100% de cumplimiento · 12/12 características" in html
    assert "Fase Internacionalización" in html
    assert "60% de cumplimiento · 3/5 características" in html
    assert "32. Definir estrategia de comercialización exportadora" in html
    assert "ebct-chip--no" in html
    assert "Sí cumple · Peso 1" in html
