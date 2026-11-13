# Imagen con el ODBC Driver 18 de Microsoft. Se usa para migrar los datos a SQL Server desde Windows
# (migracion/migrar.ps1) y sirve también para publicar como contenedor si se prefiere a App Service con código.
FROM docker.io/library/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gnupg ca-certificates \
 && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
 && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
 && apt-get purge -y curl gnupg && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN sed -i 's/\r$//' startup.sh && chmod +x startup.sh \
 && DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput -v 0

EXPOSE 8000
CMD ["./startup.sh"]
