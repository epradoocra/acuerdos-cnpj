"""Catálogos base: instituciones y temas.

Los nombres de las fiscalías estatales son genéricos y editables desde
Administración; las siglas son las que usa el sistema como identificador.
"""

ENTIDADES = [
    ("AGS", "Aguascalientes"), ("BC", "Baja California"), ("BCS", "Baja California Sur"),
    ("CAMP", "Campeche"), ("CHIS", "Chiapas"), ("CHIH", "Chihuahua"), ("CDMX", "Ciudad de México"),
    ("COAH", "Coahuila"), ("COL", "Colima"), ("DGO", "Durango"), ("GTO", "Guanajuato"),
    ("GRO", "Guerrero"), ("HGO", "Hidalgo"), ("JAL", "Jalisco"), ("MEX", "Estado de México"),
    ("MICH", "Michoacán"), ("MOR", "Morelos"), ("NAY", "Nayarit"), ("NL", "Nuevo León"),
    ("OAX", "Oaxaca"), ("PUE", "Puebla"), ("QRO", "Querétaro"), ("QROO", "Quintana Roo"),
    ("SLP", "San Luis Potosí"), ("SIN", "Sinaloa"), ("SON", "Sonora"), ("TAB", "Tabasco"),
    ("TAMS", "Tamaulipas"), ("TLAX", "Tlaxcala"), ("VER", "Veracruz"), ("YUC", "Yucatán"),
    ("ZAC", "Zacatecas"),
]


# Denominación oficial vigente (nov. 2026). BCS e Hidalgo conservan la figura de Procuraduría:
# BCS no ha iniciado la conversión y la de Hidalgo está en transición. Tlaxcala es Fiscalía desde el 1/08/2024.
NOMBRES_OFICIALES = {
    "AGS": "Fiscalía General del Estado de Aguascalientes",
    "BC": "Fiscalía General del Estado de Baja California",
    "BCS": "Procuraduría General de Justicia del Estado de Baja California Sur",
    "CAMP": "Fiscalía General del Estado de Campeche",
    "CHIS": "Fiscalía General del Estado de Chiapas",
    "CHIH": "Fiscalía General del Estado de Chihuahua",
    "CDMX": "Fiscalía General de Justicia de la Ciudad de México",
    "COAH": "Fiscalía General del Estado de Coahuila de Zaragoza",
    "COL": "Fiscalía General del Estado de Colima",
    "DGO": "Fiscalía General del Estado de Durango",
    "GTO": "Fiscalía General del Estado de Guanajuato",
    "GRO": "Fiscalía General del Estado de Guerrero",
    "HGO": "Procuraduría General de Justicia del Estado de Hidalgo",
    "JAL": "Fiscalía del Estado de Jalisco",
    "MEX": "Fiscalía General de Justicia del Estado de México",
    "MICH": "Fiscalía General del Estado de Michoacán",
    "MOR": "Fiscalía General del Estado de Morelos",
    "NAY": "Fiscalía General del Estado de Nayarit",
    "NL": "Fiscalía General de Justicia del Estado de Nuevo León",
    "OAX": "Fiscalía General del Estado de Oaxaca",
    "PUE": "Fiscalía General del Estado de Puebla",
    "QRO": "Fiscalía General del Estado de Querétaro",
    "QROO": "Fiscalía General del Estado de Quintana Roo",
    "SLP": "Fiscalía General del Estado de San Luis Potosí",
    "SIN": "Fiscalía General del Estado de Sinaloa",
    "SON": "Fiscalía General de Justicia del Estado de Sonora",
    "TAB": "Fiscalía General del Estado de Tabasco",
    "TAMS": "Fiscalía General de Justicia del Estado de Tamaulipas",
    "TLAX": "Fiscalía General de Justicia del Estado de Tlaxcala",
    "VER": "Fiscalía General del Estado de Veracruz",
    "YUC": "Fiscalía General del Estado de Yucatán",
    "ZAC": "Fiscalía General de Justicia del Estado de Zacatecas",
}

# Regionalización de la CNPJ (mapa oficial de zonas, confirmado por el usuario el 14/11/2026). Abreviaturas de ENTIDADES.
ZONAS = {
    "Noroeste": ["BC", "BCS", "CHIH", "SIN", "SON"],
    "Noreste": ["COAH", "DGO", "NL", "SLP", "TAMS", "ZAC"],
    "Occidente": ["AGS", "COL", "GTO", "JAL", "MICH", "NAY", "QRO"],
    "Centro": ["CDMX", "MEX", "HGO", "MOR", "PUE", "TLAX"],
    "Sureste": ["CAMP", "CHIS", "GRO", "OAX", "QROO", "TAB", "VER", "YUC"],
}


def siglas_estatal(abrev):
    """Siglas con que el sistema identifica a la fiscalía/procuraduría de una entidad."""
    return "FGJCDMX" if abrev == "CDMX" else f"F-{abrev}"


def zona(nombre):
    """Siglas de las fiscalías/procuradurías que integran una zona de la CNPJ."""
    return [siglas_estatal(a) for a in ZONAS[nombre]]


# Prefijo del nombre genérico que usaban versiones anteriores; si una institución aún lo tiene,
# cargar_liv lo sustituye por el oficial (sin tocar nombres editados a mano).
PREFIJO_GENERICO = "Fiscalía / Procuraduría General de "


def fiscalias_estatales():
    for abrev, entidad in ENTIDADES:
        yield (siglas_estatal(abrev), NOMBRES_OFICIALES[abrev], entidad)


# (siglas, nombre, tipo)
INSTITUCIONES = [
    ("PRES-CNPJ", "Presidencia de la Conferencia Nacional de Procuración de Justicia", "instancia"),
    ("ST-CNPJ", "Secretaría Técnica de la Conferencia Nacional de Procuración de Justicia", "instancia"),
    ("FGR", "Fiscalía General de la República", "federal"),
    ("CFIC", "Centro Federal de Inteligencia Criminal (FGR)", "federal"),
    ("CFPF", "Centro Federal Pericial Forense (FGR)", "federal"),
    ("FEMDH", "Fiscalía Especializada en materia de Derechos Humanos (FGR)", "federal"),
    ("FECOR", "Fiscalía Especializada de Control Regional (FGR)", "federal"),
    ("AIC", "Agencia de Investigación Criminal (FGR)", "federal"),
    ("SESNSP", "Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública", "federal"),
    ("INACIPE", "Instituto Nacional de Ciencias Penales", "federal"),
    ("CNI", "Centro Nacional de Inteligencia", "federal"),
    ("ATDT", "Agencia de Transformación Digital y Telecomunicaciones", "federal"),
    ("UNAM", "Universidad Nacional Autónoma de México", "otra"),
]

TEMAS = [
    ("Personas desaparecidas", "#7a1c2e"),
    ("Personas defensoras de DD.HH.", "#9d174d"),
    ("Servicios forenses", "#1d4ed8"),
    ("Extorsión", "#b45309"),
    ("Estadística e incidencia", "#0f766e"),
    ("Feminicidio", "#7e22ce"),
    ("Reformas legislativas", "#374151"),
    ("Innovación tecnológica", "#0369a1"),
    ("Capacitación", "#15803d"),
    ("Presupuesto", "#a16207"),
]
