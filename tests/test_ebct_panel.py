from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.ebct import EBCT_CHARACTERISTICS, EBCT_PHASES
from core.ebct_panel import build_phase_summary, format_weight, prepare_panel_data


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



def test_build_phase_summary_returns_expected_labels() -> None:
    true_ids = {item["id"] for item in EBCT_CHARACTERISTICS}
    true_ids.difference_update({32, 34})
    responses_map = build_responses_map(true_ids)

    summaries = build_phase_summary(responses_map)
    assert len(summaries) == len({phase["id"] for phase in EBCT_PHASES})

    summary_map = {entry["id"]: entry for entry in summaries}

    assert summary_map["validacion_pi"]["percentage_label"] == "100%"
    assert summary_map["validacion_pi"]["achieved_label"] == "9"
    assert summary_map["validacion_pi"]["total_label"] == "9"

    assert summary_map["internacionalizacion"]["percentage_label"] == "60%"
    assert summary_map["internacionalizacion"]["achieved_label"] == "3"
    assert summary_map["internacionalizacion"]["total_label"] == "5"
