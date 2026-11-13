# Contexto del proyecto — Sistema de Seguimiento de Acuerdos (versión nube)

Traspaso desde la sesión que construyó el sistema en `C:\Users\usuario\Documents\ocra\acuerdos` (versión local:
PostgreSQL + Podman). Esta carpeta es la **versión para la nube**: Azure SQL Database + Azure App Service,
publicada con GitHub Actions. Idioma de trabajo con el usuario: **español**. Plataforma: Windows 11, PowerShell 5.1.

## Qué es el sistema
Django 5.2 para dar seguimiento, reunión por reunión, a los acuerdos de la Conferencia Nacional de Procuración de
Justicia (CNPJ). Caso inicial: LIV Asamblea Plenaria (18 acuerdos → 46 compromisos → 515 entregas por institución).
Modelo: `Organo → Reunion → Acuerdo → Compromiso → (Entrega por institución, Avance/bitácora)`, más `Institucion`,
`Tema`, `PerfilUsuario` (usuario ↔ institución). Ver `PROPUESTA.md` y el manual en `seguimiento/templates/seguimiento/manual.html`.

Funcionalidad ya hecha: tablero con semáforo, buscador general (palabras/frases, sin acentos), captura propia de
reuniones/acuerdos/compromisos/catálogos, importador de acuerdos desde texto pegado del PDF (`seguimiento/importar.py`),
administración propia (`/administracion/`: panel, usuarios, validar responsables, exportar), "Mi cuenta",
modo de prueba (`DJANGO_MODO_PRUEBA=1`: cualquier usuario agrega/modifica; borrar y usuarios siguen restringidos),
enlaces ligados a su institución (solo editan sus entregas).

Perfiles (grupos, creados por `manage.py cargar_liv`): Administrador del sistema, Secretaría Técnica,
Enlace institucional, Consulta.

## Cambios de esta versión respecto a la local
- `config/settings.py`: prioridad de BD `MSSQL_HOST` (mssql-django, ODBC Driver 18, `Encrypt=yes`) → `POSTGRES_HOST` → SQLite.
  En Azure (`WEBSITE_HOSTNAME`) agrega el host a ALLOWED_HOSTS/CSRF, `SECURE_PROXY_SSL_HEADER` y cookies seguras.
  `django.contrib.postgres` solo se instala con PostgreSQL. `psycopg` sigue en requirements porque la migración
  `0003_extension_unaccent` importa `django.contrib.postgres.operations` (es no-op fuera de PostgreSQL).
- `seguimiento/busqueda.py`: en SQL Server usa `IContains(Collate(F(campo), "Latin1_General_100_CI_AI"), normalizar(t))`.
  Verificado el SQL generado: `UPPER(col COLLATE [Latin1_General_100_CI_AI]) LIKE UPPER(%s)` con parámetros sin acentos.
- `seguimiento/management/commands/conteo_datos.py`: conteo JSON por modelo (comparar origen/destino).
- `startup.sh` (comando de inicio en App Service), `.github/workflows/azure-webapp.yml`, `Containerfile`
  (python:3.12-slim-**bookworm** + msodbcsql18; no usar slim a secas: es Debian 13 y el repo de Microsoft configurado es Debian 12).
- Se excluyeron de esta versión: instalador sin red, `podman.ps1`, `compose.yaml`, `iniciar/detener.bat` (siguen en la versión local).
- Textos de respaldo en plantillas apuntan a los respaldos automáticos de Azure SQL.

## Estado al traspaso (2026-11-13)
- Probado: las 81 pruebas existentes pasan en esta carpeta (SQLite); `manage.py check` pasa con el motor `mssql`
  dentro de la imagen `localhost/acuerdos-azure:latest` (ODBC Driver 18.7.1 instalado y funcionando).
- **Datos exportados** de la versión local: `migracion/datos_actuales.json` (641 objetos: 1 usuario `admin`,
  4 grupos, 45 instituciones, 10 temas, 1 reunión, 18 acuerdos, 46 compromisos, 515 entregas; 0 evidencias).
  Ensayo de carga en base vacía: conteos idénticos, hash de contraseña y permisos de grupos (claves naturales) correctos.
  **Contiene hashes de contraseñas: está en .gitignore, nunca subirlo.**
- Git: rama `main`, commit `19046df` "Respaldo inicial del sistema de seguimiento de acuerdos CNPJ" (autor epradoocra),
  remoto `origin` = https://github.com/epradoocra/acuerdos-cnpj.git. Verificado que el commit NO contiene `.env`,
  `migracion/*.json|*.tgz`, `venv/` ni bases locales. Este `CLAUDE.md` quedó en *stage*, pendiente de commit.
- `venv/` de esta carpeta lo creó el usuario y está vacío; para pruebas se usó el venv de la versión local
  (`C:\Users\usuario\Documents\ocra\acuerdos\venv\Scripts\python.exe`).

## Pendiente (siguiente paso)
1. El usuario debe crear `.env` (desde `.env.example`) con `MSSQL_HOST`, `MSSQL_DB`, `MSSQL_USER`, `MSSQL_PASSWORD`
   — pedirle que lo escriba en el archivo, no por chat — y permitir la IP de este equipo en el firewall de Azure SQL
   (usuario con `db_owner`).
2. Ejecutar `.\migracion\migrar.ps1` (desde esta carpeta). Re-exporta del contenedor `acuerdos-web` de la versión
   local (debe estar corriendo: `iniciar` en `ocra\acuerdos`), construye la imagen, `migrate`, `loaddata` y compara
   conteos. Se niega a cargar si el destino ya tiene acuerdos (salvo `-Forzar`). No se ha probado aún contra un
   SQL Server real: vigilar `IDENTITY_INSERT` al cargar PKs explícitas (mssql-django debería manejarlo) y el tiempo
   de conexión si la base es *serverless*.
3. Confirmar si ya se hizo push a GitHub (`git status -sb`); incluir `CLAUDE.md` en el siguiente commit si el usuario lo aprueba.
4. Configurar en GitHub: variable `AZURE_WEBAPP_NAME`, secreto `AZURE_WEBAPP_PUBLISH_PROFILE`. En App Service:
   comando de inicio `startup.sh`, variables de entorno (`MSSQL_*`, `DJANGO_SECRET_KEY`, `DJANGO_MEDIA_ROOT=/home/media`,
   `DJANGO_MODO_PRUEBA`, `CARGAR_LIV=0`, `SCM_DO_BUILD_DURING_DEPLOYMENT=true`) y "Solo HTTPS".
   Supuesto pendiente de confirmar: que el destino es Azure App Service + Azure SQL.

## Notas prácticas del entorno
- PowerShell 5.1: no usar `2>&1` con ejecutables; `$ErrorActionPreference="Continue"` y revisar `$LASTEXITCODE`.
  Los `.ps1` con acentos deben guardarse en UTF-8 **con BOM**. `Set-Content -Encoding ascii` destruye acentos.
  Las variables no distinguen mayúsculas (`$origen` pisa a `$Origen`).
- Git Bash convierte rutas tipo `/prueba` en argumentos de podman: usar `MSYS_NO_PATHCONV=1`.
- Podman 6.1.4 sobre WSL; la máquina `podman-machine-default` también corre `ollama` del usuario: **no detener la máquina**.
- Hechos verificados de los datos: fecha de la LIV sesión provisional 13/08/2026 (Nayarit); BCS e Hidalgo siguen siendo
  Procuradurías; 25 compromisos tienen responsable "por validar" (asignado por criterio).
