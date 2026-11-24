import re
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@override_settings(
    ADMIN_RESET_EMAIL="autorizado@example.com", ADMIN_RESET_USERNAME="admin", EMAIL_CONFIGURADO=True,
    PORTAL_URL="https://portal.example.com", SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
)
class RecuperarAdminTests(TestCase):
    NUEVA = "Nueva-Clave-8842"

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser("admin", "otro@example.com", "Vieja-Clave-1173")
        self.url = reverse("recuperar_admin")

    def solicitar(self, **datos):
        return self.client.post(self.url, datos)

    def ruta(self):
        return re.search(r"https://portal\.example\.com(/\S+)", mail.outbox[-1].body).group(1)

    def test_login_muestra_la_opcion(self):
        self.assertContains(self.client.get(reverse("login")), self.url)

    def test_get_no_envia(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(mail.outbox, [])

    def test_destinatario_fijo_y_no_cambia_la_contrasena(self):
        self.solicitar(email="intruso@example.com")
        self.assertEqual(mail.outbox[0].to, ["autorizado@example.com"])
        self.ruta()
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password("Vieja-Clave-1173"))

    def test_liga_de_un_solo_uso(self):
        self.solicitar()
        ruta = self.ruta()
        r = self.client.get(ruta, follow=True)
        self.assertTrue(r.context["validlink"])
        r = self.client.post(r.redirect_chain[-1][0],
                             {"new_password1": self.NUEVA, "new_password2": self.NUEVA}, follow=True)
        self.assertContains(r, "se cambió correctamente")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(self.NUEVA))
        self.assertFalse(self.client_class().get(ruta, follow=True).context["validlink"])

    def test_cierra_sesiones_abiertas(self):
        otro = self.client_class()
        otro.force_login(self.admin)
        self.admin.refresh_from_db()
        self.solicitar()
        r = self.client.get(self.ruta(), follow=True)
        self.client.post(r.redirect_chain[-1][0], {"new_password1": self.NUEVA, "new_password2": self.NUEVA})
        self.assertEqual(otro.get(reverse("password_change")).status_code, 302)

    def test_liga_caduca(self):
        self.solicitar()
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            self.assertFalse(self.client.get(self.ruta(), follow=True).context["validlink"])

    def test_limite_de_solicitudes(self):
        self.solicitar()
        self.assertContains(self.solicitar(), "solicitud reciente")
        self.assertEqual(len(mail.outbox), 1)

    def test_otra_cuenta_no_se_puede_cambiar(self):
        u = User.objects.create_superuser("otra", "", "Vieja-Clave-1173")
        ruta = reverse("recuperar_admin_confirmar", args=[
            urlsafe_base64_encode(force_bytes(u.pk)), default_token_generator.make_token(u)])
        self.assertFalse(self.client.get(ruta, follow=True).context["validlink"])

    def test_fallo_de_correo_permite_reintentar(self):
        with mock.patch("seguimiento.recuperar_admin.send_mail", side_effect=OSError), self.assertLogs(level="ERROR"):
            self.assertContains(self.solicitar(), "No se pudo enviar")
        self.assertContains(self.solicitar(), "Se envió la liga")

    def test_sin_configurar(self):
        with override_settings(EMAIL_CONFIGURADO=False):
            self.assertContains(self.solicitar(), "no está configurado")
        self.assertEqual(mail.outbox, [])


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
