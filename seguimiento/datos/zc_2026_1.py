"""Acuerdos de la Primera Sesión Ordinaria 2026 de la Zona Centro de la CNPJ (4 de agosto de 2026).

Fuente: documentos/1ª Sesión Ordinaria 2026 de la Zona Centro de la Conferencia Nacional de Procuración de Justicia.pdf

Mismo formato que ``liv_2026`` y se carga con ``manage.py cargar_acta zc_2026_1``.

Convenciones del campo ``entregas`` de cada compromiso:
    "zona"  -> se crea una Entrega por cada institución de ``GRUPOS_ENTREGA["zona"]``.
    None    -> el compromiso lo cumple solo el responsable.

El acta no fija plazos: los compromisos quedan sin fecha límite (semáforo gris) hasta que la ST los defina.
"""
from datetime import date

from .catalogos import zona
from .liv_2026 import C

REUNION = {
    "organo": ("ZC-CNPJ", "Zona Centro de la Conferencia Nacional de Procuración de Justicia"),
    "numero": 1,
    "numeral": "I",
    "anio": 2026,
    "nombre": "Primera Sesión Ordinaria 2026 de la Zona Centro de la Conferencia Nacional de Procuración de Justicia",
    "tipo": "ordinaria",
    "fecha": date(2026, 8, 4),
    "sede": "",
    "observaciones": (
        "El acta no indica sede ni modalidad. Integrantes de la Zona Centro (regionalización de la CNPJ): "
        "Ciudad de México, Estado de México, Hidalgo, Morelos, Puebla y Tlaxcala."
    ),
}

# Integrantes de la Zona Centro según el mapa de zonas de la CNPJ (catalogos.ZONAS).
GRUPOS_ENTREGA = {"zona": zona("Centro")}

TEMAS_NUEVOS = [("Violencia contra las mujeres", "#be185d")]

_ST_SIN_SUJETO = "El acuerdo instruye la acción sin nombrar responsable; se asignó a la ST como coordinadora."
_ST_COORDINA = ("La obligación recae en las instituciones de la Zona (explícito); se asignó a la ST la coordinación "
                "del seguimiento.")
_ZONA = " Una entrega por cada una de las 6 instituciones de la Zona Centro."
INFERIDOS = {
    (3, "2"): ("El acuerdo pide 'recabar su interés y disposición' sin plazo ni formato; se asignó a la ST y se "
               "pide a cada institución manifestarlo." + _ZONA),
    (5, "1"): _ST_SIN_SUJETO + " El acta dice 'las instituciones integrantes acuerdan'.",
    (5, "2"): _ST_COORDINA + _ZONA,
    (5, "3"): "'Se realizarán acciones de capacitación y certificación' sin sujeto; se asignó a la ST." + _ZONA,
    (6, "1"): _ST_COORDINA + " AIC y CFIC acompañan (explícito)." + _ZONA,
    (6, "2"): _ST_COORDINA + " AIC y CFIC acompañan (explícito)." + _ZONA,
    (6, "3"): _ST_COORDINA + " AIC y CFIC acompañan (explícito)." + _ZONA,
}

ACUERDOS = [
    {
        "numero": 1,
        "titulo": "Difusión del Programa de Identificación Humana",
        "naturaleza": "conocimiento",
        "temas": ["Servicios forenses", "Personas desaparecidas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "PRIMERO.- DIFUSIÓN DE LA INICIATIVA DEL PROGRAMA DE IDENTIFICACIÓN HUMANA. Las personas integrantes de "
            "la Zona Centro de la Conferencia Nacional de Procuración de Justicia tomaron conocimiento del "
            "\"Programa de Identificación Humana\", presentado ante este órgano colegiado como una herramienta "
            "orientada a fortalecer los procesos de identificación forense y contribuir a la localización y "
            "reconocimiento de personas. Considerando la relevancia de esta experiencia para el fortalecimiento de "
            "las capacidades institucionales en la materia, se instruye a la Secretaría Técnica de la Conferencia "
            "para que difunda dicho programa entre las instituciones que integran la Zona, a efecto de que puedan "
            "valorar su implementación, adaptación o réplica conforme a sus propias necesidades operativas."
        ),
        "compromisos": [
            C("1", "Difundir el Programa de Identificación Humana entre las instituciones de la Zona Centro, para que "
                   "valoren su implementación, adaptación o réplica.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Oficio de difusión a las instituciones de la Zona Centro"),
        ],
    },
    {
        "numero": 2,
        "titulo": "Divulgación del proyecto \"Centros Libre Casas Carmen Serdán\"",
        "naturaleza": "conocimiento",
        "temas": ["Violencia contra las mujeres"],
        "responsable": "ST-CNPJ",
        "texto": (
            "SEGUNDO.- DIVULGACIÓN DEL PROYECTO \"CENTROS LIBRE CASAS CARMEN SERDÁN\". Las personas titulares "
            "integrantes de la Zona Centro de la Conferencia Nacional de Procuración de Justicia tomamos "
            "conocimiento de la presentación \"Centros Libre Casas Carmen Serdán\", como una política pública que "
            "incorpora la investigación y persecución del delito en los espacios destinados a la atención integral "
            "de mujeres víctimas de violencia. En consecuencia, se acuerda que la Secretaría Técnica difunda el "
            "presente modelo, entre las y los integrantes de Zona, a fin de garantizar protección, atención "
            "integral y acceso efectivo a la justicia para las mujeres en situación de violencia."
        ),
        "compromisos": [
            C("1", "Difundir el modelo \"Centros Libre Casas Carmen Serdán\" entre las y los integrantes de la Zona "
                   "Centro.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Oficio de difusión a las instituciones de la Zona Centro"),
        ],
    },
    {
        "numero": 3,
        "titulo": "Red Nacional de Interoperabilidad Tecnológica y Buenas Prácticas en las Fiscalías",
        "naturaleza": "conocimiento",
        "temas": ["Innovación tecnológica"],
        "responsable": "ST-CNPJ",
        "texto": (
            "TERCERO.- IMPULSO A LA \"RED NACIONAL DE INTEROPERABILIDAD TECNOLÓGICA Y BUENAS PRÁCTICAS EN LAS "
            "FISCALÍAS\". Las personas integrantes de la Zona Centro toman conocimiento de la propuesta para la "
            "creación de la Red Nacional de Interoperabilidad Tecnológica y Buenas Prácticas, iniciativa orientada "
            "al fortalecimiento de las capacidades sustantivas de las fiscalías mediante el intercambio de "
            "información, la homologación de criterios técnicos y la adopción conjunta de soluciones tecnológicas "
            "que faciliten la comunicación entre instituciones. Por lo anterior, se solicita a la Secretaría "
            "Técnica de la Conferencia dar a conocer dicha iniciativa entre las instituciones que integran la "
            "Zona, a fin de recabar su interés y disposición para sumarse a este esfuerzo conjunto."
        ),
        "compromisos": [
            C("1", "Dar a conocer la iniciativa de la Red Nacional de Interoperabilidad Tecnológica y Buenas "
                   "Prácticas entre las instituciones de la Zona Centro.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Oficio de difusión a las instituciones de la Zona Centro"),
            C("2", "Manifestar el interés y la disposición de la institución para sumarse a la Red.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Oficio de respuesta de cada institución", entregas="zona"),
        ],
    },
    {
        "numero": 4,
        "titulo": "Socialización de las estrategias en materia de búsqueda de personas",
        "naturaleza": "conocimiento",
        "temas": ["Personas desaparecidas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "CUARTO.- SOCIALIZACIÓN DE LAS ESTRATEGIAS EN MATERIA DE BÚSQUEDA DE PERSONAS. Las personas integrantes "
            "de la Zona Centro de la Conferencia Nacional de Procuración de Justicia tomaron conocimiento de las "
            "estrategias expuestas en materia de búsqueda de personas, las cuales comprenden acciones de "
            "coordinación interinstitucional, protocolos de actuación inmediata y mecanismos de vinculación con "
            "las familias de personas desaparecidas. Dichas estrategias fueron presentadas como un esfuerzo por "
            "robustecer la respuesta institucional ante este fenómeno y por generar resultados más efectivos en la "
            "localización de personas. Con base en lo anterior, se acuerda que la Secretaría Técnica de la "
            "Conferencia comparta dichas estrategias con las instituciones integrantes de la Zona, a fin de "
            "fortalecer su implementación conjunta y promover la adopción de acciones coordinadas entre las "
            "fiscalías."
        ),
        "compromisos": [
            C("1", "Compartir las estrategias en materia de búsqueda de personas con las instituciones de la Zona "
                   "Centro.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Oficio de envío de las estrategias a la Zona Centro"),
        ],
    },
    {
        "numero": 5,
        "titulo": "Actualización del Protocolo Homologado de Investigación en materia de personas desaparecidas",
        "naturaleza": "compromiso",
        "temas": ["Personas desaparecidas", "Capacitación"],
        "responsable": "ST-CNPJ",
        "texto": (
            "QUINTO.- ACTUALIZACIÓN DEL PROTOCOLO HOMOLOGADO DE INVESTIGACIÓN EN MATERIA DE PERSONAS DESAPARECIDAS. "
            "Las instituciones integrantes acuerdan dar continuidad al proceso de actualización del Protocolo "
            "Homologado de Investigación, así como impulsar el fortalecimiento de las Fiscalías en materia de "
            "Búsqueda e Investigación de Personas Desaparecidas, a fin de garantizar la aplicación uniforme de "
            "criterios, técnicas y estándares de investigación. Asimismo, se realizarán acciones de capacitación y "
            "certificación, en la materia."
        ),
        "compromisos": [
            C("1", "Dar continuidad al proceso de actualización del Protocolo Homologado de Investigación.",
              "ST-CNPJ", plazo="Sin plazo en el acta", entregable="Versión actualizada del PHI"),
            C("2", "Impulsar el fortalecimiento de la fiscalía en materia de búsqueda e investigación de personas "
                   "desaparecidas.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Reporte de acciones de fortalecimiento", entregas="zona"),
            C("3", "Realizar acciones de capacitación y certificación en materia de búsqueda e investigación de "
                   "personas desaparecidas.", "ST-CNPJ",
              plazo="Sin plazo en el acta", entregable="Reporte de personas capacitadas y certificadas",
              entregas="zona"),
        ],
    },
    {
        "numero": 6,
        "titulo": "Diagnóstico de capacidades forenses (Banco Nacional de Datos Forenses y Registros Nacionales Forenses)",
        "naturaleza": "compromiso",
        "temas": ["Servicios forenses", "Personas desaparecidas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "SEXTO.- DIAGNÓSTICO DE CAPACIDADES FORENSES (BANCO NACIONAL DE DATOS FORENSES Y REGISTROS NACIONALES "
            "FORENSES). Las y los integrantes de la Zona Centro de la Conferencia refrendamos nuestro compromiso con "
            "la Estrategia Nacional de Búsqueda de Personas, fortaleciendo la coordinación e intercambio de "
            "información entre instituciones de procuración de justicia. En consecuencia, acordamos: 1. Designar a "
            "las personas servidoras públicas que fungirán como usuarios institucionales para concluir su "
            "credencialización y acceso a la plataforma del Banco Nacional de Datos Forenses. 2. Integrar y "
            "mantener actualizada la información, además, designar enlaces institucionales responsables de la "
            "captura, validación y actualización permanente de los Registros Nacionales Forenses. 3. Continuar con "
            "la recopilación, validación y entrega de información, mediante enlaces institucionales, para "
            "consolidar el Diagnóstico Nacional de Capacidades Forenses a través del Sistema Integral de "
            "Capacidades Forenses (SICAF). La Fiscalía General de la República, a través de la Agencia de "
            "Investigación Criminal y el Centro Federal de Inteligencia Criminal, brindará acompañamiento técnico "
            "para la implementación de estos compromisos, en coordinación con las Fiscalías y Procuradurías "
            "estatales."
        ),
        "compromisos": [
            C("1", "Designar a las personas servidoras públicas que fungirán como usuarios institucionales y "
                   "concluir su credencialización y acceso a la plataforma del Banco Nacional de Datos Forenses.",
              "ST-CNPJ", ["AIC", "CFIC"], plazo="Sin plazo en el acta",
              entregable="Oficio de designación de usuarios del BNDF y credenciales emitidas", entregas="zona"),
            C("2", "Designar enlaces institucionales responsables de la captura, validación y actualización "
                   "permanente de los Registros Nacionales Forenses, y mantener actualizada la información.",
              "ST-CNPJ", ["AIC", "CFIC"], plazo="Sin plazo en el acta",
              entregable="Oficio de designación de enlaces de los Registros Nacionales Forenses", entregas="zona"),
            C("3", "Continuar con la recopilación, validación y entrega de información para consolidar el "
                   "Diagnóstico Nacional de Capacidades Forenses a través del SICAF.",
              "ST-CNPJ", ["AIC", "CFIC"], plazo="Sin plazo en el acta",
              entregable="Información validada y entregada en el SICAF", entregas="zona"),
        ],
    },
    {
        "numero": 7,
        "titulo": "Designación de la persona representante de la Zona Centro",
        "naturaleza": "aprueba",
        "temas": [],
        "responsable": "FGJCDMX",
        "texto": (
            "SÉPTIMO.- DESIGNACIÓN DE LA PERSONA REPRESENTANTE DE LA ZONA CENTRO. Las personas integrantes de la "
            "Zona Centro de la Conferencia Nacional de Procuración de Justicia, por consenso, designamos a la "
            "Maestra Bertha María Alcalde Luján, Fiscal General de Justicia de la Ciudad de México como "
            "Representante de la Zona, de conformidad con lo dispuesto en los artículos 35 y 43, fracción IV de los "
            "Estatutos de la Conferencia Nacional de Procuración de Justicia."
        ),
        # La designación surte efecto en la propia sesión: no genera compromisos pendientes (el acuerdo queda cumplido).
        "compromisos": [],
    },
]
