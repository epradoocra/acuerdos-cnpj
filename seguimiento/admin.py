from django.contrib import admin

from .models import Acuerdo, Avance, Compromiso, Entrega, Institucion, Organo, Reunion, Tema


@admin.register(Organo)
class OrganoAdmin(admin.ModelAdmin):
    list_display = ("siglas", "nombre")


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ("siglas", "nombre", "tipo", "entidad_federativa", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre", "siglas", "entidad_federativa")


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "color")


class AcuerdoInline(admin.TabularInline):
    model = Acuerdo
    fields = ("clave", "titulo", "naturaleza", "responsable")
    extra = 0
    show_change_link = True


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "organo", "tipo", "modalidad", "fecha", "sede")
    list_filter = ("organo", "tipo", "modalidad")
    search_fields = ("nombre", "numeral")
    inlines = [AcuerdoInline]


class CompromisoInline(admin.StackedInline):
    model = Compromiso
    extra = 0
    autocomplete_fields = ("responsable", "corresponsables")
    fields = (
        ("inciso", "estatus", "porcentaje"),
        "descripcion",
        ("responsable", "corresponsables"),
        ("responsable_validado", "nota_asignacion"),
        ("fecha_limite", "plazo_texto"),
        ("entregable", "requiere_entregas"),
    )


@admin.register(Acuerdo)
class AcuerdoAdmin(admin.ModelAdmin):
    list_display = ("clave", "titulo", "naturaleza", "responsable", "avance_pct", "estatus_calc")
    list_filter = ("reunion", "naturaleza", "temas")
    search_fields = ("clave", "titulo", "texto")
    filter_horizontal = ("temas",)
    autocomplete_fields = ("responsable",)
    inlines = [CompromisoInline]

    @admin.display(description="Avance")
    def avance_pct(self, obj):
        return f"{obj.avance}%"

    @admin.display(description="Estatus")
    def estatus_calc(self, obj):
        return obj.estatus.replace("_", " ")


class EntregaInline(admin.TabularInline):
    model = Entrega
    extra = 0
    autocomplete_fields = ("institucion",)
    fields = ("institucion", "estatus", "fecha_entrega", "oficio", "evidencia")


class AvanceInline(admin.TabularInline):
    model = Avance
    extra = 0
    fields = ("fecha", "descripcion", "porcentaje", "nuevo_estatus", "evidencia", "registrado_por")
    readonly_fields = ("registrado_por",)


@admin.register(Compromiso)
class CompromisoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "responsable", "responsable_validado", "fecha_limite", "estatus", "porcentaje", "vencido")
    list_filter = ("responsable_validado", "estatus", "acuerdo__reunion", "responsable__tipo", "responsable")
    search_fields = ("descripcion", "acuerdo__clave")
    autocomplete_fields = ("acuerdo", "responsable", "corresponsables")
    inlines = [EntregaInline, AvanceInline]
    actions = ["validar_responsable"]

    @admin.action(description="Confirmar el responsable asignado (validar)")
    def validar_responsable(self, request, queryset):
        n = queryset.update(responsable_validado=True)
        self.message_user(request, f"{n} compromisos con responsable validado.")

    @admin.display(boolean=True, description="Vencido")
    def vencido(self, obj):
        return obj.vencido

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, Avance) and not obj.registrado_por_id:
                obj.registrado_por = request.user
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


@admin.register(Avance)
class AvanceAdmin(admin.ModelAdmin):
    list_display = ("compromiso", "fecha", "porcentaje", "nuevo_estatus", "registrado_por")
    list_filter = ("fecha", "nuevo_estatus")
    search_fields = ("descripcion", "compromiso__acuerdo__clave")
    autocomplete_fields = ("compromiso",)

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ("compromiso", "institucion", "estatus", "fecha_entrega", "oficio")
    list_filter = ("estatus", "institucion__tipo", "compromiso__acuerdo__reunion")
    search_fields = ("institucion__nombre", "institucion__siglas", "compromiso__acuerdo__clave")
    autocomplete_fields = ("compromiso", "institucion")
