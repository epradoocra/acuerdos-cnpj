"""Carga catálogos, grupos de permisos y los acuerdos de la LIV sesión de la CNPJ.

Es idempotente: puede ejecutarse varias veces sin duplicar registros ni
sobrescribir el avance capturado (estatus, porcentaje, entregas, bitácora).

    python manage.py cargar_liv --fecha 2026-06-25 --sede "Ciudad de México"
"""
import calendar
from datetime import date

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from seguimiento.datos import catalogos, liv_2026
from seguimiento.models import Acuerdo, Compromiso, Entrega, Institucion, Organo, Reunion, Tema


def sumar_un_mes(d):
    anio, mes = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1]))


GRUPOS = {
    # Captura y administra todo el seguimiento.
    "Secretaría Técnica": ["view", "add", "change", "delete"],
    # Enlaces de cada institución: consultan, registran avances y actualizan sus entregas.
    "Enlace institucional": ["view", ("add", "avance"), ("change", "entrega")],
    # Solo lectura (titulares, órganos de control).
    "Consulta": ["view"],
    # Todo lo de la Secretaría Técnica, más la gestión de usuarios.
    "Administrador del sistema": ["view", "add", "change", "delete",
                                  ("auth", "view_user"), ("auth", "add_user"), ("auth", "change_user"),
                                  ("auth", "view_group")],
}
MODELOS = ["organo", "institucion", "tema", "reunion", "acuerdo", "compromiso", "entrega", "avance", "perfilusuario"]


class Command(BaseCommand):
    help = "Carga los acuerdos de la LIV Asamblea Plenaria de la CNPJ (2026) y los catálogos base."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", help="Fecha de la sesión (AAAA-MM-DD). Se usa para plazos relativos.")
        parser.add_argument("--sede", default="")
        parser.add_argument("--modalidad", default="presencial", choices=["presencial", "virtual", "hibrida"])

    @transaction.atomic
    def handle(self, *args, **opts):
        fecha = None
        if opts["fecha"]:
            try:
                fecha = date.fromisoformat(opts["fecha"])
            except ValueError as exc:
                raise CommandError("--fecha debe tener formato AAAA-MM-DD") from exc

        self._grupos()
        inst = self._instituciones()
        temas = {nombre: Tema.objects.update_or_create(nombre=nombre, defaults={"color": color})[0]
                 for nombre, color in catalogos.TEMAS}

        estatales = [i for i in inst.values() if i.tipo == Institucion.Tipo.ESTATAL]
        grupos_entrega = {"estatales": estatales, "pleno": estatales + [inst["FGR"]]}

        siglas_org, nombre_org = liv_2026.REUNION["organo"]
        organo, _ = Organo.objects.get_or_create(siglas=siglas_org, defaults={"nombre": nombre_org})
        reunion, creada = Reunion.objects.get_or_create(
            organo=organo, numero=liv_2026.REUNION["numero"], tipo=liv_2026.REUNION["tipo"],
            defaults={"numeral": liv_2026.REUNION["numeral"], "nombre": liv_2026.REUNION["nombre"]},
        )
        if fecha:
            reunion.fecha = fecha
        if opts["sede"]:
            reunion.sede = opts["sede"]
        reunion.modalidad = opts["modalidad"]
        reunion.save()

        n_comp = n_ent = 0
        for datos in liv_2026.ACUERDOS:
            clave = f"{siglas_org}/{reunion.numeral}/{datos['numero']:02d}/2026"
            acuerdo, _ = Acuerdo.objects.update_or_create(
                clave=clave,
                defaults={
                    "reunion": reunion, "numero": datos["numero"], "titulo": datos["titulo"],
                    "texto": datos["texto"], "naturaleza": datos["naturaleza"],
                    "responsable": inst[datos["responsable"]],
                },
            )
            acuerdo.temas.set([temas[t] for t in datos["temas"]])

            for c in datos["compromisos"]:
                limite = c["fecha"]
                if limite == liv_2026.UN_MES:
                    limite = sumar_un_mes(fecha) if fecha else None
                nota = liv_2026.INFERIDOS.get((datos["numero"], c["inciso"]), "")
                comp, _ = Compromiso.objects.update_or_create(
                    acuerdo=acuerdo, inciso=c["inciso"],
                    defaults={
                        "descripcion": c["descripcion"], "responsable": inst[c["responsable"]],
                        "fecha_limite": limite, "plazo_texto": c["plazo"], "entregable": c["entregable"],
                        "requiere_entregas": bool(c["entregas"]), "nota_asignacion": nota,
                    },
                    # La validación solo se fija al crear: una recarga no deshace lo que validó la ST.
                    create_defaults={
                        "descripcion": c["descripcion"], "responsable": inst[c["responsable"]],
                        "fecha_limite": limite, "plazo_texto": c["plazo"], "entregable": c["entregable"],
                        "requiere_entregas": bool(c["entregas"]), "nota_asignacion": nota,
                        "responsable_validado": not nota,
                    },
                )
                comp.corresponsables.set([inst[s] for s in c["corresponsables"]])
                n_comp += 1
                for institucion in grupos_entrega.get(c["entregas"], []):
                    _, nueva = Entrega.objects.get_or_create(compromiso=comp, institucion=institucion)
                    n_ent += nueva

        self.stdout.write(self.style.SUCCESS(
            f"{reunion}: {len(liv_2026.ACUERDOS)} acuerdos, {n_comp} compromisos, {n_ent} entregas nuevas "
            f"({'reunión creada' if creada else 'reunión actualizada'})."
        ))
        pendientes = Compromiso.objects.filter(acuerdo__reunion=reunion, responsable_validado=False).count()
        if pendientes:
            self.stdout.write(f"{pendientes} compromisos con responsable por validar.")
        if not reunion.fecha:
            self.stdout.write(self.style.WARNING(
                "La sesión no tiene fecha: el plazo de 'un mes' del acuerdo 10 quedó sin fecha límite. "
                "Vuelva a ejecutar con --fecha AAAA-MM-DD."
            ))

    def _instituciones(self):
        resultado = {}
        for siglas, nombre, tipo in catalogos.INSTITUCIONES:
            resultado[siglas], _ = Institucion.objects.get_or_create(
                siglas=siglas, defaults={"nombre": nombre, "tipo": tipo})
        for siglas, nombre, entidad in catalogos.fiscalias_estatales():
            obj, _ = Institucion.objects.get_or_create(
                siglas=siglas, defaults={"nombre": nombre, "tipo": "estatal", "entidad_federativa": entidad})
            if obj.nombre.startswith(catalogos.PREFIJO_GENERICO):
                obj.nombre = nombre
                obj.save(update_fields=["nombre"])
            resultado[siglas] = obj
        return resultado

    def _grupos(self):
        for nombre, reglas in GRUPOS.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            seguimiento, auth = [], []
            for regla in reglas:
                if isinstance(regla, tuple) and regla[0] == "auth":
                    auth.append(regla[1])
                elif isinstance(regla, tuple):
                    seguimiento.append(f"{regla[0]}_{regla[1]}")
                else:
                    seguimiento += [f"{regla}_{m}" for m in MODELOS]
            grupo.permissions.set(Permission.objects.filter(
                Q(content_type__app_label="seguimiento", codename__in=seguimiento)
                | Q(content_type__app_label="auth", codename__in=auth)))
