"""Modelo de datos para el seguimiento de acuerdos por reunión.

Jerarquía:
    Organo  ─┬─ Reunion ── Acuerdo ── Compromiso ─┬─ Entrega (una por institución obligada)
             │                                     └─ Avance  (bitácora con evidencia)
    Institucion (responsables, corresponsables y obligados)

* Un **Acuerdo** es el texto aprobado en la sesión (p. ej. CNPJ/LIV/07/2026).
* Un **Compromiso** es cada acción verificable que se desprende del acuerdo
  (incisos a, b, c, d…), con responsable, fecha límite y estatus.
* Una **Entrega** registra el cumplimiento individual cuando el compromiso
  obliga a varias instituciones (p. ej. "las 32 fiscalías enviarán observaciones").
* Un **Avance** es una nota fechada en la bitácora, con evidencia opcional.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Organo(models.Model):
    """Instancia colegiada que sesiona (CNPJ, Consejo Nacional de Seguridad Pública, etc.)."""

    nombre = models.CharField(max_length=200, unique=True)
    siglas = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "órgano colegiado"
        verbose_name_plural = "órganos colegiados"
        ordering = ["siglas"]

    def __str__(self):
        return self.siglas


class Institucion(models.Model):
    class Tipo(models.TextChoices):
        FEDERAL = "federal", "Federal"
        ESTATAL = "estatal", "Fiscalía / Procuraduría estatal"
        INSTANCIA = "instancia", "Instancia de coordinación"
        OTRA = "otra", "Otra"

    nombre = models.CharField(max_length=250, unique=True)
    siglas = models.CharField(max_length=30, unique=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.OTRA)
    entidad_federativa = models.CharField(max_length=60, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        ordering = ["tipo", "nombre"]

    def __str__(self):
        return self.siglas


class Tema(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    color = models.CharField(max_length=7, default="#6b7280", help_text="Color hex para etiquetas")

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Reunion(models.Model):
    class Tipo(models.TextChoices):
        ORDINARIA = "ordinaria", "Ordinaria"
        EXTRAORDINARIA = "extraordinaria", "Extraordinaria"
        TRABAJO = "trabajo", "Reunión de trabajo"

    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        VIRTUAL = "virtual", "Virtual"
        HIBRIDA = "hibrida", "Híbrida"

    organo = models.ForeignKey(Organo, verbose_name="órgano", on_delete=models.PROTECT, related_name="reuniones")
    numero = models.PositiveIntegerField("número", help_text="Número ordinal de la sesión (LIV = 54)")
    numeral = models.CharField(max_length=12, help_text="Numeral romano tal como aparece en las claves, p. ej. LIV")
    nombre = models.CharField(max_length=250)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ORDINARIA)
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices, default=Modalidad.PRESENCIAL)
    fecha = models.DateField(null=True, blank=True)
    sede = models.CharField(max_length=200, blank=True)
    acta = models.FileField(upload_to="actas/%Y/", blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "reunión"
        verbose_name_plural = "reuniones"
        ordering = ["-fecha", "-numero"]
        constraints = [
            models.UniqueConstraint(fields=["organo", "numero", "tipo"], name="reunion_unica_por_organo"),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("seguimiento:reunion", args=[self.pk])


class Acuerdo(models.Model):
    class Naturaleza(models.TextChoices):
        APRUEBA = "aprueba", "Aprobación"
        CONOCIMIENTO = "conocimiento", "Toma de conocimiento"
        INSTRUYE = "instruye", "Instrucción"
        EXHORTO = "exhorto", "Exhorto"
        COMPROMISO = "compromiso", "Compromiso de las partes"

    reunion = models.ForeignKey(Reunion, verbose_name="reunión", on_delete=models.CASCADE, related_name="acuerdos")
    clave = models.CharField(max_length=40, unique=True, help_text="p. ej. CNPJ/LIV/01/2026")
    numero = models.PositiveIntegerField("número")
    titulo = models.CharField("título", max_length=250, help_text="Resumen corto para tableros")
    texto = models.TextField(help_text="Texto íntegro del acuerdo")
    naturaleza = models.CharField(max_length=20, choices=Naturaleza.choices)
    temas = models.ManyToManyField(Tema, blank=True, related_name="acuerdos")
    responsable = models.ForeignKey(
        Institucion, on_delete=models.PROTECT, null=True, blank=True,
        related_name="acuerdos_coordinados", help_text="Instancia que coordina el seguimiento",
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["reunion", "numero"]

    def __str__(self):
        return self.clave

    def get_absolute_url(self):
        return reverse("seguimiento:acuerdo", args=[self.pk])

    @property
    def avance(self):
        """Promedio de avance de sus compromisos (0–100). Sin compromisos = 100."""
        compromisos = [c for c in self.compromisos.all() if c.estatus != Compromiso.Estatus.CANCELADO]
        if not compromisos:
            return 100
        return round(sum(c.avance_efectivo for c in compromisos) / len(compromisos))

    @property
    def estatus(self):
        compromisos = [c for c in self.compromisos.all() if c.estatus != Compromiso.Estatus.CANCELADO]
        if not compromisos or all(c.estatus == Compromiso.Estatus.CUMPLIDO for c in compromisos):
            return "cumplido"
        if any(c.vencido for c in compromisos):
            return "vencido"
        if any(c.estatus != Compromiso.Estatus.PENDIENTE for c in compromisos):
            return "en_proceso"
        return "pendiente"


class Compromiso(models.Model):
    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        CUMPLIDO = "cumplido", "Cumplido"
        CANCELADO = "cancelado", "Cancelado / sin materia"

    acuerdo = models.ForeignKey(Acuerdo, on_delete=models.CASCADE, related_name="compromisos")
    inciso = models.CharField(max_length=10, blank=True, help_text="a, b, 1, 2…")
    descripcion = models.TextField("descripción")
    responsable = models.ForeignKey(Institucion, on_delete=models.PROTECT, related_name="compromisos")
    corresponsables = models.ManyToManyField(Institucion, blank=True, related_name="compromisos_corresponsable")
    responsable_validado = models.BooleanField(
        default=True,
        help_text="Desmarcado cuando el texto del acuerdo no nombra al responsable y este se asignó por inferencia",
    )
    nota_asignacion = models.CharField(
        "nota de asignación",
        max_length=300, blank=True, help_text="Criterio con el que se asignó el responsable, para su validación",
    )
    fecha_limite = models.DateField("fecha límite", null=True, blank=True)
    plazo_texto = models.CharField(
        max_length=200, blank=True,
        help_text="Plazo tal como lo expresa el acuerdo (p. ej. 'un mes', 'último día hábil de agosto')",
    )
    entregable = models.CharField(max_length=250, blank=True, help_text="Producto verificable esperado")
    estatus = models.CharField(max_length=20, choices=Estatus.choices, default=Estatus.PENDIENTE)
    porcentaje = models.PositiveSmallIntegerField(default=0, help_text="Avance capturado manualmente (0–100)")
    requiere_entregas = models.BooleanField(
        default=False, help_text="Marcar si cada institución obligada debe acreditar su cumplimiento por separado",
    )
    fecha_cumplimiento = models.DateField("fecha de cumplimiento", null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["acuerdo", "inciso", "pk"]

    def __str__(self):
        return f"{self.acuerdo.clave} {self.inciso}".strip()

    @property
    def vencido(self):
        return (
            self.fecha_limite is not None
            and self.estatus in (self.Estatus.PENDIENTE, self.Estatus.EN_PROCESO)
            and self.fecha_limite < timezone.localdate()
        )

    @property
    def avance_efectivo(self):
        if self.estatus == self.Estatus.CUMPLIDO:
            return 100
        if self.requiere_entregas:
            entregas = list(self.entregas.all())
            if entregas:
                hechas = sum(1 for e in entregas if e.estatus == Entrega.Estatus.ENTREGADO)
                return round(100 * hechas / len(entregas))
        return self.porcentaje

    @property
    def semaforo(self):
        if self.estatus == self.Estatus.CUMPLIDO:
            return "verde"
        if self.vencido:
            return "rojo"
        if self.fecha_limite and (self.fecha_limite - timezone.localdate()).days <= 30:
            return "ambar"
        return "gris"


class Entrega(models.Model):
    """Cumplimiento individual de una institución frente a un compromiso colectivo."""

    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ENTREGADO = "entregado", "Entregado"
        NO_APLICA = "no_aplica", "No aplica"

    compromiso = models.ForeignKey(Compromiso, on_delete=models.CASCADE, related_name="entregas")
    institucion = models.ForeignKey(Institucion, verbose_name="institución", on_delete=models.PROTECT, related_name="entregas")
    estatus = models.CharField(max_length=20, choices=Estatus.choices, default=Estatus.PENDIENTE)
    fecha_entrega = models.DateField("fecha de entrega", null=True, blank=True)
    oficio = models.CharField(max_length=120, blank=True, help_text="Número de oficio o referencia")
    evidencia = models.FileField(upload_to="entregas/%Y/", blank=True)
    nota = models.TextField(blank=True)

    class Meta:
        ordering = ["institucion__nombre"]
        constraints = [
            models.UniqueConstraint(fields=["compromiso", "institucion"], name="entrega_unica"),
        ]

    def __str__(self):
        return f"{self.compromiso} — {self.institucion}"


class Avance(models.Model):
    """Bitácora de seguimiento: cada nota queda fechada y firmada por quien la registra."""

    compromiso = models.ForeignKey(Compromiso, on_delete=models.CASCADE, related_name="avances")
    fecha = models.DateField(default=timezone.localdate)
    descripcion = models.TextField("descripción")
    porcentaje = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Nuevo % de avance (opcional)")
    nuevo_estatus = models.CharField(max_length=20, choices=Compromiso.Estatus.choices, blank=True)
    evidencia = models.FileField(upload_to="evidencias/%Y/%m/", blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="registrado por", on_delete=models.SET_NULL, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avance"
        verbose_name_plural = "bitácora de avances"
        ordering = ["-fecha", "-creado"]

    def __str__(self):
        return f"{self.compromiso} · {self.fecha:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        """Al registrar un avance se actualiza el compromiso, para que el tablero refleje la última nota."""
        super().save(*args, **kwargs)
        c = self.compromiso
        cambios = []
        if self.porcentaje is not None:
            c.porcentaje = min(self.porcentaje, 100)
            cambios.append("porcentaje")
        if self.nuevo_estatus:
            c.estatus = self.nuevo_estatus
            cambios.append("estatus")
            if self.nuevo_estatus == Compromiso.Estatus.CUMPLIDO:
                c.fecha_cumplimiento = self.fecha
                c.porcentaje = 100
                cambios += ["fecha_cumplimiento", "porcentaje"]
        elif c.estatus == Compromiso.Estatus.PENDIENTE:
            c.estatus = Compromiso.Estatus.EN_PROCESO
            cambios.append("estatus")
        if cambios:
            c.save(update_fields=list(set(cambios)) + ["actualizado"])


class PerfilUsuario(models.Model):
    """Datos del usuario propios del sistema. Hoy: la institución a la que pertenece un enlace."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    institucion = models.ForeignKey(
        Institucion, verbose_name="institución", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="usuarios",
        help_text="Para enlaces institucionales: solo podrán actualizar las entregas de esta institución.",
    )

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"{self.usuario} ({self.institucion or 'sin institución'})"


def institucion_de(usuario):
    """Institución ligada al usuario, o None (sin perfil, sin institución o anónimo)."""
    if not getattr(usuario, "is_authenticated", False):
        return None
    perfil = PerfilUsuario.objects.filter(usuario=usuario).select_related("institucion").first()
    return perfil.institucion if perfil else None
