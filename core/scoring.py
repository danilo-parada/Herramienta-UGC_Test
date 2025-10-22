import pandas as pd
from .config import IMPACTO_ORDER

def filter_candidatos(df: pd.DataFrame, impacto_min="Medio", puntaje_min=140,
                      exigir_resp_in=True, exigir_abierto=True, excluir_cerrados=True):
    df = df.copy()
    thr = 2 if impacto_min.lower()=="medio" else 3
    impacto_ok = df["impacto"].str.lower().map(IMPACTO_ORDER).fillna(0) >= thr
    puntaje_ok = df["evaluacion_numerica"].fillna(-1) >= puntaje_min
    resp_ok = ~df["falta_resp_in"] if exigir_resp_in else True
    pm_ok = (df["estado_pm"].str.lower()=="abierto") if exigir_abierto else True
    not_closed = ~df["cerrado"] if excluir_cerrados else True
    mask = impacto_ok & puntaje_ok & resp_ok & pm_ok & not_closed
    out = df[mask].copy()
    out["candidato_alto_potencial"] = True
    return out
