#!/usr/bin/env python
"""
Test: Verificar qué endpoints funcionan con nuestra API key
"""
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

print("="*80)
print("🔍 TEST: Verificando endpoints disponibles con esta API key")
print("="*80)
print(f"API Key: {EOSDA_API_KEY[:25]}...{EOSDA_API_KEY[-10:]}")
print(f"Base URL: {BASE_URL}\n")

# Lista de endpoints para probar
endpoints_test = [
    ("GET", "/field-management/fields", "Field Management - Listar campos"),
    ("GET", "/field-management/fields/10800114", "Field Management - Campo específico"),
    ("GET", "/field-management/fields/crop-types", "Field Management - Tipos de cultivo"),
    ("POST", "/api/gdw/api", "Statistics API - Crear tarea"),
    ("GET", "/field-analytics/trend/10800114", "Field Analytics - Tendencias"),
]

print("📊 Probando endpoints:\n")

for method, endpoint, descripcion in endpoints_test:
    url = f"{BASE_URL}{endpoint}"
    print(f"🔬 {method} {endpoint}")
    print(f"   {descripcion}")
    
    try:
        if method == "GET":
            response = session.get(url, timeout=10)
        elif method == "POST":
            # Payload mínimo para Statistics
            payload = {"type": "test"}
            response = session.post(url, json=payload, timeout=10)
        
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"   📦 Datos: Lista con {len(data)} items")
            elif isinstance(data, dict):
                print(f"   📦 Keys: {list(data.keys())[:5]}")
        elif response.status_code == 403:
            print(f"   ❌ FORBIDDEN - Este endpoint NO está disponible con esta API key")
        elif response.status_code == 401:
            print(f"   ❌ UNAUTHORIZED - Problema de autenticación")
        elif response.status_code == 404:
            print(f"   ⚠️  NOT FOUND - Endpoint no existe o recurso no encontrado")
        else:
            print(f"   ⚠️  Respuesta: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()

print("="*80)
print("✅ Test completado")
