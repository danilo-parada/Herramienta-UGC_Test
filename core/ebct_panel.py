from __future__ import annotations

from typing import Mapping, Union

from .ebct import EBCT_PHASES, get_characteristics_by_phase


def format_weight(value: Union[float, int, str]) -> str:
    """Format a weight value for display, avoiding unnecessary decimals."""

    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value_float.is_integer():
        return str(int(value_float))
    return f"{value_float:.2f}"


def prepare_panel_data(responses_map: Mapping[int, bool]) -> list[dict[str, object]]:
    """Return EBCT phase summaries ready for rendering."""

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


def build_phase_summary(responses_map: Mapping[int, bool]) -> list[dict[str, object]]:
    """Return lightweight phase summaries ready for table-based rendering."""

    phase_summaries: list[dict[str, object]] = []
    for data in prepare_panel_data(responses_map):
        phase = data["phase"]
        total = data["total"] or 0.0
        achieved = data["achieved"] or 0.0
        percentage = data["percentage"]
        phase_summaries.append(
            {
                "id": phase.get("id"),
                "name": phase.get("name", "Fase"),
                "subtitle": phase.get("subtitle", ""),
                "percentage_value": percentage,
                "percentage_label": f"{percentage:.0f}%",
                "achieved_value": achieved,
                "achieved_label": format_weight(achieved),
                "total_value": total,
                "total_label": format_weight(total),
            }
        )
    return phase_summaries


__all__ = ["format_weight", "prepare_panel_data", "build_phase_summary"]
