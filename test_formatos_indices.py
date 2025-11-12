#!/usr/bin/env python
"""
Probar diferentes formatos para bm_type (índices)
"""
import os, requests, json
from dotenv import load_dotenv
from datetime import date

load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

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

# Probar diferentes formatos
formatos = [
    (['NDVI'], "NDVI mayúsculas"),
    (['ndvi'], "ndvi minúsculas"),
    (['Ndvi'], "Ndvi capitalizado"),
    (['NDVI', 'NDMI', 'SAVI'], "Múltiples índices mayúsculas"),
]

fecha_inicio = date(2024, 10, 1)
fecha_fin = date(2024, 11, 10)

print("="*80)
print("🧪 PROBANDO FORMATOS DE ÍNDICES")
print("="*80)

for indices, desc in formatos:
    print(f"\n📊 Test: {desc}")
    print(f"   Índices: {indices}")
    
    payload = {
        'type': 'mt_stats',
        'params': {
            'bm_type': indices,
            'date_start': fecha_inicio.isoformat(),
            'date_end': fecha_fin.isoformat(),
            'geometry': geometria,
            'sensors': ['S2L2A'],
            'reference': f'test_{desc.replace(" ", "_")}',
            'limit': 10,
            'max_cloud_cover_in_aoi': 50,
            'exclude_cover_pixels': True,
            'cloud_masking_level': 3
        }
    }
    
    url = f"{BASE_URL}/api/gdw/api"
    response = session.post(url, json=payload, timeout=30)
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201, 202]:
        data = response.json()
        task_id = data.get('task_id')
        print(f"   ✅ Tarea creada: {task_id}")
        
        # Verificar inmediatamente el estado
        check_url = f"{BASE_URL}/api/gdw/api/{task_id}"
        check_response = session.get(check_url, timeout=30)
        check_data = check_response.json()
        
        task_type = check_data.get('task_type', 'unknown')
        if task_type == 'error':
            error_msg = check_data.get('error_message', {})
            print(f"   ❌ Error: {error_msg}")
        else:
            print(f"   ✅ Sin errores inmediatos (task_type: {task_type})")
    else:
        print(f"   ❌ Error: {response.text[:200]}")

print("\n" + "="*80)
