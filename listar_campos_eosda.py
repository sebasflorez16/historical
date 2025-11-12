#!/usr/bin/env python
"""
Listar campos reales en la cuenta EOSDA
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

print("="*80)
print("📋 CAMPOS EN TU CUENTA DE EOSDA")
print("="*80)

url = f"{BASE_URL}/field-management/fields"
response = session.get(url, timeout=30)

if response.status_code == 200:
    campos = response.json()
    print(f"\n✅ Encontrados {len(campos)} campos:\n")
    
    for i, campo in enumerate(campos, 1):
        print(f"Campo {i}:")
        print(f"   ID: {campo.get('id')}")
        print(f"   Nombre: {campo.get('name', 'Sin nombre')}")
        print(f"   Cultivo: {campo.get('crop_type', 'Sin cultivo')}")
        print(f"   Área: {campo.get('area', 0)} ha")
        print(f"   Creado: {campo.get('created', 'N/A')}")
        
        if 'boundary' in campo:
            geom = campo['boundary']
            print(f"   Geometría: {geom.get('type', 'N/A')}")
        
        print()
else:
    print(f"❌ Error {response.status_code}: {response.text}")

print("="*80)
