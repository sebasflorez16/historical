"""
Script para actualizar etiquetas de fuente_datos de 'Open-Meteo' a 'Solo Clima'
Hace el nombre más claro y menos confuso para los usuarios
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual

print("=" * 60)
print("ACTUALIZACIÓN DE ETIQUETAS DE FUENTE")
print("=" * 60)

# Buscar registros con fuente_datos='Open-Meteo'
registros_openmeteo = IndiceMensual.objects.filter(fuente_datos='Open-Meteo')
total = registros_openmeteo.count()

print(f"\n📊 Registros con fuente_datos='Open-Meteo': {total}")

if total > 0:
    print(f"\n🔄 Actualizando a 'Solo Clima'...")
    actualizados = registros_openmeteo.update(fuente_datos='Solo Clima')
    print(f"✅ {actualizados} registros actualizados correctamente")
    print(f"\n💡 Ahora se mostrará como '🌦️ Solo Clima' con tooltip explicativo")
else:
    print("✅ No hay registros que actualizar")
