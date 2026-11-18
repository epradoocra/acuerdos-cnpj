"""Carga los acuerdos de un acta desglosada en un módulo de ``seguimiento/datos`` (mismo formato que ``liv_2026``).

    python manage.py cargar_acta zc_2026_1 --simular   # muestra lo que cargaría y deshace los cambios
    python manage.py cargar_acta zc_2026_1

El módulo define REUNION, ACUERDOS e INFERIDOS, y opcionalmente GRUPOS_ENTREGA ({"zona": [siglas, ...]}) y
TEMAS_NUEVOS ([(nombre, color), ...]). Es idempotente como ``cargar_liv``: no duplica registros ni sobrescribe
el avance capturado ni la validación de responsables que ya hizo la Secretaría Técnica.
"""
import importlib
from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from seguimiento.datos import catalogos
from seguimiento.datos.liv_2026 import UN_MES
from seguimiento.models import Acuerdo, Compromiso, Entrega, Institucion, Organo, Reunion, Tema

from .cargar_liv import Command as CargarLiv, sumar_un_mes


class Simulacion(Exception):
    pass


class Command(BaseCommand):
    help = "Carga los acuerdos de un acta desglosada en seguimiento/datos/<modulo>.py."

    def add_arguments(self, parser):
        parser.add_argument("modulo", help="Nombre del módulo en seguimiento/datos, p. ej. zc_2026_1")
        parser.add_argument("--simular", action="store_true", help="Muestra el resultado y deshace los cambios")

    def handle(self, *args, **opts):
        try:
            datos = importlib.import_module(f"seguimiento.datos.{opts['modulo']}")
        except ModuleNotFoundError as exc:
            raise CommandError(f"No existe seguimiento/datos/{opts['modulo']}.py") from exc
        try:
            with transaction.atomic():
                self._cargar(datos)
                if opts["simular"]:
                    raise Simulacion
        except Simulacion:
            self.stdout.write(self.style.WARNING("Simulación: no se guardó ningún cambio."))

    def _cargar(self, datos):
        base = CargarLiv(stdout=self.stdout, stderr=self.stderr)
        base._grupos()
        inst = base._instituciones()
        for nombre, color in list(catalogos.TEMAS) + list(getattr(datos, "TEMAS_NUEVOS", [])):
            Tema.objects.get_or_create(nombre=nombre, defaults={"color": color})
        temas = {t.nombre: t for t in Tema.objects.all()}

        estatales = [i for i in inst.values() if i.tipo == Institucion.Tipo.ESTATAL]
        grupos = {"estatales": estatales, "pleno": estatales + [inst["FGR"]]}
        for nombre, siglas in getattr(datos, "GRUPOS_ENTREGA", {}).items():
            faltan = [s for s in siglas if s not in inst]
            if faltan:
                raise CommandError(f"Grupo '{nombre}': instituciones inexistentes {faltan}")
            grupos[nombre] = [inst[s] for s in siglas]

        r = datos.REUNION
        siglas_org, nombre_org = r["organo"]
        organo, _ = Organo.objects.get_or_create(siglas=siglas_org, defaults={"nombre": nombre_org})
        reunion, creada = Reunion.objects.get_or_create(
            organo=organo, numero=r["numero"], tipo=r["tipo"],
            defaults={"numeral": r["numeral"], "nombre": r["nombre"]},
        )
        for campo in ("fecha", "sede", "modalidad", "observaciones"):
            if r.get(campo):
                setattr(reunion, campo, r[campo])
        reunion.save()

        anio = r.get("anio") or (r["fecha"].year if r.get("fecha") else None)
        if not anio:
            raise CommandError("REUNION debe indicar 'anio' o 'fecha' para formar las claves.")
        inferidos = getattr(datos, "INFERIDOS", {})
        n_comp = n_ent = n_quitadas = 0
        for a in datos.ACUERDOS:
            acuerdo, _ = Acuerdo.objects.update_or_create(
                clave=f"{siglas_org}/{r['numeral']}/{a['numero']:02d}/{anio}",
                defaults={
                    "reunion": reunion, "numero": a["numero"], "titulo": a["titulo"], "texto": a["texto"],
                    "naturaleza": a["naturaleza"], "responsable": inst[a["responsable"]],
                },
            )
            acuerdo.temas.set([temas[t] for t in a["temas"]])
            for c in a["compromisos"]:
                limite = c["fecha"]
                if limite == UN_MES:
                    limite = sumar_un_mes(reunion.fecha) if reunion.fecha else None
                nota = inferidos.get((a["numero"], c["inciso"]), "")
                valores = {
                    "descripcion": c["descripcion"], "responsable": inst[c["responsable"]],
                    "fecha_limite": limite, "plazo_texto": c["plazo"], "entregable": c["entregable"],
                    "requiere_entregas": bool(c["entregas"]), "nota_asignacion": nota,
                }
                comp, _ = Compromiso.objects.update_or_create(
                    acuerdo=acuerdo, inciso=c["inciso"], defaults=valores,
                    create_defaults={**valores, "responsable_validado": not nota},
                )
                comp.corresponsables.set([inst[s] for s in c["corresponsables"]])
                n_comp += 1
                if c["entregas"] and c["entregas"] not in grupos:
                    raise CommandError(f"Acuerdo {a['numero']} inciso {c['inciso']}: grupo '{c['entregas']}' no definido")
                obligadas = grupos.get(c["entregas"], [])
                for institucion in obligadas:
                    n_ent += Entrega.objects.get_or_create(compromiso=comp, institucion=institucion)[1]
                # Si cambió la lista de obligadas, quita las entregas sobrantes que aún no tienen nada capturado.
                sobrantes = comp.entregas.exclude(institucion__in=obligadas).filter(
                    estatus=Entrega.Estatus.PENDIENTE, fecha_entrega__isnull=True, oficio="", nota="", evidencia="")
                n_quitadas += sobrantes.delete()[0]

        self._resumen(reunion, creada, n_comp, n_ent, n_quitadas)

    def _resumen(self, reunion, creada, n_comp, n_ent, n_quitadas):
        out = self.stdout.write
        out(self.style.SUCCESS(
            f"{reunion} ({reunion.fecha or 'sin fecha'}): {reunion.acuerdos.count()} acuerdos, {n_comp} compromisos, "
            f"{n_ent} entregas nuevas, {n_quitadas} entregas sobrantes quitadas "
            f"({'reunión creada' if creada else 'reunión actualizada'})."))
        for a in reunion.acuerdos.prefetch_related("temas", "compromisos__corresponsables", "compromisos__entregas"):
            out(f"\n{a.clave}  [{a.get_naturaleza_display()}]  {a.titulo}")
            out(f"    temas: {', '.join(t.nombre for t in a.temas.all()) or '—'} | coordina: {a.responsable}")
            for c in a.compromisos.all():
                corr = f" + {', '.join(i.siglas for i in c.corresponsables.all())}" if c.corresponsables.exists() else ""
                ent = Counter(e.institucion.siglas for e in c.entregas.all())
                out(f"    {c.inciso:>2}. {c.descripcion}")
                out(f"        responsable: {c.responsable}{corr}{'' if c.responsable_validado else '  (POR VALIDAR)'}"
                    f" | entregable: {c.entregable or '—'} | plazo: {c.plazo_texto or c.fecha_limite or '—'}"
                    f"{f' | entregas: {len(ent)} ({chr(44).join(sorted(ent))})' if ent else ''}")
            if not a.compromisos.exists():
                out("    (sin compromisos: el acuerdo surte efecto en la sesión)")
        pendientes = Compromiso.objects.filter(acuerdo__reunion=reunion, responsable_validado=False).count()
        out(f"\n{pendientes} compromisos con responsable por validar.")
