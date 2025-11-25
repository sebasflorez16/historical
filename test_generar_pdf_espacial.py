"""
Script para generar un PDF de prueba con análisis espacial
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional


def generar_pdf_prueba():
    """
    Generar un PDF de prueba con análisis espacial
    """
    print("=" * 80)
    print("📄 GENERACIÓN DE PDF CON ANÁLISIS ESPACIAL")
    print("=" * 80)
    
    # Buscar una parcela con datos
    parcela = Parcela.objects.filter(
        eosda_sincronizada=True,
        indices_mensuales__isnull=False
    ).first()
    
    if not parcela:
        print("❌ No se encontró ninguna parcela con datos para probar")
        return
    
    print(f"\n✅ Parcela seleccionada: {parcela.nombre}")
    print(f"   - ID EOSDA: {parcela.eosda_field_id}")
    print(f"   - Área: {parcela.area_hectareas:.2f} ha")
    
    # Crear generador
    generador = GeneradorPDFProfesional()
    
    # Generar PDF
    print("\n🔧 Generando PDF...")
    try:
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=6
        )
        
        print(f"\n✅ PDF generado exitosamente!")
        print(f"📁 Ubicación: {pdf_path}")
        
        # Verificar tamaño
        if os.path.exists(pdf_path):
            size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"📊 Tamaño: {size_mb:.2f} MB")
        
        print("\n" + "=" * 80)
        print("✅ PRUEBA COMPLETADA")
        print("=" * 80)
        print("\nAbre el PDF para verificar:")
        print("1. ✅ Sección 'Resumen Ejecutivo' con contexto espacial")
        print("2. ✅ Sección 'Análisis Inteligente con Gemini AI'")
        print("3. ✅ Subsección '🛰️ Análisis Visual de Imágenes Satelitales' (si hay imágenes)")
        print("4. ✅ Referencias a 'zona norte', 'zona sur', etc. en el texto")
        print("5. ✅ Recomendaciones espacialmente específicas")
        
        print(f"\n💡 Para abrir el PDF:")
        print(f"   open '{pdf_path}'")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    generar_pdf_prueba()
