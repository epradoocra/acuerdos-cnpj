#!/bin/sh
# Comando de inicio en Azure App Service (Configuración > Configuración general > Comando de inicio: startup.sh)
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput -v 0

# Carga inicial opcional de los acuerdos de la LIV sesión (no es necesaria si se migraron los datos).
if [ "${CARGAR_LIV:-0}" = "1" ]; then
    python manage.py cargar_liv ${LIV_FECHA:+--fecha "$LIV_FECHA"} ${LIV_SEDE:+--sede "$LIV_SEDE"}
fi

# Superusuario inicial si se definieron las variables y aún no existe.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@localhost}" 2>/dev/null \
        || echo "Superusuario '$DJANGO_SUPERUSER_USERNAME' ya existe."
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 120 --access-logfile -
