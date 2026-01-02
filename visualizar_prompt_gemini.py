#!/usr/bin/env python
"""
Script para VISUALIZAR el prompt generado sin consumir cuota de Gemini.
Solo muestra cómo se ve el prompt enriquecido que se enviará a Gemini.
"""

import os
import sys
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.gemini_service import GeminiService


def visualizar_prompt_ejemplo():
    """Genera y muestra el prompt sin llamar a Gemini"""
    print("\n" + "="*100)
    print("🔍 VISUALIZACIÓN DEL NUEVO PROMPT ENRIQUECIDO PARA GEMINI")
    print("="*100 + "\n")
    
    # Buscar una parcela con datos
    parcela = Parcela.objects.filter(tipo_cultivo__isnull=False).exclude(tipo_cultivo='').first()
    
    if not parcela:
        print("⚠️  No hay parcelas con cultivo. Mostrando ejemplo genérico...")
        parcela_data = {
            'nombre': 'Parcela Ejemplo',
            'tipo_cultivo': 'Maíz',
            'area_hectareas': 50.0,
            'propietario': 'Juan Pérez',
            'ubicacion': 'Valle del Cauca, Colombia'
        }
        indices_data = [
            {
                'periodo': '01/2025', 'mes': 1, 'año': 2025,
                'ndvi_promedio': 0.65, 'ndvi_minimo': 0.55, 'ndvi_maximo': 0.75,
                'ndmi_promedio': 0.35, 'ndmi_minimo': 0.25, 'ndmi_maximo': 0.45,
                'savi_promedio': 0.60, 'savi_minimo': 0.50, 'savi_maximo': 0.70,
                'temperatura_promedio': 24.5, 'precipitacion_total': 120.0,
                'nubosidad_promedio': 25.0, 'calidad_datos': 'Buena'
            },
            {
                'periodo': '02/2025', 'mes': 2, 'año': 2025,
                'ndvi_promedio': 0.67, 'ndvi_minimo': 0.57, 'ndvi_maximo': 0.77,
                'ndmi_promedio': 0.33, 'ndmi_minimo': 0.23, 'ndmi_maximo': 0.43,
                'savi_promedio': 0.62, 'savi_minimo': 0.52, 'savi_maximo': 0.72,
                'temperatura_promedio': 25.2, 'precipitacion_total': 85.5,
                'nubosidad_promedio': 30.0, 'calidad_datos': 'Buena'
            },
            {
                'periodo': '03/2025', 'mes': 3, 'año': 2025,
                'ndvi_promedio': 0.71, 'ndvi_minimo': 0.61, 'ndvi_maximo': 0.81,
                'ndmi_promedio': 0.30, 'ndmi_minimo': 0.20, 'ndmi_maximo': 0.40,
                'savi_promedio': 0.66, 'savi_minimo': 0.56, 'savi_maximo': 0.76,
                'temperatura_promedio': 26.8, 'precipitacion_total': 55.2,
                'nubosidad_promedio': 35.0, 'calidad_datos': 'Regular'
            }
        ]
    else:
        # Usar datos reales
        print(f"✅ Usando datos reales de: {parcela.nombre}")
        parcela_data = {
            'nombre': parcela.nombre,
            'tipo_cultivo': parcela.tipo_cultivo,
            'area_hectareas': parcela.area_hectareas,
            'propietario': str(parcela.propietario),
            'ubicacion': getattr(parcela, 'ubicacion', None) or 'No especificada'
        }
        
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:6]
        indices_data = []
        for idx in reversed(list(indices)):
            indices_data.append({
                'periodo': f"{idx.mes:02d}/{idx.año}",
                'mes': idx.mes,
                'año': idx.año,
                'ndvi_promedio': idx.ndvi_promedio,
                'ndvi_minimo': idx.ndvi_minimo,
                'ndvi_maximo': idx.ndvi_maximo,
                'ndmi_promedio': idx.ndmi_promedio,
                'savi_promedio': idx.savi_promedio,
                'temperatura_promedio': idx.temperatura_promedio,
                'precipitacion_total': idx.precipitacion_total,
                'nubosidad_promedio': idx.nubosidad_promedio,
                'calidad_datos': idx.calidad_datos
            })
    
    # Crear instancia del servicio (sin llamar a la API)
    gemini = GeminiService()
    
    # Generar el prompt (sin enviarlo a Gemini)
    prompt = gemini._construir_prompt(
        parcela_data=parcela_data,
        indices_mensuales=indices_data,
        tipo_analisis='completo'
    )
    
    # Mostrar el prompt
    print("\n" + "━"*100)
    print("📝 PROMPT QUE SE ENVIARÁ A GEMINI:")
    print("━"*100 + "\n")
    print(prompt)
    print("\n" + "━"*100)
    
    # Estadísticas del prompt
    num_caracteres = len(prompt)
    num_lineas = prompt.count('\n')
    num_tokens_aprox = num_caracteres // 4  # Aproximación: 1 token ≈ 4 caracteres
    
    print("\n📊 ESTADÍSTICAS DEL PROMPT:")
    print(f"  - Caracteres: {num_caracteres:,}")
    print(f"  - Líneas: {num_lineas}")
    print(f"  - Tokens aproximados: {num_tokens_aprox:,} (~{num_tokens_aprox/1000:.1f}K)")
    print(f"  - Meses de datos: {len(indices_data)}")
    
    # Validación
    print("\n✅ VALIDACIÓN DEL PROMPT:")
    validaciones = {
        "Menciona 'agrónomo experto'": "agrónomo experto" in prompt.lower(),
        "Incluye tabla de datos": "|" in prompt and "NDVI" in prompt,
        "Solicita tendencias": "tendencias" in prompt.lower(),
        "Solicita alertas": "alertas" in prompt.lower() or "alerta" in prompt.lower(),
        "Solicita recomendaciones": "recomendaciones" in prompt.lower(),
        "Incluye contexto de cultivo": parcela_data['tipo_cultivo'] in prompt or "cultivo" in prompt.lower(),
        "Incluye estadísticas": "Promedio" in prompt or "promedio" in prompt.lower(),
        "Formato estructurado": "###" in prompt or "**" in prompt
    }
    
    for validacion, resultado in validaciones.items():
        icono = "✅" if resultado else "❌"
        print(f"  {icono} {validacion}")
    
    # Resumen
    aprobadas = sum(validaciones.values())
    total = len(validaciones)
    porcentaje = (aprobadas / total) * 100
    
    print(f"\n📈 CALIDAD DEL PROMPT: {aprobadas}/{total} validaciones aprobadas ({porcentaje:.0f}%)")
    
    if porcentaje >= 80:
        print("🎉 ¡EXCELENTE! El prompt está bien estructurado y completo.")
    elif porcentaje >= 60:
        print("⚠️  BUENO, pero hay margen de mejora.")
    else:
        print("❌ NECESITA MEJORAS. Revisar implementación.")
    
    print("\n" + "="*100)
    print("✅ VISUALIZACIÓN COMPLETADA - NO SE CONSUMIÓ CUOTA DE GEMINI")
    print("="*100 + "\n")


if __name__ == '__main__':
    visualizar_prompt_ejemplo()
