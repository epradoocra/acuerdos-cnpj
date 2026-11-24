"""Recuperación de la cuenta de administrador.

Desde el inicio de sesión se solicita el cambio; la liga se envía SIEMPRE al correo fijo ADMIN_RESET_EMAIL
(nunca a uno escrito por el visitante). Solicitarlo no modifica la cuenta. La liga caduca
(PASSWORD_RESET_TIMEOUT) y deja de servir en cuanto se cambia la contraseña o el administrador inicia sesión.
"""
import logging

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

log = logging.getLogger(__name__)
ESPERA = 300  # segundos entre solicitudes
CLAVE_ESPERA = "recuperar_admin_espera"


def _liga(request, usuario):
    ruta = reverse("recuperar_admin_confirmar", args=[
        urlsafe_base64_encode(force_bytes(usuario.pk)), default_token_generator.make_token(usuario)])
    base = settings.PORTAL_URL or f"{request.scheme}://{request.get_host()}"
    return base.rstrip("/") + ruta


def _enviar(request, usuario):
    minutos = settings.PASSWORD_RESET_TIMEOUT // 60
    send_mail(
        "Cambio de contraseña del administrador — Seguimiento de Acuerdos",
        f"Se solicitó cambiar la contraseña de la cuenta «{usuario.username}» del Sistema de Seguimiento de Acuerdos.\n\n"
        f"Para confirmarlo y elegir una contraseña nueva, abra esta liga:\n\n{_liga(request, usuario)}\n\n"
        f"La liga es de un solo uso y caduca en {minutos} minutos.\n"
        "Si usted no lo solicitó, ignore este mensaje: la contraseña no ha cambiado.\n",
        None, [settings.ADMIN_RESET_EMAIL],
    )


@never_cache
@require_http_methods(["GET", "POST"])
def solicitar(request):
    ctx = {"configurado": bool(settings.ADMIN_RESET_EMAIL and settings.EMAIL_CONFIGURADO)}
    if request.method == "POST" and ctx["configurado"]:
        usuario = User.objects.filter(
            username=settings.ADMIN_RESET_USERNAME, is_active=True, is_superuser=True).first()
        if not cache.add(CLAVE_ESPERA, 1, ESPERA):
            ctx["espera"] = True
        elif usuario is None:
            log.error("Recuperación: no existe el superusuario activo %r.", settings.ADMIN_RESET_USERNAME)
            ctx["fallo"] = True
        else:
            try:
                _enviar(request, usuario)
                log.warning("Recuperación de la cuenta de administrador: se envió la liga.")
                ctx["enviado"] = True
            except Exception:  # error de SMTP: se registra y se permite reintentar
                log.exception("Recuperación: no se pudo enviar el correo.")
                cache.delete(CLAVE_ESPERA)
                ctx["fallo"] = True
    return render(request, "registration/recuperar_admin.html", ctx)


class Confirmar(auth_views.PasswordResetConfirmView):
    template_name = "registration/recuperar_admin_confirmar.html"
    success_url = reverse_lazy("recuperar_admin_listo")

    def get_user(self, uidb64):
        """Solo la cuenta de administrador puede cambiarse por esta vía."""
        u = super().get_user(uidb64)
        ok = u and u.is_active and u.is_superuser and u.username == settings.ADMIN_RESET_USERNAME
        return u if ok else None


class Listo(auth_views.PasswordResetCompleteView):
    template_name = "registration/recuperar_admin_listo.html"
