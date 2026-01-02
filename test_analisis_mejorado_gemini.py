#!/usr/bin/env python
"""
Script de prueba para validar el nuevo prompt enriquecido de Gemini.
Genera un análisis con serie temporal completa, contexto agronómico y recomendaciones.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.gemini_service import GeminiService


def test_analisis_con_cultivo():
    """Prueba de análisis con cultivo activo (maíz)"""
    print("\n" + "="*80)
    print("🌽 TEST 1: ANÁLISIS CON CULTIVO ACTIVO (MAÍZ)")
    print("="*80 + "\n")
    
    # Buscar una parcela con cultivo
    parcela = Parcela.objects.filter(tipo_cultivo__isnull=False).exclude(tipo_cultivo='').first()
    
    if not parcela:
        print("⚠️  No se encontraron parcelas con cultivo activo. Creando datos de prueba...")
        # Crear parcela de prueba si no existe
        from django.contrib.auth.models import User
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('test_user', 'test@test.com', 'password')
        
        parcela = Parcela.objects.create(
            nombre="Parcela Test Maíz",
            tipo_cultivo="Maíz",
            area_hectareas=5.5,
            propietario=user,
            ubicacion="Valle del Cauca, Colombia"
        )
        print(f"✅ Parcela de prueba creada: {parcela.nombre}")
    
    print(f"📍 Parcela: {parcela.nombre}")
    print(f"🌾 Cultivo: {parcela.tipo_cultivo}")
    print(f"📏 Área: {parcela.area_hectareas} ha")
    ubicacion = getattr(parcela, 'ubicacion', None) or 'No especificada'
    print(f"📍 Ubicación: {ubicacion}")
    
    # Obtener índices mensuales
    indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:12]
    
    if indices.count() == 0:
        print("⚠️  No hay datos de índices mensuales. Creando datos de prueba...")
        # Crear datos mensuales de prueba
        for i in range(12):
            fecha = datetime.now() - timedelta(days=30*i)
            IndiceMensual.objects.create(
                parcela=parcela,
                mes=fecha.month,
                año=fecha.year,
                ndvi_promedio=0.65 + (i * 0.02),  # Tendencia creciente
                ndvi_minimo=0.55 + (i * 0.02),
                ndvi_maximo=0.75 + (i * 0.02),
                ndmi_promedio=0.35 - (i * 0.01),  # Tendencia decreciente (estrés hídrico)
                savi_promedio=0.60 + (i * 0.015),
                temperatura_promedio=24 + (i % 3),
                precipitacion_total=50 + (i * 10),
                nubosidad_promedio=30 - (i * 2),
                calidad_datos='Buena'
            )
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:12]
        print(f"✅ {indices.count()} meses de datos creados")
    
    print(f"📊 Datos disponibles: {indices.count()} meses\n")
    
    # Preparar datos para Gemini
    parcela_data = {
        'nombre': parcela.nombre,
        'tipo_cultivo': parcela.tipo_cultivo,
        'area_hectareas': parcela.area_hectareas,
        'propietario': str(parcela.propietario),
        'ubicacion': getattr(parcela, 'ubicacion', None) or 'No especificada'
    }
    
    indices_data = []
    for idx in reversed(list(indices)):  # Orden cronológico
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
    
    # Generar análisis con Gemini
    print("🤖 Generando análisis con Gemini AI (nuevo prompt enriquecido)...")
    print("-" * 80)
    
    try:
        gemini = GeminiService()
        resultado = gemini.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_data,
            tipo_analisis='completo'
        )
        
        print("\n✅ ANÁLISIS GENERADO:\n")
        print("📝 RESUMEN EJECUTIVO:")
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        print("\n" + "="*80)
        print("📈 ANÁLISIS DE TENDENCIAS:")
        print(resultado.get('analisis_tendencias', 'N/A'))
        print("\n" + "="*80)
        print("⚠️  ALERTAS:")
        print(resultado.get('alertas', 'N/A'))
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES:")
        print(resultado.get('recomendaciones', 'N/A'))
        
        if 'error' in resultado:
            print(f"\n❌ Error: {resultado['error']}")
        
    except Exception as e:
        print(f"❌ Error al generar análisis: {str(e)}")
        import traceback
        traceback.print_exc()


def test_analisis_sin_cultivo():
    """Prueba de análisis sin cultivo (terreno para planificación)"""
    print("\n\n" + "="*80)
    print("🌱 TEST 2: ANÁLISIS SIN CULTIVO (TERRENO PARA PLANIFICACIÓN)")
    print("="*80 + "\n")
    
    # Buscar una parcela sin cultivo
    parcela = Parcela.objects.filter(tipo_cultivo__isnull=True).first() or \
              Parcela.objects.filter(tipo_cultivo='').first()
    
    if not parcela:
        print("⚠️  No se encontraron parcelas sin cultivo. Creando datos de prueba...")
        from django.contrib.auth.models import User
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('test_user', 'test@test.com', 'password')
        
        # Crear parcela sin cultivo (sin campo ubicacion que no existe en el modelo)
        from datetime import date
        parcela = Parcela.objects.create(
            nombre="Terreno Sin Sembrar",
            tipo_cultivo="",  # Sin cultivo
            propietario="Usuario Test",
            fecha_inicio_monitoreo=date.today()
        )
        print(f"✅ Parcela de prueba creada: {parcela.nombre}")
    
    print(f"📍 Parcela: {parcela.nombre}")
    print(f"🌾 Estado: Sin cultivo activo")
    print(f"📏 Área: {parcela.area_hectareas} ha")
    ubicacion = getattr(parcela, 'ubicacion', None) or 'No especificada'
    print(f"📍 Ubicación: {ubicacion}")
    
    # Obtener o crear índices mensuales
    indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:12]
    
    if indices.count() == 0:
        print("⚠️  No hay datos de índices mensuales. Creando datos de prueba...")
        for i in range(6):
            fecha = datetime.now() - timedelta(days=30*i)
            IndiceMensual.objects.create(
                parcela=parcela,
                mes=fecha.month,
                año=fecha.year,
                ndvi_promedio=0.25 + (i * 0.03),  # Vegetación natural baja
                ndvi_minimo=0.15 + (i * 0.02),
                ndvi_maximo=0.35 + (i * 0.04),
                ndmi_promedio=0.20 + (i * 0.02),
                savi_promedio=0.22 + (i * 0.025),
                temperatura_promedio=26 + (i % 2),
                precipitacion_total=80 + (i * 5),
                nubosidad_promedio=40 - (i * 3),
                calidad_datos='Buena'
            )
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:12]
        print(f"✅ {indices.count()} meses de datos creados")
    
    print(f"📊 Datos disponibles: {indices.count()} meses\n")
    
    # Preparar datos para Gemini
    parcela_data = {
        'nombre': parcela.nombre,
        'tipo_cultivo': parcela.tipo_cultivo or '',
        'area_hectareas': parcela.area_hectareas,
        'propietario': str(parcela.propietario),
        'ubicacion': getattr(parcela, 'ubicacion', None) or 'No especificada'
    }
    
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
    
    # Generar análisis con Gemini
    print("🤖 Generando análisis con Gemini AI (prompt para planificación)...")
    print("-" * 80)
    
    try:
        gemini = GeminiService()
        resultado = gemini.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_data,
            tipo_analisis='completo'
        )
        
        print("\n✅ ANÁLISIS GENERADO:\n")
        print("📝 RESUMEN EJECUTIVO:")
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        print("\n" + "="*80)
        print("📊 ANÁLISIS DE CONDICIONES BASE:")
        print(resultado.get('analisis_tendencias', 'N/A'))
        print("\n" + "="*80)
        print("⚠️  ALERTAS Y CONSIDERACIONES:")
        print(resultado.get('alertas', 'N/A'))
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES:")
        print(resultado.get('recomendaciones', 'N/A'))
        
        if 'error' in resultado:
            print(f"\n❌ Error: {resultado['error']}")
        
    except Exception as e:
        print(f"❌ Error al generar análisis: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n🚀 INICIANDO PRUEBA DE ANÁLISIS MEJORADO CON GEMINI")
    print("="*80)
    print("Esta prueba validará:")
    print("  ✓ Prompt enriquecido con contexto agronómico")
    print("  ✓ Serie temporal completa (NDVI, NDMI, SAVI, clima)")
    print("  ✓ Detección de alertas y recomendaciones")
    print("  ✓ Análisis diferenciado para cultivo activo vs terreno sin sembrar")
    print("="*80)
    
    # Test 1: Con cultivo activo
    test_analisis_con_cultivo()
    
    # Test 2: Sin cultivo (planificación)
    test_analisis_sin_cultivo()
    
    print("\n" + "="*80)
    print("✅ PRUEBA COMPLETADA")
    print("="*80)
    print("\nRevisa los análisis generados arriba para validar la calidad del prompt.")
    print("El análisis debería incluir:")
    print("  - Interpretación de tendencias temporales")
    print("  - Alertas específicas (estrés hídrico, plagas, etc.)")
    print("  - Recomendaciones accionables para el agricultor")
    print("  - Lenguaje técnico pero comprensible")
    print("\n")
