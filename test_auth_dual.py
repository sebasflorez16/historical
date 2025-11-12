#!/usr/bin/env python
"""
Test de autenticación dual: Bearer Token + x-api-key
"""
import os
import requests
from dotenv import load_dotenv
import json
from datetime import date

load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
EOSDA_JWT_TOKEN = os.getenv('EOSDA_JWT_TOKEN', '')  # Añadir esto al .env
BASE_URL = "https://api-connect.eos.com"

print("="*80)
print("🔐 TEST DE AUTENTICACIÓN DUAL")
print("="*80)
print(f"x-api-key: {EOSDA_API_KEY[:25]}..." if EOSDA_API_KEY else "❌ Sin API Key")
print(f"JWT Token: {EOSDA_JWT_TOKEN[:25]}..." if EOSDA_JWT_TOKEN else "❌ Sin JWT Token")
print()

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

# Fechas de verano
fecha_inicio = date(2023, 12, 1)
fecha_fin = date(2024, 3, 31)

# TEST 1: Solo x-api-key (método actual)
print("📝 TEST 1: Solo x-api-key")
print("-" * 80)

session1 = requests.Session()
session1.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

payload = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],
        'date_start': fecha_inicio.isoformat(),
        'date_end': fecha_fin.isoformat(),
        'geometry': geometria,
        'sensors': ['S2_MSI_L2A'],
        'reference': 'test_auth1',
        'limit': 10,
        'max_cloud_cover_in_aoi': 50,
        'exclude_cover_pixels': True,
        'cloud_masking_level': 3
    }
}

url = f"{BASE_URL}/api/gdw/api"
print(f"POST {url}")
response1 = session1.post(url, json=payload, timeout=30)
print(f"Status: {response1.status_code}")
if response1.status_code in [200, 201, 202]:
    data = response1.json()
    print(f"✅ ÉXITO! Task ID: {data.get('task_id', 'N/A')}")
else:
    print(f"❌ Error: {response1.text[:200]}")

print()

# TEST 2: Bearer Token + x-api-key (método dual)
if EOSDA_JWT_TOKEN:
    print("📝 TEST 2: Bearer Token + x-api-key")
    print("-" * 80)
    
    session2 = requests.Session()
    session2.headers.update({
        'Authorization': f'Bearer {EOSDA_JWT_TOKEN}',
        'x-api-key': EOSDA_API_KEY,
        'Content-Type': 'application/json'
    })
    
    payload['params']['reference'] = 'test_auth2'
    
    print(f"POST {url}")
    response2 = session2.post(url, json=payload, timeout=30)
    print(f"Status: {response2.status_code}")
    if response2.status_code in [200, 201, 202]:
        data = response2.json()
        print(f"✅ ÉXITO! Task ID: {data.get('task_id', 'N/A')}")
    else:
        print(f"❌ Error: {response2.text[:200]}")
else:
    print("⚠️  TEST 2 OMITIDO: No hay JWT Token configurado")
    print("    Añade EOSDA_JWT_TOKEN al archivo .env")

print()

# TEST 3: Solo Bearer Token (sin x-api-key)
if EOSDA_JWT_TOKEN:
    print("📝 TEST 3: Solo Bearer Token (sin x-api-key)")
    print("-" * 80)
    
    session3 = requests.Session()
    session3.headers.update({
        'Authorization': f'Bearer {EOSDA_JWT_TOKEN}',
        'Content-Type': 'application/json'
    })
    
    payload['params']['reference'] = 'test_auth3'
    
    print(f"POST {url}")
    response3 = session3.post(url, json=payload, timeout=30)
    print(f"Status: {response3.status_code}")
    if response3.status_code in [200, 201, 202]:
        data = response3.json()
        print(f"✅ ÉXITO! Task ID: {data.get('task_id', 'N/A')}")
    else:
        print(f"❌ Error: {response3.text[:200]}")

print()
print("="*80)
print("💡 INSTRUCCIONES:")
print("="*80)
print("1. Obtén el JWT Token de tu otra aplicación")
print("2. Añádelo al archivo .env:")
print("   EOSDA_JWT_TOKEN=tu_jwt_token_aqui")
print("3. Ejecuta este script de nuevo para probar")
print("="*80)
