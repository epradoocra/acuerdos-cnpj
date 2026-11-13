# Habilita la extensión unaccent de PostgreSQL para que el buscador ignore acentos.
# En otras bases de datos (SQLite de desarrollo) la operación no hace nada.
from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("seguimiento", "0002_validacion_responsable"),
    ]

    operations = [UnaccentExtension()]
