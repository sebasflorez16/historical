"""
Script de prueba para la integración de Gemini AI con AgroTech Histórico
Verifica que el servicio funcione correctamente con datos reales
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.gemini_service import GeminiService


def test_conexion_gemini():
    """Prueba 1: Verificar conexión con API de Gemini"""
    print("\n" + "="*80)
    print("🧪 PRUEBA 1: Conexión con Gemini API")
    print("="*80)
    
    try:
        servicio = GeminiService()
        resultado = servicio.probar_conexion()
        
        if resultado['exito']:
            print("✅ Conexión exitosa con Gemini API")
            print(f"📝 Respuesta: {resultado['respuesta']}")
            return True
        else:
            print(f"❌ Error en conexión: {resultado['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error inicializando servicio: {str(e)}")
        return False


def test_analisis_simple():
    """Prueba 2: Análisis simple sin imágenes"""
    print("\n" + "="*80)
    print("🧪 PRUEBA 2: Análisis simple (sin imágenes)")
    print("="*80)
    
    try:
        servicio = GeminiService()
        
        # Datos de prueba simulados
        parcela_data = {
            'nombre': 'Parcela de Prueba',
            'area_hectareas': 10.5,
            'tipo_cultivo': 'Café',
            'propietario': 'Test User'
        }
        
        indices_mensuales = [
            {
                'periodo': '2024-12',
                'ndvi_promedio': 0.75,
                'ndmi_promedio': 0.42,
                'savi_promedio': 0.68,
                'nubosidad_promedio': 25.5,
                'temperatura_promedio': 22.3,
                'precipitacion_total': 145.2,
                'calidad_datos': 'BUENA'
            },
            {
                'periodo': '2025-01',
                'ndvi_promedio': 0.71,
                'ndmi_promedio': 0.38,
                'savi_promedio': 0.65,
                'nubosidad_promedio': 18.2,
                'temperatura_promedio': 23.1,
                'precipitacion_total': 98.7,
                'calidad_datos': 'BUENA'
            }
        ]
        
        print(f"📊 Analizando parcela: {parcela_data['nombre']}")
        print(f"📅 Datos de {len(indices_mensuales)} meses")
        
        resultado = servicio.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_mensuales,
            tipo_analisis='completo'
        )
        
        if 'error' in resultado:
            print(f"❌ Error en análisis: {resultado['error']}")
            return False
        
        print("\n✅ Análisis generado exitosamente!\n")
        print("-" * 80)
        print("📋 RESUMEN EJECUTIVO:")
        print("-" * 80)
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        
        print("\n" + "-" * 80)
        print("📈 ANÁLISIS DE TENDENCIAS:")
        print("-" * 80)
        print(resultado.get('analisis_tendencias', 'N/A'))
        
        print("\n" + "-" * 80)
        print("💡 RECOMENDACIONES:")
        print("-" * 80)
        print(resultado.get('recomendaciones', 'N/A'))
        
        print("\n" + "-" * 80)
        print("⚠️ ALERTAS:")
        print("-" * 80)
        print(resultado.get('alertas', 'N/A'))
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analisis_con_datos_reales():
    """Prueba 3: Análisis con datos reales de la BD"""
    print("\n" + "="*80)
    print("🧪 PRUEBA 3: Análisis con datos reales de la base de datos")
    print("="*80)
    
    try:
        # Buscar una parcela con datos
        parcela = Parcela.objects.filter(activa=True).first()
        
        if not parcela:
            print("⚠️ No hay parcelas activas en la base de datos")
            return False
        
        print(f"📍 Parcela seleccionada: {parcela.nombre}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        print(f"   Propietario: {parcela.propietario}")
        
        # Obtener índices mensuales
        indices = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('-año', '-mes')[:6]  # Últimos 6 meses
        
        if not indices.exists():
            print(f"⚠️ No hay índices mensuales para la parcela {parcela.nombre}")
            return False
        
        print(f"📊 Se encontraron {indices.count()} meses de datos")
        
        # Preparar datos
        parcela_data = {
            'nombre': parcela.nombre,
            'area_hectareas': float(parcela.area_hectareas) if parcela.area_hectareas else 0,
            'tipo_cultivo': parcela.tipo_cultivo or 'No especificado',
            'propietario': parcela.propietario if isinstance(parcela.propietario, str) else (parcela.propietario.username if parcela.propietario else 'No especificado')
        }
        
        indices_data = []
        for idx in indices:
            indices_data.append({
                'periodo': f"{idx.año}-{idx.mes:02d}",
                'ndvi_promedio': float(idx.ndvi_promedio) if idx.ndvi_promedio else None,
                'ndmi_promedio': float(idx.ndmi_promedio) if idx.ndmi_promedio else None,
                'savi_promedio': float(idx.savi_promedio) if idx.savi_promedio else None,
                'nubosidad_promedio': float(idx.nubosidad_promedio) if idx.nubosidad_promedio else None,
                'temperatura_promedio': float(idx.temperatura_promedio) if idx.temperatura_promedio else None,
                'precipitacion_total': float(idx.precipitacion_total) if idx.precipitacion_total else None,
                'calidad_datos': idx.calidad_datos or 'N/A'
            })
        
        # Generar análisis
        servicio = GeminiService()
        
        print("\n🤖 Generando análisis con Gemini AI...")
        resultado = servicio.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_data,
            tipo_analisis='completo'
        )
        
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
            return False
        
        # Mostrar resultados
        print("\n" + "="*80)
        print("✅ ANÁLISIS GENERADO CON ÉXITO")
        print("="*80)
        
        print("\n📋 RESUMEN EJECUTIVO:")
        print("-" * 80)
        print(resultado.get('resumen_ejecutivo', 'N/A'))
        
        print("\n📈 ANÁLISIS DE TENDENCIAS:")
        print("-" * 80)
        print(resultado.get('analisis_tendencias', 'N/A'))
        
        print("\n💡 RECOMENDACIONES:")
        print("-" * 80)
        print(resultado.get('recomendaciones', 'N/A'))
        
        print("\n⚠️ ALERTAS:")
        print("-" * 80)
        print(resultado.get('alertas', 'N/A'))
        
        # Guardar resultado en archivo
        output_file = f"analisis_gemini_{parcela.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"ANÁLISIS GENERADO POR GEMINI AI\n")
            f.write(f"Parcela: {parcela_data['nombre']}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n{'='*80}\n\n")
            f.write(f"RESUMEN EJECUTIVO:\n{resultado.get('resumen_ejecutivo', 'N/A')}\n\n")
            f.write(f"ANÁLISIS DE TENDENCIAS:\n{resultado.get('analisis_tendencias', 'N/A')}\n\n")
            f.write(f"RECOMENDACIONES:\n{resultado.get('recomendaciones', 'N/A')}\n\n")
            f.write(f"ALERTAS:\n{resultado.get('alertas', 'N/A')}\n")
        
        print(f"\n💾 Resultado guardado en: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*80)
    print("🚀 PRUEBAS DE INTEGRACIÓN DE GEMINI AI")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    resultados = []
    
    # Prueba 1: Conexión
    resultados.append(("Conexión API", test_conexion_gemini()))
    
    # Prueba 2: Análisis simple
    resultados.append(("Análisis simple", test_analisis_simple()))
    
    # Prueba 3: Datos reales
    resultados.append(("Análisis con datos reales", test_analisis_con_datos_reales()))
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*80)
    
    for nombre, exito in resultados:
        status = "✅ PASS" if exito else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    total = len(resultados)
    exitosas = sum(1 for _, exito in resultados if exito)
    
    print(f"\n🎯 Resultado final: {exitosas}/{total} pruebas exitosas")
    
    if exitosas == total:
        print("\n🎉 ¡Todas las pruebas pasaron correctamente!")
        print("💚 La integración de Gemini AI está lista para usar")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")


if __name__ == '__main__':
    main()
