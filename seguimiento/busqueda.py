"""Búsqueda general por palabra o frase.

Sintaxis:
    extorsion manual            -> registros que contienen AMBAS palabras (en cualquier campo)
    "Secretaría Técnica"        -> la frase exacta
    "fiscalías especializadas" 2027   -> se pueden combinar

Ignora acentos y mayúsculas en:
  - SQL Server / Azure SQL: comparación con la intercalación Latin1_General_100_CI_AI.
  - PostgreSQL: extensión unaccent.
En SQLite (solo desarrollo) ignora mayúsculas pero distingue acentos.
"""
import re
import unicodedata

from django.db import connection
from django.db.models import F, Func, Q
from django.db.models.lookups import IContains
from django.utils.html import escape
from django.utils.safestring import mark_safe

# Intercalación de SQL Server que no distingue mayúsculas (CI) ni acentos (AI).
COLACION_SIN_ACENTOS = "Latin1_General_100_CI_AI"


class SinAcentos(Func):
    """``campo COLLATE Latin1_General_100_CI_AI`` para SQL Server.

    No se usa ``django.db.models.functions.Collate`` porque con mssql-django escribe el nombre entre
    corchetes (``COLLATE [Latin1_General_100_CI_AI]``) y SQL Server lo rechaza: "Incorrect syntax near ...".
    """
    template = "%(expressions)s COLLATE " + COLACION_SIN_ACENTOS

_TOKEN = re.compile(r'"([^"]*)"|(\S+)')
MAX_TERMINOS = 10


def _base(c):
    """Letra base en minúscula de un carácter (á -> a, Ñ -> n), siempre de longitud 1."""
    d = unicodedata.normalize("NFD", c)[:1] or c
    b = d.lower()
    return b if len(b) == 1 else d


def normalizar(texto):
    """Quita acentos y pasa a minúsculas conservando la longitud (para ubicar coincidencias en el original)."""
    return "".join(_base(c) for c in texto)


def terminos(consulta):
    """Separa la consulta en palabras sueltas y frases entre comillas."""
    out = []
    for frase, palabra in _TOKEN.findall(consulta or ""):
        t = " ".join((frase or palabra).replace('"', "").split())
        if len(t) >= 2 and t not in out:
            out.append(t)
    return out[:MAX_TERMINOS]


def filtro(campos, terms):
    """Q que exige que CADA término aparezca en AL MENOS uno de los campos."""
    motor = connection.vendor
    q = Q()
    for t in terms:
        alguno = Q()
        for campo in campos:
            if motor == "microsoft":
                alguno |= Q(IContains(SinAcentos(F(campo)), normalizar(t)))
            elif motor == "postgresql":
                alguno |= Q(**{f"{campo}__unaccent__icontains": normalizar(t)})
            else:
                alguno |= Q(**{f"{campo}__icontains": t})
        q &= alguno
    return q


def resaltar(texto, terms, ancho=None):
    """HTML con las coincidencias en <mark>. Con `ancho`, recorta un fragmento alrededor de la primera."""
    if not texto:
        return ""
    texto = str(texto)
    norm = normalizar(texto)
    spans = sorted(
        (m.start(), m.end())
        for t in terms
        for m in re.finditer(re.escape(normalizar(t)), norm)
    )
    unidos = []
    for s, e in spans:
        if unidos and s <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(e, unidos[-1][1]))
        else:
            unidos.append((s, e))

    ini, fin = 0, len(texto)
    if ancho and len(texto) > ancho:
        centro = unidos[0][0] if unidos else 0
        ini = max(0, centro - ancho // 3)
        fin = min(len(texto), ini + ancho)
        if ini > 0:  # no cortar palabras a la mitad
            esp = texto.find(" ", ini, centro)
            ini = esp + 1 if esp != -1 else ini
        if fin < len(texto):
            esp = texto.rfind(" ", ini, fin)
            fin = esp if esp > ini else fin

    partes, pos = [], ini
    for s, e in unidos:
        if e <= ini or s >= fin:
            continue
        s, e = max(s, ini), min(e, fin)
        partes += [escape(texto[pos:s]), "<mark>", escape(texto[s:e]), "</mark>"]
        pos = e
    partes.append(escape(texto[pos:fin]))
    html = "".join(partes)
    if ini > 0:
        html = "…" + html
    if fin < len(texto):
        html += "…"
    return mark_safe(html)
