"""Persistence helpers for the EBCT evaluation (Fase 2)."""

from __future__ import annotations

from datetime import datetime
import sqlite3
from typing import Iterable

import pandas as pd
import pytz

from .config import DB_PATH, TABLE_EBCT, TZ_NAME


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db_ebct() -> None:
    """Ensure the SQLite table for EBCT evaluations exists."""

    with _get_conn() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_EBCT} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_innovacion INTEGER NOT NULL,
                fecha_eval TEXT NOT NULL,
                caracteristica_id INTEGER NOT NULL,
                caracteristica_nombre TEXT NOT NULL,
                fase_id TEXT NOT NULL,
                fase_nombre TEXT NOT NULL,
                peso REAL NOT NULL,
                cumple INTEGER NOT NULL
            );
            """
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_EBCT}_innovacion ON {TABLE_EBCT}(id_innovacion);"
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_EBCT}_fecha ON {TABLE_EBCT}(fecha_eval);"
        )
        conn.commit()


def save_ebct_evaluation(
    id_innovacion: int,
    responses: Iterable[dict[str, object]],
) -> str:
    """Persist an EBCT evaluation and return the timestamp used."""

    tz = pytz.timezone(TZ_NAME)
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict[str, object]] = []
    for row in responses:
        rows.append(
            {
                "id_innovacion": int(id_innovacion),
                "fecha_eval": timestamp,
                "caracteristica_id": int(row.get("id")),
                "caracteristica_nombre": str(row.get("name", "")),
                "fase_id": str(row.get("phase_id", "")),
                "fase_nombre": str(row.get("phase_name", "")),
                "peso": float(row.get("weight", 1.0)),
                "cumple": 1 if row.get("value") else 0,
            }
        )

    if not rows:
        return timestamp

    df = pd.DataFrame(rows)
    with _get_conn() as conn:
        df.to_sql(TABLE_EBCT, conn, if_exists="append", index=False)
    return timestamp


def get_ebct_history(id_innovacion: int) -> pd.DataFrame:
    """Return the full EBCT history for a project (latest first)."""

    with _get_conn() as conn:
        return pd.read_sql_query(
            f"""
            SELECT *
            FROM {TABLE_EBCT}
            WHERE id_innovacion = ?
            ORDER BY fecha_eval DESC, id DESC
            """,
            conn,
            params=(id_innovacion,),
        )


def get_latest_ebct_evaluation(id_innovacion: int) -> pd.DataFrame:
    """Return only the latest EBCT evaluation rows for the project."""

    history = get_ebct_history(id_innovacion)
    if history.empty:
        return history
    latest_timestamp = history["fecha_eval"].iloc[0]
    return history[history["fecha_eval"] == latest_timestamp].copy()


__all__ = ["init_db_ebct", "save_ebct_evaluation", "get_ebct_history", "get_latest_ebct_evaluation"]
