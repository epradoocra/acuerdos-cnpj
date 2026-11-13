from datetime import date

from django import forms
from django.contrib.auth.models import Group, User
from django.db.models import Max

from .models import Acuerdo, Avance, Compromiso, Entrega, Institucion, Organo, PerfilUsuario, Reunion, Tema


class AvanceForm(forms.ModelForm):
    class Meta:
        model = Avance
        fields = ["fecha", "descripcion", "porcentaje", "nuevo_estatus", "evidencia"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "porcentaje": forms.NumberInput(attrs={"min": 0, "max": 100}),
        }
        labels = {"nuevo_estatus": "Cambiar estatus a", "porcentaje": "Avance (%)"}

    def clean_porcentaje(self):
        p = self.cleaned_data.get("porcentaje")
        if p is not None and not 0 <= p <= 100:
            raise forms.ValidationError("El avance debe estar entre 0 y 100.")
        return p


class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ["estatus", "fecha_entrega", "oficio", "evidencia", "nota"]
        widgets = {
            "fecha_entrega": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "nota": forms.Textarea(attrs={"rows": 2}),
        }


# ----------------------------------------------------------------------------------- captura

FECHA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class ReunionForm(forms.ModelForm):
    class Meta:
        model = Reunion
        fields = ["organo", "numero", "numeral", "nombre", "tipo", "modalidad", "fecha", "sede", "acta", "observaciones"]
        widgets = {"fecha": FECHA, "observaciones": forms.Textarea(attrs={"rows": 3})}
        labels = {"numero": "Número de sesión", "numeral": "Numeral romano", "acta": "Acta o documento de acuerdos (PDF)"}

    def clean_numeral(self):
        return self.cleaned_data["numeral"].strip().upper()


class AcuerdoForm(forms.ModelForm):
    class Meta:
        model = Acuerdo
        fields = ["numero", "clave", "titulo", "naturaleza", "temas", "responsable", "texto", "observaciones"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 10}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
            "temas": forms.CheckboxSelectMultiple,
        }
        labels = {"numero": "Número", "responsable": "Coordina el seguimiento"}

    def __init__(self, *args, reunion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reunion = reunion or self.instance.reunion
        if not self.instance.pk:
            n = (self.reunion.acuerdos.aggregate(m=Max("numero"))["m"] or 0) + 1
            self.initial.setdefault("numero", n)
            self.initial.setdefault("clave", sugerir_clave(self.reunion, n))

    def clean_clave(self):
        clave = self.cleaned_data["clave"].strip().upper()
        if Acuerdo.objects.filter(clave=clave).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un acuerdo con esa clave.")
        return clave


def sugerir_clave(reunion, numero):
    anio = (reunion.fecha.year if reunion.fecha else None) or date.today().year
    return f"{reunion.organo.siglas}/{reunion.numeral}/{numero:02d}/{anio}"


class CompromisoForm(forms.ModelForm):
    OBLIGADOS = [
        ("", "Nadie más (lo cumple solo el responsable)"),
        ("estatales", "Las 32 fiscalías y procuradurías estatales"),
        ("pleno", "Todo el Pleno (32 estatales + FGR)"),
        ("seleccion", "Instituciones seleccionadas"),
    ]
    obligados = forms.ChoiceField(choices=OBLIGADOS, required=False, label="Instituciones obligadas a entregar")
    seleccion = forms.ModelMultipleChoiceField(
        queryset=Institucion.objects.filter(activa=True), required=False,
        widget=forms.SelectMultiple(attrs={"size": 10}), label="Selección (Ctrl+clic para varias)",
    )

    class Meta:
        model = Compromiso
        fields = ["inciso", "descripcion", "responsable", "corresponsables", "fecha_limite", "plazo_texto",
                  "entregable", "estatus", "porcentaje", "responsable_validado", "nota_asignacion"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "fecha_limite": FECHA,
            "corresponsables": forms.SelectMultiple(attrs={"size": 6}),
            "porcentaje": forms.NumberInput(attrs={"min": 0, "max": 100}),
        }
        labels = {"porcentaje": "Avance (%)", "plazo_texto": "Plazo como lo dice el acuerdo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Institucion.objects.filter(activa=True)
        self.fields["corresponsables"].queryset = Institucion.objects.filter(activa=True)
        if self.instance.pk and self.instance.requiere_entregas:
            self.initial["obligados"] = "seleccion"
            self.initial["seleccion"] = list(self.instance.entregas.values_list("institucion_id", flat=True))

    def clean_porcentaje(self):
        p = self.cleaned_data.get("porcentaje") or 0
        if not 0 <= p <= 100:
            raise forms.ValidationError("Debe estar entre 0 y 100.")
        return p

    def clean(self):
        datos = super().clean()
        if datos.get("obligados") == "seleccion" and not datos.get("seleccion"):
            self.add_error("seleccion", "Seleccione al menos una institución.")
        return datos

    def instituciones_obligadas(self):
        """Lista de instituciones que deben tener Entrega, o None si el compromiso no requiere entregas."""
        modo = self.cleaned_data.get("obligados")
        estatales = Institucion.objects.filter(tipo=Institucion.Tipo.ESTATAL, activa=True)
        if modo == "estatales":
            return list(estatales)
        if modo == "pleno":
            return list(estatales) + list(Institucion.objects.filter(siglas="FGR"))
        if modo == "seleccion":
            return list(self.cleaned_data["seleccion"])
        return None


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ["siglas", "nombre", "tipo", "entidad_federativa", "activa"]


class TemaForm(forms.ModelForm):
    class Meta:
        model = Tema
        fields = ["nombre", "color"]
        widgets = {"color": forms.TextInput(attrs={"type": "color"})}


class OrganoForm(forms.ModelForm):
    class Meta:
        model = Organo
        fields = ["siglas", "nombre"]


class ImportarForm(forms.Form):
    texto = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 16}),
        label="Texto de los acuerdos",
        help_text="Pegue el texto completo del documento. Cada acuerdo debe iniciar con su clave, p. ej. CNPJ/LV/01/2027.",
    )


# ----------------------------------------------------------------------------------- usuarios

PERFILES = ["Administrador del sistema", "Secretaría Técnica", "Enlace institucional", "Consulta"]


class UsuarioForm(forms.ModelForm):
    perfil = forms.ChoiceField(choices=[(p, p) for p in PERFILES], label="Perfil")
    institucion = forms.ModelChoiceField(
        Institucion.objects.filter(activa=True), required=False, label="Institución",
        help_text="Obligatoria para enlaces: solo podrán actualizar las entregas de esta institución.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "perfil", "institucion", "is_active"]
        labels = {"username": "Usuario", "first_name": "Nombre", "last_name": "Apellidos",
                  "email": "Correo electrónico", "is_active": "Activo (puede iniciar sesión)"}
        help_texts = {"username": "Sin espacios. Letras, números y @ . + - _"}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        u = self.instance
        if u.pk:
            grupo = u.groups.filter(name__in=PERFILES).first()
            self.initial.setdefault("perfil", grupo.name if grupo else "Consulta")
            perfil = PerfilUsuario.objects.filter(usuario=u).first()
            self.initial.setdefault("institucion", perfil.institucion_id if perfil else None)
        else:
            self.initial.setdefault("perfil", "Enlace institucional")
        if editor and u.pk == editor.pk:
            # Nadie puede quitarse a sí mismo el acceso ni el perfil de administración.
            for campo in ("perfil", "is_active"):
                self.fields[campo].disabled = True
                self.fields[campo].help_text = "No puede cambiar su propio perfil ni desactivarse."

    def clean(self):
        datos = super().clean()
        if datos.get("perfil") == "Enlace institucional" and not datos.get("institucion"):
            self.add_error("institucion", "Indique la institución del enlace.")
        return datos

    def save(self, commit=True):
        u = super().save(commit=False)
        perfil = self.cleaned_data["perfil"]
        u.is_staff = u.is_superuser or perfil == "Administrador del sistema"
        u.save()
        u.groups.remove(*Group.objects.filter(name__in=PERFILES))
        u.groups.add(Group.objects.get(name=perfil))
        PerfilUsuario.objects.update_or_create(usuario=u, defaults={"institucion": self.cleaned_data["institucion"]})
        return u
