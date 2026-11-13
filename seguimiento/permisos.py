"""Modo de prueba: permisos amplios para ensayar el sistema con usuarios de cualquier perfil.

Con DJANGO_MODO_PRUEBA=1, todo usuario activo con sesión puede CONSULTAR, AGREGAR y MODIFICAR los
datos del seguimiento (reuniones, acuerdos, compromisos, entregas, avances y catálogos), sin importar
su perfil ni su institución. Eliminar registros y administrar usuarios siguen restringidos a sus perfiles.

Se apaga con DJANGO_MODO_PRUEBA=0 (valor predeterminado) y reiniciando el sistema.
"""
from django.conf import settings
from django.contrib.auth.backends import BaseBackend

ACCIONES_PERMITIDAS = ("view", "add", "change")


class PermisosModoPrueba(BaseBackend):
    def authenticate(self, request, **credenciales):
        return None  # no autentica: solo concede permisos

    def has_perm(self, user_obj, perm, obj=None):
        if not settings.MODO_PRUEBA or not getattr(user_obj, "is_active", False):
            return False
        app, _, codigo = perm.partition(".")
        return app == "seguimiento" and codigo.split("_", 1)[0] in ACCIONES_PERMITIDAS

    def has_module_perms(self, user_obj, app_label):
        return bool(settings.MODO_PRUEBA and getattr(user_obj, "is_active", False) and app_label == "seguimiento")
