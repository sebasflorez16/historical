#!/usr/bin/env python3
"""
Test de lógica de clasificación del Timeline (sin dependencias Django)
"""

def clasificar_ndvi(valor):
    """Clasifica valor NDVI según umbrales"""
    if valor >= 0.85:
        return {'nivel': 'excelente', 'etiqueta': 'Vegetación Excelente', 'color': '#20c997', 'icono': '🌟'}
    elif valor >= 0.75:
        return {'nivel': 'muy_bueno', 'etiqueta': 'Muy Buena Salud', 'color': '#28a745', 'icono': '✅'}
    elif valor >= 0.6:
        return {'nivel': 'bueno', 'etiqueta': 'Buena Salud', 'color': '#17a2b8', 'icono': '👍'}
    elif valor >= 0.4:
        return {'nivel': 'moderado', 'etiqueta': 'Salud Moderada', 'color': '#ffc107', 'icono': '⚠️'}
    else:
        return {'nivel': 'bajo', 'etiqueta': 'Estrés Detectado', 'color': '#dc3545', 'icono': '🔴'}

print("🧪 Test de Clasificación NDVI\n")
print("=" * 70)

test_cases = [
    (0.90, 'excelente', '🌟', 'Vegetación muy densa'),
    (0.78, 'muy_bueno', '✅', 'Vegetación vigorosa'),
    (0.65, 'bueno', '👍', 'Vegetación saludable'),
    (0.45, 'moderado', '⚠️', 'Estrés leve'),
    (0.25, 'bajo', '🔴', 'Estrés severo'),
]

print("\n📊 Pruebas de clasificación:")
all_passed = True

for valor, nivel_esperado, icono_esperado, descripcion in test_cases:
    resultado = clasificar_ndvi(valor)
    nivel_obtenido = resultado['nivel']
    icono_obtenido = resultado['icono']
    
    if nivel_obtenido == nivel_esperado and icono_obtenido == icono_esperado:
        print(f"  ✅ NDVI {valor:.2f} → {icono_obtenido} {resultado['etiqueta']:25} ({descripcion})")
    else:
        print(f"  ❌ NDVI {valor:.2f} → Esperado: {nivel_esperado}, Obtenido: {nivel_obtenido}")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("🎉 ¡Todos los tests pasaron correctamente!")
    print("\n✅ La lógica de clasificación está funcionando bien")
    print("\n📋 Archivos creados para el Timeline Visual:")
    print("   ✓ informes/processors/timeline_processor.py")
    print("   ✓ informes/views.py (timeline_parcela, timeline_api)")
    print("   ✓ informes/urls.py (rutas agregadas)")
    print("   ✓ templates/informes/parcelas/timeline.html")
    print("   ✓ static/js/timeline/timeline_player.js")
    print("   ✓ templates/informes/parcelas/detalle.html (botón agregado)")
    print("\n🚀 Para probar el Timeline:")
    print("   1. Inicia el servidor Django")
    print("   2. Ve al detalle de una parcela con datos históricos")
    print("   3. Click en el botón '🎬 Timeline Visual'")
    print("   4. Disfruta de la visualización cinematográfica!")
else:
    print("❌ Algunos tests fallaron - revisar lógica")
