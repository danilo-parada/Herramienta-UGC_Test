import pandas as pd
from .utils import normalize_df
from .db import replace_all, fetch_df

SEED_DATA = [
    [1,"2025-06-24","Sensor IoT para riego eficiente","Comercial","MVP","Alto",
     "Plataforma AgroTech","AGT-001","María Torres","Abierto","Sí","Dr. Juan Pérez","Sí",
     "2025-07-24","2025-09-17","", "132,5","Fuera de plazo; Impacto alto; Prioridad alta"],
    [2,"2025-08-23","Algoritmo de predicción de incendios","Uso de trasferencia","Prototipo","Alto",
     "","","","Abierto","Sí","","No","2025-09-07","2025-11-06","", "150",
     "Dentro de plazo; Impacto alto; Sin Resp IN; Prioridad alta"],
    [3,"2025-09-12","App de seguimiento de EBCT","Bien publico","Tecnología","Medio",
     "Suite Innovación Digital","SID-010","Carlos Rivas","Abierto","Sí","","No",
     "2025-09-17","2025-10-12","", "145","Dentro de plazo; Sin Resp IN; Prioridad alta"],
    [4,"2025-05-25","Sistema modular de casas (layout)","Uso de trasferencia","Servicio","Alto",
     "Constructiva 4.0","CON-777","Ana González","Cerrado","No","Ing. Paula Méndez","Sí",
     "2025-06-14","2025-09-12","2025-09-10", "0","Proy. cerrado; Fuera de plazo; Impacto alto; Prioridad baja"],
    [5,"2025-03-06","Impresión 3D de biopolímeros","Comercial","EBCT","Medio",
     "BioFab LATAM","BIO-022","Equipo BioFab","Cerrado","No","Dra. Camila Soto","Sí",
     "2025-03-26","2025-08-13","2025-08-08", "0","Proy. cerrado; Fuera de plazo; Prioridad baja"],
    [6,"2025-07-14","Plataforma de trazabilidad hospitalaria","Uso de trasferencia","Prototipo","Medio",
     "Salud Digital","SAL-115","Ignacio Rojas","Abierto","Sí","","No",
     "2025-07-24","2025-09-27","", "130","Fuera de plazo; Sin Resp IN; Prioridad alta"],
    [7,"2025-09-07","Marketplace de tecnología EBCT","Conocimiento para futura investigacion","Idea","Bajo",
     "","","","Abierto","Sí","MSc. Daniela Vidal","Sí",
     "2025-09-12","2025-11-21","", "92,5","Dentro de plazo; Prioridad media"],
    [8,"2025-08-08","Optimización logística forestal","Conocimiento para futura investigacion","Prototipo","Alto",
     "CMPC Logística IA","CMPC-LOG-09","Equipo CMPC","Abierto","Sí","","No",
     "2025-08-09","2025-10-07","", "160","Dentro de plazo; Impacto alto; Sin Resp IN; Prioridad alta"]
]

def seed_if_empty():
    df = fetch_df()
    if df.empty:
        cols = ["id_innovacion","fecha_creacion","nombre_innovacion","potencial_transferencia",
                "estatus","impacto","nombre_pm","codigo_pm","responsable_pm","estado_pm",
                "activo_pm","responsable_innovacion","tiene_resp_in","fecha_inicio_pm",
                "fecha_termino_pm","fecha_termino_real_pm","evaluacion_numerica","sugerencia_rapida"]
        seed = pd.DataFrame(SEED_DATA, columns=cols)
        seed = normalize_df(seed)
        replace_all(seed)
