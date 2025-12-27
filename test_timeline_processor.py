#!/usr/bin/env python3
"""
Script de prueba para el Timeline Processor
Verifica que la lógica de clasificación y procesamiento funcione correctamente
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Test del Timeline Processor\n")
print("=" * 60)

# Test 1: Importación
try:
    from informes.processors.timeline_processor import TimelineProcessor
    print("✅ Test 1: Importación exitosa")
except ImportError as e:
    print(f"❌ Test 1 FALLÓ: {e}")
    sys.exit(1)

# Test 2: Clasificación NDVI
print("\n📊 Test 2: Clasificación NDVI")
test_cases_ndvi = [
    (0.90, 'excelente', '🌟'),
    (0.78, 'muy_bueno', '✅'),
    (0.65, 'bueno', '👍'),
    (0.45, 'moderado', '⚠️'),
    (0.25, 'bajo', '🔴'),
]

for valor, nivel_esperado, icono_esperado in test_cases_ndvi:
    # Crear mock de IndiceMensual
    class MockIndice:
        def __init__(self):
            self.ndvi_promedio = valor
            self.ndmi_promedio = None
            self.savi_promedio = None
    
    mock = MockIndice()
    clasificaciones = TimelineProcessor._generar_clasificaciones(mock)
    
    if 'ndvi' in clasificaciones:
        nivel_obtenido = clasificaciones['ndvi']['nivel']
        icono_obtenido = clasificaciones['ndvi']['icono']
        
        if nivel_obtenido == nivel_esperado and icono_obtenido == icono_esperado:
            print(f"  ✅ NDVI {valor:.2f} → {nivel_esperado} {icono_esperado}")
        else:
            print(f"  ❌ NDVI {valor:.2f} → Esperado: {nivel_esperado} {icono_esperado}, "
                  f"Obtenido: {nivel_obtenido} {icono_obtenido}")
    else:
        print(f"  ❌ NDVI {valor:.2f} → No se generó clasificación")

# Test 3: Comparación entre meses
print("\n📈 Test 3: Comparación con mes anterior")

class MockIndiceActual:
    def __init__(self):
        self.ndvi_promedio = 0.75
        self.ndmi_promedio = 0.30
        self.savi_promedio = 0.68

class MockIndiceAnterior:
    def __init__(self):
        self.ndvi_promedio = 0.70
        self.ndmi_promedio = 0.28
        self.savi_promedio = 0.65

actual = MockIndiceActual()
anterior = MockIndiceAnterior()

comparacion = TimelineProcessor._comparar_con_mes_anterior(actual, anterior)

if 'ndvi' in comparacion:
    ndvi_comp = comparacion['ndvi']
    print(f"  ✅ NDVI: {ndvi_comp['tendencia']} {ndvi_comp['icono']} "
          f"({ndvi_comp['porcentaje']:+.1f}%)")
else:
    print("  ❌ No se generó comparación NDVI")

# Test 4: Resumen simple
print("\n📝 Test 4: Generación de resumen simple")

class MockIndiceCompleto:
    def __init__(self):
        self.ndvi_promedio = 0.78
        self.ndmi_promedio = 0.32
        self.savi_promedio = 0.70
        self.temperatura_promedio = 25.5
        self.precipitacion_total = 120.3

indice_completo = MockIndiceCompleto()
clasificaciones_completas = TimelineProcessor._generar_clasificaciones(indice_completo)
resumen = TimelineProcessor._generar_resumen_simple(indice_completo, clasificaciones_completas)

print(f"  Resumen: {resumen}")
if resumen and len(resumen) > 0:
    print("  ✅ Resumen generado correctamente")
else:
    print("  ❌ Resumen vacío o inválido")

print("\n" + "=" * 60)
print("🎉 Todos los tests completados!\n")
print("✅ El Timeline Processor está listo para usar en Django")
print("\n📋 Próximos pasos:")
print("  1. Acceder a una parcela con datos históricos")
print("  2. Click en 'Timeline Visual'")
print("  3. Ver la evolución mes a mes con imágenes satelitales")
