"""
Script de prueba para Open-Meteo Weather API
Verifica que se puedan obtener datos climáticos históricos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from datetime import datetime, timedelta
from informes.services.weather_service import OpenMeteoWeatherService

# Coordenadas de lote 2 (Colombia)
latitud = 5.736933
longitud = -71.520019

# Rango de fechas: últimos 3 meses
fecha_fin = datetime.now()
fecha_inicio = fecha_fin - timedelta(days=90)

print("=" * 60)
print("TEST OPEN-METEO WEATHER API")
print("=" * 60)
print(f"Ubicación: lat={latitud}, lon={longitud} (Colombia)")
print(f"Rango: {fecha_inicio.date()} a {fecha_fin.date()}")
print()

# Obtener datos diarios
print("1️⃣ Obteniendo datos diarios...")
datos_diarios = OpenMeteoWeatherService.obtener_datos_historicos(
    latitud=latitud,
    longitud=longitud,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin
)

if datos_diarios:
    print(f"✅ Obtenidos {len(datos_diarios)} días de datos")
    print(f"\nEjemplo (primeros 3 días):")
    for dato in datos_diarios[:3]:
        print(f"  {dato['fecha']}: Temp={dato['temperatura_promedio']:.1f}°C, "
              f"Precip={dato['precipitacion_total']:.1f}mm")
else:
    print("❌ No se obtuvieron datos")
    exit(1)

# Agrupar por mes
print("\n2️⃣ Agrupando por mes...")
datos_por_mes = OpenMeteoWeatherService.agrupar_por_mes(datos_diarios)

if datos_por_mes:
    print(f"✅ Datos agrupados en {len(datos_por_mes)} meses")
    print(f"\nResumen mensual:")
    for (year, month), datos in sorted(datos_por_mes.items()):
        temp = datos.get('temperatura_promedio')
        precip = datos.get('precipitacion_total')
        temp_str = f"{temp:.1f}" if temp else "N/A"
        precip_str = f"{precip:.1f}" if precip else "N/A"
        print(f"  {year}-{month:02d}: Temp promedio={temp_str}°C, "
              f"Precip total={precip_str}mm")
else:
    print("❌ Error agrupando datos")
    exit(1)

print("\n" + "=" * 60)
print("✅ TEST EXITOSO - Open-Meteo funcionando correctamente")
print("=" * 60)
