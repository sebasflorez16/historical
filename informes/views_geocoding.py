"""
Vista proxy para geocodificación evitando problemas CORS
"""
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import logging

logger = logging.getLogger(__name__)


@require_GET
def geocode_proxy(request):
    """
    Proxy para peticiones de geocodificación a Nominatim
    Evita problemas CORS y agrega User-Agent apropiado
    """
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'error': 'Parámetro q requerido'}, status=400)
    
    try:
        # Petición a Nominatim con User-Agent apropiado
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': 5,
            'countrycodes': 'co'
        }
        headers = {
            'User-Agent': 'AgroTech-Historico/1.0 (Django Application)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            logger.error(f"Error Nominatim: {response.status_code}")
            return JsonResponse({'error': 'Servicio no disponible'}, status=503)
            
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Timeout en geocodificación'}, status=504)
    except Exception as e:
        logger.error(f"Error en geocodificación: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
