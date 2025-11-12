#!/usr/bin/env python
"""
Debug: Consultar estado de tarea EOSDA directamente
"""
import os
import requests
import json
from datetime import date, timedelta

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"  # URL correcta de EOSDA

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,  # EOSDA usa x-api-key
    'Content-Type': 'application/json'
})

# Geometría de lote4
geometria = {
    "type": "Polygon",
    "coordinates": [[
        [-72.15004, 5.161715],
        [-72.15168, 5.159044],
        [-72.14694, 5.155168],
        [-72.14469, 5.159084],
        [-72.15004, 5.161715]
    ]]
}

# Fechas de verano 2023-2024
fecha_inicio = date(2023, 12, 1)
fecha_fin = date(2024, 3, 31)

print("="*80)
print("🔍 DEBUG: Consultando EOSDA Statistics API")
print("="*80)
print(f"Período: {fecha_inicio} → {fecha_fin}")
print(f"Geometría: {geometria['type']} con {len(geometria['coordinates'][0])} puntos")
print()

# PASO 1: Crear tarea
payload = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],  # Solo NDVI para debug
        'date_start': fecha_inicio.isoformat(),
        'date_end': fecha_fin.isoformat(),
        'geometry': geometria,
        'sensors': ['S2_MSI_L2A'],
        'reference': 'debug_test',
        'limit': 50,
        'max_cloud_cover_in_aoi': 50,
        'exclude_cover_pixels': True,
        'cloud_masking_level': 3
    }
}

print("📤 PASO 1: Crear tarea")
print(f"   Payload: {json.dumps(payload, indent=2)[:300]}...")

url_create = f"{BASE_URL}/api/gdw/api"
response = session.post(url_create, json=payload, timeout=60)

print(f"\n📥 Respuesta: {response.status_code}")

if response.status_code not in [200, 201, 202]:
    print(f"❌ Error: {response.text}")
    exit(1)

data = response.json()
task_id = data.get('task_id')

print(f"✅ Tarea creada: {task_id}")
print(f"   Respuesta completa: {json.dumps(data, indent=2)}")

# PASO 2: Consultar estado múltiples veces
print(f"\n📊 PASO 2: Consultando estado de la tarea...")
print(f"   URL: {BASE_URL}/api/gdw/api/{task_id}")

import time

for intento in range(20):
    print(f"\n🔄 Intento {intento + 1}/20:")
    
    response = session.get(f"{BASE_URL}/api/gdw/api/{task_id}", timeout=30)
    
    if response.status_code != 200:
        print(f"   ❌ Status: {response.status_code}")
        print(f"   Respuesta: {response.text[:200]}")
        
        if response.status_code == 429:
            print("   ⏳ Rate limit, esperando 15s...")
            time.sleep(15)
        continue
    
    data = response.json()
    status = data.get('status', 'unknown')
    
    print(f"   Status: {status}")
    
    # Mostrar toda la estructura de la respuesta
    print(f"   Keys en respuesta: {list(data.keys())}")
    
    if 'result' in data:
        result = data['result']
        print(f"   result type: {type(result)}")
        print(f"   result length: {len(result) if isinstance(result, list) else 'N/A'}")
        if result:
            print(f"   ✅ RESULTADOS ENCONTRADOS!")
            print(f"   Primera escena: {json.dumps(result[0], indent=2)[:300]}")
            break
    else:
        print(f"   result: NO PRESENTE")
    
    if 'errors' in data and data['errors']:
        print(f"   ❌ Errores: {data['errors']}")
        break
    
    if 'message' in data:
        print(f"   message: {data['message']}")
    
    # Mostrar toda la respuesta en intento 5
    if intento == 4:
        print(f"\n   📋 Respuesta completa (intento 5):")
        print(f"   {json.dumps(data, indent=2)[:1000]}")
    
    if intento < 19:
        print(f"   ⏳ Esperando 10s...")
        time.sleep(10)

print("\n" + "="*80)
print("✅ Debug completado")
