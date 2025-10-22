import pandas as pd
from .config import DIMENSIONES_TRL

def esquema_respuestas():
    return pd.DataFrame([{"dimension": d["id"], "nivel": None, "evidencia": ""} for d in DIMENSIONES_TRL])

def calcular_trl(df_dim: pd.DataFrame):
    # Promedio de niveles 1–9
    niveles = df_dim["nivel"].dropna()
    if niveles.empty: return None
    try:
        niveles = niveles.astype(int)
        if not ((niveles >= 1) & (niveles <= 9)).all():
            return None
        return float(niveles.mean())
    except:
        return None

def labels_dimensiones():
    return [d["label"] for d in DIMENSIONES_TRL]

def ids_dimensiones():
    return [d["id"] for d in DIMENSIONES_TRL]
