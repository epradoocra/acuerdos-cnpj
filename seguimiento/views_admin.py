"""Administración del sistema: panel, usuarios, validación de responsables y exportación de datos.

Acceso: permiso auth.change_user (perfil "Administrador del sistema" y superusuarios).
"""
import csv
import io
import os
import secrets
import string
from datetime import timedelta

import django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import PERFILES, UsuarioForm
from .models import Acuerdo, Avance, Compromiso, Entrega, Institucion, Reunion


def solo_admin(vista):
    return login_required(permission_required("auth.change_user", raise_exception=True)(vista))


def _clave_temporal(n=12):
    alfabeto = "".join(c for c in string.ascii_letters + string.digits if c not in "0OoIl1")
    return "".join(secrets.choice(alfabeto) for _ in range(n))


def _tamano(ruta):
    total = archivos = 0
    for raiz, _, nombres in os.walk(ruta):
        for n in nombres:
            try:
                total += os.path.getsize(os.path.join(raiz, n))
                archivos += 1
            except OSError:
                pass
    return total, archivos


def _version_bd():
    try:
        with connection.cursor() as c:
            if connection.vendor == "postgresql":
                c.execute("SHOW server_version")
                return f"PostgreSQL {c.fetchone()[0]}"
            c.execute("select sqlite_version()")
            return f"SQLite {c.fetchone()[0]}"
    except Exception as exc:  # el panel no debe caerse por esto
        return f"No disponible ({exc.__class__.__name__})"


# ----------------------------------------------------------------------------------- panel

@solo_admin
def panel(request):
    hoy = timezone.localdate()
    abiertos = Q(estatus__in=[Compromiso.Estatus.PENDIENTE, Compromiso.Estatus.EN_PROCESO])
    hace_30 = timezone.now() - timedelta(days=30)
    peso, n_archivos = _tamano(settings.MEDIA_ROOT)

    perfiles = {g.name: g.n for g in Group.objects.filter(name__in=PERFILES)
                .annotate(n=Count("user", filter=Q(user__is_active=True)))}
    activos = User.objects.filter(is_active=True)
    return render(request, "seguimiento/admin/panel.html", {
        "cifras": [
            ("Reuniones", Reunion.objects.count()),
            ("Acuerdos", Acuerdo.objects.count()),
            ("Compromisos", Compromiso.objects.count()),
            ("Entregas", Entrega.objects.count()),
            ("Avances registrados", Avance.objects.count()),
            ("Instituciones activas", Institucion.objects.filter(activa=True).count()),
        ],
        "atencion": [
            ("Compromisos vencidos sin cumplir", Compromiso.objects.filter(abiertos, fecha_limite__lt=hoy).count(),
             "seguimiento:tablero", ""),
            ("Responsables por validar", Compromiso.objects.filter(responsable_validado=False).count(),
             "seguimiento:admin_validar", ""),
            ("Enlaces sin institución asignada",
             activos.filter(groups__name="Enlace institucional").filter(
                 Q(perfil__isnull=True) | Q(perfil__institucion__isnull=True)).count(),
             "seguimiento:admin_usuarios", "?perfil=Enlace institucional"),
            ("Usuarios activos que nunca han entrado", activos.filter(last_login__isnull=True).count(),
             "seguimiento:admin_usuarios", "?estado=nunca"),
        ],
        "perfiles": [(p, perfiles.get(p, 0)) for p in PERFILES],
        "usuarios_activos": activos.count(),
        "avances_30": Avance.objects.filter(creado__gte=hace_30).count(),
        "ultimos_avances": Avance.objects.select_related("compromiso__acuerdo", "registrado_por")[:8],
        "ultimos_accesos": User.objects.filter(last_login__isnull=False).order_by("-last_login")[:8],
        "tecnico": [
            ("Base de datos", _version_bd()),
            ("Django", django.get_version()),
            ("Evidencias y actas", f"{n_archivos} archivo(s), {peso / 1048576:.1f} MB"),
            ("Zona horaria", settings.TIME_ZONE),
            ("Modo depuración", "Activado (no usar en producción)" if settings.DEBUG else "Desactivado"),
        ],
    })


# ----------------------------------------------------------------------------------- usuarios

@solo_admin
def usuarios(request):
    qs = User.objects.prefetch_related("groups").select_related("perfil__institucion").order_by("username")
    perfil = request.GET.get("perfil", "")
    estado = request.GET.get("estado", "")
    q = request.GET.get("q", "").strip()
    if perfil:
        qs = qs.filter(groups__name=perfil)
    if estado == "activos":
        qs = qs.filter(is_active=True)
    elif estado == "inactivos":
        qs = qs.filter(is_active=False)
    elif estado == "nunca":
        qs = qs.filter(is_active=True, last_login__isnull=True)
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                       | Q(email__icontains=q) | Q(perfil__institucion__siglas__icontains=q))
    filas = []
    for u in qs.distinct():
        grupo = next((g.name for g in u.groups.all() if g.name in PERFILES), "")
        inst = getattr(getattr(u, "perfil", None), "institucion", None) if hasattr(u, "perfil") else None
        filas.append({"u": u, "perfil": grupo, "institucion": inst})
    return render(request, "seguimiento/admin/usuarios.html", {
        "filas": filas, "perfiles": PERFILES, "perfil": perfil, "estado": estado, "q": q,
    })


@solo_admin
def usuario_crear(request):
    form = UsuarioForm(request.POST or None, editor=request.user)
    if request.method == "POST" and form.is_valid():
        u = form.save()
        clave = _clave_temporal()
        u.set_password(clave)
        u.save(update_fields=["password"])
        messages.warning(request, f"Usuario «{u.username}» creado. Contraseña temporal: {clave} — "
                                  "entréguela de forma segura; no se volverá a mostrar.")
        return redirect("seguimiento:admin_usuarios")
    return render(request, "seguimiento/captura/form.html", {
        "form": form, "titulo": "Nuevo usuario", "cancelar": reverse("seguimiento:admin_usuarios"),
        "subtitulo": "La contraseña temporal se genera automáticamente al guardar."})


@solo_admin
def usuario_editar(request, pk):
    u = get_object_or_404(User, pk=pk)
    form = UsuarioForm(request.POST or None, instance=u, editor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Usuario «{u.username}» actualizado.")
        return redirect("seguimiento:admin_usuarios")
    return render(request, "seguimiento/admin/usuario_form.html", {
        "form": form, "titulo": f"Editar usuario {u.username}", "cancelar": reverse("seguimiento:admin_usuarios"),
        "usuario": u, "es_yo": u.pk == request.user.pk,
        "n_avances": Avance.objects.filter(registrado_por=u).count()})


@solo_admin
@require_POST
def usuario_restablecer(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.pk == request.user.pk:
        messages.error(request, "Para cambiar su propia contraseña use «Mi cuenta».")
        return redirect("seguimiento:admin_usuario_editar", pk=pk)
    clave = _clave_temporal()
    u.set_password(clave)
    u.save(update_fields=["password"])
    messages.warning(request, f"Nueva contraseña temporal de «{u.username}»: {clave} — "
                              "entréguela de forma segura; no se volverá a mostrar.")
    return redirect("seguimiento:admin_usuarios")


# ----------------------------------------------------------------------------------- validación

@solo_admin
def validar(request):
    pendientes = (Compromiso.objects.filter(responsable_validado=False)
                  .select_related("acuerdo__reunion", "responsable").prefetch_related("corresponsables")
                  .order_by("acuerdo__reunion", "acuerdo__numero", "inciso"))
    if request.method == "POST":
        ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
        n = pendientes.filter(pk__in=ids).update(responsable_validado=True)
        messages.success(request, f"{n} compromiso(s) con responsable confirmado.")
        return redirect("seguimiento:admin_validar")
    return render(request, "seguimiento/admin/validar.html", {"pendientes": pendientes})


# ----------------------------------------------------------------------------------- exportación

@solo_admin
def exportar(request):
    return render(request, "seguimiento/admin/exportar.html", {"reuniones": Reunion.objects.all()})


@solo_admin
def exportar_compromisos(request):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="compromisos_{timezone.localdate():%Y%m%d}.csv"'
    resp.write("﻿")
    w = csv.writer(resp)
    w.writerow(["Reunión", "Fecha reunión", "Clave", "Acuerdo", "Naturaleza", "Inciso", "Compromiso", "Responsable",
                "Corresponsables", "Fecha límite", "Plazo", "Entregable", "Estatus", "Avance %", "Vencido",
                "Entregas hechas", "Entregas obligadas", "Responsable validado", "Último avance"])
    qs = (Compromiso.objects.select_related("acuerdo__reunion", "responsable")
          .prefetch_related("corresponsables", "entregas", "avances").order_by("acuerdo__reunion", "acuerdo__numero", "inciso"))
    for c in qs:
        a, r = c.acuerdo, c.acuerdo.reunion
        entregas = list(c.entregas.all())
        ultimo = next(iter(c.avances.all()), None)
        w.writerow([r.nombre, r.fecha.isoformat() if r.fecha else "", a.clave, a.titulo, a.get_naturaleza_display(),
                    c.inciso, c.descripcion, c.responsable.siglas, ", ".join(i.siglas for i in c.corresponsables.all()),
                    c.fecha_limite.isoformat() if c.fecha_limite else "", c.plazo_texto, c.entregable,
                    c.get_estatus_display(), c.avance_efectivo, "Sí" if c.vencido else "No",
                    sum(1 for e in entregas if e.estatus == Entrega.Estatus.ENTREGADO), len(entregas),
                    "Sí" if c.responsable_validado else "No",
                    f"{ultimo.fecha:%Y-%m-%d} {ultimo.descripcion}" if ultimo else ""])
    return resp


@solo_admin
def exportar_json(request):
    """Copia íntegra de los datos del seguimiento (sin usuarios ni contraseñas) en JSON."""
    buf = io.StringIO()
    call_command("dumpdata", "seguimiento", exclude=["seguimiento.perfilusuario"], indent=1, stdout=buf)
    resp = HttpResponse(buf.getvalue(), content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="acuerdos_datos_{timezone.localdate():%Y%m%d}.json"'
    return resp
