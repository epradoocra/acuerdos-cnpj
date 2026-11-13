from django.conf import settings

from .models import institucion_de


def institucion_usuario(request):
    """Expone en todas las plantillas la institución del usuario (para el enlace 'Mis pendientes')."""
    return {"mi_institucion": institucion_de(request.user), "modo_prueba": settings.MODO_PRUEBA}
