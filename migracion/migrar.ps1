<#
.SYNOPSIS
  Migra los datos actuales del sistema (PostgreSQL local, contenedor acuerdos-web) a Microsoft SQL Server / Azure SQL.

.DESCRIPTION
  1. Exporta los datos del sistema actual: reuniones, acuerdos, compromisos, entregas, bitácora, catálogos,
     usuarios (con sus contraseñas cifradas), perfiles y grupos. También exporta las evidencias.
  2. Construye una imagen con el ODBC Driver 18 de Microsoft (no requiere instalar nada en Windows).
  3. Crea la estructura completa en SQL Server (migraciones de Django).
  4. Carga los datos y compara el número de registros de cada tabla entre origen y destino.

  Requisitos: el sistema anterior corriendo (contenedor acuerdos-web), el archivo ..\.env con las variables
  MSSQL_* y la IP de este equipo permitida en el firewall del servidor de Azure SQL.

.EXAMPLE
  .\migracion\migrar.ps1                 # migración completa
  .\migracion\migrar.ps1 -SoloExportar   # solo genera migracion\datos_actuales.json
  .\migracion\migrar.ps1 -Forzar         # carga aunque el destino ya tenga acuerdos (puede duplicar o fallar)
#>
param([switch]$SoloExportar, [switch]$Forzar)

$ErrorActionPreference = "Continue"   # PowerShell 5.1 convierte stderr de podman en errores; se usa $LASTEXITCODE
$Proyecto = Split-Path $PSScriptRoot -Parent
$Datos    = Join-Path $PSScriptRoot "datos_actuales.json"
$Media    = Join-Path $PSScriptRoot "evidencias_actuales.tgz"
$Origen   = "acuerdos-web"
$Imagen   = "localhost/acuerdos-azure:latest"
$Conteo   = "import json; from django.apps import apps; print(json.dumps({m._meta.label_lower: m.objects.count() for a in ['seguimiento', 'auth'] for m in apps.get_app_config(a).get_models() if m._meta.label_lower != 'auth.permission'}, sort_keys=True))"

function Paso($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }
function Falla($t) { Write-Host "ERROR: $t" -ForegroundColor Red; exit 1 }

# ------------------------------------------------------------------------------------------- 1. exportar
Paso "1/5 Exportando los datos del sistema actual ($Origen)"
podman container exists $Origen
if ($LASTEXITCODE -ne 0) { Falla "No existe el contenedor $Origen. Inicie el sistema anterior (iniciar.bat)." }
podman start $Origen | Out-Null

# Claves naturales: los permisos y tipos de contenido se regeneran en el destino con otros identificadores.
podman exec $Origen python manage.py dumpdata --natural-foreign --natural-primary `
    -e contenttypes -e auth.permission -e admin.logentry -e sessions --indent 1 -o /tmp/datos.json
if ($LASTEXITCODE -ne 0) { Falla "Falló dumpdata en el origen." }
podman cp "${Origen}:/tmp/datos.json" $Datos | Out-Null
podman exec $Origen rm -f /tmp/datos.json
$cuentaOrigen = (podman exec $Origen python manage.py shell -v 0 -c $Conteo | Select-Object -Last 1) | ConvertFrom-Json

podman exec $Origen tar czf /tmp/evidencias.tgz -C /app media
podman cp "${Origen}:/tmp/evidencias.tgz" $Media | Out-Null
podman exec $Origen rm -f /tmp/evidencias.tgz
$archivos = @(podman exec $Origen find /app/media -type f).Count
Write-Host ("   {0:N0} KB de datos; {1} archivo(s) de evidencia." -f ((Get-Item $Datos).Length / 1KB), $archivos)
Write-Host "   $Datos" -ForegroundColor DarkGray
Write-Host "   (contiene usuarios y contraseñas cifradas: no lo comparta ni lo suba a GitHub)" -ForegroundColor Yellow
if ($SoloExportar) { exit 0 }

# ------------------------------------------------------------------------------------------- 2. configuración
Paso "2/5 Verificando la configuración de SQL Server"
$envArchivo = Join-Path $Proyecto ".env"
if (-not (Test-Path $envArchivo)) { Falla "Falta $envArchivo. Copie .env.example a .env y capture los datos de conexión." }
$vars = @{}
Get-Content $envArchivo | Where-Object { $_ -match '^\s*([A-Z_]+)=(.*)$' } | ForEach-Object { $vars[$Matches[1]] = $Matches[2].Trim() }
foreach ($v in "MSSQL_HOST", "MSSQL_DB", "MSSQL_USER", "MSSQL_PASSWORD") {
    if (-not $vars[$v] -or $vars[$v] -match 'miservidor|cambie-esta') { Falla "Capture $v en .env." }
}
# Copia con saltos de línea Unix: un .env guardado con CRLF dejaría un \r al final de la contraseña.
$envLimpio = Join-Path $env:TEMP "acuerdos-mssql.env"
[IO.File]::WriteAllText($envLimpio, ((Get-Content $envArchivo) -join "`n") + "`n")
Write-Host "   Servidor: $($vars.MSSQL_HOST)  Base: $($vars.MSSQL_DB)  Usuario: $($vars.MSSQL_USER)"

function EnDestino {
    podman run --rm --env-file $envLimpio -e DJANGO_SECRET_KEY=migracion -v "${PSScriptRoot}:/datos" $Imagen @args
}

# ------------------------------------------------------------------------------------------- 3. imagen
Paso "3/5 Preparando la imagen con el ODBC Driver 18"
podman build -t $Imagen -f (Join-Path $Proyecto "Containerfile") $Proyecto | Select-Object -Last 1
if ($LASTEXITCODE -ne 0) { Falla "No se pudo construir la imagen." }

# ------------------------------------------------------------------------------------------- 4. estructura
Paso "4/5 Creando la estructura en SQL Server (migraciones)"
EnDestino python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) {
    Falla ("No se pudo crear la estructura. Revise: datos de conexión en .env, que la IP pública de este equipo " +
           "esté permitida en el firewall del servidor de Azure SQL, y que el usuario tenga permisos db_owner.")
}
$cuentaPrevia = (EnDestino python manage.py conteo_datos | Select-Object -Last 1) | ConvertFrom-Json
if ($cuentaPrevia.'seguimiento.acuerdo' -gt 0 -and -not $Forzar) {
    Falla "El destino ya tiene $($cuentaPrevia.'seguimiento.acuerdo') acuerdos. Para no duplicar, no se cargó nada (use -Forzar si está seguro)."
}

# ------------------------------------------------------------------------------------------- 5. datos
Paso "5/5 Cargando los datos y verificando"
EnDestino python manage.py loaddata /datos/datos_actuales.json
if ($LASTEXITCODE -ne 0) { Falla "Falló la carga de datos." }
$cuentaDestino = (EnDestino python manage.py conteo_datos | Select-Object -Last 1) | ConvertFrom-Json

$diferencias = 0
$filas = foreach ($p in $cuentaOrigen.PSObject.Properties) {
    $d = $cuentaDestino.($p.Name)
    if ($d -ne $p.Value) { $diferencias++ }
    [pscustomobject]@{ Tabla = $p.Name; Origen = $p.Value; Destino = $d; Estado = $(if ($d -eq $p.Value) { "OK" } else { "DIFERENTE" }) }
}
$filas | Format-Table -AutoSize | Out-Host
Remove-Item $envLimpio -ErrorAction SilentlyContinue

if ($diferencias) { Falla "$diferencias tabla(s) con diferencias. Revise antes de publicar." }
Write-Host "Migración completa: todas las tablas coinciden." -ForegroundColor Green
if ($archivos -gt 0) {
    Write-Host "Hay $archivos archivo(s) de evidencia en $Media; súbalos a /home/media del App Service (ver README)." -ForegroundColor Yellow
}
