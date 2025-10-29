import sqlite3
import pandas as pd
import streamlit as st
from .config import DB_PATH, TABLE

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
            id_innovacion INTEGER PRIMARY KEY,
            fecha_creacion TEXT,
            nombre_innovacion TEXT,
            potencial_transferencia TEXT,
            estatus TEXT,
            impacto TEXT,
            nombre_pm TEXT,
            codigo_pm TEXT,
            responsable_pm TEXT,
            estado_pm TEXT,
            activo_pm TEXT,
            responsable_innovacion TEXT,
            tiene_resp_in TEXT,
            fecha_inicio_pm TEXT,
            fecha_termino_pm TEXT,
            fecha_termino_real_pm TEXT,
            evaluacion_numerica REAL,
            sugerencia_rapida TEXT
        );
        """)
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_estado ON {TABLE}(estado_pm);")
        conn.commit()

@st.cache_data(ttl=300)
def fetch_df() -> pd.DataFrame:
    """Fetch the portfolio table as a DataFrame and cache the result for 5 minutes.

    The cache is cleared by write operations (replace_all / upsert_merge) to
    ensure subsequent reads return fresh data.
    """
    with get_conn() as conn:
        return pd.read_sql_query(f"SELECT * FROM {TABLE} ORDER BY id_innovacion", conn)

def replace_all(df: pd.DataFrame):
    with get_conn() as conn:
        conn.execute(f"DELETE FROM {TABLE};")
        df.to_sql(TABLE, conn, if_exists="append", index=False)
    # Invalidate cached reads after a write
    try:
        st.cache_data.clear()
    except Exception:
        # If Streamlit cache API is unavailable for some reason, ignore
        pass

def upsert_merge(df_new: pd.DataFrame):
    current = fetch_df()
    merged = pd.concat([current, df_new]).sort_values("id_innovacion")\
             .drop_duplicates(subset=["id_innovacion"], keep="last")
    replace_all(merged)
    # ensure cache cleared (replace_all already clears but keep as safety)
    try:
        st.cache_data.clear()
    except Exception:
        pass
