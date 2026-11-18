# Habilita la extensión unaccent de PostgreSQL para que el buscador ignore acentos.
# En otras bases de datos (SQL Server, SQLite) no hace nada.
#
# No se usa django.contrib.postgres.operations.UnaccentExtension porque importarla carga psycopg aunque la base
# no sea PostgreSQL; en Windows con Control de aplicaciones activo la DLL de psycopg está bloqueada y el sistema
# no arranca. Esta versión ejecuta el mismo SQL solo cuando el motor es PostgreSQL.
from django.db import migrations


def crear(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def quitar(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP EXTENSION IF EXISTS unaccent")


class Migration(migrations.Migration):
    dependencies = [
        ("seguimiento", "0002_validacion_responsable"),
    ]

    operations = [migrations.RunPython(crear, quitar)]
