from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 🏠 Página principal
    path('', views.index, name='index'),            # URL raíz
    path('home/', views.index, name='home'),

    # 📄 Páginas informativas
    path('sidebar_left/', views.sidebar_left, name='sidebar_left'),
    path('sidebar_right/', views.sidebar_right, name='sidebar_right'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),

    # 🔐 Autenticación
    path('registrar/', views.registrar, name='registrar'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar/', views.recuperar_contraseña, name='recuperar'),
    path('correo-enviado/', views.correo_enviado, name='correo_enviado'),
    path('restablecer/<str:token>/', views.restablecer_contraseña, name='restablecer'),

    # 🏠 Dashboard / Inicio
    path('inicio/', views.inicio, name='inicio'),

    # 👥 Empleados
    path('registrar_empleado/', views.registrar_empleado, name='registrar_empleado'),
    path('buscar/', views.buscar_empleado, name='buscar_empleado'),
    path('perfil/<str:numero_documento>/', views.perfil_empleado, name='perfil_empleado'),

    # 📊 Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes_descarga/', views.reportes_descarga, name='reportes_descarga'),
    path('reporte_individual/', views.reporte_individual, name='reporte_individual'),
    path('reporte_general/', views.reporte_general, name='reporte_general'),
    path('reporte_nomina/', views.reporte_nomina, name='reporte_nomina'),

    # ⚙️ Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
]
