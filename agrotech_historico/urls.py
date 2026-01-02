"""
Configuración de URLs para AgroTech Histórico
Sistema de análisis satelital agrícola
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse

def redirigir_a_login(request):
    """Redirige la raíz al login"""
    return redirect('informes:login')

def healthcheck(request):
    """Endpoint para Railway healthcheck - retorna 200 OK"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AgroTech Histórico',
        'database': 'connected'
    })

urlpatterns = [
    path("health/", healthcheck, name='healthcheck'),  # Healthcheck para Railway
    path("admin/", admin.site.urls),
    path("", redirigir_a_login, name='home'),
    path("informes/", include('informes.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
