from django import template

from seguimiento.busqueda import resaltar as _resaltar

register = template.Library()


@register.simple_tag
def resaltar(texto, terminos, ancho=None):
    """{% resaltar acuerdo.texto terminos 220 %}"""
    return _resaltar(texto, terminos, ancho)

ETIQUETAS = {
    "pendiente": "Pendiente",
    "en_proceso": "En proceso",
    "cumplido": "Cumplido",
    "vencido": "Vencido",
    "cancelado": "Cancelado",
}


@register.inclusion_tag("seguimiento/_estatus.html")
def estatus(valor):
    return {"valor": valor, "etiqueta": ETIQUETAS.get(valor, valor)}


@register.inclusion_tag("seguimiento/_barra.html")
def barra(pct):
    return {"pct": pct or 0}


@register.filter
def tipo_campo(campo):
    """Clasifica un campo de formulario para acomodarlo: 'casilla', 'ancho' (ocupa toda la fila) o 'normal'."""
    w = campo.field.widget
    nombre = type(w).__name__
    if nombre == "CheckboxInput":
        return "casilla"
    if nombre in ("Textarea", "CheckboxSelectMultiple", "SelectMultiple", "ClearableFileInput"):
        return "ancho"
    return "normal"
