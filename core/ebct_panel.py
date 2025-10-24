from __future__ import annotations

from html import escape
from typing import Mapping

from .ebct import EBCT_PHASES, get_characteristics_by_phase


def format_weight(value: float | int | str) -> str:
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


def render_panel_html(responses_map: Mapping[int, bool]) -> str:
    """Generate the HTML snippet used to display EBCT phase progress."""

    panel_data = prepare_panel_data(responses_map)
    html_chunks = ["<div class='ebct-roadmap'>"]
    for data in panel_data:
        phase = data["phase"]
        total = data["total"] or 0.0
        achieved = data["achieved"] or 0.0
        percentage = data["percentage"]
        percentage_label = f"{percentage:.0f}%"
        achieved_label = format_weight(achieved)
        total_label = format_weight(total)
        score_caption = (
            f"{achieved_label}/{total_label} características" if total else "Sin características registradas"
        )
        tooltip = (
            f"{percentage:.0f}% de cumplimiento · {achieved_label}/{total_label} características"
            if total
            else "Sin características registradas"
        )
        item_chunks: list[str] = []
        for item in data["items"]:
            chip_class = "ebct-chip ebct-chip--yes" if item["status"] else "ebct-chip ebct-chip--no"
            tooltip_status = "Sí cumple" if item["status"] else "No cumple"
            tooltip_label = f"{tooltip_status} · Peso {format_weight(item['weight'])}"
            item_chunks.append(
                (
                    f"<div class=\"{chip_class}\" "
                    f"style=\"--chip-color-start: {item['color_primary']}; --chip-color-end: {item['color_secondary']}\" "
                    f"title=\"{escape(tooltip_label)}\">"
                    f"<span class='ebct-chip__title'>{item['id']}. {escape(item['name'])}</span>"
                    f"<small>Peso {format_weight(item['weight'])}</small>"
                    "</div>"
                )
            )
        items_html = "".join(item_chunks)
        html_chunks.append(
            """
            <div class='ebct-phase' style='--phase-accent: {accent}'>
                <div class='ebct-phase__header' title='{tooltip}'>
                    <div>
                        <h4>{title}</h4>
                        <span>{subtitle}</span>
                    </div>
                    <div class='ebct-phase__score'>
                        <strong>{percentage}</strong>
                        <span>{score_caption}</span>
                    </div>
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
                score_caption=escape(score_caption),
                items=items_html,
            )
        )
    html_chunks.append("</div>")
    return "".join(html_chunks)


__all__ = ["format_weight", "prepare_panel_data", "render_panel_html"]
