from __future__ import annotations

import json
import math
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler


DEFAULT_PAGE_SIZES: tuple[int, int, int] = (25, 50, 100)


@dataclass
class TableState:
    key: str
    page: int
    page_size: int
    total_rows: int


def _auto_key() -> str:
    counter_key = "_andes_table_auto_counter"
    counter = st.session_state.get(counter_key, 0)
    st.session_state[counter_key] = counter + 1
    return f"andes_table_{counter}"


def _coerce_dataframe(data: Any) -> tuple[pd.DataFrame, Styler | None]:
    if isinstance(data, Styler):
        return data.data.copy(), data
    if isinstance(data, pd.DataFrame):
        return data.copy(), None
    if isinstance(data, pd.Series):
        return data.to_frame(), None
    if isinstance(data, Mapping):
        return pd.DataFrame(data), None
    if isinstance(data, Iterable):
        return pd.DataFrame(list(data)), None
    return pd.DataFrame(), None


def _reset_page(page_state_key: str) -> None:
    st.session_state[page_state_key] = 1


def _pagination_state(
    *,
    key: str,
    total_rows: int,
    page_size_options: Sequence[int],
    default_page_size: int,
) -> TableState:
    state_key = key or _auto_key()
    page_state_key = f"{state_key}__page"
    size_state_key = f"{state_key}__page_size"

    valid_sizes = [size for size in page_size_options if size > 0]
    if not valid_sizes:
        valid_sizes = list(DEFAULT_PAGE_SIZES)

    default_size = default_page_size if default_page_size in valid_sizes else valid_sizes[0]
    if size_state_key not in st.session_state:
        st.session_state[size_state_key] = default_size

    if page_state_key not in st.session_state:
        st.session_state[page_state_key] = 1

    def _on_change() -> None:
        _reset_page(page_state_key)

    col_size, col_summary = st.columns([1.6, 2])

    with col_size:
        st.selectbox(
            "Filas por página",
            valid_sizes,
            key=size_state_key,
            on_change=_on_change,
        )

    page_size = int(st.session_state[size_state_key])
    total_pages = max(1, math.ceil(total_rows / page_size))
    current_page = int(st.session_state[page_state_key])
    current_page = max(1, min(current_page, total_pages))
    st.session_state[page_state_key] = current_page

    start = (current_page - 1) * page_size
    end = min(total_rows, start + page_size)

    with col_summary:
        if total_rows:
            st.markdown(
                f"<div class='andes-table__pagination-summary'>{start + 1}–{end} de {total_rows}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.empty()

    return TableState(key=state_key, page=current_page, page_size=page_size, total_rows=total_rows)


def _render_skeleton(rows: int = 7, cols: int = 6) -> None:
    skeleton_rows = []
    for _ in range(rows):
        skeleton_cells = "".join("<span class='andes-table-skeleton__cell'></span>" for _ in range(cols))
        skeleton_rows.append(f"<div class='andes-table-skeleton__row'>{skeleton_cells}</div>")

    skeleton_html = "".join(
        ["<div class='andes-table-skeleton' role='status'>", *skeleton_rows, "</div>"]
    )
    st.markdown(skeleton_html, unsafe_allow_html=True)


def _render_empty(cta_label: str | None, on_cta: Callable[[], None] | None, *, key: str | None) -> None:
    st.markdown(
        """
        <div class="andes-table-empty">
            <div class="andes-table-empty__title">No hay registros para mostrar</div>
            <div class="andes-table-empty__hint">Añade filtros diferentes o ingresa nuevos registros para ver resultados.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_label:
        button_key = f"{key or 'andes_table'}__empty_cta"
        if st.button(cta_label, key=button_key):
            if on_cta:
                on_cta()


def _render_error(on_retry: Callable[[], None] | None, *, key: str | None) -> None:
    retry_key = f"{key or 'andes_table'}__retry"
    container = st.container()
    with container:
        st.markdown(
            """
            <div class="andes-table-error" role="alert">
                <div class="andes-table-error__title">No pudimos cargar la tabla.</div>
                <div class="andes-table-error__hint">Intenta nuevamente para recargar los datos.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Reintentar", key=retry_key):
            if on_retry:
                on_retry()


def _inject_metadata(
    *,
    table_id: str,
    variant: str,
    state: TableState,
    highlight_top_rows: int | None,
    include_actions: bool,
) -> None:
    options = {
        "page": state.page,
        "pageSize": state.page_size,
        "totalRows": state.total_rows,
        "highlightTopRows": highlight_top_rows,
        "hasActions": include_actions,
    }
    options_json = json.dumps(options, ensure_ascii=False)
    safe_json = options_json.replace("\\", "\\\\").replace("'", "\\'")

    st.markdown(
        f"""
        <script>
        (function() {{
            const doc = window.parent?.document || document;
            if (!doc) return;
            const tables = doc.querySelectorAll('[data-testid="stDataFrameResizable"], [data-testid="stTable"]');
            if (!tables.length) return;
            const target = tables[tables.length - 1];
            if (!target) return;
            target.setAttribute('data-andes-table-id', '{table_id}');
            target.setAttribute('data-andes-variant', '{variant}');
            target.setAttribute('data-andes-options', '{safe_json}');
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_table(
    data: Any,
    *,
    key: str | None = None,
    variant: str = "andes",
    state: str = "ready",
    empty_cta_label: str | None = None,
    on_empty_cta: Callable[[], None] | None = None,
    on_retry: Callable[[], None] | None = None,
    highlight_top_rows: int | None = None,
    include_actions: bool = False,
    page_size_options: Sequence[int] = DEFAULT_PAGE_SIZES,
    default_page_size: int = 25,
    use_container_width: bool = True,
    hide_index: bool = True,
    column_config: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Render a themed data table with Andes styling and UX affordances."""

    table_key = key or _auto_key()

    if state == "loading":
        _render_skeleton()
        return pd.DataFrame()
    if state == "error":
        _render_error(on_retry, key=table_key)
        return pd.DataFrame()

    df, styler = _coerce_dataframe(data)

    if df.empty:
        _render_empty(empty_cta_label, on_empty_cta, key=table_key)
        return df

    total_rows = len(df)

    st.markdown("<div class='andes-table__controls'>", unsafe_allow_html=True)
    table_state = _pagination_state(
        key=table_key,
        total_rows=total_rows,
        page_size_options=page_size_options,
        default_page_size=default_page_size,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    start = (table_state.page - 1) * table_state.page_size
    end = start + table_state.page_size
    sliced_df = df.iloc[start:end].copy()

    display_df: Any
    if styler is not None:
        sliced_styler = sliced_df.style
        try:
            sliced_styler._todo.extend(styler._todo)  # type: ignore[attr-defined]
        except Exception:
            pass
        display_df = sliced_styler
    else:
        display_df = sliced_df

    if include_actions and "Acciones" not in sliced_df.columns:
        display_df = sliced_df.copy()
        display_df["Acciones"] = ""

    height_threshold = kwargs.pop("height", None)
    if height_threshold is None and total_rows > 1000:
        kwargs["height"] = 520
    elif height_threshold is not None:
        kwargs["height"] = height_threshold

    table_id = f"andes-{uuid.uuid4().hex}"

    st.dataframe(
        display_df,
        use_container_width=use_container_width,
        hide_index=hide_index,
        column_config=column_config,
        **kwargs,
    )

    _inject_metadata(
        table_id=table_id,
        variant=variant,
        state=table_state,
        highlight_top_rows=highlight_top_rows,
        include_actions=include_actions,
    )

    return sliced_df


@contextmanager
def unstyled_table() -> Iterable[None]:
    marker_id = f"andes-marker-{uuid.uuid4().hex}"
    st.markdown(
        f"<div id='{marker_id}'></div>",
        unsafe_allow_html=True,
    )
    yield
    st.markdown(
        f"""
        <script>
        (function() {{
            const doc = window.parent?.document || document;
            if (!doc) return;
            const marker = doc.getElementById('{marker_id}');
            if (!marker) return;
            let sibling = marker.nextElementSibling;
            while (sibling) {{
                if (sibling.matches('[data-testid="stDataFrameResizable"], [data-testid="stTable"]')) {{
                    sibling.setAttribute('data-andes-variant', 'unstyled');
                    break;
                }}
                sibling = sibling.nextElementSibling;
            }}
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )
