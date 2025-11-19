"""
Script para depurar la descarga de imagen - ver qué responde la API
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.services.eosda_api import eosda_service
import json
import time

def debug_descarga():
    """
    Debug completo del proceso de descarga
    """
    print("\n" + "="*80)
    print("🐛 DEBUG DESCARGA DE IMAGEN")
    print("="*80)
    
    field_id = "10804354"
    view_id = "S2L2A/18/N/YL/2025/11/7/0"
    indice = "NDVI"
    
    # Paso 1: POST para crear request
    url_post = f"{eosda_service.base_url}/field-imagery/indicies/{field_id}"
    payload = {
        'params': {
            'view_id': view_id,
            'index': indice,
            'format': 'png'
        }
    }
    
    print(f"\n📤 PASO 1: POST para crear request")
    print(f"   URL: {url_post}")
    print(f"   Payload:")
    print(json.dumps(payload, indent=6))
    
    response = eosda_service.session.post(url_post, json=payload, timeout=60)
    
    print(f"\n📥 Respuesta:")
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Body: {response.text}")
    
    if response.status_code not in [200, 201, 202]:
        print(f"\n❌ Error en POST inicial")
        return
    
    try:
        data = response.json()
        request_id = data.get('request_id')
        print(f"\n✅ Request ID obtenido: {request_id}")
    except:
        print(f"\n❌ No se pudo parsear JSON")
        return
    
    if not request_id:
        print(f"\n❌ No hay request_id en la respuesta")
        return
    
    # Paso 2: GET para obtener imagen
    url_get = f"{eosda_service.base_url}/field-imagery/{field_id}/{request_id}"
    
    print(f"\n📤 PASO 2: GET para obtener imagen")
    print(f"   URL: {url_get}")
    print(f"   Intentos: 3 (cada 10 segundos)")
    
    for intento in range(3):
        print(f"\n   ⏳ Intento {intento + 1}/3...")
        time.sleep(10)
        
        response = eosda_service.session.get(url_get, timeout=60)
        
        print(f"      Status: {response.status_code}")
        print(f"      Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"      Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                print(f"\n   ✅ IMAGEN DESCARGADA")
                print(f"      Tamaño: {len(response.content)} bytes")
                
                # Guardar imagen
                with open('debug_imagen.png', 'wb') as f:
                    f.write(response.content)
                print(f"      Guardada como: debug_imagen.png")
                return
            else:
                # Mostrar respuesta JSON
                try:
                    data = response.json()
                    print(f"      JSON: {json.dumps(data, indent=9)}")
                except:
                    print(f"      Body (primeros 200 chars): {response.text[:200]}")
        else:
            print(f"      Body: {response.text[:200]}")
    
    print(f"\n⏱️  Timeout - no se obtuvo la imagen")


if __name__ == "__main__":
    debug_descarga()
