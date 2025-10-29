import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from .config import DB_PATH, TABLE_TRL, TZ_NAME

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db_trl():
    with get_conn() as conn:
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_TRL}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_innovacion INTEGER,
            fecha_eval TEXT,
            dimension TEXT,
            nivel INTEGER,
            evidencia TEXT,
            trl_global REAL
        );
        """)
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_TRL}_idinv ON {TABLE_TRL}(id_innovacion);")
        conn.commit()

def save_trl_result(id_innovacion: int, df_dim: pd.DataFrame, trl_global: float | None):
    tz = pytz.timezone(TZ_NAME)
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    if df_dim.empty:
        rows.append({
            "id_innovacion": id_innovacion,
            "fecha_eval": now_str,
            "dimension": None,
            "nivel": None,
            "evidencia": "",
            "trl_global": trl_global,
        })
    else:
        for _, r in df_dim.iterrows():
            rows.append({
                "id_innovacion": id_innovacion,
                "fecha_eval": now_str,
                "dimension": str(r.get("dimension")),
                "nivel": int(r.get("nivel")) if pd.notna(r.get("nivel")) else None,
                "evidencia": str(r.get("evidencia")) if r.get("evidencia") is not None else "",
                "trl_global": trl_global,
            })
    df_save = pd.DataFrame(rows)
    with get_conn() as conn:
        df_save.to_sql(TABLE_TRL, conn, if_exists="append", index=False)
    # Clear cache for history reads so subsequent get_trl_history returns fresh data
    try:
        st.cache_data.clear()
    except Exception:
        pass

@st.cache_data(ttl=300)
def get_trl_history(id_innovacion: int) -> pd.DataFrame:
    """Return TRL history for a project; cached for short period to avoid repeated DB hits."""
    with get_conn() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {TABLE_TRL} WHERE id_innovacion=? ORDER BY fecha_eval DESC, id DESC",
            conn, params=(id_innovacion,)
        )
