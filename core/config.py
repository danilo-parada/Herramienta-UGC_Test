APP_TITLE = "UGC – Plataforma de Innovación"
TZ_NAME = "America/Santiago"
DB_PATH = "db.sqlite"

TABLE = "innovaciones"
TABLE_TRL = "trl_resultados"
TABLE_EBCT = "ebct_evaluaciones"

IMPACTO_ORDER = {"bajo": 1, "medio": 2, "alto": 3}

# Defaults Fase 0
F0_DEFAULTS = {
    "impacto_min": "Medio",
    "puntaje_min": 140,
    "exigir_resp_in": True,
    "exigir_abierto": True,
    "excluir_cerrados": True,
}

# Dimensiones TRL (puedes ajustar etiquetas)
DIMENSIONES_TRL = [
    {"id":"TRL","label":"Tecnológico"},
    {"id":"BRL","label":"Negocio/Modelo"},
    {"id":"CRL","label":"Clientes/Mercado"},
    {"id":"IPRL","label":"Propiedad Intelectual"},
    {"id":"TmRL","label":"Equipo/Capacidades"},
    {"id":"FRL","label":"Finanzas/Riesgo"},
]
