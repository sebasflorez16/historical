#!/usr/bin/env python3
"""
Script de diagnóstico simplificado para EOSDA API
No requiere Django, solo variables de entorno
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar .env local si existe
load_dotenv()

def diagnosticar_eosda():
    """Realiza un diagnóstico completo de la configuración de EOSDA"""
    
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO DE EOSDA API")
    print("=" * 80)
    
    # 1. Verificar variables de entorno
    print("\n📋 1. VARIABLES DE ENTORNO")
    print("-" * 80)
    
    api_key = os.getenv('EOSDA_API_KEY')
    base_url = os.getenv('EOSDA_BASE_URL', 'https://api.eos.com')
    
    print(f"EOSDA_API_KEY:  {'✅ Configurada' if api_key else '❌ NO configurada'}")
    if api_key:
        print(f"  - Longitud: {len(api_key)} caracteres")
        print(f"  - Prefijo: {api_key[:15]}...")
        print(f"  - Sufijo: ...{api_key[-10:]}")
        print(f"  - ¿Es demo? {'⚠️  SÍ (reemplazar)' if 'demo' in api_key.lower() else '✅ NO'}")
    
    print(f"EOSDA_BASE_URL: {base_url}")
    
    if not api_key:
        print("\n❌ No se puede continuar sin API key")
        return
    
    # 2. Probar diferentes formas de autenticación
    print("\n🔐 2. PRUEBAS DE AUTENTICACIÓN")
    print("-" * 80)
    
    # Endpoint de prueba (obtener campos)
    test_url = f"{base_url}/field-management/fields"
    print(f"Endpoint de prueba: {test_url}\n")
    
    # Prueba 1: Header x-api-key (método recomendado por EOSDA)
    print("🔍 Prueba 1: Header 'x-api-key' (método actual)")
    try:
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  ├─ Status: {response.status_code}")
        print(f"  ├─ Response: {response.text[:150]}{'...' if len(response.text) > 150 else ''}")
        
        if response.status_code == 200:
            print("  └─ ✅ ÉXITO - La API key funciona correctamente")
            try:
                data = response.json()
                print(f"\n  📊 Datos obtenidos: {len(data)} campos")
                if data:
                    print(f"  └─ Ejemplo: {data[0].get('name', 'Sin nombre')}")
            except:
                pass
        elif response.status_code == 401:
            print("  └─ ❌ Error 401 - API key inválida o expirada")
        elif response.status_code == 403:
            print("  └─ ❌ Error 403 - Acceso denegado (Missing Authentication Token)")
            print("      Posibles causas:")
            print("      - API key incompleta o incorrecta")
            print("      - Header mal formado")
            print("      - Restricciones de IP/dominio")
        else:
            print(f"  └─ ❌ Error {response.status_code}")
    except Exception as e:
        print(f"  └─ ❌ ERROR: {str(e)}")
    
    # Prueba 2: Header Authorization Bearer
    print("\n🔍 Prueba 2: Header 'Authorization: Bearer'")
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  ├─ Status: {response.status_code}")
        print(f"  ├─ Response: {response.text[:100]}{'...' if len(response.text) > 100 else ''}")
        
        if response.status_code == 200:
            print("  └─ ✅ ÉXITO - Funciona con Bearer token")
        else:
            print(f"  └─ ❌ FALLO - No funciona con Bearer")
    except Exception as e:
        print(f"  └─ ❌ ERROR: {str(e)}")
    
    # Prueba 3: Header X-API-Key (mayúsculas)
    print("\n🔍 Prueba 3: Header 'X-API-Key' (mayúsculas)")
    try:
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  ├─ Status: {response.status_code}")
        print(f"  ├─ Response: {response.text[:100]}{'...' if len(response.text) > 100 else ''}")
        
        if response.status_code == 200:
            print("  └─ ✅ ÉXITO - Funciona con mayúsculas")
        else:
            print(f"  └─ ❌ FALLO")
    except Exception as e:
        print(f"  └─ ❌ ERROR: {str(e)}")
    
    # 3. Análisis detallado de la última respuesta
    print("\n📋 3. ANÁLISIS DETALLADO DE ERROR")
    print("-" * 80)
    
    try:
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"\nHeaders de Respuesta:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nCuerpo completo:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # 4. Validar formato de API key
    print("\n🔍 4. VALIDACIÓN DE API KEY")
    print("-" * 80)
    
    print(f"Formato: {'✅ Comienza con apk.' if api_key.startswith('apk.') else '⚠️  No comienza con apk.'}")
    print(f"Longitud: {len(api_key)} caracteres {'✅' if len(api_key) > 60 else '⚠️  Parece corta'}")
    
    # Verificar si tiene caracteres extraños
    import string
    valid_chars = string.ascii_letters + string.digits + '.'
    invalid_chars = [c for c in api_key if c not in valid_chars]
    if invalid_chars:
        print(f"⚠️  Caracteres inválidos encontrados: {set(invalid_chars)}")
    else:
        print(f"✅ Caracteres válidos")
    
    # 5. Recomendaciones
    print("\n💡 5. RECOMENDACIONES")
    print("-" * 80)
    
    if not api_key:
        print("❌ Configurar EOSDA_API_KEY en variables de entorno")
    elif 'demo' in api_key.lower():
        print("❌ Reemplazar el token demo con una API key real de EOSDA")
    elif len(api_key) < 40:
        print("⚠️  La API key parece demasiado corta, verificar que sea completa")
    else:
        print("✅ La API key tiene formato correcto")
        print("\n📋 Próximos pasos si sigue fallando:")
        print("  1. Verificar que la API key esté activa en https://eos.com/dashboard")
        print("  2. Verificar que no haya restricciones de IP/dominio configuradas")
        print("  3. Verificar que la cuenta EOSDA tenga permisos para Field Management API")
        print("  4. Verificar que la key no haya expirado")
        print("  5. Probar crear una nueva API key en el panel de EOSDA")
        print("  6. Contactar soporte de EOSDA: support@eos.com")
    
    print("\n" + "=" * 80)
    print("\n🔗 Recursos útiles:")
    print("  - Documentación EOSDA: https://doc.eos.com/")
    print("  - Dashboard EOSDA: https://eos.com/dashboard")
    print("  - Field Management API: https://doc.eos.com/docs/field-management-api/")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    diagnosticar_eosda()
