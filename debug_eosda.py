#!/usr/bin/env python
"""
Script de debugging para investigar por qué EOSDA no responde
"""
import os
import sys
import django
import requests
import time
import json
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.conf import settings

def debug_eosda_request():
    """
    Prueba directa a EOSDA API para ver qué está pasando
    """
    print("=" * 80)
    print("🔍 DEBUG EOSDA API - Investigación profunda")
    print("=" * 80)
    
    # 1. Obtener configuración desde settings
    api_key = settings.EOSDA_API_KEY
    base_url = settings.EOSDA_BASE_URL
    
    if not api_key or api_key == 'demo_token_reemplazar_con_real':
        print("❌ EOSDA_API_KEY no configurada en settings")
        return
    
    print(f"\n✅ Configuración desde settings:")
    print(f"   API Key: {api_key[:20]}... (longitud: {len(api_key)} chars)")
    print(f"   Base URL: {base_url}")
    
    # 2. Preparar sesión HTTP
    session = requests.Session()
    session.headers.update({
        'x-api-key': api_key,  # EOSDA usa x-api-key
        'Content-Type': 'application/json'
    })
    
    # 3. Parámetros de prueba
    field_id = "10800114"
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    print(f"\n📊 Parámetros de prueba:")
    print(f"   Field ID: {field_id}")
    print(f"   Período: {fecha_inicio} → {fecha_fin}")
    
    # 4. Verificar que el field existe en EOSDA
    print(f"\n🔎 PASO 1: Verificar que el field existe...")
    try:
        field_url = f"{base_url}/field-management/fields/{field_id}"
        print(f"   GET {field_url}")
        
        field_response = session.get(field_url, timeout=30)
        print(f"   Status: {field_response.status_code}")
        
        if field_response.status_code == 200:
            field_data = field_response.json()
            print(f"   ✅ Field encontrado:")
            print(f"      Nombre: {field_data.get('name', 'N/A')}")
            print(f"      Área: {field_data.get('area', 'N/A')} ha")
            print(f"      Estado: {field_data.get('status', 'N/A')}")
            print(f"      JSON completo:")
            print(f"      {json.dumps(field_data, indent=2)}")
        else:
            print(f"   ❌ Error: {field_response.text[:300]}")
            print(f"   ⚠️  El field_id puede no existir o no tener acceso")
            # Continuar de todas formas para probar la petición de estadísticas
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # 5. Hacer petición de estadísticas
    print(f"\n📡 PASO 2: Solicitar estadísticas (batch request)...")
    
    url = f"{base_url}/api/gdw/api"
    payload = {
        'type': 'mt_stats',
        'params': {
            'bm_type': ['ndvi', 'ndmi', 'savi'],
            'date_start': fecha_inicio.isoformat(),
            'date_end': fecha_fin.isoformat(),
            'field_id': field_id,
            'sensors': ['S2_MSI_L2A'],
            'reference': f'debug_test_{int(time.time())}',
            'limit': 50,
            'max_cloud_cover_in_aoi': 50,
            'exclude_cover_pixels': True,
            'cloud_masking_level': 3
        }
    }
    
    print(f"   POST {url}")
    print(f"   Payload:")
    print(f"   {json.dumps(payload, indent=2)}")
    
    try:
        response = session.post(url, json=payload, timeout=60)
        print(f"\n   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            print(f"\n   ✅ Respuesta recibida:")
            print(f"   {json.dumps(data, indent=2)}")
            
            task_id = data.get('task_id')
            if task_id:
                print(f"\n   📋 Task ID: {task_id}")
                
                # 6. Consultar estado de la tarea
                print(f"\n⏳ PASO 3: Monitorear tarea...")
                task_url = f"{url}/{task_id}"
                
                for intento in range(20):
                    print(f"\n   Intento {intento + 1}/20:")
                    try:
                        task_response = session.get(task_url, timeout=30)
                        print(f"   Status: {task_response.status_code}")
                        
                        if task_response.status_code == 200:
                            task_data = task_response.json()
                            
                            # Mostrar toda la respuesta
                            print(f"   Respuesta completa:")
                            print(f"   {json.dumps(task_data, indent=2)}")
                            
                            # Verificar estado
                            status = task_data.get('status', 'unknown')
                            print(f"\n   📊 Estado: {status}")
                            
                            # Verificar resultados
                            if 'result' in task_data and task_data['result']:
                                print(f"   ✅ RESULTADOS ENCONTRADOS!")
                                print(f"   Total escenas: {len(task_data['result'])}")
                                if task_data['result']:
                                    print(f"   Primera escena:")
                                    print(f"   {json.dumps(task_data['result'][0], indent=2)}")
                                break
                            
                            # Verificar errores
                            if 'errors' in task_data and task_data['errors']:
                                print(f"   ❌ ERRORES:")
                                print(f"   {json.dumps(task_data['errors'], indent=2)}")
                                break
                            
                            # Verificar si aún está procesando
                            if status in ['pending', 'processing', 'running']:
                                print(f"   ⏳ Aún procesando...")
                            elif status == 'finished':
                                print(f"   ✅ Tarea completada")
                                if not task_data.get('result'):
                                    print(f"   ⚠️  Pero no hay resultados en 'result'")
                                    print(f"   Claves disponibles: {list(task_data.keys())}")
                                break
                            elif status == 'failed':
                                print(f"   ❌ Tarea falló")
                                break
                            
                        elif task_response.status_code == 429:
                            print(f"   ⚠️  Rate limit!")
                            time.sleep(10)
                            continue
                        else:
                            print(f"   ❌ Error: {task_response.text[:300]}")
                            break
                        
                        # Esperar antes del siguiente intento
                        if intento < 19:
                            print(f"   💤 Esperando 5 segundos...")
                            time.sleep(5)
                        
                    except Exception as e:
                        print(f"   ❌ Excepción: {e}")
                        break
                
            else:
                print(f"   ❌ No se obtuvo task_id")
        else:
            print(f"   ❌ Error en petición:")
            print(f"   {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT después de 60 segundos")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 Debug completado")
    print("=" * 80)

if __name__ == '__main__':
    debug_eosda_request()
