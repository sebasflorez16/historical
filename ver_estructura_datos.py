#!/usr/bin/env python
"""
Ver estructura real de datos que devuelve EOSDA
"""
import os, requests, json, time
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

session = requests.Session()
session.headers.update({
    'x-api-key': os.getenv('EOSDA_API_KEY'),
    'Content-Type': 'application/json'
})

# Geometría lote4
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

# Últimos 90 días
fecha_fin = date.today()
fecha_inicio = fecha_fin - timedelta(days=90)

payload = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['NDVI', 'NDMI', 'SAVI'],
        'date_start': fecha_inicio.isoformat(),
        'date_end': fecha_fin.isoformat(),
        'geometry': geometria,
        'sensors': ['S2L2A'],
        'reference': 'debug_structure',
        'limit': 10,
        'max_cloud_cover_in_aoi': 50,
        'exclude_cover_pixels': True,
        'cloud_masking_level': 3
    }
}

print("Creando tarea...")
response = session.post('https://api-connect.eos.com/api/gdw/api', json=payload, timeout=30)
task_id = response.json().get('task_id')
print(f"Task ID: {task_id}")

print("\nEsperando resultados...")
time.sleep(30)  # Esperar 30s

response = session.get(f'https://api-connect.eos.com/api/gdw/api/{task_id}', timeout=30)
data = response.json()

if 'result' in data and data['result']:
    print(f"\n✅ {len(data['result'])} escenas obtenidas")
    print("\n📊 ESTRUCTURA DE LA PRIMERA ESCENA:")
    print("="*80)
    print(json.dumps(data['result'][0], indent=2))
    print("="*80)
    
    # Mostrar keys de indexes
    if 'indexes' in data['result'][0]:
        print("\n📈 ÍNDICES DISPONIBLES:")
        for idx_name in data['result'][0]['indexes'].keys():
            print(f"  - {idx_name}")
            print(f"    Keys: {list(data['result'][0]['indexes'][idx_name].keys())}")
else:
    print("\n❌ Sin resultados")
    print(json.dumps(data, indent=2)[:500])
