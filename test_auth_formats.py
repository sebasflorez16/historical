#!/usr/bin/env python3
"""
Script para probar diferentes formatos de autenticación con EOSDA
Basado en la documentación oficial y AWS API Gateway
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('EOSDA_API_KEY')
base_url = os.getenv('EOSDA_BASE_URL', 'https://api.eos.com')

print("=" * 80)
print("PRUEBAS DE AUTENTICACIÓN EOSDA - TODOS LOS FORMATOS")
print("=" * 80)

test_url = f"{base_url}/field-management/fields"

# AWS API Gateway puede usar varios métodos
tests = [
    {
        'nombre': 'x-api-key (minúsculas)',
        'headers': {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'X-API-Key (capitalized)',
        'headers': {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'X-Api-Key (mixed case)',
        'headers': {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'api-key (sin x)',
        'headers': {
            'api-key': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'API-Key',
        'headers': {
            'API-Key': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'apikey (sin guiones)',
        'headers': {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'APIKey',
        'headers': {
            'APIKey': api_key,
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'Authorization: Api-Key',
        'headers': {
            'Authorization': f'Api-Key {api_key}',
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'Authorization: ApiKey',
        'headers': {
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        }
    },
    {
        'nombre': 'Query parameter',
        'headers': {
            'Content-Type': 'application/json'
        },
        'params': {'api_key': api_key}
    },
    {
        'nombre': 'Query parameter (x-api-key)',
        'headers': {
            'Content-Type': 'application/json'
        },
        'params': {'x-api-key': api_key}
    }
]

for i, test in enumerate(tests, 1):
    print(f"\n{'─' * 80}")
    print(f"🔍 Prueba {i}/{len(tests)}: {test['nombre']}")
    print(f"{'─' * 80}")
    
    try:
        params = test.get('params', {})
        response = requests.get(test_url, headers=test['headers'], params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅✅✅ ÉXITO - ESTE ES EL FORMATO CORRECTO ✅✅✅")
            try:
                data = response.json()
                print(f"Datos recibidos: {len(data)} campos")
                if data:
                    print(f"Primer campo: {json.dumps(data[0], indent=2)[:200]}")
            except:
                pass
        elif response.status_code == 401:
            print("❌ 401 - API key inválida")
        elif response.status_code == 403:
            print("❌ 403 - Acceso denegado")
            print(f"Mensaje: {response.text[:100]}")
        else:
            print(f"❌ {response.status_code}")
            print(f"Respuesta: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

print(f"\n{'=' * 80}")
print("FIN DE PRUEBAS")
print(f"{'=' * 80}\n")
