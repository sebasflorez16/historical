#!/usr/bin/env python3
"""
Script de diagnóstico completo para verificar la API de EOSDA
Verifica configuración, headers, y autenticación
"""

import os
import sys
import django
import requests
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from django.conf import settings

def diagnosticar_eosda():
    """Realiza un diagnóstico completo de la configuración de EOSDA"""
    
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO DE EOSDA API")
    print("=" * 80)
    
    # 1. Verificar variables de entorno
    print("\n📋 1. VARIABLES DE ENTORNO")
    print("-" * 80)
    
    api_key_env = os.getenv('EOSDA_API_KEY')
    base_url_env = os.getenv('EOSDA_BASE_URL')
    
    print(f"EOSDA_API_KEY (env):  {'✅ Configurada' if api_key_env else '❌ NO configurada'}")
    if api_key_env:
        print(f"  - Longitud: {len(api_key_env)} caracteres")
        print(f"  - Prefijo: {api_key_env[:15]}...")
        print(f"  - Sufijo: ...{api_key_env[-10:]}")
    
    print(f"EOSDA_BASE_URL (env): {base_url_env or '❌ NO configurada'}")
    
    # 2. Verificar settings de Django
    print("\n📋 2. CONFIGURACIÓN DE DJANGO")
    print("-" * 80)
    
    api_key_settings = getattr(settings, 'EOSDA_API_KEY', None)
    base_url_settings = getattr(settings, 'EOSDA_BASE_URL', None)
    
    print(f"EOSDA_API_KEY (settings):  {'✅ Configurada' if api_key_settings else '❌ NO configurada'}")
    if api_key_settings:
        print(f"  - Longitud: {len(api_key_settings)} caracteres")
        print(f"  - Prefijo: {api_key_settings[:15]}...")
        print(f"  - Sufijo: ...{api_key_settings[-10:]}")
        print(f"  - ¿Coincide con env? {'✅ SÍ' if api_key_settings == api_key_env else '❌ NO'}")
    
    print(f"EOSDA_BASE_URL (settings): {base_url_settings or '❌ NO configurada'}")
    
    # 3. Probar diferentes formas de autenticación
    print("\n🔐 3. PRUEBAS DE AUTENTICACIÓN")
    print("-" * 80)
    
    if not api_key_settings or not base_url_settings:
        print("❌ No se puede continuar sin API key y base URL")
        return
    
    # Endpoint de prueba (obtener campos)
    test_url = f"{base_url_settings}/field-management/fields"
    
    # Prueba 1: Header x-api-key (método actual)
    print("\n🔍 Prueba 1: Header 'x-api-key'")
    try:
        headers = {
            'x-api-key': api_key_settings,
            'Content-Type': 'application/json'
        }
        print(f"  Headers: {json.dumps({k: v if k != 'x-api-key' else f'{v[:15]}...' for k, v in headers.items()}, indent=4)}")
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("  ✅ ÉXITO - La API key funciona con 'x-api-key'")
        else:
            print(f"  ❌ FALLO - Error {response.status_code}")
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
    
    # Prueba 2: Header Authorization Bearer
    print("\n🔍 Prueba 2: Header 'Authorization: Bearer'")
    try:
        headers = {
            'Authorization': f'Bearer {api_key_settings}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("  ✅ ÉXITO - La API key funciona con 'Authorization: Bearer'")
        else:
            print(f"  ❌ FALLO - Error {response.status_code}")
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
    
    # Prueba 3: Query parameter
    print("\n🔍 Prueba 3: Query parameter '?api_key='")
    try:
        response = requests.get(f"{test_url}?api_key={api_key_settings}", timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("  ✅ ÉXITO - La API key funciona como query parameter")
        else:
            print(f"  ❌ FALLO - Error {response.status_code}")
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
    
    # Prueba 4: Header X-API-Key (mayúsculas)
    print("\n🔍 Prueba 4: Header 'X-API-Key' (mayúsculas)")
    try:
        headers = {
            'X-API-Key': api_key_settings,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("  ✅ ÉXITO - La API key funciona con 'X-API-Key'")
        else:
            print(f"  ❌ FALLO - Error {response.status_code}")
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
    
    # 4. Verificar respuesta completa de error
    print("\n📋 4. ANÁLISIS DETALLADO DE ERROR")
    print("-" * 80)
    
    try:
        headers = {
            'x-api-key': api_key_settings,
            'Content-Type': 'application/json'
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers de Respuesta:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nCuerpo completo:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # 5. Recomendaciones
    print("\n💡 5. RECOMENDACIONES")
    print("-" * 80)
    
    if not api_key_settings:
        print("❌ Configurar EOSDA_API_KEY en variables de entorno de Railway")
    elif api_key_settings == 'demo_token_reemplazar_con_real':
        print("❌ Reemplazar el token demo con una API key real de EOSDA")
    elif len(api_key_settings) < 20:
        print("⚠️  La API key parece demasiado corta, verificar que sea la key completa")
    else:
        print("✅ La API key está configurada")
        print("\nSi sigue fallando:")
        print("  1. Verificar que la API key esté activa en el panel de EOSDA")
        print("  2. Verificar que no haya restricciones de IP/dominio")
        print("  3. Verificar que la cuenta tenga los permisos necesarios")
        print("  4. Contactar con soporte de EOSDA para validar la key")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    diagnosticar_eosda()
