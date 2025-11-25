"""
Script de prueba para el servicio de Gemini AI
Prueba la conexión y la generación de análisis con datos reales
"""

import os
import sys
import django
from pathlib import Path

# Cargar variables de entorno desde .env
from dotenv import load_dotenv

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar .env antes de configurar Django
base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / '.env'
load_dotenv(dotenv_path=env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.services.gemini_service import gemini_service
from informes.models import Parcela, IndiceMensual
from datetime import datetime, timedelta


def test_conexion():
    """Prueba 1: Verificar conexión con Gemini API"""
    print("\n" + "="*60)
    print("PRUEBA 1: Conexión con Gemini API")
    print("="*60)
    
    if not gemini_service:
        print("❌ ERROR: GeminiService no se pudo instanciar")
        return False
    
    resultado = gemini_service.probar_conexion()
    
    if resultado['exito']:
        print(f"✅ {resultado['mensaje']}")
        print(f"📝 Respuesta: {resultado['respuesta']}")
        return True
    else:
        print(f"❌ Error: {resultado['error']}")
        return False


def test_analisis_basico():
    """Prueba 2: Generar análisis con datos simulados"""
    print("\n" + "="*60)
    print("PRUEBA 2: Análisis con datos simulados")
    print("="*60)
    
    # Datos simulados de prueba
    parcela_data = {
        'nombre': 'Parcela de Prueba - Lote 1',
        'area_hectareas': 15.5,
        'tipo_cultivo': 'Maíz',
        'propietario': 'Juan Pérez'
    }
    
    indices_mensuales = [
        {
            'periodo': 'Enero 2025',
            'ndvi_promedio': 0.65,
            'ndmi_promedio': 0.45,
            'savi_promedio': 0.55,
            'nubosidad_promedio': 15.0,
            'temperatura_promedio': 28.5,
            'precipitacion_total': 120.0,
            'calidad_datos': 'buena'
        },
        {
            'periodo': 'Febrero 2025',
            'ndvi_promedio': 0.58,
            'ndmi_promedio': 0.38,
            'savi_promedio': 0.48,
            'nubosidad_promedio': 25.0,
            'temperatura_promedio': 30.2,
            'precipitacion_total': 45.0,
            'calidad_datos': 'regular'
        },
        {
            'periodo': 'Marzo 2025',
            'ndvi_promedio': 0.72,
            'ndmi_promedio': 0.52,
            'savi_promedio': 0.62,
            'nubosidad_promedio': 10.0,
            'temperatura_promedio': 27.8,
            'precipitacion_total': 180.0,
            'calidad_datos': 'buena'
        }
    ]
    
    try:
        resultado = gemini_service.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_mensuales,
            tipo_analisis='completo'
        )
        
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
            return False
        
        print("\n📊 ANÁLISIS GENERADO:\n")
        print("-" * 60)
        print("RESUMEN EJECUTIVO:")
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        print("\n" + "-" * 60)
        print("ANÁLISIS DE TENDENCIAS:")
        print(resultado.get('analisis_tendencias', 'N/A'))
        print("\n" + "-" * 60)
        print("RECOMENDACIONES:")
        print(resultado.get('recomendaciones', 'N/A'))
        print("\n" + "-" * 60)
        print("ALERTAS:")
        print(resultado.get('alertas', 'N/A'))
        print("-" * 60)
        
        print("\n✅ Análisis generado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error generando análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analisis_con_datos_reales():
    """Prueba 3: Generar análisis con datos reales de una parcela"""
    print("\n" + "="*60)
    print("PRUEBA 3: Análisis con datos reales de una parcela")
    print("="*60)
    
    # Buscar una parcela con datos
    parcela = Parcela.objects.filter(activa=True).first()
    
    if not parcela:
        print("⚠️ No hay parcelas activas en la base de datos")
        return False
    
    print(f"📍 Usando parcela: {parcela.nombre} (ID: {parcela.id})")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
    
    # Obtener índices mensuales
    indices = IndiceMensual.objects.filter(
        parcela=parcela
    ).order_by('-año', '-mes')[:6]  # Últimos 6 meses
    
    if not indices:
        print("⚠️ No hay datos mensuales para esta parcela")
        return False
    
    print(f"📊 Encontrados {indices.count()} meses de datos")
    
    # Preparar datos
    parcela_data = {
        'nombre': parcela.nombre,
        'area_hectareas': parcela.area_hectareas or 0,
        'tipo_cultivo': parcela.tipo_cultivo or 'No especificado',
        'propietario': parcela.propietario
    }
    
    indices_mensuales = []
    for indice in indices:
        indices_mensuales.append({
            'periodo': indice.periodo_texto,
            'ndvi_promedio': indice.ndvi_promedio,
            'ndmi_promedio': indice.ndmi_promedio,
            'savi_promedio': indice.savi_promedio,
            'nubosidad_promedio': indice.nubosidad_promedio,
            'temperatura_promedio': indice.temperatura_promedio,
            'precipitacion_total': indice.precipitacion_total,
            'calidad_datos': indice.calidad_datos,
            'tiene_imagen_ndvi': bool(indice.imagen_ndvi),
            'tiene_imagen_ndmi': bool(indice.imagen_ndmi),
            'tiene_imagen_savi': bool(indice.imagen_savi),
            'nubosidad_imagen': indice.nubosidad_imagen or 0
        })
    
    try:
        print("\n🤖 Generando análisis con Gemini...")
        resultado = gemini_service.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_mensuales,
            tipo_analisis='completo'
        )
        
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
            return False
        
        print("\n📊 ANÁLISIS GENERADO PARA DATOS REALES:\n")
        print("=" * 60)
        print("RESUMEN EJECUTIVO:")
        print("=" * 60)
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        print("\n" + "=" * 60)
        print("ANÁLISIS DE TENDENCIAS:")
        print("=" * 60)
        print(resultado.get('analisis_tendencias', 'N/A'))
        print("\n" + "=" * 60)
        print("RECOMENDACIONES:")
        print("=" * 60)
        print(resultado.get('recomendaciones', 'N/A'))
        print("\n" + "=" * 60)
        print("ALERTAS:")
        print("=" * 60)
        print(resultado.get('alertas', 'N/A'))
        print("=" * 60)
        
        print("\n✅ Análisis con datos reales generado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error generando análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "🤖 "*30)
    print("PRUEBAS DE INTEGRACIÓN CON GEMINI AI")
    print("🤖 "*30)
    
    resultados = {
        'Conexión API': test_conexion(),
        'Análisis Simulado': test_analisis_basico(),
        'Análisis Datos Reales': test_analisis_con_datos_reales()
    }
    
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    for nombre, exito in resultados.items():
        estado = "✅ EXITOSA" if exito else "❌ FALLIDA"
        print(f"{nombre}: {estado}")
    
    total_exitosas = sum(resultados.values())
    print(f"\nTotal: {total_exitosas}/{len(resultados)} pruebas exitosas")
    print("="*60)


if __name__ == '__main__':
    main()
