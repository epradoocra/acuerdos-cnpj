# Sistema de Seguimiento de Acuerdos

Plataforma web (Django 5.2) para dar seguimiento, reunión por reunión, al cumplimiento de los acuerdos de la
Conferencia Nacional de Procuración de Justicia. Versión para la nube: **Azure SQL Database** (Microsoft SQL Server)
y **Azure App Service**, publicada automáticamente desde GitHub. La propuesta funcional está en [PROPUESTA.md](PROPUESTA.md)
y el manual de usuario dentro del sistema (menú **Manual**).

## Arquitectura

```
GitHub (rama main) ──GitHub Actions──► Azure App Service (Linux, Python 3.12, gunicorn)
                                              │  ODBC Driver 18, conexión cifrada
                                              ▼
                                       Azure SQL Database
```

| Variable | Uso |
|---|---|
| `MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_DB`, `MSSQL_USER`, `MSSQL_PASSWORD` | Conexión a SQL Server / Azure SQL |
| `MSSQL_DRIVER` | Controlador ODBC (predeterminado `ODBC Driver 18 for SQL Server`) |
| `DJANGO_SECRET_KEY` | Cadena larga y aleatoria, distinta en cada ambiente |
| `DJANGO_MEDIA_ROOT` | En Azure: `/home/media` (almacenamiento persistente de evidencias y actas) |
| `DJANGO_MODO_PRUEBA` | `1` permite a cualquier usuario agregar y modificar datos (muestra un aviso); `0` en producción |
| `CARGAR_LIV` | `1` carga los acuerdos de la LIV sesión al arrancar; `0` si los datos se migraron |

Sin `MSSQL_HOST` el sistema usa PostgreSQL (si hay `POSTGRES_HOST`) o SQLite para desarrollo local.
En Azure, el dominio `*.azurewebsites.net` se admite automáticamente y las cookies se marcan como seguras.

## 1. Crear los recursos en Azure

1. **Azure SQL Database**: cree un servidor lógico y una base (`acuerdos`). En *Redes* agregue la IP pública del
   equipo desde el que se hará la migración y active *Permitir que los servicios de Azure accedan a este servidor*.
2. **App Service** (Linux, pila *Python 3.12*). En *Configuración*:
   - *Variables de entorno*: las de la tabla anterior, más `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
   - *Configuración general → Comando de inicio*: `startup.sh`.
   - *Configuración general*: active **Solo HTTPS**.

## 2. Migrar los datos actuales

Con el sistema anterior en ejecución (contenedor `acuerdos-web`) y Podman disponible:

```powershell
copy .env.example .env          # capture los datos de conexión MSSQL_*
.\migracion\migrar.ps1
```

El script exporta todos los datos (incluidos usuarios y perfiles), crea la estructura en SQL Server con las
migraciones de Django, carga los datos y compara tabla por tabla el número de registros. Usa un contenedor con el
ODBC Driver 18, por lo que no es necesario instalar controladores en Windows. Los archivos exportados quedan en
`migracion/` y **están excluidos de Git** porque contienen las contraseñas cifradas de los usuarios.

Si hay evidencias (`migracion/evidencias_actuales.tgz` no vacío), súbalas al App Service y extráigalas en `/home`
(Herramientas avanzadas → Kudu → Bash: `tar xzf evidencias_actuales.tgz -C /home`).

## 3. Publicar desde GitHub

1. Cree el repositorio en GitHub y suba el código:
   ```powershell
   git remote add origin https://github.com/<organizacion>/<repositorio>.git
   git push -u origin main
   ```
2. En GitHub, *Settings → Secrets and variables → Actions*:
   - Variable `AZURE_WEBAPP_NAME` = nombre del App Service.
   - Secreto `AZURE_WEBAPP_PUBLISH_PROFILE` = contenido del perfil de publicación (portal de Azure → App Service →
     *Descargar perfil de publicación*; requiere tener habilitada la autenticación básica de SCM).
3. Cada `push` a `main` ejecuta [.github/workflows/azure-webapp.yml](.github/workflows/azure-webapp.yml): revisa la
   configuración y las migraciones y, si todo está bien, publica. Al arrancar, `startup.sh` aplica migraciones
   pendientes y recopila los archivos estáticos.

## Desarrollo local

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
$env:DJANGO_DEBUG=1
.\venv\Scripts\python manage.py migrate
.\venv\Scripts\python manage.py cargar_liv --fecha 2026-08-13 --sede Nayarit
.\venv\Scripts\python manage.py createsuperuser
.\venv\Scripts\python manage.py runserver
```

Para trabajar contra SQL Server en local se necesita el *ODBC Driver 18 for SQL Server* instalado en Windows y las
variables `MSSQL_*` definidas.

## Búsqueda sin acentos

En SQL Server el buscador compara con la intercalación `Latin1_General_100_CI_AI` (no distingue mayúsculas ni
acentos), sin requerir cambios en la base. En PostgreSQL usa la extensión `unaccent`.

## Estructura

```
config/                  configuración (bases de datos, Azure, seguridad)
seguimiento/             modelos, vistas, captura, administración, búsqueda, importador de acuerdos
  management/commands/   cargar_liv, conteo_datos
templates/               base, inicio de sesión, cuenta
migracion/migrar.ps1     migración de PostgreSQL a SQL Server
startup.sh               arranque en Azure App Service
Containerfile            imagen con ODBC Driver 18 (migración o despliegue como contenedor)
.github/workflows/       publicación automática en Azure
```
