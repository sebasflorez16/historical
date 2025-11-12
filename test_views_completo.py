#!/usr/bin/env python
"""
Test completo del procesamiento de datos EOSDA desde views.py
Simula exactamente el flujo completo de obtención y guardado de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from django.contrib.auth.models import User
from informes.services.eosda_api import eosda_service
from datetime import date, datetime
from collections import defaultdict

print("=" * 80)
print("TEST COMPLETO: Views.py - Obtener y Guardar Datos EOSDA")
print("=" * 80)

# Obtener parcela y usuario
parcela = Parcela.objects.get(id=2)
usuario = User.objects.first()

print(f"\n📍 Parcela: {parcela.nombre}")
print(f"👤 Usuario: {usuario.username}")

# Limpiar datos previos
registros_previos = IndiceMensual.objects.filter(parcela=parcela).count()
IndiceMensual.objects.filter(parcela=parcela).delete()
print(f"\n🗑️  Eliminados {registros_previos} registros previos")

# Obtener datos de EOSDA (igual que en views.py)
print("\n📡 Obteniendo datos de EOSDA...")
datos_satelitales = eosda_service.obtener_datos_optimizado(
    parcela=parcela,
    fecha_inicio=date(2025, 10, 1),
    fecha_fin=date(2025, 11, 11),
    indices=['NDVI', 'NDMI', 'SAVI'],
    usuario=usuario,
    max_nubosidad=80
)

print(f"✅ Datos obtenidos: {len(datos_satelitales.get('resultados', []))} escenas")
print(f"   Método: {datos_satelitales.get('metodo', 'N/A')}")
print(f"   Field ID: {datos_satelitales.get('field_id', 'N/A')}")

# === PROCESAMIENTO EXACTO COMO EN VIEWS.PY ===
print("\n" + "=" * 80)
print("PROCESAMIENTO (código de views.py líneas 1214-1315)")
print("=" * 80)

indices_creados = 0
datos_procesados = 0

# Agrupar datos por año-mes desde la estructura real de EOSDA
datos_por_mes = defaultdict(lambda: {
    'ndvi_valores': [], 'ndvi_max': [], 'ndvi_min': [],
    'ndmi_valores': [], 'ndmi_max': [], 'ndmi_min': [],
    'savi_valores': [], 'savi_max': [], 'savi_min': [],
    'nubosidad': []
})

# Procesar cada escena satelital
for escena in datos_satelitales.get('resultados', []):
    try:
        fecha_str = escena.get('date')
        if not fecha_str:
            continue
        
        fecha = datetime.fromisoformat(fecha_str).date()
        clave_mes = (fecha.year, fecha.month)
        
        # Extraer índices de cada escena
        indexes = escena.get('indexes', {})
        nubosidad = escena.get('cloud', 0)
        
        # NDVI
        if 'NDVI' in indexes:
            datos_por_mes[clave_mes]['ndvi_valores'].append(indexes['NDVI'].get('average', 0))
            datos_por_mes[clave_mes]['ndvi_max'].append(indexes['NDVI'].get('max', 0))
            datos_por_mes[clave_mes]['ndvi_min'].append(indexes['NDVI'].get('min', 0))
        
        # NDMI
        if 'NDMI' in indexes:
            datos_por_mes[clave_mes]['ndmi_valores'].append(indexes['NDMI'].get('average', 0))
            datos_por_mes[clave_mes]['ndmi_max'].append(indexes['NDMI'].get('max', 0))
            datos_por_mes[clave_mes]['ndmi_min'].append(indexes['NDMI'].get('min', 0))
        
        # SAVI
        if 'SAVI' in indexes:
            datos_por_mes[clave_mes]['savi_valores'].append(indexes['SAVI'].get('average', 0))
            datos_por_mes[clave_mes]['savi_max'].append(indexes['SAVI'].get('max', 0))
            datos_por_mes[clave_mes]['savi_min'].append(indexes['SAVI'].get('min', 0))
        
        datos_por_mes[clave_mes]['nubosidad'].append(nubosidad)
        
    except Exception as e:
        print(f"❌ Error procesando escena: {str(e)}")
        continue

print(f"\n📊 Datos agrupados por mes: {len(datos_por_mes)} meses")

# Guardar datos agrupados por mes
for (year, month), datos in datos_por_mes.items():
    try:
        # Calcular promedios
        ndvi_prom = sum(datos['ndvi_valores']) / len(datos['ndvi_valores']) if datos['ndvi_valores'] else None
        ndvi_max = max(datos['ndvi_max']) if datos['ndvi_max'] else None
        ndvi_min = min(datos['ndvi_min']) if datos['ndvi_min'] else None
        
        ndmi_prom = sum(datos['ndmi_valores']) / len(datos['ndmi_valores']) if datos['ndmi_valores'] else None
        ndmi_max = max(datos['ndmi_max']) if datos['ndmi_max'] else None
        ndmi_min = min(datos['ndmi_min']) if datos['ndmi_min'] else None
        
        savi_prom = sum(datos['savi_valores']) / len(datos['savi_valores']) if datos['savi_valores'] else None
        savi_max = max(datos['savi_max']) if datos['savi_max'] else None
        savi_min = min(datos['savi_min']) if datos['savi_min'] else None
        
        nub_prom = sum(datos['nubosidad']) / len(datos['nubosidad']) if datos['nubosidad'] else 0
        
        # Crear o actualizar registro mensual
        defaults = {
            'ndvi_promedio': ndvi_prom,
            'ndvi_maximo': ndvi_max,
            'ndvi_minimo': ndvi_min,
            'ndmi_promedio': ndmi_prom,
            'ndmi_maximo': ndmi_max,
            'ndmi_minimo': ndmi_min,
            'savi_promedio': savi_prom,
            'savi_maximo': savi_max,
            'savi_minimo': savi_min,
            'nubosidad_promedio': nub_prom,
            'fuente_datos': 'EOSDA',
            'calidad_datos': 'buena' if nub_prom < 30 else ('regular' if nub_prom < 50 else 'pobre')
        }
        
        indice, created = IndiceMensual.objects.update_or_create(
            parcela=parcela,
            año=year,
            mes=month,
            defaults=defaults
        )
        
        if created:
            indices_creados += 1
        datos_procesados += 1
        
        ndvi_str = f"{ndvi_prom:.3f}" if ndvi_prom else "N/A"
        ndvi_min_str = f"{ndvi_min:.3f}" if ndvi_min else "N/A"
        ndvi_max_str = f"{ndvi_max:.3f}" if ndvi_max else "N/A"
        ndmi_str = f"{ndmi_prom:.3f}" if ndmi_prom else "N/A"
        ndmi_min_str = f"{ndmi_min:.3f}" if ndmi_min else "N/A"
        ndmi_max_str = f"{ndmi_max:.3f}" if ndmi_max else "N/A"
        savi_str = f"{savi_prom:.3f}" if savi_prom else "N/A"
        savi_min_str = f"{savi_min:.3f}" if savi_min else "N/A"
        savi_max_str = f"{savi_max:.3f}" if savi_max else "N/A"
        
        print(f"\n   ✅ {month:02d}/{year} ({'NUEVO' if created else 'ACTUALIZADO'}):")
        print(f"      - Escenas procesadas: {len(datos['ndvi_valores'])}")
        print(f"      - NDVI: {ndvi_str} (rango: {ndvi_min_str} - {ndvi_max_str})")
        print(f"      - NDMI: {ndmi_str} (rango: {ndmi_min_str} - {ndmi_max_str})")
        print(f"      - SAVI: {savi_str} (rango: {savi_min_str} - {savi_max_str})")
        print(f"      - Nubosidad: {nub_prom:.1f}%")
        print(f"      - Calidad: {defaults['calidad_datos']}")
        
    except Exception as e:
        print(f"❌ Error guardando datos de {month}/{year}: {str(e)}")

# Procesar datos climáticos si existen
for dato in datos_satelitales.get('datos_clima', []):
    try:
        fecha_dato = dato.get('fecha')
        if isinstance(fecha_dato, str):
            fecha_dato = datetime.fromisoformat(fecha_dato).date()
        
        IndiceMensual.objects.filter(
            parcela=parcela,
            año=fecha_dato.year,
            mes=fecha_dato.month
        ).update(
            temperatura_promedio=dato.get('temperatura_promedio'),
            temperatura_maxima=dato.get('temperatura_maxima'),
            temperatura_minima=dato.get('temperatura_minima'),
            precipitacion_total=dato.get('precipitacion_total')
        )
    except Exception as e:
        print(f"❌ Error procesando dato climático: {str(e)}")

print("\n" + "=" * 80)
print("RESULTADOS FINALES")
print("=" * 80)
print(f"\n✅ Datos históricos procesados para {parcela.nombre}:")
print(f"   - {indices_creados} nuevos registros")
print(f"   - {datos_procesados} datos procesados")
print(f"   - Total en BD: {IndiceMensual.objects.filter(parcela=parcela).count()} registros")

# Verificar en base de datos
print("\n📋 Verificación en base de datos:")
registros = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
for reg in registros:
    ndvi_str = f"{reg.ndvi_promedio:.3f}" if reg.ndvi_promedio else "N/A"
    ndmi_str = f"{reg.ndmi_promedio:.3f}" if reg.ndmi_promedio else "N/A"
    savi_str = f"{reg.savi_promedio:.3f}" if reg.savi_promedio else "N/A"
    print(f"   - {reg.mes:02d}/{reg.año}: NDVI={ndvi_str}, NDMI={ndmi_str}, SAVI={savi_str}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO CON ÉXITO")
print("=" * 80)
