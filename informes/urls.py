"""
URLs para la aplicación de informes
"""

from django.urls import path
from . import views
from .views_geocoding import geocode_proxy

app_name = 'informes'

urlpatterns = [
    # Autenticación
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard principal (solo superusuarios)
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    
    # Gestión de parcelas
    path('parcelas/', views.lista_parcelas, name='lista_parcelas'),
    path('parcelas/crear/', views.crear_parcela, name='crear_parcela'),
    path('parcelas/registro-cliente/', views.registro_cliente, name='registro_cliente'),
    path('parcelas/<int:parcela_id>/', views.detalle_parcela, name='detalle_parcela'),
    path('parcelas/<int:parcela_id>/mapa/', views.mapa_parcela, name='mapa_parcela'),
    
    # Sistema de invitaciones
    path('invitaciones/', views.gestionar_invitaciones, name='gestionar_invitaciones'),
    path('invitaciones/crear/', views.crear_invitacion, name='crear_invitacion'),
    path('invitaciones/<int:invitacion_id>/', views.detalle_invitacion, name='detalle_invitacion'),
    path('cliente/<str:token>/', views.registro_invitacion, name='registro_invitacion'),
    
    # Análisis de datos
    path('parcelas/<int:parcela_id>/analisis/', views.analisis_tendencias, name='analisis_tendencias'),
    path('parcelas/<int:parcela_id>/procesar/', views.procesar_datos_parcela, name='procesar_datos_parcela'),
    
    # Gestión de informes
    path('informes/', views.lista_informes, name='lista_informes'),
    path('informes/<int:informe_id>/', views.detalle_informe, name='detalle_informe'),
    
    # Sistema
    path('sistema/estado/', views.estado_sistema, name='estado_sistema'),
    path('sistema/probar-email/', views.probar_email, name='probar_email'),
    path('sistema/verificar-eosda/', views.verificar_eosda, name='verificar_eosda'),
    path('sistema/sincronizacion-eosda/', views.estado_sincronizacion_eosda, name='estado_sincronizacion_eosda'),
    
    # EOSDA y datos satelitales
    # Datos históricos y análisis
    path('parcelas/<int:parcela_id>/datos-historicos/', views.obtener_datos_historicos, name='obtener_datos_historicos'),
    path('parcelas/<int:parcela_id>/datos-guardados/', views.ver_datos_guardados, name='ver_datos_guardados'),
    path('parcelas/<int:parcela_id>/sincronizar-eosda/', views.sincronizar_con_eosda, name='sincronizar_con_eosda'),
    
    # API endpoints
    path('api/parcelas/<int:parcela_id>/datos/', views.api_datos_parcela, name='api_datos_parcela'),
    path('api/geocode/', geocode_proxy, name='geocode_proxy'),  # Proxy para evitar CORS
]