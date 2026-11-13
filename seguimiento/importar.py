"""Separa el texto pegado de un documento de acuerdos en acuerdos individuales.

Cada acuerdo se reconoce porque una línea inicia con su clave, p. ej.:

    CNPJ/LIV/07/2026. La Conferencia Nacional de Procuración de Justicia tiene por presentado...

Además del corte, se proponen (para que la persona los revise) la naturaleza del acuerdo, un título
corto y los temas, con base en palabras clave.
"""
import re
from collections import Counter
from dataclasses import dataclass, field

from .busqueda import normalizar

CLAVE = re.compile(r"(?m)^[ \t]*([A-Z]{2,12}/[IVXLCDM]+/(\d{1,3})/(\d{4}))\.?[ \t]*")
PIE_PAGINA = re.compile(r"(?im)^\s*p[aá]gina\s+\d+\s+de\s+\d+\s*$")

# El orden importa: se toma la primera regla que coincida con el inicio del acuerdo.
NATURALEZA = [
    ("exhorto", r"\bexhorto\b"),
    ("aprueba", r"\baprueba[n]?\b|\baprobamos\b"),
    ("conocimiento", r"toma(?: de)? conocimiento|tiene por (?:presentad|analizad)|da por recibid"),
    ("instruye", r"\bse instruye\b|\binstruye\b"),
]

TEMAS = {
    "Personas desaparecidas": r"desaparec|busqueda de personas",
    "Personas defensoras de DD.HH.": r"defensor",
    "Servicios forenses": r"forense|pericial|genetic",
    "Extorsión": r"extorsi",
    "Estadística e incidencia": r"incidencia delictiva|registro nacional|estadistic|banci",
    "Feminicidio": r"feminicid",
    "Reformas legislativas": r"reforma|iniciativa de ley|ley general|codigo nacional",
    "Innovación tecnológica": r"tecnolog|plataforma|inteligencia artificial",
    "Capacitación": r"capacitaci|profesionaliz|certificaci",
    "Presupuesto": r"presupuest|partidas especificas",
}


@dataclass
class AcuerdoDetectado:
    clave: str
    numero: int
    anio: int
    texto: str
    naturaleza: str = "compromiso"
    titulo: str = ""
    temas: list = field(default_factory=list)


def limpiar(texto):
    """Quita pies de página y encabezados repetidos, y une las líneas cortadas por el PDF."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = PIE_PAGINA.sub("", texto)
    lineas = [l.strip() for l in texto.split("\n")]
    # Encabezados: líneas cortas idénticas que se repiten en varias páginas.
    repetidas = {l for l, n in Counter(lineas).items() if n >= 2 and 0 < len(l) <= 90 and not CLAVE.match(l)}
    lineas = [l for l in lineas if l not in repetidas]
    # Una línea vacía separa párrafos; los saltos simples se convierten en espacios.
    parrafos, actual = [], []
    for l in lineas:
        if not l:
            if actual:
                parrafos.append(" ".join(actual))
                actual = []
        elif CLAVE.match(l) and actual:
            parrafos.append(" ".join(actual))
            actual = [l]
        else:
            actual.append(l)
    if actual:
        parrafos.append(" ".join(actual))
    return "\n\n".join(re.sub(r"\s{2,}", " ", p) for p in parrafos)


# Arranques que se repiten en casi todos los acuerdos y no aportan al título.
SUJETO = re.compile(
    r"^(?:Las y los integrantes de |Los integrantes de )?(?:El Pleno|La Conferencia|el pleno|La Asamblea)"
    r"(?: de la Conferencia)?(?: Nacional)?(?: de Procuraci[oó]n de Justicia)?,?\s+",
    re.IGNORECASE,
)


def _titulo(texto, largo=160):
    primera = re.split(r"(?<=[.;:])\s", texto, maxsplit=1)[0]
    sin_sujeto = SUJETO.sub("", primera)
    if sin_sujeto != primera and sin_sujeto:
        primera = sin_sujeto[0].upper() + sin_sujeto[1:]
    if len(primera) <= largo:
        return primera.rstrip(".;:")
    corte = primera.rfind(" ", 0, largo)
    return primera[: corte if corte > 0 else largo] + "…"


def separar(texto):
    texto = limpiar(texto)
    marcas = list(CLAVE.finditer(texto))
    resultado = []
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        cuerpo = texto[m.end():fin].strip()
        if not cuerpo:
            continue
        norm = normalizar(cuerpo)
        inicio = norm[:400]
        naturaleza = next((n for n, rx in NATURALEZA if re.search(rx, inicio)), "compromiso")
        temas = [t for t, rx in TEMAS.items() if re.search(rx, norm)]
        resultado.append(AcuerdoDetectado(
            clave=m.group(1), numero=int(m.group(2)), anio=int(m.group(3)), texto=cuerpo,
            naturaleza=naturaleza, titulo=_titulo(cuerpo), temas=temas,
        ))
    return resultado
