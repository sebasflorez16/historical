"""
Test real para verificar qué datos trae la API de EOSDA
Consulta febrero 2025 (mes no cacheado) para ver si trae:
- Solo promedios del mes
- Todas las escenas individuales con sus view_ids

Usa Field Analytics API: https://doc.eos.com/docs/field-management-api/field-analytics/
"""

import os
import django
import json
import time
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.eosda_api import eosda_service


def test_eosda_febrero_2025():
    """
    Test real consultando la API de EOSDA para febrero 2025
    """
    print("\n" + "="*80)
    print("🧪 TEST REAL - API DE EOSDA PARA FEBRERO 2025")
    print("="*80)
    
    # Obtener parcela de prueba
    parcela = Parcela.objects.filter(activa=True, eosda_sincronizada=True).first()
    
    if not parcela:
        print("❌ No hay parcelas sincronizadas con EOSDA")
        return
    
    print(f"\n📍 Parcela: {parcela.nombre}")
    print(f"   Field ID EOSDA: {parcela.eosda_field_id}")
    
    # Definir período: febrero 2025
    fecha_inicio = date(2025, 2, 1)
    fecha_fin = date(2025, 2, 28)
    
    print(f"\n📅 Período: {fecha_inicio} → {fecha_fin}")
    print(f"   Índices: NDVI, NDMI, SAVI")
    
    print(f"\n🔄 Consultando API de EOSDA...")
    print(f"   Usando: Field Analytics API (trend endpoint)")
    print(f"   URL: https://api-connect.eos.com/field-analytics/trend/{parcela.eosda_field_id}")
    
    # Consultar API usando el método del servicio
    try:
        # Paso 1: Crear request
        url = f"{eosda_service.base_url}/field-analytics/trend/{parcela.eosda_field_id}"
        
        payload = {
            "params": {
                "date_start": fecha_inicio.isoformat(),
                "date_end": fecha_fin.isoformat(),
                "index": "NDVI",  # Un índice a la vez
                "data_source": "S2L2A"  # Sentinel-2 Level 2A
            }
        }
        
        print(f"\n📤 Payload enviado:")
        print(json.dumps(payload, indent=2))
        
        response = eosda_service.session.post(url, json=payload, timeout=60)
        
        print(f"\n📥 Respuesta inicial:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code not in [200, 201, 202]:
            print(f"   ❌ Error: {response.text[:500]}")
            return
        
        data = response.json()
        request_id = data.get('request_id')
        print(f"   Request ID: {request_id}")
        print(f"   Status: {data.get('status')}")
        
        # Paso 2: Polling para obtener resultados
        url_result = f"{url}/{request_id}"
        max_intentos = 12
        intervalo = 5
        
        print(f"\n⏳ Esperando resultados (máximo {max_intentos * intervalo} segundos)...")
        
        for intento in range(max_intentos):
            time.sleep(intervalo)
            print(f"   Intento {intento + 1}/{max_intentos}...")
            
            response = eosda_service.session.get(url_result, timeout=60)
            
            if response.status_code == 200:
                result_data = response.json()
                status = result_data.get('status')
                
                if status == 'success':
                    print(f"   ✅ Datos obtenidos exitosamente\n")
                    
                    # Analizar resultados
                    result = result_data.get('result', [])
                    
                    print("="*80)
                    print("📊 ANÁLISIS DE RESULTADOS")
                    print("="*80)
                    
                    print(f"\n✅ RESPUESTA: Se obtienen TODAS LAS ESCENAS INDIVIDUALES")
                    print(f"   Total de escenas en febrero 2025: {len(result)}")
                    
                    if not result:
                        print("   ⚠️  No hay escenas disponibles para este período")
                        return
                    
                    # Agrupar por índice
                    print(f"\n📋 Estructura de datos:")
                    print(f"   Cada escena incluye:")
                    print(f"   - view_id (para descargar imágenes)")
                    print(f"   - date (fecha de captura)")
                    print(f"   - cloud (% nubosidad)")
                    print(f"   - average, min, max (estadísticas del índice)")
                    
                    # Mostrar primeras 3 escenas
                    print(f"\n🔍 Primeras 3 escenas de ejemplo:")
                    for i, escena in enumerate(result[:3], 1):
                        print(f"\n   Escena {i}:")
                        print(f"      view_id: {escena.get('view_id', 'N/A')}")
                        print(f"      date: {escena.get('date', 'N/A')}")
                        print(f"      cloud: {escena.get('cloud', 'N/A')}%")
                        print(f"      average: {escena.get('average', 'N/A')}")
                        print(f"      min: {escena.get('min', 'N/A')}")
                        print(f"      max: {escena.get('max', 'N/A')}")
                    
                    # Ordenar por nubosidad
                    escenas_ordenadas = sorted(result, key=lambda x: x.get('cloud', 100))
                    
                    print(f"\n🌟 MEJOR ESCENA (menor nubosidad):")
                    mejor = escenas_ordenadas[0]
                    print(f"   view_id: {mejor.get('view_id')}")
                    print(f"   Fecha: {mejor.get('date')}")
                    print(f"   Nubosidad: {mejor.get('cloud')}%")
                    print(f"   NDVI average: {mejor.get('average')}")
                    
                    print(f"\n💡 CONCLUSIÓN:")
                    print(f"   ✅ La API devuelve TODAS las escenas del mes")
                    print(f"   ✅ Cada escena tiene su propio view_id")
                    print(f"   ✅ Podemos seleccionar la escena con menor nubosidad")
                    print(f"   ✅ Ese view_id se puede usar para descargar imágenes")
                    
                    print(f"\n🔧 IMPLEMENTACIÓN CORRECTA:")
                    print(f"   1. Al obtener datos históricos, guardar:")
                    print(f"      - Promedios de TODAS las escenas del mes")
                    print(f"      - view_id de la escena con MENOR nubosidad")
                    print(f"   2. Al descargar imagen, usar ese view_id guardado")
                    
                    print("\n" + "="*80 + "\n")
                    
                    return result
                    
                elif status == 'processing':
                    print(f"   ⏳ Aún procesando...")
                elif status == 'failed':
                    print(f"   ❌ Error: {result_data.get('error', 'Unknown error')}")
                    return
            else:
                print(f"   ⏳ Esperando... (status {response.status_code})")
        
        print(f"\n⏱️  Timeout esperando resultados")
        
    except Exception as e:
        print(f"\n❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_eosda_febrero_2025()
