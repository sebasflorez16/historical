"""
Test para verificar el procesamiento de datos EOSDA
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from datetime import datetime

# Simular la estructura de datos que llega de EOSDA
datos_ejemplo = {
    'resultados': [
        {
            'scene_id': 'S2A_tile_20251107_18NZM_0',
            'view_id': 'S2L2A/18/N/ZM/2025/11/7/0',
            'date': '2025-11-07',
            'cloud': 17.14801444043321,
            'notes': [],
            'indexes': {
                'NDVI': {
                    'average': 0.6010434691866585,
                    'max': 0.8524904251098633,
                    'min': 0.06519772112369537
                },
                'SAVI': {
                    'average': 0.3899280358925624,
                    'max': 0.672706663608551,
                    'min': 0.06930605322122574
                },
                'NDMI': {
                    'average': 0.06087676522211523,
                    'max': 0.3501596450805664,
                    'min': -0.16985644400119781
                }
            }
        }
    ],
    'datos_clima': [],
    'field_id': '10800473',
    'indices': ['NDVI', 'SAVI', 'NDMI'],
    'fecha_consulta': '2025-11-11T19:25:00',
    'num_escenas': 6,
    'metodo': 'statistics_api'
}

print("=" * 80)
print("TEST: Procesamiento de datos EOSDA")
print("=" * 80)

print(f"\n✅ Estructura recibida:")
print(f"   - Claves: {list(datos_ejemplo.keys())}")
print(f"   - Número de escenas: {len(datos_ejemplo['resultados'])}")
print(f"   - Índices: {datos_ejemplo['indices']}")

print(f"\n📊 Ejemplo de escena:")
escena = datos_ejemplo['resultados'][0]
print(f"   - Fecha: {escena['date']}")
print(f"   - Nubosidad: {escena['cloud']}%")
print(f"   - Índices disponibles: {list(escena['indexes'].keys())}")

print(f"\n🔍 Valores de índices:")
for indice, valores in escena['indexes'].items():
    print(f"   - {indice}:")
    print(f"     * Promedio: {valores['average']}")
    print(f"     * Máximo: {valores['max']}")
    print(f"     * Mínimo: {valores['min']}")

print(f"\n" + "=" * 80)
print("ANÁLISIS DEL PROBLEMA:")
print("=" * 80)

print("""
El código en views.py está buscando:
  - datos_satelitales.get('ndvi', [])  ❌ (minúsculas)
  - datos_satelitales.get('ndmi', [])  ❌ (minúsculas)
  - datos_satelitales.get('savi', [])  ❌ (minúsculas)

Pero los datos llegan en:
  - datos_satelitales['resultados'][i]['indexes']['NDVI']  ✅ (dentro de cada escena)
  - datos_satelitales['resultados'][i]['indexes']['NDMI']  ✅ (dentro de cada escena)
  - datos_satelitales['resultados'][i]['indexes']['SAVI']  ✅ (dentro de cada escena)

SOLUCIÓN:
  Necesitamos procesar los datos desde 'resultados' agrupándolos por mes
  y extrayendo los valores de 'indexes' de cada escena.
""")

print("\n" + "=" * 80)
print("PROCESAMIENTO CORRECTO:")
print("=" * 80)

# Agrupar por año-mes
from collections import defaultdict

datos_por_mes = defaultdict(lambda: {
    'ndvi': [], 'ndmi': [], 'savi': [],
    'nubosidad': [], 'fechas': []
})

for escena in datos_ejemplo['resultados']:
    fecha = datetime.fromisoformat(escena['date']).date()
    clave_mes = (fecha.year, fecha.month)
    
    # Extraer valores de cada índice
    if 'NDVI' in escena['indexes']:
        datos_por_mes[clave_mes]['ndvi'].append(escena['indexes']['NDVI']['average'])
    if 'NDMI' in escena['indexes']:
        datos_por_mes[clave_mes]['ndmi'].append(escena['indexes']['NDMI']['average'])
    if 'SAVI' in escena['indexes']:
        datos_por_mes[clave_mes]['savi'].append(escena['indexes']['SAVI']['average'])
    
    datos_por_mes[clave_mes]['nubosidad'].append(escena['cloud'])
    datos_por_mes[clave_mes]['fechas'].append(fecha)

print(f"\n✅ Datos agrupados por mes:")
for (year, month), datos in sorted(datos_por_mes.items()):
    ndvi_prom = sum(datos['ndvi']) / len(datos['ndvi']) if datos['ndvi'] else None
    ndmi_prom = sum(datos['ndmi']) / len(datos['ndmi']) if datos['ndmi'] else None
    savi_prom = sum(datos['savi']) / len(datos['savi']) if datos['savi'] else None
    nub_prom = sum(datos['nubosidad']) / len(datos['nubosidad']) if datos['nubosidad'] else None
    
    print(f"\n   📅 {month:02d}/{year}:")
    print(f"      - Escenas: {len(datos['fechas'])}")
    print(f"      - NDVI promedio: {ndvi_prom:.4f}" if ndvi_prom else "      - NDVI: Sin datos")
    print(f"      - NDMI promedio: {ndmi_prom:.4f}" if ndmi_prom else "      - NDMI: Sin datos")
    print(f"      - SAVI promedio: {savi_prom:.4f}" if savi_prom else "      - SAVI: Sin datos")
    print(f"      - Nubosidad promedio: {nub_prom:.2f}%" if nub_prom else "      - Nubosidad: Sin datos")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80)
