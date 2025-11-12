#!/usr/bin/env python
"""
Sincronizar campo lote4 correctamente con EOSDA
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.eosda_api import eosda_service
import json

print("="*80)
print("🔄 SINCRONIZAR LOTE4 CON EOSDA")
print("="*80)

# Obtener parcela
parcela = Parcela.objects.get(id=6)
print(f"\n📦 Parcela local:")
print(f"   Nombre: {parcela.nombre}")
print(f"   Cultivo: {parcela.cultivo}")
print(f"   Field ID actual: {parcela.eosda_field_id}")

# Obtener geometría
geometria = json.loads(parcela.poligono_geojson)
print(f"   Geometría: {geometria['type']} con {len(geometria['coordinates'][0])} puntos")

print(f"\n🔄 Sincronizando con EOSDA...")

try:
    # Usar el método de sincronización
    resultado = eosda_service.sincronizar_campo(parcela)
    
    if resultado.get('success'):
        print(f"✅ ÉXITO!")
        print(f"   Field ID: {resultado.get('field_id')}")
        print(f"   Mensaje: {resultado.get('message', 'Campo sincronizado')}")
        
        # Recargar parcela
        parcela.refresh_from_db()
        print(f"\n📦 Parcela actualizada:")
        print(f"   Field ID: {parcela.eosda_field_id}")
        print(f"   Fecha sincronización: {parcela.eosda_ultima_sincronizacion}")
    else:
        print(f"❌ Error: {resultado.get('error', 'Desconocido')}")
        if 'details' in resultado:
            print(f"   Detalles: {resultado['details']}")
            
except Exception as e:
    print(f"❌ Excepción: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
