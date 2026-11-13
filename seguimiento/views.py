import csv
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .busqueda import filtro, terminos
from .forms import AvanceForm, EntregaForm
from .models import Acuerdo, Avance, Compromiso, Entrega, Institucion, Reunion, institucion_de

ABIERTOS = [Compromiso.Estatus.PENDIENTE, Compromiso.Estatus.EN_PROCESO]


def puede_editar_entrega(usuario, entrega):
    """Quien captura compromisos (ST) edita cualquier entrega; un enlace ligado a una institución, solo las suyas."""
    if not usuario.has_perm("seguimiento.change_entrega"):
        return False
    if usuario.has_perm("seguimiento.change_compromiso") or settings.MODO_PRUEBA:
        return True
    propia = institucion_de(usuario)
    return propia is None or propia.pk == entrega.institucion_id


def _acuerdos_qs():
    return Acuerdo.objects.select_related("reunion", "responsable").prefetch_related(
        "temas",
        Prefetch(
            "compromisos",
            queryset=Compromiso.objects.select_related("responsable").prefetch_related("entregas", "corresponsables"),
        ),
    )


@login_required
def tablero(request):
    hoy = timezone.localdate()
    compromisos = Compromiso.objects.select_related("acuerdo", "responsable")
    abiertos = compromisos.filter(estatus__in=ABIERTOS)

    por_estatus = dict(compromisos.values_list("estatus").annotate(n=Count("pk")))
    vencidos = abiertos.filter(fecha_limite__lt=hoy).order_by("fecha_limite")
    proximos = abiertos.filter(fecha_limite__gte=hoy, fecha_limite__lte=hoy + timedelta(days=30)).order_by("fecha_limite")

    por_responsable = (
        Institucion.objects.annotate(
            total=Count("compromisos", distinct=True),
            abiertos=Count("compromisos", filter=Q(compromisos__estatus__in=ABIERTOS), distinct=True),
            vencidos=Count(
                "compromisos",
                filter=Q(compromisos__estatus__in=ABIERTOS, compromisos__fecha_limite__lt=hoy),
                distinct=True,
            ),
            cumplidos=Count("compromisos", filter=Q(compromisos__estatus=Compromiso.Estatus.CUMPLIDO), distinct=True),
        )
        .filter(total__gt=0)
        .order_by("-vencidos", "-abiertos")
    )

    reuniones = Reunion.objects.select_related("organo").prefetch_related(
        Prefetch("acuerdos", queryset=_acuerdos_qs())
    )[:10]

    total = sum(por_estatus.values())
    return render(request, "seguimiento/tablero.html", {
        "total": total,
        "cumplidos": por_estatus.get(Compromiso.Estatus.CUMPLIDO, 0),
        "en_proceso": por_estatus.get(Compromiso.Estatus.EN_PROCESO, 0),
        "pendientes": por_estatus.get(Compromiso.Estatus.PENDIENTE, 0),
        "n_vencidos": vencidos.count(),
        "por_validar": compromisos.filter(responsable_validado=False).count(),
        "vencidos": vencidos[:15],
        "proximos": proximos[:15],
        "por_responsable": por_responsable,
        "reuniones": reuniones,
        "hoy": hoy,
    })


LIMITE_RESULTADOS = 50


@login_required
def buscar(request):
    consulta = request.GET.get("q", "").strip()
    terms = terminos(consulta)
    reunion_id = request.GET.get("reunion", "")
    reunion_id = int(reunion_id) if reunion_id.isdigit() else None
    ctx = {"q": consulta, "terminos": terms, "reunion_id": reunion_id,
           "todas_reuniones": Reunion.objects.all(), "secciones": [], "total": 0}
    if not terms:
        return render(request, "seguimiento/buscar.html", ctx)

    def en_reunion(qs, ruta):
        return qs.filter(**{ruta: reunion_id}) if reunion_id else qs

    consultas = [
        ("acuerdos", "Acuerdos", en_reunion(
            Acuerdo.objects.filter(filtro(["clave", "titulo", "texto", "observaciones", "temas__nombre"], terms))
            .select_related("reunion"), "reunion_id")),
        ("compromisos", "Compromisos", en_reunion(
            Compromiso.objects.filter(filtro(
                ["descripcion", "entregable", "plazo_texto", "nota_asignacion",
                 "responsable__siglas", "responsable__nombre"], terms))
            .select_related("acuerdo__reunion", "responsable"), "acuerdo__reunion_id")),
        ("avances", "Bitácora de avances", en_reunion(
            Avance.objects.filter(filtro(["descripcion"], terms))
            .select_related("compromiso__acuerdo", "registrado_por"), "compromiso__acuerdo__reunion_id")),
        ("entregas", "Entregas", en_reunion(
            Entrega.objects.filter(filtro(["oficio", "nota"], terms))
            .select_related("compromiso__acuerdo", "institucion"), "compromiso__acuerdo__reunion_id")),
        ("instituciones", "Instituciones", None if reunion_id else
            Institucion.objects.filter(filtro(["nombre", "siglas", "entidad_federativa"], terms))),
        ("reuniones", "Reuniones", None if reunion_id else
            Reunion.objects.filter(filtro(["nombre", "numeral", "sede", "observaciones"], terms))),
    ]
    for clave, titulo, qs in consultas:
        if qs is None:
            continue
        qs = qs.distinct()
        n = qs.count()
        if n:
            ctx["secciones"].append({"clave": clave, "titulo": titulo, "n": n,
                                     "items": list(qs[:LIMITE_RESULTADOS])})
            ctx["total"] += n
    ctx["limite"] = LIMITE_RESULTADOS
    return render(request, "seguimiento/buscar.html", ctx)


def manual(request):
    """Manual de usuario. Es público para poder consultarlo antes de iniciar sesión; no contiene datos."""
    return render(request, "seguimiento/manual.html")


@login_required
def reuniones(request):
    qs = Reunion.objects.select_related("organo").annotate(n_acuerdos=Count("acuerdos"))
    return render(request, "seguimiento/reuniones.html", {"reuniones": qs})


@login_required
def reunion(request, pk):
    obj = get_object_or_404(Reunion.objects.select_related("organo"), pk=pk)
    acuerdos = list(_acuerdos_qs().filter(reunion=obj))
    estatus = request.GET.get("estatus")
    if estatus:
        acuerdos = [a for a in acuerdos if a.estatus == estatus]
    return render(request, "seguimiento/reunion.html", {"reunion": obj, "acuerdos": acuerdos, "estatus": estatus})


@login_required
def acuerdo(request, pk):
    obj = get_object_or_404(_acuerdos_qs(), pk=pk)
    compromisos = Compromiso.objects.filter(acuerdo=obj).select_related("responsable").prefetch_related(
        "corresponsables",
        Prefetch("avances", queryset=Avance.objects.select_related("registrado_por")),
        Prefetch("entregas", queryset=Entrega.objects.select_related("institucion")),
    )
    return render(request, "seguimiento/acuerdo.html", {
        "acuerdo": obj,
        "compromisos": compromisos,
        "form": AvanceForm(initial={"fecha": timezone.localdate()}),
    })


@login_required
@permission_required("seguimiento.add_avance", raise_exception=True)
@require_POST
def registrar_avance(request, pk):
    compromiso = get_object_or_404(Compromiso, pk=pk)
    form = AvanceForm(request.POST, request.FILES)
    if form.is_valid():
        avance = form.save(commit=False)
        avance.compromiso = compromiso
        avance.registrado_por = request.user
        avance.save()
        messages.success(request, f"Avance registrado en {compromiso}.")
    else:
        messages.error(request, "No se registró el avance: " + "; ".join(
            f"{k}: {' '.join(v)}" for k, v in form.errors.items()))
    return redirect(compromiso.acuerdo.get_absolute_url() + f"#c{compromiso.pk}")


@login_required
@permission_required("seguimiento.change_entrega", raise_exception=True)
def editar_entrega(request, pk):
    entrega = get_object_or_404(Entrega.objects.select_related("compromiso__acuerdo", "institucion"), pk=pk)
    if not puede_editar_entrega(request.user, entrega):
        raise PermissionDenied("Solo puede actualizar las entregas de su institución.")
    form = EntregaForm(request.POST or None, request.FILES or None, instance=entrega)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Entrega de {entrega.institucion} actualizada.")
        return redirect(entrega.compromiso.acuerdo.get_absolute_url() + f"#c{entrega.compromiso_id}")
    return render(request, "seguimiento/entrega_form.html", {"form": form, "entrega": entrega})


@login_required
def institucion(request, pk):
    obj = get_object_or_404(Institucion, pk=pk)
    compromisos = (
        Compromiso.objects.filter(Q(responsable=obj) | Q(corresponsables=obj))
        .select_related("acuerdo__reunion", "responsable").distinct().order_by("fecha_limite")
    )
    entregas = obj.entregas.select_related("compromiso__acuerdo").order_by("compromiso__fecha_limite")
    return render(request, "seguimiento/institucion.html", {
        "institucion": obj, "compromisos": compromisos, "entregas": entregas,
    })


@login_required
def exportar_reunion(request, pk):
    obj = get_object_or_404(Reunion, pk=pk)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="acuerdos_{obj.numeral}.csv"'
    resp.write("﻿")  # BOM para que Excel abra bien los acentos
    w = csv.writer(resp)
    w.writerow(["Clave", "Acuerdo", "Inciso", "Compromiso", "Responsable", "Fecha límite",
                "Plazo", "Estatus", "Avance %", "Vencido", "Responsable validado", "Criterio de asignación"])
    for a in _acuerdos_qs().filter(reunion=obj):
        for c in a.compromisos.all():
            w.writerow([
                a.clave, a.titulo, c.inciso, c.descripcion, c.responsable.siglas,
                c.fecha_limite.isoformat() if c.fecha_limite else "", c.plazo_texto,
                c.get_estatus_display(), c.avance_efectivo, "Sí" if c.vencido else "No",
                "Sí" if c.responsable_validado else "No", c.nota_asignacion,
            ])
    return resp


@login_required
def descargar_evidencia(request, tipo, pk):
    modelo, campo = {"avance": (Avance, "evidencia"), "entrega": (Entrega, "evidencia"),
                     "acta": (Reunion, "acta")}.get(tipo, (None, None))
    if modelo is None:
        raise Http404
    archivo = getattr(get_object_or_404(modelo, pk=pk), campo)
    if not archivo:
        raise Http404
    return FileResponse(archivo.open("rb"), as_attachment=True, filename=archivo.name.rsplit("/", 1)[-1])
