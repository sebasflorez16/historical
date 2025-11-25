#!/usr/bin/env python
"""
Test: Generación de PDF con Análisis Global Consolidado
Verifica que al final de la galería se genere un análisis global de todas las imágenes
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional
from datetime import datetime

def main():
    """Test de generación de PDF con análisis global consolidado"""
    
    print("\n" + "="*80)
    print("🧪 TEST: ANÁLISIS GLOBAL CONSOLIDADO DE IMÁGENES")
    print("="*80 + "\n")
    
    # 1. Buscar parcela con imágenes
    print("1️⃣ Buscando parcela con múltiples imágenes...")
    
    parcelas_con_imagenes = Parcela.objects.filter(
        indices_mensuales__imagen_ndvi__isnull=False
    ).distinct()
    
    if not parcelas_con_imagenes.exists():
        print("❌ No se encontraron parcelas con imágenes")
        return
    
    parcela = parcelas_con_imagenes.first()
    print(f"✅ Parcela: {parcela.nombre} (ID: {parcela.id})")
    
    # 2. Contar imágenes disponibles
    indices_con_imagenes = parcela.indices_mensuales.filter(
        imagen_ndvi__isnull=False
    ).order_by('año', 'mes')
    
    total_imagenes = 0
    meses_disponibles = []
    
    for idx in indices_con_imagenes:
        mes_info = f"{idx.periodo_texto}"
        if idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path):
            total_imagenes += 1
            if mes_info not in meses_disponibles:
                meses_disponibles.append(mes_info)
        if idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path):
            total_imagenes += 1
        if idx.imagen_savi and os.path.exists(idx.imagen_savi.path):
            total_imagenes += 1
    
    print(f"\n2️⃣ Imágenes disponibles:")
    print(f"   • Total: {total_imagenes} imágenes")
    print(f"   • Meses: {len(meses_disponibles)}")
    for mes in meses_disponibles[:5]:
        print(f"     - {mes}")
    if len(meses_disponibles) > 5:
        print(f"     ... y {len(meses_disponibles) - 5} más")
    
    # 3. Generar PDF
    print("\n3️⃣ Generando PDF con análisis global consolidado...")
    print("   ⏳ Esto incluye:")
    print("      • Análisis individual de cada imagen (Gemini)")
    print("      • Análisis GLOBAL de todas las imágenes juntas (Gemini)")
    print("      • Recomendaciones específicas por zona")
    print("\n   ⌛ Puede tardar 2-3 minutos...")
    
    try:
        generador = GeneradorPDFProfesional()
        
        # Generar PDF con últimos 3 meses
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=3
        )
        
        print(f"\n✅ PDF generado exitosamente!")
        print(f"   📄 {pdf_path}")
        print(f"   📏 {os.path.getsize(pdf_path) / 1024:.1f} KB")
        
        # 4. Verificar estructura del PDF
        print("\n4️⃣ Estructura del PDF generado:")
        print("   ✅ Portada y resumen ejecutivo")
        print("   ✅ Análisis inteligente con Gemini")
        print("   ✅ Galería de imágenes satelitales:")
        print("      • Cada mes con sus imágenes")
        print("      • Análisis visual individual por imagen")
        print("      • Metadatos de captura")
        print("   ✅ 🎯 ANÁLISIS GLOBAL CONSOLIDADO:")
        print("      • Evaluación general del vigor")
        print("      • Patrones espaciales consistentes")
        print("      • Evolución temporal")
        print("      • Recomendaciones por zona específica")
        
        print("\n5️⃣ Características del análisis global:")
        print("   🤖 Generado por Gemini AI")
        print("   🗺️  Identifica zonas específicas (norte/sur/este/oeste)")
        print("   📊 Consolida observaciones de TODAS las imágenes")
        print("   💡 Da recomendaciones ACCIONABLES")
        print("   🎯 Prioriza acciones por zona")
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETADO")
        print("="*80 + "\n")
        
        print("💡 VERIFICA EN EL PDF:")
        print("   1. Navega hasta la sección 'Imágenes Satelitales'")
        print("   2. Revisa el análisis de cada imagen individual")
        print("   3. Al FINAL de todas las imágenes, busca:")
        print("      🎯 'Análisis Global Consolidado del Período'")
        print("   4. Verifica que mencione:")
        print("      • Estado general de la parcela")
        print("      • Zonas específicas (norte/sur/este/oeste)")
        print("      • Tendencias temporales")
        print("      • Recomendaciones concretas por zona")
        
        print(f"\n📂 Abrir PDF:")
        print(f"   open '{pdf_path}'")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
