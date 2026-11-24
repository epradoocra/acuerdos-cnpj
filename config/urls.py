from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cuenta/contrasena/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("cuenta/contrasena/listo/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    # Las evidencias no se publican en /media: se sirven por una vista que exige sesión.
    path("", include("seguimiento.urls")),
]
