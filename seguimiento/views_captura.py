"""Captura desde la interfaz principal: reuniones, acuerdos, compromisos, entregas y catálogos.

Los permisos son los estándar de Django (add/change/delete por modelo); el grupo
"Secretaría Técnica" los tiene todos. Los enlaces institucionales no ven estas opciones.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.db.models import Count, ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (AcuerdoForm, CompromisoForm, ImportarForm, InstitucionForm, OrganoForm, ReunionForm,
                    TemaForm)
from .importar import separar
from .models import Acuerdo, Avance, Compromiso, Entrega, Institucion, Organo, Reunion, Tema


def requiere(perm):
    """login + permiso del modelo; sin permiso responde 403."""
    def deco(vista):
        return login_required(permission_required(f"seguimiento.{perm}", raise_exception=True)(vista))
    return deco


def _form(request, form, titulo, cancelar, subtitulo="", plantilla="seguimiento/captura/form.html", **extra):
    return render(request, plantilla, {"form": form, "titulo": titulo, "subtitulo": subtitulo,
                                       "cancelar": cancelar, **extra})


def _confirmar(request, titulo, objeto, cancelar, consecuencias, palabra=None):
    """Página de confirmación de borrado. Con `palabra`, exige escribirla para continuar."""
    return render(request, "seguimiento/captura/borrar.html", {
        "titulo": titulo, "objeto": objeto, "cancelar": cancelar,
        "consecuencias": [c for c in consecuencias if c], "palabra": palabra,
    })


# ------------------------------------------------------------------------------- reuniones

@requiere("add_reunion")
def reunion_crear(request):
    form = ReunionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        r = form.save()
        messages.success(request, f"Reunión «{r}» registrada. Ahora capture sus acuerdos.")
        return redirect(r)
    return _form(request, form, "Nueva reunión", reverse("seguimiento:reuniones"))


@requiere("change_reunion")
def reunion_editar(request, pk):
    r = get_object_or_404(Reunion, pk=pk)
    form = ReunionForm(request.POST or None, request.FILES or None, instance=r)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Reunión actualizada.")
        return redirect(r)
    return _form(request, form, "Editar reunión", r.get_absolute_url(), str(r))


@requiere("delete_reunion")
def reunion_borrar(request, pk):
    r = get_object_or_404(Reunion, pk=pk)
    if request.method == "POST":
        if request.POST.get("confirmacion", "").strip().upper() != r.numeral.upper():
            messages.error(request, f"Para eliminar escriba exactamente {r.numeral}.")
        else:
            nombre = str(r)
            r.delete()
            messages.success(request, f"Reunión «{nombre}» eliminada.")
            return redirect("seguimiento:reuniones")
    n_ac = r.acuerdos.count()
    n_co = Compromiso.objects.filter(acuerdo__reunion=r).count()
    n_av = Avance.objects.filter(compromiso__acuerdo__reunion=r).count()
    return _confirmar(request, "Eliminar reunión", r, r.get_absolute_url(), [
        f"{n_ac} acuerdo(s)" if n_ac else "",
        f"{n_co} compromiso(s) con sus entregas" if n_co else "",
        f"{n_av} avance(s) de la bitácora" if n_av else "",
    ], palabra=r.numeral)


# ------------------------------------------------------------------------------- acuerdos

@requiere("add_acuerdo")
def acuerdo_crear(request, reunion_pk):
    reunion = get_object_or_404(Reunion.objects.select_related("organo"), pk=reunion_pk)
    form = AcuerdoForm(request.POST or None, reunion=reunion)
    if request.method == "POST" and form.is_valid():
        a = form.save(commit=False)
        a.reunion = reunion
        a.save()
        form.save_m2m()
        messages.success(request, f"Acuerdo {a.clave} registrado. Agregue sus compromisos.")
        if "otro" in request.POST:
            return redirect("seguimiento:acuerdo_crear", reunion_pk=reunion.pk)
        return redirect(a)
    return _form(request, form, "Nuevo acuerdo", reunion.get_absolute_url(), str(reunion), otro=True)


@requiere("change_acuerdo")
def acuerdo_editar(request, pk):
    a = get_object_or_404(Acuerdo.objects.select_related("reunion__organo"), pk=pk)
    form = AcuerdoForm(request.POST or None, instance=a)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Acuerdo actualizado.")
        return redirect(a)
    return _form(request, form, f"Editar {a.clave}", a.get_absolute_url(), str(a.reunion))


@requiere("delete_acuerdo")
def acuerdo_borrar(request, pk):
    a = get_object_or_404(Acuerdo, pk=pk)
    if request.method == "POST":
        reunion = a.reunion
        a.delete()
        messages.success(request, f"Acuerdo {a.clave} eliminado.")
        return redirect(reunion)
    n_co = a.compromisos.count()
    n_av = Avance.objects.filter(compromiso__acuerdo=a).count()
    return _confirmar(request, "Eliminar acuerdo", a, a.get_absolute_url(), [
        f"{n_co} compromiso(s) con sus entregas" if n_co else "",
        f"{n_av} avance(s) de la bitácora" if n_av else "",
    ])


@requiere("add_acuerdo")
def acuerdos_importar(request, reunion_pk):
    """Paso 1: pegar texto. Paso 2: revisar lo detectado. Paso 3: crear."""
    reunion = get_object_or_404(Reunion.objects.select_related("organo"), pk=reunion_pk)
    form = ImportarForm(request.POST or None)
    detectados = []
    if request.method == "POST" and form.is_valid():
        detectados = separar(form.cleaned_data["texto"])
        existentes = set(Acuerdo.objects.filter(clave__in=[d.clave for d in detectados])
                         .values_list("clave", flat=True))
        for i, d in enumerate(detectados):
            d.indice = i
            d.existe = d.clave in existentes
            d.otra_reunion = f"/{reunion.numeral}/" not in d.clave

        if request.POST.get("accion") == "crear":
            temas = {t.nombre: t for t in Tema.objects.all()}
            creados = 0
            with transaction.atomic():
                for d in detectados:
                    if d.existe or not request.POST.get(f"incluir_{d.indice}"):
                        continue
                    a = Acuerdo.objects.create(
                        reunion=reunion, clave=d.clave, numero=d.numero,
                        titulo=(request.POST.get(f"titulo_{d.indice}") or d.titulo)[:250],
                        naturaleza=request.POST.get(f"naturaleza_{d.indice}") or d.naturaleza,
                        texto=d.texto,
                    )
                    a.temas.set([temas[t] for t in d.temas if t in temas])
                    creados += 1
            messages.success(request, f"Se registraron {creados} acuerdo(s). Ahora agregue los compromisos de cada uno.")
            return redirect(reunion)
        if not detectados:
            messages.error(request, "No se encontró ninguna clave de acuerdo al inicio de un renglón "
                                    "(p. ej. CNPJ/LIV/01/2026). Revise el texto pegado.")
    return render(request, "seguimiento/captura/importar.html", {
        "reunion": reunion, "form": form, "detectados": detectados,
        "naturalezas": Acuerdo.Naturaleza.choices,
    })


# ------------------------------------------------------------------------------- compromisos

def sincronizar_entregas(compromiso, instituciones):
    """Crea las entregas que falten y quita las sobrantes que aún no tienen información capturada."""
    obligadas = {i.pk for i in instituciones or []}
    creadas = eliminadas = conservadas = 0
    actuales = {e.institucion_id: e for e in compromiso.entregas.all()}
    for pk in obligadas - actuales.keys():
        Entrega.objects.create(compromiso=compromiso, institucion_id=pk)
        creadas += 1
    for pk in actuales.keys() - obligadas:
        e = actuales[pk]
        if e.estatus == Entrega.Estatus.PENDIENTE and not (e.oficio or e.evidencia or e.nota or e.fecha_entrega):
            e.delete()
            eliminadas += 1
        else:
            conservadas += 1
    requiere = bool(obligadas) or conservadas > 0
    if compromiso.requiere_entregas != requiere:
        compromiso.requiere_entregas = requiere
        compromiso.save(update_fields=["requiere_entregas", "actualizado"])
    return creadas, eliminadas, conservadas


def _guardar_compromiso(request, form, acuerdo):
    with transaction.atomic():
        c = form.save(commit=False)
        c.acuerdo = acuerdo
        c.save()
        form.save_m2m()
        creadas, eliminadas, conservadas = sincronizar_entregas(c, form.instituciones_obligadas())
    partes = [f"Compromiso {c} guardado."]
    if creadas:
        partes.append(f"{creadas} entrega(s) asignada(s).")
    if eliminadas:
        partes.append(f"{eliminadas} entrega(s) sin información retirada(s).")
    if conservadas:
        partes.append(f"Se conservaron {conservadas} entrega(s) que ya tienen información capturada.")
    messages.success(request, " ".join(partes))
    return c


@requiere("add_compromiso")
def compromiso_crear(request, acuerdo_pk):
    acuerdo = get_object_or_404(Acuerdo, pk=acuerdo_pk)
    siguiente = chr(ord("a") + acuerdo.compromisos.count()) if acuerdo.compromisos.count() < 26 else ""
    form = CompromisoForm(request.POST or None, initial={
        "inciso": siguiente, "responsable": acuerdo.responsable_id, "responsable_validado": True})
    if request.method == "POST" and form.is_valid():
        c = _guardar_compromiso(request, form, acuerdo)
        if "otro" in request.POST:
            return redirect("seguimiento:compromiso_crear", acuerdo_pk=acuerdo.pk)
        return redirect(acuerdo.get_absolute_url() + f"#c{c.pk}")
    return _form(request, form, "Nuevo compromiso", acuerdo.get_absolute_url(),
                 f"{acuerdo.clave} · {acuerdo.titulo}", otro=True, acuerdo=acuerdo)


@requiere("change_compromiso")
def compromiso_editar(request, pk):
    c = get_object_or_404(Compromiso.objects.select_related("acuerdo"), pk=pk)
    form = CompromisoForm(request.POST or None, instance=c)
    if request.method == "POST" and form.is_valid():
        _guardar_compromiso(request, form, c.acuerdo)
        return redirect(c.acuerdo.get_absolute_url() + f"#c{c.pk}")
    return _form(request, form, f"Editar compromiso {c}", c.acuerdo.get_absolute_url() + f"#c{c.pk}",
                 c.acuerdo.titulo, acuerdo=c.acuerdo)


@requiere("delete_compromiso")
def compromiso_borrar(request, pk):
    c = get_object_or_404(Compromiso.objects.select_related("acuerdo"), pk=pk)
    if request.method == "POST":
        acuerdo = c.acuerdo
        c.delete()
        messages.success(request, f"Compromiso {c} eliminado.")
        return redirect(acuerdo)
    n_en = c.entregas.count()
    n_av = c.avances.count()
    return _confirmar(request, "Eliminar compromiso", f"{c} — {c.descripcion}", c.acuerdo.get_absolute_url(), [
        f"{n_en} entrega(s)" if n_en else "", f"{n_av} avance(s) de la bitácora" if n_av else ""])


# ------------------------------------------------------------------------------- catálogos

CATALOGOS = {
    "instituciones": (Institucion, InstitucionForm, "Institución", "institucion"),
    "temas": (Tema, TemaForm, "Tema", "tema"),
    "organos": (Organo, OrganoForm, "Órgano colegiado", "organo"),
}


def _catalogo(tipo):
    if tipo not in CATALOGOS:
        raise Http404
    return CATALOGOS[tipo]


@login_required
def catalogos(request):
    if not request.user.has_perm("seguimiento.change_institucion"):
        raise PermissionDenied
    return render(request, "seguimiento/captura/catalogos.html", {
        "instituciones": Institucion.objects.annotate(n=Count("compromisos")),
        "temas": Tema.objects.annotate(n=Count("acuerdos")),
        "organos": Organo.objects.annotate(n=Count("reuniones")),
    })


@login_required
def catalogo_form(request, tipo, pk=None):
    modelo, form_cls, nombre, codigo = _catalogo(tipo)
    perm = f"seguimiento.{'change' if pk else 'add'}_{codigo}"
    if not request.user.has_perm(perm):
        raise PermissionDenied
    obj = get_object_or_404(modelo, pk=pk) if pk else None
    form = form_cls(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{nombre} guardado(a).")
        return redirect(reverse("seguimiento:catalogos") + f"#{tipo}")
    return _form(request, form, f"{'Editar' if obj else 'Nuevo(a)'} {nombre.lower()}",
                 reverse("seguimiento:catalogos") + f"#{tipo}", str(obj) if obj else "")


@login_required
def catalogo_borrar(request, tipo, pk):
    modelo, _, nombre, codigo = _catalogo(tipo)
    if not request.user.has_perm(f"seguimiento.delete_{codigo}"):
        raise PermissionDenied
    obj = get_object_or_404(modelo, pk=pk)
    volver = reverse("seguimiento:catalogos") + f"#{tipo}"
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, f"{nombre} «{obj}» eliminado(a).")
        except ProtectedError:
            messages.error(request, f"No se puede eliminar «{obj}» porque está en uso. "
                                    "Puede marcarla como inactiva." if tipo == "instituciones" else
                                    f"No se puede eliminar «{obj}» porque está en uso.")
        return redirect(volver)
    return _confirmar(request, f"Eliminar {nombre.lower()}", obj, volver, [])
