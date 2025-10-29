import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pathlib import Path
from html import escape
import re
from typing import Any


def _rerun_app() -> None:
    """Trigger a Streamlit rerun compatible with multiple versions."""

    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover - fallback for older Streamlit versions
        st.experimental_rerun()

from core import db, utils, trl, irl_level_flow
from core.data_table import render_table
from core.db_trl import save_trl_result, get_trl_history
from core.theme import load_theme

# Definiciones de dimensiones con sus descripciones
DIMENSION_DESCRIPTIONS = {
    "CRL": "Clientes/Mercado",
    "BRL": "Negocio/Modelo",
    "TRL": "Tecnológico",
    "IPRL": "Propiedad Intelectual",
    "TmRL": "Equipo/Capacidades",
    "FRL": "Finanzas/Riesgo",
}

IRL_DIMENSIONS = [
    ("CRL", 0),
    ("BRL", 0),
    ("TRL", 4),
    ("IPRL", 5),
    ("TmRL", 6),
    ("FRL", 5),
]

CRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Hipótesis especulativa sobre una posible necesidad en el mercado.",
        "preguntas": [
            "¿Tiene alguna hipótesis sobre un problema o necesidad que podría existir en el mercado?",
            "¿Ha identificado quiénes podrían ser sus posibles clientes, aunque sea de manera especulativa?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Familiarización inicial con el mercado y necesidades más específicas detectadas.",
        "preguntas": [
            "¿Ha realizado alguna investigación secundaria o revisión de mercado para entender problemas del cliente?",
            "¿Tiene una descripción más clara y específica de las necesidades o problemas detectados?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Primer feedback de mercado y validación preliminar de necesidades.",
        "preguntas": [
            "¿Ha iniciado contactos directos con posibles usuarios o expertos del mercado para obtener retroalimentación?",
            "¿Ha comenzado a desarrollar una hipótesis más clara sobre los segmentos de clientes y sus problemas?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Confirmación del problema con varios usuarios y segmentación inicial.",
        "preguntas": [
            "¿Ha confirmado el problema o necesidad con varios clientes o usuarios reales?",
            "¿Ha definido una hipótesis de producto basada en el feedback recibido de los usuarios?",
            "¿Tiene segmentación inicial de clientes en función del problema identificado?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "Interés establecido por parte de usuarios y comprensión más profunda del mercado.",
        "preguntas": [
            "¿Cuenta con evidencia de interés concreto por parte de clientes o usuarios hacia su solución?",
            "¿Ha establecido relaciones con potenciales clientes o aliados que retroalimentan su propuesta de valor?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "Beneficios de la solución confirmados a través de pruebas o asociaciones iniciales.",
        "preguntas": [
            "¿Ha realizado pruebas del producto o solución con clientes que validen sus beneficios?",
            "¿Ha iniciado procesos de venta o pilotos con clientes reales o aliados estratégicos?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "Clientes involucrados en pruebas extendidas o primeras ventas/test comerciales.",
        "preguntas": [
            "¿Tiene acuerdos o primeras ventas del producto (aunque sea versión de prueba)?",
            "¿Los clientes han participado activamente en validaciones o pruebas extendidas del producto?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Ventas iniciales y preparación para ventas estructuradas y escalables.",
        "preguntas": [
            "¿Ha vendido sus primeros productos y validado la disposición de pago de un porcentaje relevante de clientes?",
            "¿Cuenta con una organización comercial mínima (CRM, procesos de venta, canales definidos)?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "Adopción consolidada y ventas repetibles a múltiples clientes reales.",
        "preguntas": [
            "¿Está realizando ventas escalables y repetibles con múltiples clientes?",
            "¿Su empresa está enfocada en ejecutar un proceso de crecimiento comercial con foco en la demanda de clientes?",
        ],
    },
]

FRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Idea de negocios inicial con una descripción vaga. No hay una visión clara sobre las necesidades y las opciones de financiamiento.",
        "preguntas": [
            "¿Tiene una idea de negocio inicial con una descripción?",
            "¿Tiene poco o ningún conocimiento de las actividades y costos relevantes para verificar el potencial/factibilidad de la idea?",
            "¿Tiene poco conocimiento de las diferentes opciones y tipos de financiamiento?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Descripción del concepto de negocios. Están definidas las necesidades y opciones de financiamiento para los hitos iniciales",
        "preguntas": [
            "¿Ha descrito las actividades iniciales y costos que permiten verificar el potencial/factibilidad de la idea (1-6 meses)?",
            "¿Tiene un plan básico con opciones de financiamiento para los hitos iniciales (1-6 meses)?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Concepto de negocios bien descrito, con un plan de verificación inicial. Primer pequeño financiamiento “blando” (soft funding) asegurado",
        "preguntas": [
            "¿Tiene financiamiento suficiente para asegurar la ejecución de las actividades iniciales de verificación/factibilidad (1-6 meses)?",
            "¿Conoce los diferentes tipos de financiamiento (propio, blando, de capital, de clientes, etc.) y las ventajas y desventajas de cada uno?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Se cuenta con un buen pitch y breve presentación del negocio. Se cuenta con un plan con diferentes opciones de financiamiento a lo largo del tiempo.",
        "preguntas": [
            "¿Tiene un buen pitch y una breve presentación del negocio?",
            "¿Ha preparado un plan de financiamiento para verificar el potencial comercial de la idea para los siguientes 3 a 12 meses?",
            "¿Ha identificado las fuentes de financiamiento relevantes?",
            "¿Ha obtenido fondos suficientes para implementar una parte sustancial del plan de verificación?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "Se cuenta con una presentación orientada al inversionista y material de apoyo que ha sido testeado. Se ha solicitado y obtenido un mayor financiamiento adicional (blandos u otros).",
        "preguntas": [
            "¿Ha elaborado y ensayado el pitch para obtener financiamiento en un ambiente relevante?",
            "¿Tiene una hoja de cálculo con el presupuesto inicial de ganancias y pérdidas y el flujo de caja para los próximos 12 meses?",
            "¿Ha decidido cómo abordar la estrategia de financiamiento y las fuentes de financiamiento para alcanzar un modelo de negocio viable?",
            "¿Conoce y entiende los requisitos y las consecuencias del financiamiento externo sobre el modelo de negocio, el control y la propiedad de la compañía?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "Presentación mejorada para el inversionista, la que incluye aspectos de negocios y financieros. Se ha decidido buscar inversores privados y se tomaron los primeros contactos.",
        "preguntas": [
            "¿Ha mejorado/actualizado el pitch para obtener financiamiento en una audiencia relevante?",
            "¿Tiene un presupuesto de ingresos y pérdidas y flujo de efectivo para negocios/proyectos a 3-5 años que permite esclarecer la necesidad de financiamiento a corto y mediano plazo?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "El equipo presenta un caso de inversión sólido, el que incluye estados y planes. Existen conversaciones con inversionistas potenciales sobre una oferta",
        "preguntas": [
            "¿Tiene conversaciones con posibles fuentes de financiamiento externas en torno a una oferta definida (cuánto dinero, para qué, condiciones, valoración, etc.)?",
            "¿La propuesta de financiamiento está completa, probada y comprobada, y existe un plan de negocios con proyecciones financieras y un plan de hitos?",
            "¿Existen sistemas básicos de contabilidad y documentación para el seguimiento financiero?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Existe un orden y una estructura corporativa que permiten la inversión. Existen diálogos sobre los términos del acuerdo con los inversionistas interesados.",
        "preguntas": [
            "¿Ha tenido conversaciones concretas (a nivel de Hoja de Términos) con una o varias fuentes de financiamiento externas interesadas?",
            "¿Está preparado y disponible todo el material necesario para el financiamiento externo (finanzas, plan de negocio, etc.)?",
            "¿Existe una entidad jurídica correctamente establecida con una estructura de propiedad adecuada para la fuente de financiamiento visualizada?",
            "¿Se ha recopilado y está disponible toda la documentación y acuerdos legales clave para una diligencia/revisión externa?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "La inversión fue obtenida. Las necesidades y las opciones de inversión adicionales son consideradas continuamente",
        "preguntas": [
            "¿Tiene financiamiento garantizado por al menos 6 a 12 meses de ejecución de acuerdo con el plan comercial/plan operativo actual?",
            "¿Está totalmente implementado un sistema de seguimiento financiero y contable para el control continuo del estado financiero actual?",
            "¿Existe un buen pronóstico/previsión para identificar las futuras necesidades de financiamiento?",
        ],
    },
]

TRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Principios básicos observados.",
        "preguntas": [
            "¿Ha identificado beneficios potenciales o aplicaciones útiles en los resultados de su investigación?",
            "¿Tiene una idea vaga de la tecnología a desarrollar?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Concepto y/o aplicación tecnológica formulada.",
        "preguntas": [
            "¿Cuenta con un concepto de tecnología potencial, definido y descrito en su primera versión?",
            "¿Se pueden definir o investigar aplicaciones prácticas para esta tecnologia?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Prueba de concepto analítica y experimental de funciones y/o características críticas.",
        "preguntas": [
            "¿Ha realizado pruebas analíticas y/o experimentales de funciones o características críticas en entorno de laboratorio?",
            "¿Ha iniciado una I+D activa para desarrollar aún más la tecnología?",
            "¿Tiene una primera idea de los requisitos o especificaciones del usuario final y/o casos de uso?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Validación de la tecnología en el laboratorio.",
        "preguntas": [
            "¿Ha integrado y demostrado el funcionamiento conjunto de los componentes básicos en un entorno de laboratorio?",
            "¿Los resultados de las pruebas brindan evidencia inicial que indica que el concepto de tecnología funcionará?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "Validación de tecnología en un entorno relevante.",
        "preguntas": [
            "¿Ha integrado y probado los componentes básicos de la tecnología en un entorno relevante?",
            "¿Los resultados de las pruebas brindan evidencia de que la tecnología funcionará, con validación técnica?",
            "¿Ha definido los requisitos o especificaciones del usuario final y/o casos de uso, basados en comentarios de los usuarios?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "Demostración del prototipo en un entorno relevante.",
        "preguntas": [
            "¿Ha demostrado que el modelo o prototipo representativo de la tecnología funciona realmente en un entorno relevante?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "Sistema/prototipo completo demostrado en ambiente operacional.",
        "preguntas": [
            "¿Ha demostrado que el prototipo o la tecnología completa funciona realmente en un entorno operativo?",
            "¿Ha establecido los requisitos completos del usuario final/especificaciones y/o casos de uso?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Sistema tecnológico real completado y calificado mediante pruebas y demostraciones.",
        "preguntas": [
            "¿Cuenta con una tecnología completa que contiene todo lo necesario para que el usuario la utilice?",
            "¿Cuenta con una tecnología funcional que resuelve el problema o necesidad del usuario?",
            "¿Es la tecnología compatible con personas, procesos, objetivos, infraestructura, sistemas, etc., del usuario?",
            "¿Han demostrado los primeros usuarios que la tecnología completa funciona en operaciones reales?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "Sistema tecnológico probado con éxito en entorno operativo real.",
        "preguntas": [
            "¿Es la tecnología completa escalable y ha sido comprobada en operaciones reales por varios usuarios a lo largo del tiempo?",
            "¿Está en curso el desarrollo continuo, la mejora, la optimización de la tecnología y la producción?",
        ],
    },
]


IPRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Se cuenta con una hipótesis sobre posibles derechos de propiedad intelectual que se podrían obtener (como patentes, software, derechos de autor, diseños, secretos comerciales, etc).",
        "preguntas": [
            "¿Tiene una hipótesis sobre posibles derechos de propiedad intelectual que se podrían obtener (como patentes, software, derechos de autor, diseños, secretos comerciales, etc.)?",
            "¿Tiene descripción y documentación de los posibles derechos de propiedad intelectual?",
            "¿Tiene claridad sobre aspectos legales relevantes o pertinentes (propiedad, derechos de uso, etc.)?",
            "¿Tiene conocimiento de los elementos únicos del invento y el campo técnico, estado del arte, publicaciones, etc.?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Identificación de las diferentes formas de posibles derechos de propiedad intelectual que podrían tener. La propiedad de los derechos es clara y no hay dudas de ser el dueño de los derechos de PI",
        "preguntas": [
            "¿Ha mapeado las diferentes formas de derechos de propiedad intelectual que existen o podrían surgir durante el desarrollo?",
            "¿Tiene ideas específicas sobre los derechos de propiedad intelectual, aunque no estén bien descritas ni definidas?",
            "¿Ha identificado acuerdos relacionados con la propiedad intelectual y aclarado la propiedad?",
            "¿Ha identificado a los inventores/creadores y tiene conocimiento de las políticas de PI aplicables y potenciales restricciones en los contratos?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Descripción detallada de los posibles derechos de propiedad intelectual claves (por ejemplo, invención o código).",
        "preguntas": [
            "¿Ha considerado qué formas de derechos de propiedad intelectual son claves o más importantes y podrían/deberían protegerse?",
            "¿Tiene una descripción suficientemente detallada de los posibles derechos de propiedad intelectual para evaluar la posibilidad de protección?",
            "¿Ha realizado una evaluación de las posibilidades de protección a través de búsquedas de publicaciones, estado del arte, soluciones de última generación, etc.?",
            "¿Ha realizado búsquedas o análisis iniciales del estado de la técnica pertinente o derechos de propiedad intelectual en conflicto con profesionales?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Confirmación sobre la viabilidad de la protección y mediante qué mecanismo. Decisión sobre el por qué de proteger determinados derechos de propiedad intelectual (relevancia para el negocio).",
        "preguntas": [
            "¿Ha confirmado la viabilidad de la protección de los derechos de propiedad intelectual claves a través de búsquedas/análisis por parte de un profesional?",
            "¿Ha analizado los derechos de propiedad intelectual claves y definido prioridades sobre qué proteger para crear valor para el negocio/proyecto?",
            "¿Ha presentado la primera solicitud/registro de derechos de propiedad intelectual en una forma menos elaborada (por ejemplo, patente provisional)?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "Borrador de estrategia de los derechos de propiedad intelectual para usar estos derechos con fines comerciales. Presentación de la primera solicitud de patente completa.",
        "preguntas": [
            "¿Tiene un borrador de estrategia de los derechos de propiedad intelectual definida, idealmente por un profesional, sobre cómo usar los derechos de PI para proteger y ser valiosos para el negocio?",
            "¿Ha presentado la primera solicitud/registro formal completo de derechos de propiedad intelectual claves en cooperación con un profesional?",
            "¿Tiene acuerdos básicos vigentes para determinar el control de los derechos de propiedad intelectual claves (por ejemplo, asignaciones, propiedad, etc.)?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "La estrategia de protección se encuentra implementada y apoya el negocio. Respuesta positiva en solicitudes presentadas. Evaluación inicial de la libertad para operar.",
        "preguntas": [
            "¿Ha elaborado una estrategia completa de protección de los derechos de propiedad intelectual que sustenta la estrategia de negocio?",
            "¿Ha identificado posibles derechos de propiedad intelectual complementarios/adicionales a proteger?",
            "¿Ha realizado una evaluación inicial de la libertad para operar (freedom to operate) para comprender el panorama de los derechos de PI en el campo?",
            "¿Ha recibido respuesta positiva a las solicitudes de derechos de PI por parte de las autoridades?",
            "Si no ha recibido respuesta positiva, ¿ha realizado un análisis junto con profesionales con buenas perspectivas?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "Todos los derechos de propiedad intelectual claves han sido solicitados en los paises o regiones relevantes de acuerdo con la estrategia de derechos de propiedad intelectual",
        "preguntas": [
            "¿Ha solicitado todos los derechos de propiedad intelectual claves en los países o regiones relevantes de acuerdo con la estrategia de PI?",
            "¿Ha realizado una evaluación más completa de la libertad para operar y tiene una comprensión clara de la dependencia/restricción de otros derechos de PI existentes?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Estrategia de protección y gestión de la propiedad intelectual completamente implementada. Evaluación más completa de la libertad de operar",
        "preguntas": [
            "¿Tiene una estrategia de protección y gestión de la propiedad intelectual completamente implementada?",
            "¿Ha sido otorgado los derechos de propiedad intelectual clave en el primer país/región con alcance relevante para el negocio?",
            "¿Ha presentado solicitud(es)/registro(s) de derechos de PI complementarios o adicionales?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "Sólido sustento y protección de derechos de propiedad intelectual para el negocio. Patente concedida y vigente en países relevantes",
        "preguntas": [
            "¿La estrategia de derechos de propiedad intelectual respalda y crea valor para el negocio?",
            "¿Se han otorgado y se mantienen los derechos de propiedad intelectual claves y complementarios en varios países relevantes para los negocios?",
            "¿Tiene acuerdos vigentes para acceder a todos los derechos de propiedad intelectual externos necesarios?",
        ],
    },
]

TMRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Poca comprensión de la necesidad de un equipo (generalmente un individuo). Falta de competencias y/o recursos necesarios.",
        "preguntas": [
            "¿El equipo está conformado por más de una persona que posee las competencias necesarias en áreas claves como tecnología y negocios?",
            "¿Tiene algo de conocimiento sobre las competencias y otros recursos necesarios (socios, proveedores de servicios, etc.) para verificar y desarrollar la idea?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Conocimiento y primera idea sobre las competencias necesarias o los recursos externos (por ejemplo, socios) requeridos",
        "preguntas": [
            "¿Tiene una primera idea de qué personas/competencias adicionales podrían ser necesarias para verificar/desarrollar la idea?",
            "¿Tiene una primera idea del objetivo general del proyecto?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Algunas de las competencias o recursos necesarios están presentes. Existen otras competencias o recursos que se necesitan y deben definirse (junto a un plan de búsqueda).",
        "preguntas": [
            "¿Existen personas en el equipo con algunas, pero no todas, las competencias necesarias para comenzar a verificar la idea?",
            "¿Ha identificado necesidades y brechas en competencias, capacidades y diversidad de equipos?",
            "¿Tiene un plan inicial sobre cómo encontrar las competencias necesarias a corto plazo (<1 año)?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Un champion está presente. Varias de las competencias necesarias están presentes. Se inicia un plan para reclutar o asegurar recursos claves adicionales.",
        "preguntas": [
            "¿Hay un champion (impulsor y comprometido) en el equipo?",
            "¿El equipo tiene varias, pero no todas, las competencias necesarias, generalmente en múltiples individuos?",
            "¿Ha iniciado un plan para encontrar competencias y capacidades adicionales necesarias, teniendo en cuenta la diversidad del equipo?",
            "¿El equipo ha iniciado discusiones sobre roles, compromiso, propiedad, etc., para avanzar en el proyecto?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "El equipo fundador inicial ya posee las principales competencias necesarias. El equipo acuerda la propiedad y los roles, y tiene objetivos alineados",
        "preguntas": [
            "¿Existe un equipo fundador inicial trabajando juntos y dedicando un tiempo significativo al proyecto?",
            "¿El equipo fundador tiene en conjunto las principales competencias y capacidades necesarias para comenzar a construir la startup?",
            "¿El equipo está alineado con roles claros, metas y visiones compartidas y un claro compromiso con el proyecto?",
            "¿El equipo ha acordado sus respectivas participaciones accionarias con un acuerdo firmado?",
            "¿Se han iniciado actividades para obtener competencias y capacidades adicionales, teniendo en cuenta la diversidad del equipo?",
            "¿Se han implementado sistemas/procesos/herramientas iniciales para compartir conocimientos e información dentro del equipo?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "Existe un equipo complementario, diverso y comprometido, con todas las competencias y recursos necesarios, tanto en el ámbito de los negocios como el tecnológico.",
        "preguntas": [
            "¿Existe un equipo fundador complementario y diverso, capaz de comenzar a construir un negocio?",
            "¿Se cuenta con todas las competencias clave y la capacidad necesaria para el corto plazo, con claridad sobre quién es el director ejecutivo?",
            "¿El equipo está comprometido, todos sienten responsabilidad y están preparados para asumir responsabilidades?",
            "¿Ha iniciado la contratación de asesores y/o miembros del directorio, teniendo en cuenta la diversidad del directorio?",
            "¿Existe conciencia de los riesgos que pueden afectar el desempeño del equipo (conflictos, burnout/salud mental, política, etc.)?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "El equipo y la cultura de la empresa están plenamente establecidos y desarrollados de forma proactiva. Hay un plan visualizado para formar el equipo que se necesita a largo plazo",
        "preguntas": [
            "¿El equipo funciona bien con roles claros?",
            "¿Los objetivos, la visión, el propósito y la cultura están claramente articuladas y documentadas para apoyar al equipo y el desarrollo organizacional?",
            "¿Está en marcha un plan para desarrollar la organización y hacer crecer el equipo a largo plazo (~2 años)?",
            "¿Se han implementado procesos/sistemas y un plan de aprendizaje continuo para el desarrollo del personal?",
            "¿El Directorio y los asesores están en funcionamiento y apoyan al desarrollo empresarial y organizacional?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Se cuenta con un CEO y equipo ejecutivo. Uso profesional del Directorio y de asesores. Se han activado planes y reclutamiento para la construcción de equipo a largo plazo.",
        "preguntas": [
            "¿Existe un liderazgo claro y un equipo de gestión con experiencia profesional relevante?",
            "¿Se cuenta con un Directorio competente y diverso, y asesores relevantes utilizados profesionalmente?",
            "¿Se han implementado políticas y procesos para asegurar buenas prácticas de recursos humanos y diversidad del equipo?",
            "¿Se están realizando contrataciones necesarias de acuerdo con el plan a largo plazo para determinar las competencias, capacidad y diversidad relevantes?",
            "¿Todos los niveles de la organización están debidamente capacitados y motivados?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "El equipo y la organización son de alto rendimiento y están correctamente estructurados. Ambos se mantienen y se desarrollan correctamente a lo largo del tiempo",
        "preguntas": [
            "¿La organización tiene un alto rendimiento y buen funcionamiento (cooperación, entorno social, etc.)?",
            "¿Todos los niveles de la organización participan activamente en el aprendizaje y el desarrollo continuo?",
            "¿La cultura organizacional, la estructura y los procesos se mejoran y desarrollan continuamente?",
            "¿Los incentivos/recompensas están alineados para motivar a toda la organización para alcanzar las metas y desempeñarse bien?",
            "¿El equipo directivo se mantiene, se desarrolla y se desempeña en el tiempo?",
        ],
    },
]

BRL_LEVELS = [
    {
        "nivel": 1,
        "descripcion": "Hipótesis preliminar sobre el concepto de negocio con información limitada del mercado.",
        "preguntas": [
            "¿Tiene una hipótesis preliminar del concepto de negocio?",
            "¿Cuenta con alguna información sobre el mercado y su potencial o tamaño?",
            "¿Tiene algún conocimiento o percepción de la competencia y soluciones alternativas?",
        ],
    },
    {
        "nivel": 2,
        "descripcion": "Descripción inicial estructurada del concepto de negocio y reconocimiento general del mercado.",
        "preguntas": [
            "¿Ha propuesto una descripción estructurada del concepto de negocio y la propuesta de valor?",
            "¿Se ha familiarizado brevemente con el tamaño del mercado, los segmentos y el panorama competitivo?",
            "¿Ha enumerado algunos competidores o alternativas?",
        ],
    },
    {
        "nivel": 3,
        "descripcion": "Borrador de modelo de negocios que caracteriza el mercado potencial y el panorama competitivo.",
        "preguntas": [
            "¿Ha generado un borrador del modelo de negocios (Canvas)?",
            "¿Ha descrito factores relevantes en el modelo de negocio que afectan al medio ambiente y la sociedad?",
            "¿Ha definido el mercado objetivo y estimado su tamaño (TAM, SAM)?",
            "¿Ha identificado y descrito la competencia y el panorama competitivo?",
        ],
    },
    {
        "nivel": 4,
        "descripcion": "Modelo de negocios completo inicial con primeras proyecciones de viabilidad económica.",
        "preguntas": [
            "¿Ha determinado la viabilidad económica a partir de las primeras proyecciones de pérdidas y ganancias?",
            "¿Ha realizado una evaluación inicial de la sostenibilidad ambiental y social?",
        ],
    },
    {
        "nivel": 5,
        "descripcion": "Modelo de negocios ajustado tras feedback de mercado y primeras hipótesis de ingresos.",
        "preguntas": [
            "¿Ha recibido feedback sobre los ingresos del modelo comercial de clientes potenciales o expertos?",
            "¿Ha recibido feedback sobre los costos del modelo comercial de socios, proveedores o expertos externos?",
            "¿Ha identificado medidas para aumentar las contribuciones ambientales y sociales positivas y disminuir las negativas?",
            "¿Ha actualizado la proyección de ganancias y pérdidas en función del feedback del mercado?",
            "¿Ha actualizado la descripción del mercado objetivo y el análisis competitivo basado en comentarios del mercado?",
        ],
    },
    {
        "nivel": 6,
        "descripcion": "Modelo de negocios sostenible validado mediante escenarios comerciales realistas.",
        "preguntas": [
            "¿Tiene un modelo de negocio sostenible probado en escenarios comerciales realistas (ventas de prueba, pedidos anticipados, pilotos, etc.)?",
            "¿Tiene proyecciones financieras completas basadas en comentarios de casos comerciales realistas?",
        ],
    },
    {
        "nivel": 7,
        "descripcion": "Product/market fit inicial con disposición de pago demostrada y proyecciones validadas.",
        "preguntas": [
            "¿Las primeras ventas/ingresos en términos comerciales demuestran la disposición a pagar de un número significativo de clientes?",
            "¿Existen proyecciones financieras completas validadas por primeras ventas/ingresos y datos?",
            "¿Tiene acuerdos vigentes con proveedores clave, socios y socios de canal alineados con sus expectativas de sostenibilidad?",
        ],
    },
    {
        "nivel": 8,
        "descripcion": "Modelo de negocios sostenible que demuestra capacidad de escalar con métricas operativas.",
        "preguntas": [
            "¿Las ventas y otras métricas de las operaciones comerciales iniciales muestran que el modelo de negocio sostenible se mantiene y puede escalar?",
            "¿Están establecidos y operativos los canales de venta y la cadena de suministro alineados con sus expectativas de sostenibilidad?",
            "¿El modelo comercial se ajusta para mejorar los ingresos/costos y aprovechar la sostenibilidad?",
        ],
    },
    {
        "nivel": 9,
        "descripcion": "Modelo de negocios definitivo y sostenible con ingresos recurrentes y métricas consolidadas.",
        "preguntas": [
            "¿El modelo de negocio es sostenible y operativo, y el negocio cumple o supera las expectativas internas y externas en cuanto a beneficios, crecimiento, escalabilidad e impacto ambiental y social?",
            "¿Utiliza sistemas y métricas creíbles para rastrear el desempeño económico, ambiental y social?",
            "¿Los datos históricos sobre el desempeño económico, ambiental y social prueban un negocio viable, rentable y sostenible en el tiempo?",
        ],
    },
]

STEP_TABS = [dimension for dimension, _ in IRL_DIMENSIONS]
LEVEL_DEFINITIONS = {
    "CRL": CRL_LEVELS,
    "BRL": BRL_LEVELS,
    "TRL": TRL_LEVELS,
    "IPRL": IPRL_LEVELS,
    "TmRL": TMRL_LEVELS,
    "FRL": FRL_LEVELS,
}

STEP_CONFIG = {
    "min_evidence_chars": 40,
    "soft_char_limit": 400,
    "max_char_limit": 600,
    "evidence_obligatoria_strict": False,
    "secuencia_flexible": True,
}

_STATE_KEY = "irl_stepper_state"
_ERROR_KEY = "irl_stepper_errors"
_BANNER_KEY = "irl_stepper_banner"
_CLOSE_EXPANDER_KEY = "irl_close_expander"
_READY_KEY = "irl_level_ready"
_EDIT_MODE_KEY = "irl_level_edit_mode"
_AUTO_SAVE_KEY = "irl_auto_save"
_QUESTION_PROGRESS_KEY = "irl_question_progress"
_RESTORE_ON_EDIT_KEY = "irl_restore_on_edit"
_PENDING_RESTORE_QUEUE_KEY = "irl_pending_restore_queue"

_STATUS_CLASS_MAP = {
    "Pendiente": "pending",
    "Respondido (en cálculo)": "complete",
    "Fuera de cálculo": "attention",
    "Revisión requerida": "review",
}

IRL_IMPORTANT_HTML = """
<div class="irl-important">
  <strong>Importante:</strong> Este formulario es una herramienta de auto-diagnóstico para identificar el estado actual de la EBCT respecto a: desarrollo tecnológico, estrategia de negocios, propiedad intelectual, madurez del equipo, estrategia de financiamiento y el valor generado para clientes o usuarios. Evalúa una sola tecnología por formulario. Para un seguimiento dinámico y recomendaciones detalladas, visita la plataforma <a href="https://www.calculadorarl.cl" target="_blank">Calculadora RL</a>.
  <br><span class="irl-important__hint">La calculadora solo considera alcanzado un nivel cuando <em>todas</em> las respuestas son VERDADERAS de manera consecutiva desde el primer nivel.</span>
</div>
"""


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _is_evidence_valid(texto: str | None) -> bool:
    texto_limpio = _clean_text(texto)
    return bool(texto_limpio)


def _missing_required_evidences(
    level: dict,
    respuestas: dict[str, str | None] | None,
    evidencias: dict[str, str] | None,
) -> list[int]:
    if respuestas is None:
        return []
    preguntas = level.get("preguntas") or []
    evidencias = evidencias or {}
    faltantes: list[int] = []
    for idx, _ in enumerate(preguntas, start=1):
        clave = str(idx)
        if respuestas.get(clave) == "VERDADERO" and not _is_evidence_valid(evidencias.get(clave)):
            faltantes.append(idx)
    return faltantes


def _question_is_complete(answer: str | None, evidence: str | None) -> bool:
    if answer not in {"VERDADERO", "FALSO"}:
        return False
    if answer == "VERDADERO":
        return _is_evidence_valid(evidence)
    return True


def _ensure_question_progress(
    dimension: str,
    level_id: int,
    total_questions: int,
) -> dict:
    if _QUESTION_PROGRESS_KEY not in st.session_state:
        st.session_state[_QUESTION_PROGRESS_KEY] = {dimension: {} for dimension in STEP_TABS}
    if dimension not in st.session_state[_QUESTION_PROGRESS_KEY]:
        st.session_state[_QUESTION_PROGRESS_KEY][dimension] = {}
    progress = st.session_state[_QUESTION_PROGRESS_KEY][dimension].get(level_id)
    if not isinstance(progress, dict):
        progress = {}
    saved_map = progress.get("saved")
    if not isinstance(saved_map, dict):
        saved_map = {}
    valid_keys = {str(idx) for idx in range(1, total_questions + 1)}
    for key in list(saved_map.keys()):
        if key not in valid_keys:
            saved_map.pop(key, None)
    for idx in range(1, total_questions + 1):
        saved_map.setdefault(str(idx), False)
    progress["saved"] = saved_map
    active = progress.get("active", 0)
    if active < 0 or active >= total_questions:
        active = 0
    progress["active"] = active
    st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress
    return progress


def _mark_question_pending(dimension: str, level_id: int, idx: int, total_questions: int) -> None:
    progress = _ensure_question_progress(dimension, level_id, total_questions)
    clave = str(idx)
    progress["saved"][clave] = False
    st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress
    error_key = f"question_error_{dimension}_{level_id}"
    if error_key in st.session_state:
        st.session_state[error_key] = None


def _mark_question_saved(dimension: str, level_id: int, idx: int, total_questions: int) -> None:
    progress = _ensure_question_progress(dimension, level_id, total_questions)
    clave = str(idx)
    progress["saved"][clave] = True
    st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress
    error_key = f"question_error_{dimension}_{level_id}"
    if error_key in st.session_state:
        st.session_state[error_key] = None


def _set_active_question(dimension: str, level_id: int, idx: int, total_questions: int) -> None:
    progress = _ensure_question_progress(dimension, level_id, total_questions)
    if total_questions <= 0:
        progress["active"] = 0
    else:
        progress["active"] = max(0, min(idx, total_questions - 1))
    st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress


def _init_irl_state() -> None:
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = {}

    if _RESTORE_ON_EDIT_KEY not in st.session_state:
        st.session_state[_RESTORE_ON_EDIT_KEY] = {}

    for dimension in STEP_TABS:
        if dimension not in st.session_state[_STATE_KEY]:
            st.session_state[_STATE_KEY][dimension] = {}

        if dimension not in st.session_state[_RESTORE_ON_EDIT_KEY]:
            st.session_state[_RESTORE_ON_EDIT_KEY][dimension] = {}

        for level in LEVEL_DEFINITIONS.get(dimension, []):
            if level["nivel"] not in st.session_state[_STATE_KEY][dimension]:
                st.session_state[_STATE_KEY][dimension][level["nivel"]] = {
                    "respuesta": "FALSO",
                    "respuestas_preguntas": {},
                    "evidencia": "",
                    "evidencias_preguntas": {},
                    "estado": "Pendiente",
                    "estado_auto": "Pendiente",
                    "en_calculo": False,
                    "marcado_revision": False,
                }
    for dimension in STEP_TABS:
        for level in LEVEL_DEFINITIONS.get(dimension, []):
            state = st.session_state[_STATE_KEY][dimension][level["nivel"]]
            preguntas = level.get("preguntas") or []
            existentes = state.get("respuestas_preguntas")
            if not isinstance(existentes, dict):
                existentes = {}
            normalizado: dict[str, str | None] = {}
            for idx, _ in enumerate(preguntas, start=1):
                clave = str(idx)
                valor = existentes.get(clave)
                normalizado[clave] = valor if valor in {"VERDADERO", "FALSO"} else "FALSO"
            state["respuestas_preguntas"] = normalizado
            evidencias_existentes = state.get("evidencias_preguntas")
            if not isinstance(evidencias_existentes, dict):
                evidencias_existentes = {}
            normalizado_evidencias: dict[str, str] = {}
            for idx, _ in enumerate(preguntas, start=1):
                clave = str(idx)
                valor = evidencias_existentes.get(clave)
                normalizado_evidencias[clave] = str(valor) if valor is not None else ""
            state["evidencias_preguntas"] = normalizado_evidencias
            st.session_state[_STATE_KEY][dimension][level["nivel"]] = state
    if _READY_KEY not in st.session_state:
        st.session_state[_READY_KEY] = {dimension: {} for dimension in STEP_TABS}
    for dimension in STEP_TABS:
        for level in LEVEL_DEFINITIONS.get(dimension, []):
            preguntas = level.get("preguntas") or []
            level_state = st.session_state[_STATE_KEY][dimension][level["nivel"]]
            if preguntas:
                listo = all(
                    level_state.get("respuestas_preguntas", {}).get(str(idx)) in {"VERDADERO", "FALSO"}
                    for idx in range(1, len(preguntas) + 1)
                )
            else:
                listo = level_state.get("respuesta") in {"VERDADERO", "FALSO"}
            st.session_state[_READY_KEY][dimension][level["nivel"]] = listo
    if _EDIT_MODE_KEY not in st.session_state:
        st.session_state[_EDIT_MODE_KEY] = {}
    for dimension in STEP_TABS:
        if dimension not in st.session_state[_EDIT_MODE_KEY]:
            st.session_state[_EDIT_MODE_KEY][dimension] = {}
        for level in LEVEL_DEFINITIONS.get(dimension, []):
            level_id = level["nivel"]
            if level_id not in st.session_state[_EDIT_MODE_KEY][dimension]:
                en_calculo = bool(
                    st.session_state[_STATE_KEY][dimension][level_id].get("en_calculo", False)
                )
                st.session_state[_EDIT_MODE_KEY][dimension][level_id] = not en_calculo
    if _QUESTION_PROGRESS_KEY not in st.session_state:
        st.session_state[_QUESTION_PROGRESS_KEY] = {dimension: {} for dimension in STEP_TABS}
    for dimension in STEP_TABS:
        if dimension not in st.session_state[_QUESTION_PROGRESS_KEY]:
            st.session_state[_QUESTION_PROGRESS_KEY][dimension] = {}
        for level in LEVEL_DEFINITIONS.get(dimension, []):
            level_id = level["nivel"]
            preguntas = level.get("preguntas") or []
            total_questions = len(preguntas)
            if not total_questions:
                st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = {
                    "active": 0,
                    "saved": {},
                }
                continue
            progress = _ensure_question_progress(dimension, level_id, total_questions)
            level_state = st.session_state[_STATE_KEY][dimension][level_id]
            for idx in range(1, total_questions + 1):
                clave = str(idx)
                respuesta = level_state.get("respuestas_preguntas", {}).get(clave)
                evidencia = level_state.get("evidencias_preguntas", {}).get(clave)
                is_complete = _question_is_complete(respuesta, evidencia)
                progress["saved"][clave] = is_complete
            selector_key = f"selector_{dimension}_{level_id}"
            default_active = 0
            existing_selector = st.session_state.get(selector_key)
            if isinstance(existing_selector, int) and 0 <= existing_selector < total_questions:
                progress["active"] = existing_selector
            else:
                progress["active"] = default_active
                st.session_state[selector_key] = default_active
            st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress
    if _ERROR_KEY not in st.session_state:
        st.session_state[_ERROR_KEY] = {dimension: {} for dimension in STEP_TABS}
    if _BANNER_KEY not in st.session_state:
        st.session_state[_BANNER_KEY] = {dimension: None for dimension in STEP_TABS}
    if _CLOSE_EXPANDER_KEY not in st.session_state:
        st.session_state[_CLOSE_EXPANDER_KEY] = None
    if _AUTO_SAVE_KEY not in st.session_state:
        st.session_state[_AUTO_SAVE_KEY] = None
    if "irl_scores" not in st.session_state:
        st.session_state["irl_scores"] = {dimension: default for dimension, default in IRL_DIMENSIONS}


def _level_state(dimension: str, level_id: int) -> dict:
    return st.session_state[_STATE_KEY][dimension][level_id]


def _update_ready_flag(dimension: str, level_id: int) -> None:
    _init_irl_state()
    niveles = LEVEL_DEFINITIONS.get(dimension, [])
    level_data = next((lvl for lvl in niveles if lvl.get("nivel") == level_id), None)
    if not level_data:
        return
    preguntas = level_data.get("preguntas") or []
    if preguntas:
        listo = True
        for idx in range(1, len(preguntas) + 1):
            pregunta_key = f"resp_{dimension}_{level_id}_{idx}"
            valor = st.session_state.get(pregunta_key)
            if valor not in {"VERDADERO", "FALSO"}:
                listo = False
                break
        if listo:
            for idx in range(1, len(preguntas) + 1):
                pregunta_key = f"resp_{dimension}_{level_id}_{idx}"
                evidencia_key = f"evid_{dimension}_{level_id}_{idx}"
                if st.session_state.get(pregunta_key) == "VERDADERO" and not _is_evidence_valid(
                    st.session_state.get(evidencia_key)
                ):
                    listo = False
                    break
    else:
        answer_key = f"resp_{dimension}_{level_id}"
        valor = st.session_state.get(answer_key)
        listo = valor in {"VERDADERO", "FALSO"}
        if listo and valor == "VERDADERO":
            evidencia_key = f"evid_{dimension}_{level_id}"
            listo = _is_evidence_valid(st.session_state.get(evidencia_key))
    st.session_state[_READY_KEY][dimension][level_id] = listo


def _set_level_state(
    dimension: str,
    level_id: int,
    *,
    respuesta: str | None = None,
    respuestas_preguntas: dict[str, str | None] | None = None,
    evidencia: str | None = None,
    evidencias_preguntas: dict[str, str] | None = None,
    estado_auto: str | None = None,
    en_calculo: bool | None = None,
) -> None:
    state = _level_state(dimension, level_id)
    if respuesta is not None:
        state["respuesta"] = respuesta
    if respuestas_preguntas is not None:
        state["respuestas_preguntas"] = respuestas_preguntas
    if evidencia is not None:
        state["evidencia"] = evidencia
    if evidencias_preguntas is not None:
        state["evidencias_preguntas"] = evidencias_preguntas
    if estado_auto is not None:
        state["estado_auto"] = estado_auto
    if en_calculo is not None:
        state["en_calculo"] = en_calculo
        if _EDIT_MODE_KEY not in st.session_state:
            st.session_state[_EDIT_MODE_KEY] = {}
        if dimension not in st.session_state[_EDIT_MODE_KEY]:
            st.session_state[_EDIT_MODE_KEY][dimension] = {}
        st.session_state[_EDIT_MODE_KEY][dimension][level_id] = not en_calculo
    if state.get("marcado_revision"):
        state["estado"] = "Revisión requerida"
    else:
        state["estado"] = state.get("estado_auto", "Pendiente")
    st.session_state[_STATE_KEY][dimension][level_id] = state


def _set_revision_flag(dimension: str, level_id: int, value: bool) -> None:
    state = _level_state(dimension, level_id)
    state["marcado_revision"] = value
    if state["marcado_revision"]:
        state["estado"] = "Revisión requerida"
    else:
        state["estado"] = state.get("estado_auto", "Pendiente")
    st.session_state[_STATE_KEY][dimension][level_id] = state


def _toggle_revision(dimension: str, level_id: int) -> None:
    state = _level_state(dimension, level_id)
    nuevo_valor = not state.get("marcado_revision", False)
    _set_revision_flag(dimension, level_id, nuevo_valor)

def _restore_level_form_values(dimension: str, level_id: int) -> None:
    niveles = LEVEL_DEFINITIONS.get(dimension, [])
    level_data = next((lvl for lvl in niveles if lvl.get("nivel") == level_id), None)
    if not level_data:
        return
    state = _level_state(dimension, level_id)
    preguntas = level_data.get("preguntas") or []
    selector_key = f"selector_{dimension}_{level_id}"
    if preguntas:
        evidencias_estado = state.get("evidencias_preguntas") or {}
        aggregated: list[str] = []
        for idx, _ in enumerate(preguntas, start=1):
            clave = str(idx)
            pregunta_key = f"resp_{dimension}_{level_id}_{idx}"
            toggle_key = f"toggle_{dimension}_{level_id}_{idx}"
            evidencia_key = f"evid_{dimension}_{level_id}_{idx}"
            valor = state.get("respuestas_preguntas", {}).get(clave)
            st.session_state[pregunta_key] = valor if valor in {"VERDADERO", "FALSO"} else "FALSO"
            st.session_state[toggle_key] = st.session_state[pregunta_key] == "VERDADERO"
            evidencia_val = evidencias_estado.get(clave, "")
            evidencia_texto = "" if evidencia_val is None else str(evidencia_val)
            st.session_state[evidencia_key] = evidencia_texto
            if evidencia_texto:
                aggregated.append(evidencia_texto.strip())
        evidencia_join_key = f"evid_{dimension}_{level_id}"
        st.session_state[evidencia_join_key] = " \n".join(aggregated)
        total_questions = len(preguntas)
        progress = _ensure_question_progress(dimension, level_id, total_questions)
        for idx, _ in enumerate(preguntas, start=1):
            clave = str(idx)
            respuesta_guardada = state.get("respuestas_preguntas", {}).get(clave)
            evidencia_guardada = evidencias_estado.get(clave, "")
            completo = _question_is_complete(respuesta_guardada, evidencia_guardada)
            progress["saved"][clave] = completo
        progress["active"] = 0
        st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress
        st.session_state[selector_key] = 0
    else:
        answer_key = f"resp_{dimension}_{level_id}"
        evidencia_key = f"evid_{dimension}_{level_id}"
        valor = state.get("respuesta")
        st.session_state[answer_key] = valor if valor in {"VERDADERO", "FALSO"} else "FALSO"
        evidencia_val = state.get("evidencia", "")
        st.session_state[evidencia_key] = "" if evidencia_val is None else str(evidencia_val)
    if selector_key not in st.session_state:
        st.session_state[selector_key] = 0


def _enqueue_level_restore(dimension: str, level_id: int) -> None:
    queue = st.session_state.get(_PENDING_RESTORE_QUEUE_KEY)
    if not isinstance(queue, list):
        queue = []
    item = (dimension, level_id)
    if item not in queue:
        queue.append(item)
    st.session_state[_PENDING_RESTORE_QUEUE_KEY] = queue


def _process_pending_restores(dimension: str) -> None:
    queue = st.session_state.get(_PENDING_RESTORE_QUEUE_KEY)
    if not queue:
        return
    if not isinstance(queue, list):
        queue = [queue]
    remaining: list[tuple[str, int]] = []
    for pending_entry in queue:
        if (
            not isinstance(pending_entry, tuple)
            or len(pending_entry) != 2
            or not isinstance(pending_entry[0], str)
            or not isinstance(pending_entry[1], int)
        ):
            continue
        pending_dimension, pending_level = pending_entry
        if pending_dimension == dimension:
            _restore_level_form_values(pending_dimension, pending_level)
            _update_ready_flag(pending_dimension, pending_level)
        else:
            remaining.append((pending_dimension, pending_level))
    st.session_state[_PENDING_RESTORE_QUEUE_KEY] = remaining


def _sync_dimension_score(dimension: str) -> int:
    niveles = LEVEL_DEFINITIONS.get(dimension, [])
    if not niveles:
        st.session_state["irl_scores"][dimension] = 0
        return 0
    niveles_sorted = sorted(niveles, key=lambda lvl: lvl.get("nivel", 0))
    baseline = niveles_sorted[0].get("nivel", 0)
    highest = baseline - 1
    for level in niveles_sorted:
        nivel_actual = level.get("nivel", baseline)
        expected_next = highest + 1
        if nivel_actual != expected_next:
            break
        level_state = _level_state(dimension, nivel_actual)
        if level_state["respuesta"] == "VERDADERO" and level_state["en_calculo"]:
            highest = nivel_actual
        else:
            break
    approved_level = highest if highest >= baseline else 0
    st.session_state["irl_scores"][dimension] = approved_level
    return approved_level


def _sync_all_scores() -> None:
    for dimension in STEP_TABS:
        _sync_dimension_score(dimension)


def _compute_dimension_counts(dimension: str) -> dict:
    niveles = st.session_state[_STATE_KEY][dimension]
    total = len(niveles)
    completados = sum(1 for data in niveles.values() if data.get("en_calculo"))
    revision = sum(1 for data in niveles.values() if data.get("marcado_revision"))
    pendientes = max(total - completados, 0)
    return {
        "total": total,
        "completed": completados,
        "pending": pendientes,
        "revision": revision,
    }

def _dimension_badge_class(status: str) -> str:
    return {
        "Completa": "complete",
        "Parcial": "partial",
        "Pendiente": "pending",
    }.get(status, "pending")

def _dimension_badge(counts: dict) -> str:
    if counts["completed"] == counts["total"] and counts["revision"] == 0:
        return "Completa"
    if counts["completed"] or counts["revision"]:
        return "Parcial"
    return "Pendiente"


def _dimension_badge_class(status: str) -> str:
    return {
        "Completa": "complete",
        "Parcial": "partial",
        "Pendiente": "pending",
    }.get(status, "pending")


def _status_class(status: str) -> str:
    return _STATUS_CLASS_MAP.get(status, "pending")


def _normalize_question_responses(level: dict, respuestas: dict[str, str | None]) -> dict[str, str | None]:
    preguntas = level.get("preguntas") or []
    normalizado: dict[str, str | None] = {}
    for idx, _ in enumerate(preguntas, start=1):
        clave = str(idx)
        valor = respuestas.get(clave)
        normalizado[clave] = valor if valor in {"VERDADERO", "FALSO"} else None
    return normalizado


def _aggregate_question_status(respuestas: dict[str, str | None]) -> str | None:
    if not respuestas:
        return None
    valores = list(respuestas.values())
    if any(valor is None for valor in valores):
        return None
    if all(valor == "VERDADERO" for valor in valores):
        return "VERDADERO"
    return "FALSO"


def _handle_manual_answer_change(*, answer_key: str, evidencia_key: str) -> None:
    answer = st.session_state.get(answer_key)
    if answer != "VERDADERO":
        st.session_state[evidencia_key] = ""


def _handle_question_evidence_change(
    *,
    dimension: str,
    level_id: int,
    idx: int,
    total_questions: int,
) -> None:
    _mark_question_pending(dimension, level_id, idx, total_questions)


def _handle_question_toggle_change(
    *,
    dimension: str,
    level_id: int,
    idx: int,
    total_questions: int,
    pregunta_key: str,
    evidencia_key: str,
    toggle_key: str,
) -> None:
    marcado = bool(st.session_state.get(toggle_key))
    nuevo_valor = "VERDADERO" if marcado else "FALSO"
    st.session_state[pregunta_key] = nuevo_valor
    if nuevo_valor != "VERDADERO":
        st.session_state[evidencia_key] = ""
    _mark_question_pending(dimension, level_id, idx, total_questions)


def _persist_question_progress(
    dimension: str,
    level_id: int,
    idx: int,
    answer: str | None,
    evidence: str | None,
) -> None:
    level_state = _level_state(dimension, level_id)
    respuestas = dict(level_state.get("respuestas_preguntas") or {})
    evidencias = dict(level_state.get("evidencias_preguntas") or {})
    clave = str(idx)
    if answer in {"VERDADERO", "FALSO"}:
        respuestas[clave] = answer
    else:
        respuestas[clave] = None
    if answer == "VERDADERO":
        evidencias[clave] = _clean_text(evidence)
    else:
        evidencias[clave] = ""
    level_state["respuestas_preguntas"] = respuestas
    level_state["evidencias_preguntas"] = evidencias
    st.session_state[_STATE_KEY][dimension][level_id] = level_state


def _handle_level_submission(
    dimension: str,
    level_id: int,
    respuestas_preguntas: dict[str, str | None],
    evidencia: str,
    *,
    evidencias_preguntas: dict[str, str] | None = None,
    respuesta_manual: str | None = None,
) -> tuple[bool, str | None, str | None]:
    evidencia = evidencia.strip()
    niveles = LEVEL_DEFINITIONS.get(dimension, [])
    level_data = next((lvl for lvl in niveles if lvl.get("nivel") == level_id), {})
    preguntas = level_data.get("preguntas") or []
    normalizado = _normalize_question_responses(level_data, respuestas_preguntas or {})
    evidencias_normalizadas: dict[str, str] | None = None
    if preguntas and evidencias_preguntas is not None:
        evidencias_normalizadas = {}
        for idx, _ in enumerate(preguntas, start=1):
            clave = str(idx)
            evidencias_normalizadas[clave] = (evidencias_preguntas.get(clave, "") or "").strip()
        evidencia = " \n".join(
            texto for texto in evidencias_normalizadas.values() if texto
        ).strip()
    elif evidencias_preguntas is not None:
        evidencias_normalizadas = {k: str(v) for k, v in evidencias_preguntas.items()}

    # Primero validamos las respuestas y evidencias
    if preguntas:
        faltantes = _missing_required_evidences(level_data, normalizado, evidencias_normalizadas)
        if faltantes:
            mensaje = "Escribe los antecedentes de verificación para guardar como VERDADERO."
            return False, mensaje, None
        respuesta = _aggregate_question_status(normalizado) or "FALSO"
    else:
        if respuesta_manual not in {"VERDADERO", "FALSO"}:
            mensaje = "Selecciona VERDADERO o FALSO para continuar."
            return False, mensaje, None
        respuesta = respuesta_manual
        if respuesta == "VERDADERO" and not evidencia:
            mensaje = "Escribe los antecedentes de verificación para guardar como VERDADERO."
            return False, mensaje, None

    # Solo guardamos el estado cuando pasamos todas las validaciones y el usuario presiona "Guardar"
    _set_level_state(
        dimension,
        level_id,
        respuestas_preguntas=normalizado,
        evidencia=evidencia,
        evidencias_preguntas=evidencias_normalizadas,
        respuesta=respuesta,
        estado_auto="Respondido (en cálculo)",
        en_calculo=True
    )
    
    return True, None, None


def _render_level_question_flow(
    dimension: str,
    level_id: int,
    preguntas: list[str],
    descripcion: str,
    *,
    locked: bool,
) -> tuple[dict[str, str | None], dict[str, str], str, bool]:
    """Render all questions for the level in a compact grid layout."""

    irl_level_flow.inject_css()

    level_state = _level_state(dimension, level_id)
    is_saved = bool(level_state.get("en_calculo"))
    existing_answers = level_state.get("respuestas_preguntas") or {}
    existing_evidences = level_state.get("evidencias_preguntas") or {}

    questions: list[irl_level_flow.Question] = []
    for idx, pregunta in enumerate(preguntas, start=1):
        answer_key = f"resp_{dimension}_{level_id}_{idx}"
        value_key = f"toggle_{dimension}_{level_id}_{idx}"
        note_key = f"evid_{dimension}_{level_id}_{idx}"
        idx_str = str(idx)

        if answer_key not in st.session_state:
            default_option = existing_answers.get(idx_str)
            st.session_state[answer_key] = (
                default_option if default_option in {"VERDADERO", "FALSO"} else "FALSO"
            )

        if value_key not in st.session_state:
            st.session_state[value_key] = st.session_state[answer_key] == "VERDADERO"
        else:
            marcado = bool(st.session_state[value_key])
            st.session_state[value_key] = marcado
            st.session_state[answer_key] = "VERDADERO" if marcado else "FALSO"

        if note_key not in st.session_state:
            default_note = existing_evidences.get(idx_str, "")
            if not isinstance(default_note, str):
                default_note = "" if default_note is None else str(default_note)
            st.session_state[note_key] = default_note
        elif not isinstance(st.session_state[note_key], str):
            current_note = st.session_state.get(note_key)
            st.session_state[note_key] = "" if current_note is None else str(current_note)

        questions.append(
            irl_level_flow.Question(
                idx=idx,
                text=pregunta,
                value_key=value_key,
                note_key=note_key,
                answer_key=answer_key,
            )
        )

    cursor_key = f"{irl_level_flow.STATE_PREFIX}{dimension}_{level_id}_current_idx"
    irl_level_flow.init_state(questions, cursor_key=cursor_key)

    total_questions = len(questions)
    st.markdown(
        f"<div class='{irl_level_flow.CSS_SCOPE_CLASS}'>",
        unsafe_allow_html=True,
    )

    level_done = irl_level_flow.level_completed(questions)
    irl_level_flow.render_level_header(
        f"Nivel {level_id}",
        level_done,
        descripcion,
    )

    if total_questions:
        progress = _ensure_question_progress(dimension, level_id, total_questions)
        progress["active"] = 0
        st.session_state[_QUESTION_PROGRESS_KEY][dimension][level_id] = progress

        columns_per_row = 2 if total_questions > 1 else 1
        for start in range(0, total_questions, columns_per_row):
            row_questions = questions[start : start + columns_per_row]
            cols = st.columns(len(row_questions))
            for offset, (question, col) in enumerate(zip(row_questions, cols)):
                with col:
                    valid = irl_level_flow.render_question(
                        question,
                        position=start + offset,
                        total=total_questions,
                        disabled=locked,
                    )

                respuesta_actual = st.session_state.get(question.answer_key)
                evidencia_actual = st.session_state.get(question.note_key, "")
                if not isinstance(evidencia_actual, str):
                    evidencia_actual = "" if evidencia_actual is None else str(evidencia_actual)

                # Do not persist to the permanent level state while the user is
                # still navigating questions. Persist only when the user explicitly
                # clicks "Guardar y continuar...". We still track per-question
                # completion in the question progress map.
                if valid:
                    _mark_question_saved(
                        dimension,
                        level_id,
                        question.idx,
                        total_questions,
                    )
                else:
                    _mark_question_pending(
                        dimension,
                        level_id,
                        question.idx,
                        total_questions,
                    )

    st.markdown("</div>", unsafe_allow_html=True)

    respuestas_dict = irl_level_flow.serialize_answers(questions)
    evidencias_dict = irl_level_flow.serialize_evidences(questions)
    evidencia_texto = " \n".join(
        texto for texto in evidencias_dict.values() if texto
    ).strip()

    evidencia_join_key = f"evid_{dimension}_{level_id}"
    st.session_state[evidencia_join_key] = evidencia_texto

    ready_to_save = irl_level_flow.level_completed(questions)
    st.session_state[_READY_KEY][dimension][level_id] = ready_to_save

    return respuestas_dict, evidencias_dict, evidencia_texto, ready_to_save


def _render_dimension_tab(dimension: str) -> None:
    _init_irl_state()
    _process_pending_restores(dimension)
    levels = LEVEL_DEFINITIONS.get(dimension, [])
    counts = _compute_dimension_counts(dimension)

    banner_msg = st.session_state[_BANNER_KEY].get(dimension)
    banner_slot = st.empty()
    if banner_msg:
        banner_slot.info(banner_msg)

    st.markdown(IRL_IMPORTANT_HTML, unsafe_allow_html=True)

    progreso = counts["completed"] / counts["total"] if counts["total"] else 0
    st.markdown(
        f"**{counts['completed']} de {counts['total']} niveles respondidos**"
    )
    st.progress(progreso)

    for lvl_index, level in enumerate(levels):
        level_id = level["nivel"]
        state = _level_state(dimension, level_id)
        status = state.get("estado", "Pendiente")
        status_class = _status_class(status)
        card_classes = ["level-card", f"level-card--{status_class}"]
        if state.get("en_calculo"):
            card_classes.append("level-card--answered")
        if st.session_state[_ERROR_KEY][dimension].get(level_id):
            card_classes.append("level-card--error")
        edit_mode = st.session_state[_EDIT_MODE_KEY][dimension].get(
            level_id,
            not state.get("en_calculo"),
        )
        locked = bool(state.get("en_calculo")) and not edit_mode

        restore_flags = st.session_state[_RESTORE_ON_EDIT_KEY][dimension]
        if not edit_mode or locked:
            restore_flags[level_id] = False
        elif state.get("en_calculo"):
            if not restore_flags.get(level_id):
                _restore_level_form_values(dimension, level_id)
                restore_flags[level_id] = True
        else:
            restore_flags[level_id] = False

        if locked:
            card_classes.append("level-card--locked")
        elif edit_mode:
            card_classes.append("level-card--editing")

        st.markdown(
            f"<div class='{' '.join(card_classes)}' id='{dimension}-{level_id}'>",
            unsafe_allow_html=True,
        )

        expander_label = f"Nivel {level_id} · {level['descripcion']}"
        # Control expanders explicitly per-level to avoid racey JS-based close behaviour.
        expander_open_key = f"expander_open_{dimension}_{level_id}"
        # If there's an error for this level, force the expander open. Otherwise respect stored flag.
        expanded = bool(st.session_state[_ERROR_KEY][dimension].get(level_id)) or bool(
            st.session_state.get(expander_open_key, False)
        )
        with st.expander(
            expander_label,
            expanded=expanded,
        ):
            preguntas = level.get("preguntas") or []
            answer_key = f"resp_{dimension}_{level_id}"
            evidencia_key = f"evid_{dimension}_{level_id}"
            if evidencia_key not in st.session_state:
                evidencia_val = state.get("evidencia", "")
                st.session_state[evidencia_key] = "" if evidencia_val is None else str(evidencia_val)

            respuestas_dict: dict[str, str | None] = {}
            evidencias_dict_envio: dict[str, str] | None = None
            evidencia_texto = st.session_state.get(evidencia_key, "")
            respuesta_manual: str | None = None
            ready_to_save = False

            show_cancel = bool(state.get("en_calculo")) and edit_mode and not locked
            editar_label = "Cancelar" if show_cancel else "Editar"
            editar_disabled = False
            if not state.get("en_calculo") and edit_mode:
                editar_disabled = True

            if preguntas:
                (
                    respuestas_dict,
                    evidencias_dict_envio,
                    evidencia_texto,
                    ready_to_save,
                ) = _render_level_question_flow(
                    dimension,
                    level_id,
                    preguntas,
                    level.get("descripcion", ""),
                    locked=locked,
                )
            else:
                current_answer = state.get("respuesta")
                current_option = (
                    current_answer if current_answer in {"VERDADERO", "FALSO"} else "FALSO"
                )
                if answer_key not in st.session_state:
                    st.session_state[answer_key] = current_option

                st.radio(
                    "Responder",
                    options=["VERDADERO", "FALSO"],
                    key=answer_key,
                    horizontal=True,
                    disabled=locked,
                    on_change=_handle_manual_answer_change,
                    kwargs={
                        "answer_key": answer_key,
                        "evidencia_key": evidencia_key,
                    },
                )

                respuesta_manual = st.session_state.get(answer_key)
                evidencia_texto = st.text_area(
                    "Antecedentes de verificación",
                    key=evidencia_key,
                    placeholder="Describe brevemente los antecedentes que respaldan esta afirmación…",
                    height=110,
                    max_chars=STEP_CONFIG["max_char_limit"],
                    disabled=locked or respuesta_manual != "VERDADERO",
                )

                if respuesta_manual == "VERDADERO":
                    contador = len(_clean_text(evidencia_texto))
                    contador_html = (
                        f"<div class='stepper-form__counter{' stepper-form__counter--alert' if contador > STEP_CONFIG['soft_char_limit'] else ''}'>"
                        f"{contador}/{STEP_CONFIG['soft_char_limit']}"
                        "</div>"
                    )
                    st.markdown(contador_html, unsafe_allow_html=True)
                else:
                    st.caption("Disponible solo si seleccionas VERDADERO.")

                ready_to_save = respuesta_manual in {"VERDADERO", "FALSO"}
                if ready_to_save and respuesta_manual == "VERDADERO":
                    ready_to_save = _is_evidence_valid(evidencia_texto)

                evidencias_dict_envio = None
                st.session_state[_READY_KEY][dimension][level_id] = ready_to_save

            error_msg = st.session_state[_ERROR_KEY][dimension].get(level_id)
            if error_msg:
                st.error(error_msg)

            action_cols = st.columns([2, 1])
            guardar = action_cols[0].button(
                "Guardar y continuar con el siguiente nivel",
                type="primary",
                disabled=locked or not ready_to_save,
                key=f"btn_guardar_{dimension}_{level_id}",
                use_container_width=True,
            )
            editar = action_cols[1].button(
                editar_label,
                disabled=editar_disabled,
                key=f"btn_editar_{dimension}_{level_id}",
            )

            if editar:
                if locked:
                    st.session_state[_EDIT_MODE_KEY][dimension][level_id] = True
                    st.toast("Modo edición activado")
                    _rerun_app()
                elif state.get("en_calculo"):
                    _enqueue_level_restore(dimension, level_id)
                    st.session_state[_EDIT_MODE_KEY][dimension][level_id] = False
                    st.toast("Cambios descartados")
                    _rerun_app()

            if guardar:
                success, error_message, banner = _handle_level_submission(
                    dimension,
                    level_id,
                    respuestas_dict,
                    evidencia_texto,
                    evidencias_preguntas=evidencias_dict_envio,
                    respuesta_manual=respuesta_manual,
                )
                st.session_state[_BANNER_KEY][dimension] = banner
                if error_message:
                    st.session_state[_ERROR_KEY][dimension][level_id] = error_message
                else:
                    st.session_state[_ERROR_KEY][dimension][level_id] = None
                    _sync_dimension_score(dimension)
                    _set_revision_flag(dimension, level_id, False)
                    st.session_state[_EDIT_MODE_KEY][dimension][level_id] = False
                    # Close current expander and open the next one (if any) deterministically
                    st.session_state[_CLOSE_EXPANDER_KEY] = (dimension, level_id)
                    # close current
                    st.session_state[f"expander_open_{dimension}_{level_id}"] = False
                    # open next level if exists
                    if lvl_index + 1 < len(levels):
                        next_level_id = levels[lvl_index + 1]["nivel"]
                        st.session_state[f"expander_open_{dimension}_{next_level_id}"] = True

                    irl_level_flow.save_level("Nivel guardado")
                    st.toast("Guardado")
                    # Recalcular puntaje global y cachearlo para evitar cálculos en cada rerun
                    try:
                        df_all = _collect_dimension_responses()
                        if not df_all.empty:
                            st.session_state["irl_last_puntaje"] = trl.calcular_trl(
                                df_all[["dimension", "nivel", "evidencia"]]
                            )
                        else:
                            st.session_state["irl_last_puntaje"] = None
                    except Exception:
                        st.session_state["irl_last_puntaje"] = None
                    _rerun_app()
        if st.session_state.get(_CLOSE_EXPANDER_KEY) == (dimension, level_id):
            st.session_state[_CLOSE_EXPANDER_KEY] = None
            components.html(
                f"""
                <script>
                const container = window.parent.document.getElementById('{dimension}-{level_id}');
                if (container) {{
                    const details = container.querySelector("div[data-testid='stExpander'] details");
                    if (details) {{ details.open = false; }}
                }}
                </script>
                """,
                height=0,
            )

        st.markdown("</div>", unsafe_allow_html=True)

def _collect_dimension_responses() -> pd.DataFrame:
    _init_irl_state()
    dimensiones_ids = trl.ids_dimensiones()
    etiquetas = dict(zip(dimensiones_ids, trl.labels_dimensiones()))
    registros: list[dict] = []

    for dimension in dimensiones_ids:
        niveles = LEVEL_DEFINITIONS.get(dimension, [])
        evidencias: list[str] = []
        if not niveles:
            st.session_state["irl_scores"][dimension] = 0
            registros.append(
                {
                    "dimension": dimension,
                    "etiqueta": etiquetas.get(dimension, dimension),
                    "nivel": None,
                    "evidencia": "",
                }
            )
            continue
        niveles_sorted = sorted(niveles, key=lambda lvl: lvl.get("nivel", 0))
        baseline = niveles_sorted[0].get("nivel", 0)
        highest = baseline - 1
        for level in niveles_sorted:
            nivel_actual = level.get("nivel", baseline)
            expected_next = highest + 1
            if nivel_actual != expected_next:
                break
            data = _level_state(dimension, nivel_actual)
            if data.get("respuesta") == "VERDADERO" and data.get("en_calculo"):
                highest = nivel_actual
                evidencia_txt = (data.get("evidencia") or "").strip()
                if evidencia_txt:
                    evidencias.append(evidencia_txt)
            else:
                break
        approved_level = highest if highest >= baseline else 0
        st.session_state["irl_scores"][dimension] = approved_level
        registros.append(
            {
                "dimension": dimension,
                "etiqueta": etiquetas.get(dimension, dimension),
                "nivel": approved_level if approved_level else None,
                "evidencia": " · ".join(evidencias),
            }
        )

    return pd.DataFrame(registros)



def _level_has_response(state: dict | None) -> bool:
    if not state:
        return False

    estado_auto = state.get("estado_auto")
    if estado_auto and estado_auto != "Pendiente":
        return True

    if state.get("en_calculo"):
        return True

    estado = state.get("estado")
    if estado and estado != "Pendiente":
        return True

    if state.get("marcado_revision"):
        return True

    return False


def _format_answer_display(valor: str | None, state: dict | None) -> str:
    if valor == "VERDADERO":
        return "Verdadero"

    if valor == "FALSO":
        return "Falso" if _level_has_response(state) else "No respondido"

    return "No respondido"


def _collect_dimension_details() -> dict[str, dict[str, Any]]:
    _init_irl_state()
    dimensiones_ids = trl.ids_dimensiones()
    etiquetas = dict(zip(dimensiones_ids, trl.labels_dimensiones()))
    detalles: dict[str, dict[str, Any]] = {}

    for dimension in dimensiones_ids:
        niveles = LEVEL_DEFINITIONS.get(dimension, [])
        filas: list[dict[str, Any]] = []
        for level in niveles:
            nivel_id = level.get("nivel")
            state = _level_state(dimension, nivel_id)
            estado_nivel = state.get("estado", "Pendiente")
            preguntas = level.get("preguntas") or []
            if preguntas:
                respuestas = state.get("respuestas_preguntas") or {}
                evidencias_preguntas = state.get("evidencias_preguntas") or {}
                for idx, pregunta in enumerate(preguntas, start=1):
                    idx_str = str(idx)
                    filas.append(
                        {
                            "Nivel": nivel_id,
                            "Descripción del nivel": level.get("descripcion", ""),
                            "Pregunta": pregunta,
                            "Respuesta": _format_answer_display(
                                respuestas.get(idx_str), state
                            ),
                            "Antecedentes de verificación": evidencias_preguntas.get(idx_str) or "—",
                            "Estado del nivel": estado_nivel,
                        }
                    )
            else:
                filas.append(
                    {
                        "Nivel": nivel_id,
                        "Descripción del nivel": level.get("descripcion", ""),
                        "Pregunta": "—",
                        "Respuesta": _format_answer_display(state.get("respuesta"), state),
                        "Antecedentes de verificación": state.get("evidencia") or "—",
                        "Estado del nivel": estado_nivel,
                    }
                )

        detalles[dimension] = {
            "label": etiquetas.get(dimension, dimension),
            "rows": filas,
        }

    return detalles


st.set_page_config(page_title="Fase 1 - Evaluación IRL", page_icon="🌲", layout="wide")
load_theme()

st.markdown(
    """
<style>
.page-intro {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
    gap: 2.4rem;
    padding: 2.3rem 2.6rem;
    border-radius: 30px;
    background: linear-gradient(145deg, rgba(18, 48, 29, 0.94), rgba(111, 75, 44, 0.88));
    color: #fdf9f2;
    box-shadow: 0 36px 60px rgba(12, 32, 20, 0.35);
    margin-bottom: 2.6rem;
}

.page-intro h1 {
    font-size: 2.2rem;
    margin-bottom: 1rem;
    color: #fffdf8;
}

.page-intro p {
    font-size: 1.02rem;
    line-height: 1.6;
    color: rgba(253, 249, 242, 0.86);
}

.page-intro__aside {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.page-intro__aside .intro-stat {
    background: rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 1.1rem 1.3rem;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.page-intro__aside .intro-stat strong {
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-size: 0.9rem;
    margin-bottom: 0.35rem;
    color: #fefcf9;
}

.page-intro__aside .intro-stat p {
    margin: 0;
    color: rgba(253, 249, 242, 0.86);
    font-size: 0.96rem;
    line-height: 1.5;
}

.back-band {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1.6rem;
}

.metric-ribbon {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1.1rem;
    margin: 1.4rem 0 2.1rem;
}

.metric-ribbon__item {
    background: #ffffff;
    border-radius: 20px;
    padding: 1.3rem 1.4rem;
    border: 1px solid rgba(var(--shadow-color), 0.12);
    box-shadow: 0 20px 42px rgba(var(--shadow-color), 0.16);
    position: relative;
    overflow: hidden;
}

.metric-ribbon__item:after {
    content: "";
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: rgba(37, 87, 52, 0.12);
    top: -40px;
    right: -50px;
}

.metric-ribbon__value {
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--forest-700);
    position: relative;
}

.metric-ribbon__label {
    display: block;
    margin-top: 0.4rem;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.55px;
    text-transform: uppercase;
    color: var(--text-500);
}

.section-shell {
    background: #ffffff;
    border-radius: 24px;
    padding: 1.6rem 1.8rem;
    border: 1px solid rgba(var(--shadow-color), 0.12);
    box-shadow: 0 24px 48px rgba(var(--shadow-color), 0.16);
    margin-bottom: 2.3rem;
}

.section-shell--split {
    padding: 1.6rem 1.2rem 1.9rem;
}

.section-shell h3, .section-shell h4 {
    margin-top: 0;
}

.threshold-band {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin: 0.6rem 0 1rem;
}

.threshold-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 1rem;
    border-radius: 16px;
    background: rgba(var(--forest-500), 0.16);
    color: var(--text-700);
    font-weight: 600;
    border: 1px solid rgba(var(--forest-500), 0.22);
}

.threshold-chip strong {
    font-size: 1rem;
    color: var(--forest-700);
}

.selection-card {
    position: relative;
    padding: 1.8rem 2rem;
    border-radius: 26px;
    background: linear-gradient(140deg, rgba(49, 106, 67, 0.16), rgba(32, 73, 46, 0.22));
    border: 1px solid rgba(41, 96, 59, 0.45);
    box-shadow: 0 26px 48px rgba(21, 56, 35, 0.28);
    overflow: hidden;
}

.selection-card::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: rgba(103, 164, 123, 0.18);
    top: -80px;
    right: -70px;
    filter: blur(0.5px);
}

.selection-card__badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 1.1rem;
    border-radius: 999px;
    background: #1f6b36;
    color: #f4fff2;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    font-size: 0.78rem;
    font-weight: 600;
    box-shadow: 0 12px 24px rgba(31, 107, 54, 0.35);
    position: relative;
    z-index: 1;
}

.selection-card__title {
    margin: 1.1rem 0 0.6rem;
    font-size: 1.65rem;
    color: #10371d;
    position: relative;
    z-index: 1;
}

.selection-card__subtitle {
    margin: 0;
    color: rgba(16, 55, 29, 0.78);
    font-size: 1rem;
    position: relative;
    z-index: 1;
}

.selection-card__meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1.1rem;
    margin-top: 1.5rem;
    position: relative;
    z-index: 1;
}

.selection-card__meta-item {
    padding: 1rem 1.1rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(41, 96, 59, 0.18);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.selection-card__meta-label {
    display: block;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.6px;
    color: rgba(16, 55, 29, 0.64);
    margin-bottom: 0.35rem;
}

.selection-card__meta-value {
    display: block;
    font-size: 1.05rem;
    font-weight: 600;
    color: #10371d;
}

.history-caption {
    color: var(--text-500);
    margin-bottom: 0.8rem;
}

@media (max-width: 992px) {
    .page-intro {
        grid-template-columns: 1fr;
    }

    .back-band {
        justify-content: center;
    }
}

div[data-testid="stExpander"] {
    margin-bottom: 0.2rem;
}

div[data-testid="stExpander"] > details {
    border-radius: 22px;
    border: 1px solid rgba(var(--shadow-color), 0.16);
    background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(235, 229, 220, 0.9));
    box-shadow: 0 24px 52px rgba(var(--shadow-color), 0.18);
    overflow: hidden;
}

div[data-testid="stExpander"] > details > summary {
    font-weight: 700;
    font-size: 1rem;
    color: var(--forest-700);
    padding: 1rem 1.4rem;
    list-style: none;
    position: relative;
}

div[data-testid="stExpander"] > details > summary::before {
    content: "➕";
    margin-right: 0.6rem;
    color: var(--forest-600);
    font-size: 1rem;
}

div[data-testid="stExpander"] > details[open] > summary::before {
    content: "➖";
}

div[data-testid="stExpander"] > details[open] > summary {
    background: rgba(var(--forest-500), 0.12);
    color: var(--forest-800);
}

div[data-testid="stExpander"] > details > div[data-testid="stExpanderContent"] {
    padding: 1.2rem 1.5rem 1.4rem;
    background: #ffffff;
    border-top: 1px solid rgba(var(--shadow-color), 0.12);
}

.irl-bubbles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.85rem;
    margin: 1rem 0 1.4rem;
}

.irl-bubble {
    border-radius: 18px;
    padding: 0.85rem 1rem;
    background: rgba(var(--forest-100), 0.72);
    border: 1px solid rgba(var(--forest-500), 0.25);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.6);
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.irl-bubble__label {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--forest-800);
}

.irl-bubble__badge {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.55px;
}

.irl-bubble small {
    color: var(--text-500);
    font-size: 0.75rem;
}

.irl-bubble--complete {
    background: rgba(46, 142, 86, 0.18);
    border-color: rgba(46, 142, 86, 0.45);
}

.irl-bubble--partial {
    background: rgba(234, 185, 89, 0.22);
    border-color: rgba(234, 185, 89, 0.45);
}

.irl-bubble--pending {
    background: rgba(180, 196, 210, 0.25);
    border-color: rgba(143, 162, 180, 0.42);
}

.irl-important {
    margin: 0.6rem 0 1.1rem;
    padding: 0.85rem 1rem;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(56, 116, 209, 0.16), rgba(21, 118, 78, 0.14));
    border: 1px solid rgba(56, 116, 209, 0.25);
    color: rgba(26, 44, 84, 0.92);
    font-size: 0.9rem;
    line-height: 1.5;
    box-shadow: 0 12px 24px rgba(var(--shadow-color), 0.12);
}

.irl-important strong {
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

.irl-important a {
    color: rgba(12, 74, 50, 0.95);
    font-weight: 700;
    text-decoration: none;
    border-bottom: 1px solid rgba(12, 74, 50, 0.4);
}

.irl-important a:hover {
    color: rgba(12, 74, 50, 0.8);
}

.irl-important__hint {
    display: block;
    margin-top: 0.4rem;
    font-size: 0.82rem;
    color: rgba(26, 44, 84, 0.78);
}

.level-card {
    border-radius: 20px;
    border: 1px solid rgba(var(--shadow-color), 0.12);
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 10px 20px rgba(var(--shadow-color), 0.1);
    margin-bottom: 0.3rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.level-card:hover {
    box-shadow: 0 16px 28px rgba(var(--shadow-color), 0.16);
}

.level-card > div[data-testid="stExpander"] > details {
    border: none;
    background: transparent;
}

.level-card > div[data-testid="stExpander"] > details > summary {
    font-size: 1.02rem;
    font-weight: 700;
    color: var(--forest-800);
    padding: 0.8rem 1rem;
    list-style: none;
    cursor: pointer;
}

.level-card > div[data-testid="stExpander"] > details > summary::-webkit-details-marker {
    display: none;
}

.level-card > div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {
    padding: 0 1rem 0.9rem;
    background: rgba(255, 255, 255, 0.98);
    border-top: 1px solid rgba(var(--shadow-color), 0.12);
}

.level-card--answered {
    border-color: rgba(58, 181, 112, 0.75);
    box-shadow: 0 18px 32px rgba(46, 142, 86, 0.25);
    background: linear-gradient(140deg, rgba(220, 247, 229, 0.95), rgba(188, 236, 205, 0.9));
}

.level-card--editing {
    border-color: rgba(21, 118, 78, 0.88);
    box-shadow: 0 26px 48px rgba(27, 122, 84, 0.24);
}

.level-card--editing > div[data-testid="stExpander"] > details > summary {
    color: #0d4c32;
}

.level-card--locked {
    background: linear-gradient(135deg, rgba(228, 232, 238, 0.94), rgba(212, 217, 226, 0.98));
    border-color: rgba(135, 145, 163, 0.68);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55), 0 14px 30px rgba(64, 74, 92, 0.14);
}

.level-card--locked > div[data-testid="stExpander"] > details > summary {
    color: rgba(46, 59, 79, 0.88);
    text-shadow: none;
}

.level-card--locked .level-card__intro {
    color: rgba(48, 61, 80, 0.8);
}

.level-card--complete {
    border-color: rgba(30, 78, 155, 0.7);
}

.level-card--complete > div[data-testid="stExpander"] > details > summary {
    color: #10315e;
}

.level-card--answered > div[data-testid="stExpander"] > details > summary {
    background: rgba(58, 181, 112, 0.18);
    color: #145c33;
    text-shadow: none;
}

.level-card--answered > div[data-testid="stExpander"] > details[open] > summary {
    background: rgba(58, 181, 112, 0.28);
    color: #0f4c28;
}

.level-card--answered > div[data-testid="stExpander"] > details > summary::before {
    color: #145c33;
}

.level-card--answered > div[data-testid="stExpander"] > details > summary::after {
    content: "";
    display: inline-flex;
    width: 1.2rem;
    height: 1.2rem;
    margin-left: 0.5rem;
    background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAYAAADhAJiYAAAJDklEQVR4nK2YXWwc1RXH/+fe+dj1V7xrkmLaSm2eip8qrQQtLSwUx3Gwg8vDELWIfgi6VRMHCC1UtAqbVT9QVYpoEkFlGhCqVAojlTiOQxybNi6IwoMf8SNFVZXUmOzacby7M3PvPX2Ysb3+wI2bngdr1ztzz++eez4vsHUheJ5EIWd/4hOFnI1CzgaDtr74Vp4t5iVKk6rxnx2/ursVH698F4vzPPvc5JVVb3qehO/r/x9Qw4Lb9+dblO3cCse5mYLoJrbkVyjShokFiECGQ5b0AmlecFrk7//91NnZNbr4WoEIALc90JOVLfwQgfaDaDs5FqAN2Kw5FwIgRazW8DwT/s5snq08Mza2dnNbA2IQjoBQgul4pHcvC3qJBHWwitci2wIHEQDMM5jixYiZWQjXboUxYM0gKQBB4FCNRBX93YU/vHlpM6iNgYoQAIDzeZH9YurPZMu9HClNUko2BtA8QynnRa4H5wH5rhY1IU3aAEAQ6ZRr4wEQ5WGJW0iIVg4VSAqwoDLXovsrz02cQSFnY2gquhogQhGEaY+yN8wPU8ru42qkRLNrcaTHWZunofFu+djZy59o3USuf6J3e1g1PwDwJFlSstIMKQyHaqByfGJ0I6i1QHEkAcjOuSfJtfs4UApgZtAvKxfafrZs6mLewvQOhu+bdSSFnIWhKYXEgbODu7spJR8HsIsjFUIKyTU1UHl+YnTt8a0G8iDhQ2cHe05Rs7OXa5GCRcQhD1SOj42iCIFpjxKITaNlef0YLgIgsg/3nCLX7uO6UrAFOOI7KkfPvt0ItQKUwLQf6L5bpu1hDnUES4Qcqn2V4xOjONjr4tjZ4Cog1ksxbwG3G0xPU/bTl0+CqJcEWaz0W7bFe2b+2V5f2qRY3okP3XaoJ0uSXuFIa2p2bITm19cMAwBHJjWmpwm+b9yqvY+NCVlpTU3OrWGIx+D7GoWctWKhQs5GZafJXD93WLj2kzCGWJm3pArumlVXgkZ/uCbxPImuLm4vv9MnHesUa61heN4OcePM78ZnAUAAIAxNRej6iAg4AKXBhNAY+unsc5NXUNl5tf6yMQCDMge7780e6h2B72uUSmbu2PgIh2qMhJCUcrKRhfsAMAo5S8CLc05mztkFW7YBAIe6PNfR9h4A2jCKrkaKEPB93fn9/jSE+L1I2f3Zh3tOX/fI7k4wCIQxWEJDaWbCXZ855KVR2WkE0CUBAAY3kyUd2JJA+BOmsXSu/4t1CCUYeJ4M0tGrJEWzrgY1cqw+VuZGEJg0v8qBMjBMAG771xcyCr6vBbqmFYqeQ0Q3QRuw1gGBzsD3dXJcW4cp5KxP/XBXc7ZzfphSdj8rHQnbSpsg7Lt0fPwvyOetS1FlFsxvQgqQLXX2/Q9vBwCBEky2vJAC0A3DQGRq5frnzgPAuuMqJj63WQ082OtgaCqKAvqRaE31mWp9UTS5rqmHI5WjE2dQzFvYsUNgaCpi4K8QBLKsNNh8LQYCQCmHwbwY749oW3qmeZ2iYlGghCUH5w2bLw8Sx84GmcHuPjjyMb1QC0TKbeZaOFq5LXMPinkLpUmNzAeJG4hYDzOW9C/lITCtfJYmWG+ZUslkB3d52UO9I8sWKq68E4c0uP1ATz851jC0TpFtOxxGb5UvbBvA+z6jNKnR4JMEXtFDJFYBNX6WunXlwaRcZAZ79sGRL4uU3Z99ZPcp3OuJ5d+XIupif4osvArDAiAG2DCbn8D3Nc7nBdYFCC3r4SRJx3+aXCZGPbYUk0jPNSXKCNMeAZAk+Dvk2ml9pbZIrt2fvWF+OPkNKIEbIsoFOIQk4mo0UDk6EdeqydWtLzxPMnEqOTIWTPUYqJCzZ0v+IhgnYAkIx26NQvomAOBiTsL3DV7zo/LF9n6uhqdFU6qZa/UqpZy+7A0LwyjB5AoFK2lV+llpRZblmpq+p/J80mKsbsaWEzEMHoQyMKFaDFtaXmg8JmZBcwBraENM2APPc5azNAHwfVO+0PZ1roejlE41ca1eFU12X8fBXS//w/3wCdGS6jPVcDmi5p4fH9mwCfPio85W3DvIFu1gZjCqTdFiYqG4TsEJ+UUOtYJmJsIdLZ+tteE13yDpqVEEocvn8oVtA0tQZrEewLa+BaBoLtdCkbJXR1Sy9irJfCDAIGbsIUs4sCVA/MeZp8erKOTs2NE8T86Yz1dg8B4kMTlSOEF9PyiuL4mfxA64Csp1TaRqAAy5m0dUIgKdU7rzSH+aBN3HdWVgDBHjDRA4KR2JDA1FRvBhSCE40AKu/Xjmod6vYmgqQj6/MVQQnZZt6TRZZDFzsHlEASjkJEow9XLwCiTtINcSHOjJ8rHxc0tNWgzk+xqeJ+d+O/43U49OQQomgWYi8xQ8T+L2SbOcc5agfF+Xnx0bMIvhEaPNN1Q1vLVydOJtFItiXUTFMDaGpqL2Az39wrXuhjKKDV8xEIcbk2xjthUoAp0X+1P1dDhLoDTZkjhSo+UL2wbg+xr5vNWgjNZZoVgUKJXW1j+C5wn4vs4MdveRY59kpSPZkkqby/Uj5ePnSo3Ov6an9iS6fM5c2r2HHHESWse+UYvOqCruv3ziXBkrI7VOdm6hstOgq4sbYGKIzAdiSdF1j+7pN4zXYZI169GobfO+mZYwaPS3jeuRj2Q31jAMGwA2hCgL4NsfP/PG6XVH0SidLdw4/7ceuLPDlvIlcqy9HKkauXaag2jF6mssvXHVTkyY2d99F7nWCAkSrLQmS0qO9BiYJ+1sy4mZ0usfbfT69v35Fu2kbyFH5LmuvkeW2M5Ka9GSlmaxHsN0+THEkk9uCtQAlR28s5tc58dkW92mFiSjsQAbs4BIv8PAu/GwQIaImAGXwA9CiO3kxOM22RY4VApC/Ly8rfYLlCZVXLCxrt/a/LJhZV6SmYd3HybwILl2B5SOLxmSuX2dqOQSwpGAZrDAGEL9m/LRc+MJSNzCbCD//fajYYhreTR/naPsApPIQ8ovkdKtlHYIhldWY4YJ1RViVMm1ThitJ5dvPj5hnt8a0NJzay6rssXeNlTMzXCtL6OuNOL7IWIgiKRzIl1fqDdcXBGKRdogJVyz0KZXeWulmLfgeXIrCv4DrAHlWHLAUmgAAAAASUVORK5CYII=") no-repeat center center / contain;
    vertical-align: middle;
}

.level-card--pending {
    border-color: rgba(143, 162, 180, 0.4);
    background: linear-gradient(140deg, rgba(186, 198, 214, 0.18), rgba(214, 222, 232, 0.12));
}

.level-card--attention {
    border-color: rgba(224, 156, 70, 0.82);
    background: linear-gradient(135deg, rgba(224, 156, 70, 0.08), rgba(224, 156, 70, 0.14));
}

.level-card--review {
    border-color: rgba(156, 112, 230, 0.75);
    background: linear-gradient(135deg, rgba(156, 112, 230, 0.1), rgba(156, 112, 230, 0.16));
}

.level-card--error {
    border-color: rgba(206, 104, 86, 0.88);
    box-shadow: 0 24px 40px rgba(206, 104, 86, 0.24);
    background: linear-gradient(135deg, rgba(206, 104, 86, 0.08), rgba(206, 104, 86, 0.14));
}

.level-card__intro {
    font-size: 0.92rem;
    color: var(--text-600);
    margin-bottom: 0.75rem;
    line-height: 1.45;
}

.question-block {
    border: none;
    border-radius: 10px;
    padding: 0.45rem 0.6rem 0.4rem;
    margin-bottom: 0.2rem;
    background: rgba(246, 249, 253, 0.96);
    box-shadow: 0 6px 14px rgba(var(--shadow-color), 0.08);
    transition: background 0.2s ease, box-shadow 0.2s ease;
}

.question-block--true {
    background: linear-gradient(135deg, rgba(21, 118, 78, 0.22), rgba(12, 74, 50, 0.18));
    box-shadow: 0 12px 22px rgba(14, 92, 64, 0.18);
}

.question-block--pending {
    background: linear-gradient(135deg, rgba(183, 196, 212, 0.16), rgba(163, 178, 197, 0.14));
    box-shadow: 0 10px 18px rgba(120, 140, 160, 0.18);
}

.question-block--false {
    background: linear-gradient(135deg, rgba(170, 182, 198, 0.18), rgba(145, 158, 176, 0.12));
    box-shadow: 0 12px 22px rgba(120, 135, 155, 0.14);
}

.question-block--saved {
    box-shadow: 0 16px 28px rgba(14, 92, 64, 0.24);
}

.question-block--locked {
    background: rgba(244, 246, 250, 0.82);
    box-shadow: none;
    opacity: 0.78;
}

.question-block--locked .question-block__chip {
    filter: grayscale(0.4);
    opacity: 0.85;
}

.question-block__header {
    display: flex;
    gap: 0.6rem;
    align-items: flex-start;
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text-700);
}

.question-block__body {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    width: 100%;
}

.question-block__badge {
    min-width: 1.8rem;
    height: 1.8rem;
    border-radius: 999px;
    background: linear-gradient(140deg, rgba(31, 132, 92, 0.95), rgba(17, 91, 63, 0.92));
    color: #f2fff8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.82rem;
}

.question-block__text {
    flex: 1;
    line-height: 1.35;
}

.question-block__chip {
    border-radius: 999px;
    padding: 0.12rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}

.question-block__chip--true {
    background: rgba(28, 113, 83, 0.18);
    color: rgba(12, 74, 50, 0.9);
    border: none;
}

.question-block__chip--false {
    background: rgba(168, 178, 194, 0.2);
    color: rgba(68, 82, 102, 0.92);
    border: none;
}

.question-block__chip--pending {
    background: rgba(134, 149, 170, 0.18);
    color: rgba(58, 76, 102, 0.9);
    border: none;
}

.question-block__chip--draft {
    box-shadow: inset 0 0 0 1px rgba(58, 76, 102, 0.22);
}

.question-block__counter {
    text-align: right;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: rgba(var(--shadow-color), 0.65);
}

.question-block__counter--alert {
    color: rgba(184, 108, 54, 0.85);
    font-weight: 600;
}

.question-stepper {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 0.6rem;
}

.question-stepper__item {
    min-width: 2.2rem;
    padding: 0.35rem 0.7rem;
    border-radius: 12px;
    background: rgba(31, 55, 91, 0.08);
    color: rgba(38, 52, 71, 0.78);
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    border: 1px solid transparent;
    transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.question-stepper__item.is-done {
    background: linear-gradient(135deg, rgba(40, 96, 165, 0.22), rgba(29, 71, 128, 0.18));
    color: rgba(22, 52, 99, 0.95);
    box-shadow: 0 10px 20px rgba(29, 71, 128, 0.22);
}

.question-stepper__item.is-active {
    background: linear-gradient(135deg, rgba(21, 118, 78, 0.24), rgba(12, 74, 50, 0.2));
    color: rgba(12, 62, 44, 0.96);
    box-shadow: 0 12px 24px rgba(14, 92, 64, 0.2);
    border-color: rgba(14, 92, 64, 0.24);
}

.question-stepper__item.is-active.is-done {
    background: linear-gradient(135deg, rgba(21, 118, 78, 0.26), rgba(12, 74, 50, 0.22));
}

.question-actions {
    margin-top: 0.6rem;
}

.question-actions > div[data-testid="column"] {
    display: flex;
    flex-direction: column;
}

.question-actions > div[data-testid="column"] > div {
    width: 100%;
}

.question-action {
    width: 100%;
}

.question-action > div[data-testid="stButton"] > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 700;
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.question-action--next > div[data-testid="stButton"] > button,
.question-action--save > div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1e9d6c, #15754e);
    color: #ffffff;
    border: 1px solid rgba(17, 94, 63, 0.85);
    box-shadow: 0 12px 22px rgba(21, 117, 78, 0.24);
}

.question-action--next > div[data-testid="stButton"] > button:hover:enabled,
.question-action--save > div[data-testid="stButton"] > button:hover:enabled {
    background: linear-gradient(135deg, #25b27c, #1b8a5d);
    box-shadow: 0 16px 28px rgba(21, 117, 78, 0.28);
    transform: translateY(-1px);
}

.question-action--next > div[data-testid="stButton"] > button:disabled,
.question-action--save > div[data-testid="stButton"] > button:disabled {
    background: linear-gradient(135deg, #e5e7eb, #d1d5db);
    color: #1f2937;
    border: 1px solid #9ca3af;
    box-shadow: none;
    cursor: not-allowed;
    opacity: 1;
}

.question-action--prev > div[data-testid="stButton"] > button {
    background: rgba(31, 55, 91, 0.08);
    color: rgba(28, 53, 88, 0.85);
    border: 1px solid rgba(28, 53, 88, 0.14);
    box-shadow: none;
}

.question-action--prev > div[data-testid="stButton"] > button:hover:enabled {
    background: rgba(31, 55, 91, 0.12);
    color: rgba(28, 53, 88, 0.95);
}

.question-action--prev > div[data-testid="stButton"] > button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

.question-action--single {
    margin-top: 0.6rem;
}

.question-toggle {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.35rem;
}

.question-toggle > div[data-testid="stToggle"] {
    width: 100%;
    display: flex;
    justify-content: flex-end;
}

.question-toggle > div[data-testid="stToggle"] label {
    transform: scale(1.05);
}

.question-toggle__state {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.4px;
}

.question-toggle__state--true {
    color: rgba(17, 94, 63, 0.95);
}

.question-toggle__state--false {
    color: rgba(130, 32, 32, 0.92);
}

.level-card--locked .question-block__counter,
.level-card--locked .stepper-form__counter {
    opacity: 0.65;
}

.level-card--locked .stTextArea textarea,
.level-card--locked .stTextInput input,
.level-card--locked div[data-testid="stRadio"] {
    filter: grayscale(0.65);
    opacity: 0.8;
}

.level-card__lock-hint {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    font-size: 0.86rem;
    color: rgba(42, 55, 78, 0.88);
    background: rgba(64, 84, 114, 0.12);
    border: 1px dashed rgba(64, 84, 114, 0.35);
    border-radius: 14px;
    padding: 0.7rem 0.85rem;
    margin-bottom: 1.05rem;
}

.level-card__lock-hint strong {
    color: rgba(32, 45, 68, 0.92);
}

.question-block__hint {
    margin-top: 0.4rem;
    background: rgba(255, 193, 99, 0.16);
    border-left: 4px solid rgba(255, 166, 43, 0.5);
    padding: 0.55rem 0.75rem;
    border-radius: 10px;
    font-size: 0.85rem;
    color: rgba(132, 77, 7, 0.92);
}

.question-block__warning {
    margin-top: 0.6rem;
    background: rgba(206, 104, 86, 0.14);
    border-left: 5px solid rgba(206, 104, 86, 0.9);
    padding: 0.7rem 0.85rem;
    border-radius: 10px;
    font-size: 0.86rem;
    color: rgba(122, 36, 24, 0.95);
}

.question-block__error {
    margin-top: 0.35rem;
    font-size: 0.78rem;
    color: rgba(171, 44, 38, 0.98);
    font-weight: 600;
}

.stepper-form__counter {
    text-align: right;
    font-size: 0.75rem;
    color: var(--text-500);
    margin-top: -0.4rem;
}

.stepper-form__counter--alert {
    color: #a35a00;
    font-weight: 600;
}

.stepper-form__hint {
    margin-top: 0.45rem;
    background: rgba(255, 193, 99, 0.16);
    border-left: 4px solid rgba(255, 166, 43, 0.5);
    padding: 0.55rem 0.75rem;
    border-radius: 10px;
    font-size: 0.86rem;
    color: rgba(132, 77, 7, 0.92);
}

.stepper-form__warning {
    margin-top: 0.6rem;
    background: rgba(206, 104, 86, 0.14);
    border-left: 5px solid rgba(206, 104, 86, 0.9);
    padding: 0.7rem 0.9rem;
    border-radius: 10px;
    font-size: 0.87rem;
    color: rgba(122, 36, 24, 0.95);
}

div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"] {
    border: 1px solid rgba(var(--shadow-color), 0.16);
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 22px 44px rgba(var(--shadow-color), 0.18);
    background: #ffffff;
}

div[data-testid="stDataFrame"] div[role="columnheader"],
div[data-testid="stDataEditor"] div[role="columnheader"] {
    background: linear-gradient(135deg, var(--forest-700), var(--forest-500)) !important;
    color: #ffffff !important;
    font-weight: 700;
    font-size: 0.92rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 2px solid rgba(12, 32, 20, 0.22);
    box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.14);
}

div[data-testid="stDataFrame"] div[role="gridcell"],
div[data-testid="stDataEditor"] div[role="gridcell"] {
    color: var(--text-700);
    font-size: 0.92rem;
    border-bottom: 1px solid rgba(var(--forest-700), 0.14);
    border-right: 1px solid rgba(var(--forest-700), 0.1);
    padding: 0.55rem 0.75rem;
    background: rgba(255, 255, 255, 0.92);
}

div[data-testid="stDataFrame"] div[role="row"],
div[data-testid="stDataEditor"] div[role="row"] {
    transition: background 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stDataFrame"] div[role="rowgroup"] > div:nth-child(odd) div[role="row"],
div[data-testid="stDataEditor"] div[role="rowgroup"] > div:nth-child(odd) div[role="row"] {
    background: rgba(255, 255, 255, 0.98);
}

div[data-testid="stDataFrame"] div[role="rowgroup"] > div:nth-child(even) div[role="row"],
div[data-testid="stDataEditor"] div[role="rowgroup"] > div:nth-child(even) div[role="row"] {
    background: rgba(199, 217, 182, 0.32);
}

div[data-testid="stDataFrame"] div[role="rowgroup"] > div div[role="row"]:hover,
div[data-testid="stDataEditor"] div[role="rowgroup"] > div div[role="row"]:hover {
    background: rgba(63, 129, 68, 0.18);
    box-shadow: inset 0 0 0 1px rgba(12, 32, 20, 0.2);
}

div[data-testid="stDataFrame"] div[role="rowgroup"] > div div[role="row"]:hover div[role="gridcell"],
div[data-testid="stDataEditor"] div[role="rowgroup"] > div div[role="row"]:hover div[role="gridcell"] {
    border-bottom-color: transparent;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-intro">
        <div>
            <h1>Evaluacion estrategica de madurez tecnologica</h1>
            <p>
                Priorizamos proyectos del portafolio maestro para registrar evidencias por dimension, estimar el TRL e impulsar el
                cierre de brechas con una mirada integral entre cliente, negocio y tecnologia.
            </p>
        </div>
        <div class="page-intro__aside">
            <div class="intro-stat">
                <strong>Objetivo</strong>
                <p>Seleccionar iniciativas clave y capturar sus niveles IRL, alineando evidencia y responsables.</p>
            </div>
            <div class="intro-stat">
                <strong>Resultado</strong>
                <p>Perfil comparativo IRL con historial descargable y focos para la ruta comercial EBCT.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

fase0_page = next(Path("pages").glob("02_*_Fase_0_Portafolio.py"), None)
fase2_page = next(Path("pages").glob("04_*_Fase_2_*.py"), None)
if fase0_page:
    st.markdown("<div class='back-band'>", unsafe_allow_html=True)
    if st.button("Volver a Fase 0", type="primary"):
        st.switch_page(str(fase0_page))
    st.markdown("</div>", unsafe_allow_html=True)

payload = st.session_state.get('fase1_payload')
fase1_ready = st.session_state.get('fase1_ready', False)
if "fase2_ready" not in st.session_state:
    st.session_state["fase2_ready"] = False

if not payload or not fase1_ready:
    st.warning('Calcula el ranking de candidatos en Fase 0 y usa el boton "Ir a Fase 1" para continuar.')
    if fase0_page:
        if st.button('Ir a Fase 0', key='btn_ir_fase0_desde_fase1'):
            st.switch_page(str(fase0_page))
    st.stop()

ranking_df = payload['ranking'].copy().reset_index(drop=True)
if ranking_df.empty:
    st.warning('El ranking recibido esta vacio. Recalcula la priorizacion en Fase 0.')
    if fase0_page:
        if st.button('Recalcular en Fase 0', key='btn_recalcular_fase0'):
            st.switch_page(str(fase0_page))
    st.stop()

metrics_cards = payload.get('metrics_cards', [])
umbrales = payload.get('umbrales', {})

if metrics_cards:
    metrics_html = "<div class='metric-ribbon'>"
    for label, value in metrics_cards:
        metrics_html += (
            "<div class='metric-ribbon__item'>"
            f"<span class='metric-ribbon__value'>{value}</span>"
            f"<span class='metric-ribbon__label'>{label}</span>"
            "</div>"
        )
    metrics_html += "</div>"
    st.markdown(metrics_html, unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.markdown('#### Ranking de candidatos priorizados')
    if umbrales:
        thresholds = "".join(
            f"<span class='threshold-chip'><strong>{valor}</strong>{nombre}</span>" for nombre, valor in umbrales.items()
        )
        st.markdown(f"<div class='threshold-band'>{thresholds}</div>", unsafe_allow_html=True)

    ranking_display = ranking_df.copy().reset_index(drop=True)
    if 'evaluacion_calculada' in ranking_display.columns:
        ranking_display['evaluacion_calculada'] = ranking_display['evaluacion_calculada'].astype(float).round(1)

    with st.expander('Ver ranking priorizado', expanded=False):
        render_table(
            ranking_display,
            key='fase1_ranking_andes',
            highlight_top_rows=3,
            include_actions=True,
            hide_index=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
ranking_keys = ranking_df[['id_innovacion', 'ranking']].copy()
ranking_keys['id_str'] = ranking_keys['id_innovacion'].astype(str)

df_port = utils.normalize_df(db.fetch_df())
df_port['id_str'] = df_port['id_innovacion'].astype(str)
df_port = df_port[df_port['id_str'].isin(ranking_keys['id_str'])].copy()
if df_port.empty:
    st.warning('Los proyectos del ranking ya no estan disponibles en el portafolio maestro. Recalcula la priorizacion en Fase 0.')
    if fase0_page:
        if st.button('Volver a Fase 0', key='btn_volver_recalcular'):
            st.switch_page(str(fase0_page))
    st.stop()

order_map = dict(zip(ranking_keys['id_str'], ranking_keys['ranking']))
df_port['orden_ranking'] = df_port['id_str'].map(order_map)
df_port = df_port.sort_values('orden_ranking').reset_index(drop=True)
df_port = df_port.drop(columns=['id_str', 'orden_ranking'], errors='ignore')



def parse_project_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        st.error('No se puede registrar la evaluacion porque el identificador del proyecto no es numerico. Revisa la Fase 0.')
        st.stop()


def fmt_opt(identificador: int) -> str:
    fila = df_port.loc[df_port["id_innovacion"] == identificador]
    if fila.empty:
        return str(identificador)
    return f"{identificador} - {fila['nombre_innovacion'].values[0]}"


with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.markdown("### Selecciona un proyecto del portafolio maestro")
    ids = df_port["id_innovacion"].tolist()
    seleccion = st.selectbox("Proyecto", ids, format_func=fmt_opt)
    st.markdown("</div>", unsafe_allow_html=True)


project_id = parse_project_id(seleccion)

previous_project_id = st.session_state.get("fase2_last_project_id")
if previous_project_id is not None and previous_project_id != project_id:
    st.session_state["fase2_ready"] = False
    st.session_state.pop("fase2_payload", None)
st.session_state["fase2_last_project_id"] = project_id

selected_project = df_port.loc[df_port["id_innovacion"] == project_id].iloc[0]
impacto_txt = selected_project.get("impacto") or "No informado"
estado_txt = selected_project.get("estatus") or "Sin estado"
responsable_txt = selected_project.get("responsable_innovacion") or "Sin responsable asignado"
transferencia_txt = selected_project.get("potencial_transferencia") or "Sin potencial declarado"
evaluacion_val = selected_project.get("evaluacion_numerica")
evaluacion_txt = f"{float(evaluacion_val):.1f}" if pd.notna(evaluacion_val) else "—"

project_snapshot = {
    "id_innovacion": int(project_id),
    "nombre_innovacion": selected_project.get("nombre_innovacion", ""),
    "potencial_transferencia": transferencia_txt,
    "impacto": impacto_txt,
    "estatus": estado_txt,
    "responsable_innovacion": responsable_txt,
    "evaluacion_numerica": float(evaluacion_val) if pd.notna(evaluacion_val) else None,
}

selection_meta = [
    ("Impacto estratégico", impacto_txt),
    ("Estado actual", estado_txt),
    ("Responsable de innovación", responsable_txt),
    ("Evaluación Fase 0", evaluacion_txt),
]

meta_items_html = "".join(
    f"<div class='selection-card__meta-item'>"
    f"<span class='selection-card__meta-label'>{escape(label)}</span>"
    f"<span class='selection-card__meta-value'>{escape(str(value))}</span>"
    "</div>"
    for label, value in selection_meta
)

selection_card_html = f"""
<div class='selection-card'>
    <span class='selection-card__badge'>Proyecto seleccionado</span>
    <h3 class='selection-card__title'>{escape(selected_project['nombre_innovacion'])}</h3>
    <p class='selection-card__subtitle'>{escape(str(transferencia_txt))}</p>
    <div class='selection-card__meta'>
        {meta_items_html}
    </div>
</div>
"""

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.markdown(selection_card_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.markdown("### Evaluación IRL")
    st.caption(
        "Responde las preguntas de cada pestaña y acredita la evidencia para calcular automáticamente el nivel de madurez por dimensión."
    )
    _init_irl_state()
    badge_data: list[tuple[str, str, dict]] = []
    for dimension, _ in IRL_DIMENSIONS:
        counts = _compute_dimension_counts(dimension)
        badge = _dimension_badge(counts)
        badge_data.append((dimension, badge, counts))

    bubbles_html = "<div class='irl-bubbles'>"
    for dimension, badge, counts in badge_data:
        bubble_class = _dimension_badge_class(badge)
        bubbles_html += (
            "<div class='irl-bubble irl-bubble--"
            + bubble_class
            + "'>"
            + f"<span class='irl-bubble__label'>{dimension} ({DIMENSION_DESCRIPTIONS[dimension]})</span>"
            + f"<strong class='irl-bubble__badge'>{badge}</strong>"
            + f"<small>{counts['completed']}/{counts['total']} en cálculo</small>"
            + "</div>"
        )
    bubbles_html += "</div>"
    st.markdown(bubbles_html, unsafe_allow_html=True)

    tab_labels = [f"{dimension} ({DIMENSION_DESCRIPTIONS[dimension]}) · {badge}" for dimension, badge, _ in badge_data]
    tabs = st.tabs(tab_labels)
    for idx, (dimension, _, _) in enumerate(badge_data):
        with tabs[idx]:
            _render_dimension_tab(dimension)
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    df_respuestas = _collect_dimension_responses()
    detalles_dimensiones = _collect_dimension_details()
    with st.expander('Detalle de niveles por dimension', expanded=False):
        if df_respuestas.empty:
            st.info("Aún no hay niveles respondidos en esta evaluación.")

        if detalles_dimensiones:
            tab_labels = [
                f"{info['label']}" if info["label"] else dimension
                for dimension, info in detalles_dimensiones.items()
            ]
            st.markdown("**Preguntas y respuestas por dimensión**")
            tabs = st.tabs(tab_labels)
            for idx, (dimension, info) in enumerate(detalles_dimensiones.items()):
                with tabs[idx]:
                    detalle_df = pd.DataFrame(info["rows"])
                    if detalle_df.empty:
                        st.info("No hay niveles configurados para esta dimensión.")
                    else:
                        render_table(
                            detalle_df,
                            key=f'fase1_detalle_dimensiones_{dimension}',
                            include_actions=False,
                            hide_index=True,
                            page_size_options=(10, 25, 50),
                            default_page_size=10,
                        )
        else:
            st.warning("No se encontraron definiciones de niveles para las dimensiones IRL.")
    # Use cached puntaje when available; avoid recalculating on each rerun to improve responsiveness.
    puntaje = st.session_state.get("irl_last_puntaje")
    if puntaje is None and df_respuestas.empty:
        puntaje = None
    st.metric("Nivel IRL alcanzado", f"{puntaje:.1f}" if puntaje is not None else "-")

    col_guardar, col_ayuda = st.columns([1, 1])
    with col_guardar:
        finalize_clicked = st.button("Finalizar evaluación", type="primary")
        if finalize_clicked:
            # If we don't have a cached puntaje, compute it now (user-triggered expensive op)
            if puntaje is None and not df_respuestas.empty:
                try:
                    computed = trl.calcular_trl(df_respuestas[["dimension", "nivel", "evidencia"]])
                    st.session_state["irl_last_puntaje"] = computed
                    puntaje = computed
                except Exception:
                    st.session_state["irl_last_puntaje"] = None
                    puntaje = None

            if puntaje is None:
                st.info(
                    "La evaluación se guardará sin campos respondidos ni niveles acreditados para que puedas avanzar a la fase 2."
                )
            trl_value = float(puntaje) if puntaje is not None else None
            try:
                save_trl_result(
                    project_id,
                    df_respuestas[["dimension", "nivel", "evidencia"]],
                    trl_value,
                )
                _sync_all_scores()
                historial = get_trl_history(project_id)
                fecha_eval = historial["fecha_eval"].iloc[0] if not historial.empty else None
                responses_records = df_respuestas[["dimension", "nivel", "evidencia"]].to_dict("records")
                st.session_state["fase2_ready"] = True
                st.session_state["fase2_payload"] = {
                    "project_id": project_snapshot["id_innovacion"],
                    "project_snapshot": project_snapshot.copy(),
                    "responses": responses_records,
                    "irl_score": trl_value,
                    "fecha_eval": fecha_eval,
                }
                st.session_state["fase2_last_project_id"] = project_id
                if fase2_page:
                    st.switch_page(str(fase2_page))
                else:
                    st.success("Evaluacion guardada correctamente.")
                    _rerun_app()
            except Exception as error:
                st.error(f"Error al guardar: {error}")

        fase2_payload = st.session_state.get("fase2_payload")
        fase2_ready_for_project = (
            st.session_state.get("fase2_ready", False)
            and fase2_payload
            and fase2_payload.get("project_id") == project_id
        )
        go_fase2 = st.button(
            "Ir a Fase 2",
            key="btn_go_fase2",
            disabled=not fase2_ready_for_project,
        )
        if go_fase2:
            if fase2_page:
                st.switch_page(str(fase2_page))
            else:
                st.warning("La página de Fase 2 aún no está disponible.")

    with col_ayuda:
        st.info(
            "El guardado crea un registro por dimensión con las evidencias acreditadas y asocia el IRL global a la misma fecha de evaluación."
        )
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell section-shell--split'>", unsafe_allow_html=True)
    st.markdown("#### Radar IRL interactivo")
    radar_col_left, radar_col_right = st.columns([1.1, 1])
    with radar_col_left:
        st.caption("Los niveles mostrados se ajustan automáticamente según la evaluación registrada en las pestañas superiores.")
        _init_irl_state()
        radar_values = {}
        for dimension, _ in IRL_DIMENSIONS:
            valor = st.session_state["irl_scores"].get(dimension, 0)
            radar_values[dimension] = valor
        resumen_df = (
            pd.DataFrame(
                [
                    {"Dimensión": dimension, "Nivel": radar_values.get(dimension, 0)}
                    for dimension, _ in IRL_DIMENSIONS
                ]
            )
            .set_index("Dimensión")
        )
        with st.expander('Resumen numerico IRL', expanded=False):
            st.dataframe(
                resumen_df,
                use_container_width=True,
            )

    with radar_col_right:
        labels = list(radar_values.keys())
        values = list(radar_values.values())
        values_cycle = values + values[:1]
        theta = labels + labels[:1]
        radar_fig = go.Figure()
        radar_fig.add_trace(
            go.Scatterpolar(
                r=values_cycle,
                theta=theta,
                fill="toself",
                name="Perfil IRL",
                line_color="#3f8144",
                fillcolor="rgba(63, 129, 68, 0.25)",
            )
        )
        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 9])),
            template="plotly_white",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(radar_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
    st.subheader("Historial del proyecto")

    historial = get_trl_history(project_id)
    if historial.empty:
        st.warning("Aun no existe historial IRL para este proyecto.")
    else:
        ultimo_registro = historial["fecha_eval"].iloc[0]
        st.caption(f"Ultima evaluacion registrada: {ultimo_registro}")
        with st.expander('Historial de evaluaciones', expanded=False):
            render_table(
                historial,
                key='fase1_historial_trl',
                include_actions=True,
                hide_index=True,
            )

        datos_ultimo = historial[historial["fecha_eval"] == ultimo_registro].copy()
        pivot = datos_ultimo.groupby("dimension", as_index=False)["nivel"].mean()
        dimensiones_ids = trl.ids_dimensiones()
        dimensiones_labels = trl.labels_dimensiones()

        pivot["orden"] = pivot["dimension"].apply(lambda dim: dimensiones_ids.index(dim) if dim in dimensiones_ids else 999)
        pivot = pivot.sort_values("orden")
        valores = []
        for dim_id in dimensiones_ids:
            registro = pivot.loc[pivot["dimension"] == dim_id, "nivel"]
            valores.append(float(registro.values[0]) if len(registro) > 0 and pd.notna(registro.values[0]) else np.nan)

        angles = np.linspace(0, 2 * np.pi, len(dimensiones_labels), endpoint=False).tolist()
        valores_ciclo = valores + valores[:1]
        angulos_ciclo = angles + angles[:1]

        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"polar": True})
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles)
        ax.set_xticklabels(dimensiones_labels)
        ax.set_rlabel_position(0)
        ax.set_yticks([1, 3, 5, 7, 9])
        ax.set_ylim(0, 9)

        ax.plot(angulos_ciclo, valores_ciclo, linewidth=2, color="#3f8144")
        ax.fill(angulos_ciclo, valores_ciclo, alpha=0.25, color="#3f8144")

        st.pyplot(fig)

        st.download_button(
            "Descargar historial TRL (CSV)",
            data=historial.to_csv(index=False).encode("utf-8"),
            file_name=f"trl_historial_{seleccion}.csv",
            mime="text/csv",
        )
    st.markdown("</div>", unsafe_allow_html=True)
