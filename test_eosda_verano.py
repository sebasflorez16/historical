#!/usr/bin/env python
"""
Test de EOSDA API con fechas de verano colombiano (diciembre-marzo)
Prueba directa con la parcela lote4
"""
import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, User
from informes.services.eosda_api import eosda_service
import json

print("="*80)
print("🧪 TEST EOSDA API - VERANO COLOMBIANO 2024")
print("="*80)

# Obtener parcela lote4
try:
    parcela = Parcela.objects.get(id=6)  # lote4
    print(f"\n✅ Parcela encontrada: {parcela.nombre}")
    print(f"   ID: {parcela.id}")
    print(f"   Field ID EOSDA: {parcela.eosda_field_id}")
    
    # Verificar geometría
    if parcela.poligono_geojson:
        geometria = json.loads(parcela.poligono_geojson)
        print(f"   Geometría: {geometria['type']} con {len(geometria.get('coordinates', [[]])[0])} puntos")
    else:
        print("   ❌ Sin geometría GeoJSON")
        sys.exit(1)
        
except Parcela.DoesNotExist:
    print("❌ Parcela lote4 (ID=6) no encontrada")
    sys.exit(1)

# Obtener usuario admin
try:
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario = User.objects.first()
    print(f"   Usuario: {usuario.username if usuario else 'Sin usuario'}")
except:
    usuario = None
    print("   ⚠️ Sin usuario")

# FECHAS DE VERANO COLOMBIANO (diciembre 2023 - marzo 2024)
# Época seca con buena visibilidad satelital
fecha_inicio = date(2023, 12, 1)   # Inicio de verano
fecha_fin = date(2024, 3, 31)      # Fin de verano

print(f"\n📅 PERÍODO DE ANÁLISIS:")
print(f"   Inicio: {fecha_inicio.strftime('%d/%m/%Y')} (inicio verano)")
print(f"   Fin: {fecha_fin.strftime('%d/%m/%Y')} (fin verano)")
print(f"   Duración: {(fecha_fin - fecha_inicio).days} días")
print(f"   Época: Verano/Estación seca (mejor visibilidad)")

# Índices a consultar
indices = ['ndvi', 'ndmi', 'savi']
print(f"\n📊 Índices: {', '.join([i.upper() for i in indices])}")

# Verificar API key
api_key = os.getenv('EOSDA_API_KEY')
if api_key:
    print(f"\n🔑 API Key: {api_key[:25]}...{api_key[-10:]}")
else:
    print("\n❌ No hay API Key configurada")
    sys.exit(1)

print("\n" + "="*80)
print("🚀 INICIANDO CONSULTA A EOSDA API...")
print("="*80)
print("⏳ Esto puede tardar 30-150 segundos (polling con delays de 10s)")
print("💡 Los logs del proceso aparecerán a continuación:\n")

try:
    # Llamar al servicio con método optimizado
    resultado = eosda_service.obtener_datos_optimizado(
        parcela=parcela,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        indices=indices,
        usuario=usuario,
        max_nubosidad=50
    )
    
    print("\n" + "="*80)
    print("📥 RESULTADO:")
    print("="*80)
    
    if 'error' in resultado:
        print(f"❌ ERROR: {resultado['error']}")
        if 'resultados' in resultado:
            print(f"   Resultados: {len(resultado['resultados'])} items")
    else:
        print(f"✅ ÉXITO!")
        print(f"\n📊 Resumen de datos:")
        print(f"   - Field ID: {resultado.get('field_id', 'N/A')}")
        print(f"   - Índices: {', '.join(resultado.get('indices', []))}")
        print(f"   - Fecha consulta: {resultado.get('fecha_consulta', 'N/A')}")
        print(f"   - Método: {resultado.get('metodo', 'N/A')}")
        print(f"   - Total escenas: {resultado.get('num_escenas', 0)}")
        
        if 'resultados' in resultado and resultado['resultados']:
            print(f"\n📈 Primeras 5 escenas:")
            for i, escena in enumerate(resultado['resultados'][:5], 1):
                fecha = escena.get('dt', escena.get('fecha', 'N/A'))
                cloud = escena.get('cl', escena.get('cloud_coverage', 'N/A'))
                print(f"   {i}. {fecha} - Nubes: {cloud}%")
                
                # Mostrar valores de índices
                if 'mean' in escena:
                    means = escena.get('mean', {})
                    for idx, val in means.items():
                        print(f"      {idx.upper()}: {val:.4f}")
        
        print(f"\n💾 Datos guardados en caché para futuras consultas")
    
    print("\n" + "="*80)
    
except Exception as e:
    print("\n" + "="*80)
    print(f"❌ EXCEPCIÓN:")
    print("="*80)
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    print("="*80)

print("\n✅ Test completado")
