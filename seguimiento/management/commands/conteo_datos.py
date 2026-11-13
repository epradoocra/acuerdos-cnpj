"""Imprime en JSON cuántos registros hay por modelo. Sirve para comparar origen y destino de una migración."""
import json

from django.apps import apps
from django.core.management.base import BaseCommand

APPS = ["seguimiento", "auth"]
EXCLUIR = {"auth.permission"}


class Command(BaseCommand):
    help = "Cuenta los registros de cada modelo del sistema (formato JSON)."

    def handle(self, *args, **opts):
        conteo = {}
        for etiqueta in APPS:
            for modelo in apps.get_app_config(etiqueta).get_models():
                nombre = modelo._meta.label_lower
                if nombre not in EXCLUIR:
                    conteo[nombre] = modelo.objects.count()
        self.stdout.write(json.dumps(conteo, sort_keys=True))
