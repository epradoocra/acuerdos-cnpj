from django.contrib.auth import views as auth_views
from django.urls import include, path

from seguimiento import recuperar_admin


urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cuenta/contrasena/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("cuenta/contrasena/listo/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("recuperar-admin/", recuperar_admin.solicitar, name="recuperar_admin"),
    path("recuperar-admin/listo/", recuperar_admin.Listo.as_view(), name="recuperar_admin_listo"),
    path("recuperar-admin/<uidb64>/<token>/", recuperar_admin.Confirmar.as_view(), name="recuperar_admin_confirmar"),
    # Las evidencias no se publican en /media: se sirven por una vista que exige sesión.
    path("", include("seguimiento.urls")),
]
