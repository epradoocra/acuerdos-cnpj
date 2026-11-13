# Propuesta: Sistema de Seguimiento de Acuerdos (SSA)

Plataforma web para dar seguimiento, reunión por reunión, al cumplimiento de los acuerdos de órganos
colegiados. El primer caso de uso es la **LIV Asamblea Plenaria de la Conferencia Nacional de Procuración
de Justicia (CNPJ)**, cuyos 18 acuerdos ya vienen precargados.

## 1. Lo que muestra el documento de la LIV sesión

| Hallazgo | Implicación para la plataforma |
|---|---|
| 18 acuerdos, cada uno con clave `CNPJ/LIV/NN/2026`. | La clave es el identificador único; la reunión se reconoce por su numeral (LIV). |
| Un mismo acuerdo contiene varias acciones (incisos a–d, numerales 1–4, párrafos adicionales). | El acuerdo **no** es la unidad de seguimiento: se desglosa en **compromisos** verificables (46 en total). |
| Hay acuerdos de distinta naturaleza: aprobación (01, 04, 05, 09, 10, 16), toma de conocimiento (02, 06, 08, 12, 13, 15, 17, 18), exhorto (03 y parte del 07) y compromiso de las partes (11, 14). | Se clasifica cada acuerdo por naturaleza para filtrar y reportar. |
| Muchos compromisos obligan a **las 32 fiscalías** (o a todo el Pleno) al mismo tiempo: observaciones, carga de información, actualización de registros, capacitación. | Cada compromiso colectivo genera una **entrega por institución** (515 en total), con su oficio y evidencia. El avance se calcula como "entregadas / obligadas". |
| Solo 5 compromisos tienen plazo explícito: 31 ago 2026 (07 y 16), mediados de sep 2026 (16), 31 dic 2026 (11) y "un mes" (10). | Se guarda el plazo **tal como lo dice el acuerdo** y, aparte, una fecha límite calculable. Los compromisos sin fecha se muestran como tales para que la Secretaría Técnica los calendarice. |
| El documento **no indica la fecha ni la sede de la sesión**. Según la prensa, se celebró en Nayarit y concluyó a más tardar el 13 de agosto de 2026. | Se cargó el **13/08/2026 como fecha provisional** (variable `LIV_FECHA`), de la que depende el plazo de "un mes" del acuerdo 10 (13/09/2026). Debe confirmarse con el acta. |
| En 25 de los 46 compromisos el texto **no nombra al responsable** (p. ej. "se instruye: a) su difusión…"). | Se asignó un responsable por inferencia y se marcó **"por validar"**, con el criterio aplicado, para que la Secretaría Técnica lo confirme o lo corrija. |
| Intervienen ~45 instancias: Presidencia y Secretaría Técnica, FGR y sus áreas (CFIC, CFPF, FEMDH, FECOR, AIC), SESNSP, INACIPE, CNI, ATDT, UNAM y las 32 fiscalías estatales. | Catálogo de instituciones con responsable y corresponsables por compromiso. |
| Al corte de hoy (12 nov 2026) ya vencieron los plazos de agosto y septiembre. | El tablero los marca en rojo hasta que se registre su cumplimiento. |

## 2. Modelo de información

```
Órgano colegiado (CNPJ)
 └── Reunión (LIV Asamblea Plenaria · fecha · sede · modalidad · acta)
      └── Acuerdo (CNPJ/LIV/07/2026 · texto íntegro · naturaleza · temas · coordinador)
           └── Compromiso (inciso · descripción · responsable · corresponsables ·
                │           fecha límite · plazo textual · entregable · estatus · % avance)
                ├── Entrega por institución (32 fiscalías / Pleno: estatus · fecha · oficio · evidencia)
                └── Bitácora de avances (fecha · nota · % · cambio de estatus · evidencia · quién lo registró)
```

**Estatus y semáforo**

* Compromiso: *Pendiente → En proceso → Cumplido* (o *Cancelado / sin materia*).
* Se considera **vencido** si la fecha límite pasó y no está cumplido (rojo); **ámbar** si vence en ≤ 30 días.
* El estatus del acuerdo se deriva de sus compromisos: cumplido cuando todos lo están, vencido si alguno lo está.

## 3. Funcionalidad

| Módulo | Qué permite |
|---|---|
| **Tablero** | Indicadores globales (cumplidos, en proceso, sin iniciar, vencidos), semáforo por acuerdo de cada reunión, lista de vencidos y de lo que vence en 30 días, carga por institución. |
| **Reunión** | Los acuerdos de la sesión con avance y estatus, filtros por estatus, exportación a CSV (Excel). |
| **Acuerdo** | Texto íntegro, compromisos derivados, matriz de entregas de las 32 fiscalías, bitácora y captura de avances con evidencia. |
| **Institución** | "Mis pendientes": compromisos como responsable/corresponsable y entregas que le corresponden. |
| **Administración** | Alta de nuevas reuniones, acuerdos y compromisos; catálogos; usuarios y permisos. |

**Roles** (grupos de Django, creados automáticamente)

* **Secretaría Técnica**: captura y administra todo.
* **Enlace institucional**: consulta, registra avances y actualiza entregas.
* **Consulta**: solo lectura (titulares, órganos de control).

## 4. Arquitectura

```
┌──────────── Podman ────────────┐
│  acuerdos-web   (Django 5.2 +  │  :8000
│                  Gunicorn)     │──────► navegador
│        │  red acuerdos-net     │
│  acuerdos-db    (PostgreSQL 16)│
└────────────────────────────────┘
 volúmenes: acuerdos-pgdata (BD) · acuerdos-media (evidencias)
```

* Las evidencias no se publican en una ruta abierta: se descargan por una vista que exige sesión.
* Sin dependencias de CDN: funciona en redes institucionales cerradas.

## 5. Siguientes fases sugeridas

1. **Notificaciones**: correo a responsables 15 y 5 días antes del vencimiento, y resumen semanal a la Secretaría Técnica.
2. **Restringir enlaces a su institución**: vincular cada usuario con su fiscalía para que solo edite sus entregas.
3. **Informe para el Pleno**: generar en PDF el reporte de cumplimiento de la sesión anterior, como insumo del orden del día de la siguiente.
4. **Carga asistida**: importar nuevos documentos de acuerdos (PDF) y proponer el desglose en compromisos para validación humana.
5. **Respaldo programado** de `acuerdos-pgdata` y `acuerdos-media`, y HTTPS mediante un proxy inverso.
