"""Acuerdos de la LIV Asamblea Plenaria de la CNPJ (2026), desglosados en compromisos.

Convenciones del campo ``entregas``:
    "estatales" -> se crea una Entrega por cada una de las 32 fiscalías/procuradurías.
    "pleno"     -> las 32 estatales + FGR (todas las instancias integrantes del Pleno).
    None        -> el compromiso lo cumple solo el responsable.

``fecha = UN_MES`` significa "un mes contado a partir de la sesión"; se calcula
con la fecha que se pase a ``cargar_liv --fecha``.
"""
from datetime import date

UN_MES = "un_mes"

REUNION = {
    "organo": ("CNPJ", "Conferencia Nacional de Procuración de Justicia"),
    "numero": 54,
    "numeral": "LIV",
    "nombre": "LIV Asamblea Plenaria de la Conferencia Nacional de Procuración de Justicia",
    "tipo": "ordinaria",
}

# Compromisos cuyo responsable NO está nombrado en el texto del acuerdo y se asignó por inferencia.
# Se cargan con responsable_validado=False para que la Secretaría Técnica los confirme o corrija.
_ST_SIN_SUJETO = "El acuerdo instruye la acción sin nombrar responsable; se asignó a la ST como coordinadora."
_ST_COORDINA = "La obligación recae en las fiscalías (explícito); se asignó a la ST la coordinación del seguimiento."
INFERIDOS = {
    (1, "a"): _ST_SIN_SUJETO, (1, "b"): _ST_SIN_SUJETO, (1, "c"): _ST_SIN_SUJETO,
    (1, "d"): "El acuerdo no dice quién publica en el DOF; se asignó a la ST con la FGR como corresponsable.",
    (2, "2"): "Acción derivada (las fiscalías aportan prácticas); el texto solo instruye a la ST crear el mecanismo.",
    (4, "a"): _ST_SIN_SUJETO, (4, "b"): _ST_SIN_SUJETO, (4, "c"): _ST_SIN_SUJETO,
    (4, "d"): "El acuerdo no dice quién publica en el DOF; se asignó a la ST con la FGR como corresponsable.",
    (5, "3"): "Se instruye instalar la mesa 'con el CFIC' sin decir quién la convoca; se asignó al CFIC.",
    (6, "1"): _ST_SIN_SUJETO, (6, "2"): _ST_SIN_SUJETO + " CFPF como corresponsable (inferido).",
    (6, "3"): _ST_SIN_SUJETO,
    (8, "2"): _ST_COORDINA,
    (9, "1"): "El texto no dice quién recaba la CURP; se infiere que las fiscalías reportan y el SESNSP coordina.",
    (9, "2"): "El texto dice 'para que sea compartida' sin sujeto; se asignó al SESNSP, que recibe la información.",
    (11, "1"): _ST_COORDINA + " SESNSP como corresponsable por administrar el registro (inferido).",
    (12, "1"): _ST_COORDINA + " FGR como corresponsable por la 'coordinación con la Federación'.",
    (13, "1"): "La elaboración es conjunta de FEMDH, CFIC, CFPF y FGJCDMX; se designó a FEMDH como líder (inferido).",
    (14, "1"): _ST_COORDINA,
    (15, "3"): "El texto no dice quién aprueba y publica; se asignó a la ST con CFPF y UNAM como corresponsables.",
    (16, "3a"): "El acuerdo menciona un 'grupo técnico' sin integrarlo; se asignó a FECOR, que presentó la propuesta.",
    (17, "1"): "'Se acuerda tener una reunión' sin organizador; se asignó a la ST.",
    (17, "2"): "'Se acuerda someter' sin sujeto; se asignó a la ST con la FGR como corresponsable.",
    (18, "2"): _ST_COORDINA,
}


def C(inciso, descripcion, responsable, corresponsables=(), fecha=None, plazo="", entregable="", entregas=None):
    return {
        "inciso": inciso, "descripcion": descripcion, "responsable": responsable,
        "corresponsables": corresponsables, "fecha": fecha, "plazo": plazo,
        "entregable": entregable, "entregas": entregas,
    }


ACUERDOS = [
    {
        "numero": 1,
        "titulo": "Protocolo Homologado de Investigación (PHI) en materia de desaparición — versión actualizada",
        "naturaleza": "aprueba",
        "temas": ["Personas desaparecidas", "Capacitación"],
        "responsable": "ST-CNPJ",
        "texto": (
            "Las y los integrantes de la Conferencia Nacional de Procuración de Justicia refrendamos nuestro "
            "compromiso con la Estrategia Nacional de Búsqueda de Personas; por lo que aprobamos la versión "
            "actualizada del Protocolo Homologado de Investigación (PHI) en materia de Desaparición Forzada de "
            "Personas y desaparición cometida por particulares; se instruye: a) su difusión; b) observancia "
            "obligatoria, c) la capacitación y certificación del personal ministerial, pericial, analista y "
            "policial, y d) la publicación del protocolo en el Diario Oficial de la Federación."
        ),
        "compromisos": [
            C("a", "Difundir el PHI actualizado entre las instituciones de procuración de justicia.", "ST-CNPJ",
              entregable="Oficio de difusión a las 33 instituciones"),
            C("b", "Acreditar la adopción del PHI como instrumento de observancia obligatoria.", "ST-CNPJ",
              entregable="Acuerdo o circular interna de adopción", entregas="estatales"),
            C("c", "Capacitar y certificar al personal ministerial, pericial, analista y policial en el PHI.", "ST-CNPJ",
              entregable="Reporte de personas capacitadas y certificadas", entregas="estatales"),
            C("d", "Publicar el PHI actualizado en el Diario Oficial de la Federación.", "ST-CNPJ", ["FGR"],
              entregable="Referencia de publicación en el DOF"),
        ],
    },
    {
        "numero": 2,
        "titulo": "Diagnóstico de Fiscalías Especializadas en Personas Desaparecidas y mecanismo de buenas prácticas",
        "naturaleza": "conocimiento",
        "temas": ["Personas desaparecidas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia tiene por analizado el Diagnóstico de Fiscalías "
            "Especializadas en materia de Personas Desaparecidas; sus hallazgos orientarán las acciones para el "
            "fortalecimiento institucional de las fiscalías y procuradurías generales de justicia, se instruye a "
            "la Secretaría Técnica establecer un mecanismo para recopilar y compartir las buenas prácticas de las "
            "32 instituciones de procuración de justicia con la participación activa de la Fiscalía General de "
            "Justicia de la Ciudad de México."
        ),
        "compromisos": [
            C("1", "Establecer el mecanismo para recopilar y compartir buenas prácticas de las 32 instituciones.",
              "ST-CNPJ", ["FGJCDMX"], entregable="Mecanismo / repositorio de buenas prácticas operando"),
            C("2", "Aportar buenas prácticas de la fiscalía especializada al mecanismo.", "ST-CNPJ",
              entregable="Ficha de buena práctica", entregas="estatales"),
        ],
    },
    {
        "numero": 3,
        "titulo": "Exhorto presupuestal 2027 — Fiscalías Especializadas en Personas Desaparecidas",
        "naturaleza": "exhorto",
        "temas": ["Personas desaparecidas", "Presupuesto"],
        "responsable": "ST-CNPJ",
        "texto": (
            "El Pleno de la Conferencia aprueba la emisión de un Exhorto a las personas titulares de los Poderes "
            "Ejecutivos y a las Presidencias de las Mesas Directivas del Congreso de la Unión y los Congresos "
            "locales, para prever, aprobar partidas específicas y etiquetadas en los Presupuestos de Egresos 2027 "
            "destinadas al fortalecimiento de las Fiscalías Especializadas en materia de Personas Desaparecidas "
            "para el cumplimiento de la Estrategia Nacional de Búsqueda de Personas. La Secretaría Técnica "
            "comunicará el exhorto y dará seguimiento a su atención."
        ),
        "compromisos": [
            C("1", "Comunicar el exhorto a los Poderes Ejecutivos y a las Mesas Directivas del Congreso de la Unión "
                   "y de los Congresos locales.", "ST-CNPJ", entregable="Oficios de comunicación del exhorto"),
            C("2", "Dar seguimiento a la atención del exhorto en los Presupuestos de Egresos 2027.", "ST-CNPJ",
              fecha=date(2026, 12, 31), plazo="Aprobación de los presupuestos 2027",
              entregable="Reporte de partidas etiquetadas por entidad"),
        ],
    },
    {
        "numero": 4,
        "titulo": "Protocolo Homologado para delitos contra Personas Defensoras de Derechos Humanos — versión actualizada",
        "naturaleza": "aprueba",
        "temas": ["Personas defensoras de DD.HH.", "Capacitación"],
        "responsable": "ST-CNPJ",
        "texto": (
            "El Pleno de la Conferencia aprueba la versión actualizada del Protocolo Homologado Especializado para "
            "la investigación de delitos cometidos contra las Personas Defensoras de Derechos Humanos. Se instruye: "
            "a) su difusión, b) observancia obligatoria, c) la capacitación del personal ministerial, pericial y "
            "policial y d) publicación en el Diario Oficial de la Federación."
        ),
        "compromisos": [
            C("a", "Difundir el Protocolo actualizado.", "ST-CNPJ", entregable="Oficio de difusión"),
            C("b", "Acreditar la adopción del Protocolo como instrumento de observancia obligatoria.", "ST-CNPJ",
              entregable="Acuerdo o circular interna de adopción", entregas="estatales"),
            C("c", "Capacitar al personal ministerial, pericial y policial en el Protocolo.", "ST-CNPJ",
              entregable="Reporte de personas capacitadas", entregas="estatales"),
            C("d", "Publicar el Protocolo actualizado en el Diario Oficial de la Federación.", "ST-CNPJ", ["FGR"],
              entregable="Referencia de publicación en el DOF"),
        ],
    },
    {
        "numero": 5,
        "titulo": "Informe de avances del Banco Nacional de Datos Forenses y mesa de revisión de campos",
        "naturaleza": "aprueba",
        "temas": ["Servicios forenses", "Personas desaparecidas"],
        "responsable": "FGR",
        "texto": (
            "Las y los integrantes de la Conferencia Nacional de Procuración de Justicia aprueban que la Fiscalía "
            "General de la República, con información que proporcionen las Fiscalías y Procuradurías Locales al "
            "Centro Federal de Inteligencia Criminal, rendirá un informe de seguimiento de avances para la "
            "Conferencia, relativo a los conceptos integrados en el Banco Nacional de Datos Forenses, que "
            "comprenderá el avance de registros en fuentes nacionales criminales y forenses, siendo: 1) Registro "
            "Nacional del Delito de Tortura (RENADET); 2) Base Nacional de Información Genética (BaNIG); 3) "
            "Registro Forense Federal (REFOFE); 4) Registro Nacional de Fosas Comunes y Fosas Clandestinas "
            "(RENAFO); y 5) Registro Nacional de Personas Fallecidas no Identificadas y no Reclamadas (RENAPEFA); "
            "así como el estado de la carga de información por las treinta y dos entidades federativas, los "
            "usuarios autorizados, la trazabilidad de los registros y la operación de la mesa de ayuda, se "
            "instruye instalar una mesa de revisión de campos de todos los registros nacionales forenses con el "
            "Centro Federal de Inteligencia Criminal."
        ),
        "compromisos": [
            C("1", "Proporcionar al CFIC la información de carga en RENADET, BaNIG, REFOFE, RENAFO y RENAPEFA.",
              "CFIC", entregable="Corte de carga por registro", entregas="estatales"),
            C("2", "Rendir a la Conferencia el informe de seguimiento del Banco Nacional de Datos Forenses (avance "
                   "por registro y entidad, usuarios autorizados, trazabilidad y mesa de ayuda).", "FGR", ["CFIC"],
              entregable="Informe de seguimiento BNDF"),
            C("3", "Instalar la mesa de revisión de campos de todos los registros nacionales forenses.", "CFIC",
              ["ST-CNPJ"], entregable="Minuta de instalación y calendario de la mesa"),
        ],
    },
    {
        "numero": 6,
        "titulo": "Diagnóstico del Sistema Integral de Capacidades Forenses (SICAF) y Plan de Trabajo",
        "naturaleza": "conocimiento",
        "temas": ["Servicios forenses"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia, toma conocimiento del Diagnóstico del Sistema "
            "Integral de Capacidades Forenses (SICAF), y se instruye continuar con la carga de información, el "
            "análisis de los resultados identificados, con miras a conformar un Plan de Trabajo para el "
            "fortalecimiento de capacidades forenses de las fiscalías; el instrumento considerará un cronograma de "
            "acciones, indicadores de cobertura y la elaboración de informes periódicos a la Conferencia como "
            "mecanismos permanentes de evaluación y transparencia."
        ),
        "compromisos": [
            C("1", "Continuar y completar la carga de información en el SICAF.", "ST-CNPJ",
              entregable="Carga completa en SICAF", entregas="estatales"),
            C("2", "Analizar resultados y conformar el Plan de Trabajo de fortalecimiento de capacidades forenses "
                   "(cronograma de acciones e indicadores de cobertura).", "ST-CNPJ", ["CFPF"],
              entregable="Plan de Trabajo SICAF"),
            C("3", "Presentar informes periódicos de avance del Plan a la Conferencia.", "ST-CNPJ",
              plazo="Periódico (cada sesión plenaria)", entregable="Informe periódico"),
        ],
    },
    {
        "numero": 7,
        "titulo": "Manual de operación contra la extorsión y exhorto presupuestal 2027",
        "naturaleza": "conocimiento",
        "temas": ["Extorsión", "Presupuesto"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia tiene por presentado el Manual de operación de las "
            "fiscalías o unidades especializadas para la recepción de denuncias, investigación y persecución del "
            "delito de extorsión elaborado por la Fiscalía General de la República en el mes de febrero del 2026; "
            "del cual toma conocimiento el Pleno. Se acuerda instruir a la Secretaría Técnica a recibir "
            "comentarios, observaciones al Manual y propuestas de actividades a realizar para atender el combate al "
            "delito de extorsión a más tardar el último día hábil del mes de agosto del 2026.\n\n"
            "Asimismo, el Pleno de la Conferencia aprueba la emisión de un Exhorto a las personas titulares de los "
            "Poderes Ejecutivos y a las Presidencias de las Mesas Directivas del Congreso de la Unión y los "
            "Congresos locales, para prever, aprobar partidas específicas y etiquetadas en los Presupuestos de "
            "Egresos 2027 destinadas al fortalecimiento de las Fiscalías Especializadas en materia de combate al "
            "delito de extorsión. La Secretaría Técnica comunicará el exhorto y dará seguimiento a su atención."
        ),
        "compromisos": [
            C("1", "Enviar comentarios y observaciones al Manual, así como propuestas de actividades contra la "
                   "extorsión.", "ST-CNPJ", fecha=date(2026, 8, 31), plazo="Último día hábil de agosto de 2026",
              entregable="Oficio con observaciones y propuestas", entregas="pleno"),
            C("2", "Comunicar el exhorto presupuestal en materia de extorsión.", "ST-CNPJ",
              entregable="Oficios de comunicación del exhorto"),
            C("3", "Dar seguimiento a la atención del exhorto en los Presupuestos de Egresos 2027.", "ST-CNPJ",
              fecha=date(2026, 12, 31), plazo="Aprobación de los presupuestos 2027",
              entregable="Reporte de partidas etiquetadas por entidad"),
        ],
    },
    {
        "numero": 8,
        "titulo": "Modificaciones a la Metodología del RNID y ampliación del catálogo de delitos",
        "naturaleza": "conocimiento",
        "temas": ["Estadística e incidencia"],
        "responsable": "ST-CNPJ",
        "texto": (
            "El Pleno toma conocimiento del proyecto de modificaciones a la Metodología del Registro Nacional de "
            "Incidencia Delictiva (RNID) y de la ampliación propuesta al catálogo de delitos; se instruye a la "
            "Secretaría Técnica remitirlo a las fiscalías y procuradurías, para que sea revisado y se formulen las "
            "observaciones y comentarios que se considere pertinente, a efecto de que el Secretariado Ejecutivo del "
            "Sistema Nacional de Seguridad Pública elabore la versión final."
        ),
        "compromisos": [
            C("1", "Remitir el proyecto de metodología del RNID y del catálogo ampliado a fiscalías y procuradurías.",
              "ST-CNPJ", entregable="Oficio de remisión"),
            C("2", "Revisar el proyecto y formular observaciones.", "ST-CNPJ",
              entregable="Oficio de observaciones", entregas="estatales"),
            C("3", "Elaborar la versión final de la metodología del RNID.", "SESNSP", ["ST-CNPJ"],
              entregable="Metodología RNID versión final"),
        ],
    },
    {
        "numero": 9,
        "titulo": "CURP de víctimas directas de feminicidio en el reporte del RNID (orfandad por feminicidio)",
        "naturaleza": "aprueba",
        "temas": ["Feminicidio", "Estadística e incidencia"],
        "responsable": "SESNSP",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia aprueba las modificaciones realizadas a la "
            "metodología de reporte del Registro Nacional de Incidencia Delictiva, a fin de garantizar el interés "
            "supremo de la niñez, por regla de excepción, recabar la Clave Única de Registro de Población (CURP) de "
            "las víctimas directas de feminicidio, y remitirla al Secretariado Ejecutivo del Sistema Nacional de "
            "Seguridad Pública en los reportes de incidencia delictiva, para que sea compartida con las instancias "
            "responsables del Registro Nacional de NNA en situación de orfandad por feminicidio."
        ),
        "compromisos": [
            C("1", "Recabar la CURP de las víctimas directas de feminicidio e incluirla en los reportes de "
                   "incidencia delictiva al SESNSP.", "SESNSP", plazo="Reporte mensual de incidencia",
              entregable="Reporte RNID con CURP", entregas="estatales"),
            C("2", "Compartir la información con las instancias responsables del Registro Nacional de NNA en "
                   "situación de orfandad por feminicidio.", "SESNSP", entregable="Mecanismo de intercambio operando"),
        ],
    },
    {
        "numero": 10,
        "titulo": "Mesas Técnicas para criterios del BANCI en materia de personas desaparecidas",
        "naturaleza": "aprueba",
        "temas": ["Personas desaparecidas", "Estadística e incidencia"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional aprueba la constitución de Mesas de Trabajo Técnicas, coordinadas "
            "conjuntamente entre la Secretaría Técnica de la CNPJ y el SESNSP para que, en un plazo de un mes, se "
            "definan los criterios operativos y el universo de carpetas de investigación a reportar en la Base "
            "Nacional de Carpetas de Investigación (BANCI) en materia de personas desaparecidas."
        ),
        "compromisos": [
            C("1", "Constituir las Mesas de Trabajo Técnicas ST-CNPJ / SESNSP.", "ST-CNPJ", ["SESNSP"],
              entregable="Minuta de instalación"),
            C("2", "Definir los criterios operativos y el universo de carpetas a reportar en el BANCI (personas "
                   "desaparecidas).", "ST-CNPJ", ["SESNSP"], fecha=UN_MES, plazo="Un mes a partir de la sesión",
              entregable="Documento de criterios operativos BANCI"),
        ],
    },
    {
        "numero": 11,
        "titulo": "Actualización del Registro Nacional de Personal de Seguridad Pública",
        "naturaleza": "compromiso",
        "temas": ["Estadística e incidencia"],
        "responsable": "ST-CNPJ",
        "texto": (
            "Las Procuradurías y Fiscalías Generales de las 32 entidades federativas reconocen que el Registro "
            "Nacional de Personal de Seguridad Pública constituye una herramienta para identificar a toda persona "
            "que desempeña funciones dentro de alguna institución de seguridad pública y procuración de justicia en "
            "los ámbitos federal, estatal o municipal y acuerdan actualizar la información de éste, a más tardar el "
            "último día hábil del presente año, para fortalecer el análisis del estado de fuerza de las "
            "instituciones de procuración de justicia."
        ),
        "compromisos": [
            C("1", "Actualizar la información del Registro Nacional de Personal de Seguridad Pública.", "ST-CNPJ",
              ["SESNSP"], fecha=date(2026, 12, 31), plazo="Último día hábil de 2026",
              entregable="Constancia de actualización del RNPSP", entregas="estatales"),
        ],
    },
    {
        "numero": 12,
        "titulo": "Iniciativa de Ley General para prevenir, investigar y sancionar el feminicidio",
        "naturaleza": "conocimiento",
        "temas": ["Feminicidio", "Reformas legislativas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "El pleno tiene por presentada la iniciativa de Ley General para prevenir, investigar y sancionar el "
            "delito de feminicidio, para que con ello las fiscalías y procuradurías identifiquen las acciones y "
            "necesidades que deberán atender para la implementación de la Ley, favoreciendo el intercambio de "
            "experiencias y la coordinación con la Federación."
        ),
        "compromisos": [
            C("1", "Identificar las acciones y necesidades institucionales para implementar la Ley General de "
                   "feminicidio.", "ST-CNPJ", ["FGR"], entregable="Diagnóstico de necesidades de implementación",
              entregas="estatales"),
        ],
    },
    {
        "numero": 13,
        "titulo": "Guía Práctica en temas forenses relacionados con búsqueda de personas",
        "naturaleza": "conocimiento",
        "temas": ["Servicios forenses", "Personas desaparecidas"],
        "responsable": "FEMDH",
        "texto": (
            "El Pleno toma de conocimiento del inicio de la elaboración de la Guía Práctica en temas forenses "
            "relacionados con búsqueda de personas, coordinado conjuntamente entre la Fiscalía Especializada en "
            "materia de Derechos Humanos, el Centro Federal de Inteligencia Criminal, el Centro Federal Pericial "
            "Forense y la Fiscalía General de Justicia de la Ciudad de México; una vez que se cuente con la guía, "
            "se compartirá a través de la Secretaría Técnica con las Fiscalías y Procuradurías Generales de "
            "Justicia para sus observaciones, aprobación e implementación."
        ),
        "compromisos": [
            C("1", "Elaborar la Guía Práctica en temas forenses relacionados con búsqueda de personas.", "FEMDH",
              ["CFIC", "CFPF", "FGJCDMX"], entregable="Proyecto de Guía Práctica"),
            C("2", "Compartir la Guía con fiscalías y procuradurías para observaciones, aprobación e implementación.",
              "ST-CNPJ", entregable="Oficio de remisión y compilado de observaciones"),
        ],
    },
    {
        "numero": 14,
        "titulo": "Difusión de la oferta educativa del INACIPE y propuesta de capacitación en extorsión",
        "naturaleza": "compromiso",
        "temas": ["Capacitación", "Extorsión"],
        "responsable": "INACIPE",
        "texto": (
            "Las fiscalías y procuradurías difundirán la oferta educativa del Instituto Nacional de Ciencias "
            "Penales entre su personal, como apoyo a los procesos de profesionalización. El Instituto presentará a "
            "la Secretaría Técnica una propuesta de capacitación y certificación en materia de extorsión."
        ),
        "compromisos": [
            C("1", "Difundir la oferta educativa del INACIPE entre el personal.", "ST-CNPJ",
              entregable="Evidencia de difusión interna", entregas="estatales"),
            C("2", "Presentar a la Secretaría Técnica una propuesta de capacitación y certificación en extorsión.",
              "INACIPE", ["ST-CNPJ"], entregable="Propuesta de programa de capacitación y certificación"),
        ],
    },
    {
        "numero": 15,
        "titulo": "Guías de Valoración de la Prueba Pericial (CFPF–UNAM)",
        "naturaleza": "conocimiento",
        "temas": ["Servicios forenses"],
        "responsable": "ST-CNPJ",
        "texto": (
            "El Pleno da por recibido el proyecto de las Guías de Valoración de la Prueba Pericial, elaboradas por "
            "el Centro Federal Pericial Forense y la Universidad Nacional Autónoma de México en materia de: a) "
            "identificación facial forense, b) entomología, c) química forense (con énfasis en fentanilo), y d) "
            "medicina forense (mecánica y certificación de lesiones). La Secretaría Técnica enviará el proyecto a "
            "las instancias integrantes del pleno para sus posteriores observaciones, aprobación y próxima "
            "publicación."
        ),
        "compromisos": [
            C("1", "Enviar el proyecto de Guías a las instancias integrantes del Pleno.", "ST-CNPJ",
              entregable="Oficio de remisión"),
            C("2", "Formular observaciones a las Guías de Valoración de la Prueba Pericial.", "ST-CNPJ",
              entregable="Oficio de observaciones", entregas="pleno"),
            C("3", "Someter a aprobación y publicar las Guías.", "ST-CNPJ", ["CFPF", "UNAM"],
              entregable="Guías aprobadas y publicadas"),
        ],
    },
    {
        "numero": 16,
        "titulo": "Reforma al CNPP — Fortalecimiento del Sistema de Justicia Penal Acusatorio",
        "naturaleza": "aprueba",
        "temas": ["Reformas legislativas"],
        "responsable": "PRES-CNPJ",
        "texto": (
            "El Pleno de la Conferencia toma conocimiento de las temáticas que integran la propuesta de reforma al "
            "Código Nacional de Procedimientos Penales en materia de Fortalecimiento del Sistema de Justicia Penal "
            "Acusatorio presentada por la persona titular de la Fiscalía Especializada de Control Regional, por lo "
            "que acuerda:\n"
            "1) La necesidad de impulsar una reforma al Código Nacional de Procedimientos Penales que mejore el "
            "Sistema de Justicia Penal Acusatorio sobre los temas propuestos por la Fiscalía General de la "
            "República; en particular, en cuanto a detenciones en flagrancia y casos urgentes, cateos, prueba "
            "anticipada, aseguramientos y productos de inteligencia;\n"
            "2) Los integrantes del Pleno se comprometen a hacer llegar a la Secretaría Técnica comentarios y "
            "observaciones a las propuestas de reforma, a más tardar el día 31 de agosto del 2026;\n"
            "3) Una vez integradas las observaciones y comentarios señalados en el punto anterior en un solo "
            "documento por parte del grupo técnico, la Presidencia, a través de la Secretaría Técnica, convocará a "
            "una sesión plenaria que se celebrará de forma virtual a mediados del mes de septiembre del 2026, para "
            "su discusión y, en su caso, aprobación;\n"
            "4) Las propuestas de reforma que sean aprobadas por el Pleno de acuerdo con el punto anterior, serán "
            "respaldadas por la Conferencia en el trámite legislativo que la Presidencia considere impulsar."
        ),
        "compromisos": [
            C("2", "Enviar comentarios y observaciones a las propuestas de reforma al CNPP.", "ST-CNPJ",
              fecha=date(2026, 8, 31), plazo="31 de agosto de 2026",
              entregable="Oficio con observaciones", entregas="pleno"),
            C("3a", "Integrar las observaciones en un solo documento (grupo técnico).", "FECOR", ["ST-CNPJ"],
              fecha=date(2026, 9, 11), plazo="Antes de la sesión virtual de septiembre",
              entregable="Documento consolidado de reforma"),
            C("3b", "Convocar y celebrar la sesión plenaria virtual para discusión y, en su caso, aprobación.",
              "PRES-CNPJ", ["ST-CNPJ"], fecha=date(2026, 9, 15), plazo="Mediados de septiembre de 2026",
              entregable="Convocatoria y acta de la sesión virtual"),
            C("4", "Respaldar en el trámite legislativo las propuestas aprobadas.", "PRES-CNPJ",
              entregable="Iniciativa presentada / posicionamiento"),
        ],
    },
    {
        "numero": 17,
        "titulo": "Plataformas e innovaciones tecnológicas; reunión de trabajo y actualización del convenio 2012",
        "naturaleza": "conocimiento",
        "temas": ["Innovación tecnológica", "Personas desaparecidas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia toma conocimiento de las plataformas e innovaciones "
            "tecnológicas presentadas: A) Plataforma de Inteligencia Viva para búsqueda de personas (Nuevo León), "
            "B) Modelo Integral de Identificación Forense con Inteligencia Artificial (Guanajuato), C) Programa de "
            "Identificación Humana (Puebla), y D) SINERGIA Regional coordinación e intercambio de información "
            "interinstitucional (Querétaro).\n\n"
            "Se acuerda tener una reunión de trabajo para exponer los temas relacionados con innovación tecnológica "
            "aplicados a la Procuración de justicia con la presencia del Centro Nacional de Inteligencia, "
            "Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública, Agencia de Transformación Digital y "
            "Telecomunicaciones y la Agencia de Investigación Criminal.\n\n"
            "Se acuerda someter a consideración de la Conferencia Nacional de Procuración de Justicia la "
            "actualización del convenio de colaboración que celebran la Procuraduría General de la República, la "
            "Procuraduría General de Justicia Militar y las Procuradurías y Fiscalías Generales de Justicia de las "
            "entidades federativas, publicado en el Diario Oficial de la Federación el 23 de noviembre de 2012."
        ),
        "compromisos": [
            C("1", "Organizar la reunión de trabajo sobre innovación tecnológica aplicada a la procuración de "
                   "justicia.", "ST-CNPJ", ["CNI", "SESNSP", "ATDT", "AIC"], entregable="Minuta de la reunión"),
            C("2", "Someter a la Conferencia la actualización del convenio de colaboración (DOF 23/11/2012).",
              "ST-CNPJ", ["FGR"], entregable="Proyecto de convenio actualizado"),
        ],
    },
    {
        "numero": 18,
        "titulo": "Reforma a la LNSIJPA (Sonora) y reforma constitucional en delincuencia organizada (Guanajuato)",
        "naturaleza": "conocimiento",
        "temas": ["Reformas legislativas"],
        "responsable": "ST-CNPJ",
        "texto": (
            "La Conferencia Nacional de Procuración de Justicia toma conocimiento de la propuesta de Reforma a la "
            "Ley Nacional del Sistema Integral de Justicia Penal para Adolescentes presentado por la Fiscalía "
            "General del Estado de Sonora, y el Proyecto de Reforma Constitucional en materia de Delincuencia "
            "Organizada, presentado por la Fiscalía General del Estado de Guanajuato. Se instruye a la Secretaría "
            "Técnica compartir dichas iniciativas a las fiscalías y procuradurías para sus observaciones, compilar "
            "las opiniones jurídicas."
        ),
        "compromisos": [
            C("1", "Compartir ambas iniciativas con fiscalías y procuradurías.", "ST-CNPJ", ["F-SON", "F-GTO"],
              entregable="Oficio de remisión"),
            C("2", "Emitir opinión jurídica sobre las iniciativas.", "ST-CNPJ",
              entregable="Opinión jurídica", entregas="estatales"),
            C("3", "Compilar las opiniones jurídicas recibidas.", "ST-CNPJ", entregable="Compilado de opiniones"),
        ],
    },
]
