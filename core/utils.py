from datetime import datetime
import pandas as pd
import pytz
from .config import TZ_NAME

DATE_FIELDS = ["fecha_creacion","fecha_inicio_pm","fecha_termino_pm","fecha_termino_real_pm"]

def tz_today():
    return datetime.now(pytz.timezone(TZ_NAME)).date()

def parse_date(s):
    if pd.isna(s) or s in ("", None): return pd.NaT
    # intenta ISO y DD/MM/YYYY
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try: return pd.to_datetime(str(s), format=fmt, errors="raise")
        except: pass
    return pd.to_datetime(s, errors="coerce")

def parse_float_local(v):
    if v in ("", None) or pd.isna(v): return None
    if isinstance(v,(int,float)): return float(v)
    try: return float(str(v).replace(",", "."))
    except: return None

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in DATE_FIELDS:
        if c in df.columns:
            df[c] = df[c].apply(parse_date)
        else:
            df[c] = pd.NaT
    if "evaluacion_numerica" in df.columns:
        df["evaluacion_numerica"] = df["evaluacion_numerica"].apply(parse_float_local)
    # rellenar textos
    text_cols = ["nombre_innovacion","potencial_transferencia","estatus","impacto",
                 "nombre_pm","codigo_pm","responsable_pm","estado_pm","activo_pm",
                 "responsable_innovacion","tiene_resp_in","sugerencia_rapida"]
    for c in text_cols:
        if c not in df.columns: df[c] = ""
        df[c] = df[c].fillna("")
    return df

def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    today = tz_today()
    df["cerrado"] = (
        df["estado_pm"].str.strip().str.lower().eq("cerrado") |
        df["fecha_termino_real_pm"].notna()
    )
    df["en_plazo"] = False
    has_due = df["fecha_termino_pm"].notna()
    df.loc[has_due, "en_plazo"] = (
        df.loc[has_due, "fecha_termino_pm"].dt.date >= today
    ) & (~df["cerrado"])
    df["falta_resp_in"] = (
        df["tiene_resp_in"].str.strip().str.lower().isin(["no","false","0",""]) |
        (df["responsable_innovacion"].str.strip() == "")
    )
    return df
