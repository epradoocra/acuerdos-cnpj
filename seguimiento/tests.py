from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SinLigasAdminDjangoTests(TestCase):
    def test_paginas_sin_liga_a_la_administracion_de_django(self):
        from seguimiento.models import Acuerdo, Compromiso, Institucion, Organo, Reunion
        st = Institucion.objects.create(siglas="ST", nombre="Secretaría")
        r = Reunion.objects.create(organo=Organo.objects.create(siglas="O", nombre="O"), numero=1, numeral="I", nombre="R")
        a = Acuerdo.objects.create(reunion=r, clave="O/I/01/2026", numero=1, titulo="t", texto="t", naturaleza="instruye")
        Compromiso.objects.create(acuerdo=a, descripcion="d", responsable=st, responsable_validado=False)
        self.client.force_login(User.objects.create_superuser("jefe", "", "Vieja-Clave-1173"))
        for nombre in ("tablero", "admin_panel", "admin_usuarios", "admin_validar", "admin_exportar", "catalogos"):
            with self.subTest(nombre):
                resp = self.client.get(reverse(f"seguimiento:{nombre}"))
                self.assertEqual(resp.status_code, 200)
                self.assertNotContains(resp, 'href="/admin/')
        self.assertContains(self.client.get(reverse("seguimiento:tablero")), reverse("seguimiento:admin_validar"))

    def test_administracion_de_django_desactivada(self):
        self.client.force_login(User.objects.create_superuser("jefe", "", "Vieja-Clave-1173"))
        for ruta in ("/admin/", "/admin/login/", "/admin/auth/user/"):
            self.assertEqual(self.client.get(ruta).status_code, 404, ruta)
