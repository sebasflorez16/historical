"""
Script para probar la generación de PDF con análisis de Gemini AI
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional


def test_generar_pdf_con_gemini():
    """Genera un PDF de prueba con análisis de Gemini AI"""
    print("\n" + "="*80)
    print("🚀 PRUEBA DE GENERACIÓN DE PDF CON GEMINI AI")
    print("="*80)
    
    try:
        # Buscar una parcela con datos
        parcela = Parcela.objects.filter(activa=True).first()
        
        if not parcela:
            print("❌ No hay parcelas activas en la base de datos")
            return False
        
        print(f"\n📍 Parcela seleccionada: {parcela.nombre}")
        print(f"   ID: {parcela.id}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        print(f"   Propietario: {parcela.propietario}")
        
        # Crear generador de PDF
        generador = GeneradorPDFProfesional()
        
        print("\n📄 Generando informe PDF con análisis de Gemini AI...")
        print("   (Esto puede tomar 15-30 segundos)")
        
        # Generar informe
        output_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=6  # Últimos 6 meses
        )
        
        print(f"\n✅ ¡PDF generado exitosamente!")
        print(f"📁 Ubicación: {output_path}")
        print(f"📊 Tamaño: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        # Abrir el PDF automáticamente (solo en macOS)
        if sys.platform == 'darwin':
            print("\n🔍 Abriendo PDF...")
            os.system(f'open "{output_path}"')
        
        print("\n" + "="*80)
        print("🎉 ¡Prueba completada exitosamente!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_generar_pdf_con_gemini()
