from django.urls import path

from . import views, views_admin as adm, views_captura as cap

app_name = "seguimiento"

urlpatterns = [
    path("", views.tablero, name="tablero"),
    path("manual/", views.manual, name="manual"),
    path("buscar/", views.buscar, name="buscar"),
    path("reuniones/", views.reuniones, name="reuniones"),
    path("reuniones/<int:pk>/", views.reunion, name="reunion"),
    path("reuniones/<int:pk>/exportar.csv", views.exportar_reunion, name="exportar_reunion"),
    path("acuerdos/<int:pk>/", views.acuerdo, name="acuerdo"),
    path("compromisos/<int:pk>/avance/", views.registrar_avance, name="registrar_avance"),
    path("entregas/<int:pk>/", views.editar_entrega, name="editar_entrega"),
    path("instituciones/<int:pk>/", views.institucion, name="institucion"),
    path("evidencias/<str:tipo>/<int:pk>/", views.descargar_evidencia, name="evidencia"),

    # Captura (Secretaría Técnica)
    path("reuniones/nueva/", cap.reunion_crear, name="reunion_crear"),
    path("reuniones/<int:pk>/editar/", cap.reunion_editar, name="reunion_editar"),
    path("reuniones/<int:pk>/eliminar/", cap.reunion_borrar, name="reunion_borrar"),
    path("reuniones/<int:reunion_pk>/acuerdos/nuevo/", cap.acuerdo_crear, name="acuerdo_crear"),
    path("reuniones/<int:reunion_pk>/acuerdos/importar/", cap.acuerdos_importar, name="acuerdos_importar"),
    path("acuerdos/<int:pk>/editar/", cap.acuerdo_editar, name="acuerdo_editar"),
    path("acuerdos/<int:pk>/eliminar/", cap.acuerdo_borrar, name="acuerdo_borrar"),
    path("acuerdos/<int:acuerdo_pk>/compromisos/nuevo/", cap.compromiso_crear, name="compromiso_crear"),
    path("compromisos/<int:pk>/editar/", cap.compromiso_editar, name="compromiso_editar"),
    path("compromisos/<int:pk>/eliminar/", cap.compromiso_borrar, name="compromiso_borrar"),
    path("catalogos/", cap.catalogos, name="catalogos"),
    path("catalogos/<str:tipo>/nuevo/", cap.catalogo_form, name="catalogo_crear"),
    path("catalogos/<str:tipo>/<int:pk>/", cap.catalogo_form, name="catalogo_editar"),
    path("catalogos/<str:tipo>/<int:pk>/eliminar/", cap.catalogo_borrar, name="catalogo_borrar"),

    # Administración del sistema
    path("administracion/", adm.panel, name="admin_panel"),
    path("administracion/usuarios/", adm.usuarios, name="admin_usuarios"),
    path("administracion/usuarios/nuevo/", adm.usuario_crear, name="admin_usuario_crear"),
    path("administracion/usuarios/<int:pk>/", adm.usuario_editar, name="admin_usuario_editar"),
    path("administracion/usuarios/<int:pk>/restablecer/", adm.usuario_restablecer, name="admin_usuario_restablecer"),
    path("administracion/validar/", adm.validar, name="admin_validar"),
    path("administracion/exportar/", adm.exportar, name="admin_exportar"),
    path("administracion/exportar/compromisos.csv", adm.exportar_compromisos, name="admin_exportar_compromisos"),
    path("administracion/exportar/datos.json", adm.exportar_json, name="admin_exportar_json"),
]
