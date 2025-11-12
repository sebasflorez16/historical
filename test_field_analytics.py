#!/usr/bin/env python
"""
Script para probar Field Analytics API directamente
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import requests
from informes.models import Parcela

# Configuración
EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api.eos.com"
field_id = 10800114  # lote4

print(f"🧪 Probando Field Analytics API")
print(f"   Base URL: {BASE_URL}")
print(f"   Field ID: {field_id}")
print(f"   API Key: {EOSDA_API_KEY[:20]}..." if EOSDA_API_KEY else "   ❌ No API Key")

# Configurar sesión
session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {EOSDA_API_KEY}',
    'Content-Type': 'application/json'
})

# Fechas
fecha_fin = date.today()
fecha_inicio = fecha_fin - timedelta(days=90)

print(f"\n📅 Período: {fecha_inicio} → {fecha_fin}")

# Probar con NDVI
indice = 'ndvi'
print(f"\n🔬 Probando índice: {indice.upper()}")

# Según la documentación de EOSDA Field Analytics
url = f"{BASE_URL}/field-analytics/trend/{field_id}"

# Payload basado en la documentación
payload = {
    'index': indice,
    'date_start': fecha_inicio.isoformat(),
    'date_end': fecha_fin.isoformat(),
    'satellites': ['sentinel-2'],
    'cloud_max': 50
}

print(f"\n📤 POST {url}")
print(f"   Payload: {payload}")

try:
    response = session.post(url, json=payload, timeout=30)
    
    print(f"\n📥 Respuesta: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print(f"\n✅ Éxito!")
        data = response.json()
        print(f"   Datos: {data}")
    else:
        print(f"\n❌ Error {response.status_code}")
        print(f"   Respuesta: {response.text}")
        
        # Intentar con otros formatos
        print(f"\n🔄 Probando formato alternativo...")
        payload2 = {
            'bm_type': indice,
            'date_start': fecha_inicio.isoformat(),
            'date_end': fecha_fin.isoformat(),
            'satellite': 'S2_MSI_L2A',
            'max_cloud': 50
        }
        print(f"   Payload 2: {payload2}")
        response2 = session.post(url, json=payload2, timeout=30)
        print(f"   Respuesta 2: {response2.status_code} - {response2.text[:200]}")
        
except Exception as e:
    print(f"\n❌ Excepción: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
