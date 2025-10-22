from __future__ import annotations

from pathlib import Path

import streamlit as st


def _read_asset(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_theme() -> None:
    """Inject the shared visual theme and behaviour for the INFOR experience."""
    assets_dir = Path(__file__).resolve().parent.parent / "assets"

    css = _read_asset(assets_dir / "theme.css")
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    js = _read_asset(assets_dir / "theme.js")
    if js:
        st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)
