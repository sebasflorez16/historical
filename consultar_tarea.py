#!/usr/bin/env python
"""
Consultar el estado de la tarea que acabamos de crear
"""
import os
import requests
from dotenv import load_dotenv
import time
import json

load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"

# Task ID de la prueba anterior
TASK_ID = "470a38c8-d16a-4b7f-bd5c-0123dbcb78e4"

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

print("="*80)
print(f"🔍 CONSULTANDO TAREA: {TASK_ID}")
print("="*80)
print("Período: 2023-12-01 → 2024-03-31 (verano colombiano)")
print("Índice: NDVI")
print()

url = f"{BASE_URL}/api/gdw/api/{TASK_ID}"

for intento in range(30):  # 30 intentos = 5 minutos max
    print(f"🔄 Intento {intento + 1}/30...")
    
    response = session.get(url, timeout=30)
    
    if response.status_code != 200:
        print(f"   ❌ Status: {response.status_code}")
        if response.status_code == 429:
            print("   ⏳ Rate limit, esperando 15s...")
            time.sleep(15)
            continue
        print(f"   Error: {response.text[:200]}")
        break
    
    data = response.json()
    status = data.get('status', 'unknown')
    
    print(f"   Status: {status}")
    
    # Verificar si hay resultados
    if 'result' in data and data['result']:
        print(f"\n✅ ¡RESULTADOS OBTENIDOS!")
        result = data['result']
        print(f"   Total de escenas: {len(result)}")
        
        if len(result) > 0:
            print(f"\n📊 Primeras 3 escenas:")
            for i, escena in enumerate(result[:3], 1):
                fecha = escena.get('date', escena.get('dt', 'N/A'))
                cloud = escena.get('cloud', escena.get('cl', 'N/A'))
                
                # Buscar el valor NDVI
                ndvi = None
                if 'mean' in escena:
                    ndvi = escena['mean'].get('ndvi', escena['mean'].get('NDVI'))
                elif 'average' in escena:
                    ndvi = escena.get('average')
                
                print(f"   {i}. {fecha}")
                print(f"      Nubes: {cloud}%")
                if ndvi is not None:
                    print(f"      NDVI: {ndvi:.4f}")
        
        print(f"\n💾 Estructura completa de una escena:")
        print(json.dumps(result[0], indent=2)[:500] + "...")
        break
    
    # Verificar errores
    if 'errors' in data and data['errors']:
        print(f"\n❌ ERRORES:")
        print(f"   {data['errors']}")
        break
    
    if status in ['failed', 'error']:
        print(f"\n❌ Tarea falló con status: {status}")
        break
    
    if status in ['pending', 'processing', 'running']:
        print(f"   ⏳ Aún procesando...")
    
    # Mostrar toda la respuesta cada 5 intentos
    if intento % 5 == 4:
        print(f"\n   📋 Respuesta completa:")
        print(f"   {json.dumps(data, indent=2)[:300]}...")
    
    if intento < 29:
        print(f"   Esperando 10s...")
        time.sleep(10)

print("\n" + "="*80)
