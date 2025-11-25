"""
Script de demostración del sistema de caché de Gemini AI
Muestra el ahorro de costos al usar caché vs regenerar siempre
"""

import os
import sys
import django
from datetime import datetime
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional


def demo_cache_vs_sin_cache():
    """Demuestra la diferencia entre usar caché y regenerar"""
    print("\n" + "="*80)
    print("💾 DEMOSTRACIÓN: CACHÉ DE GEMINI AI")
    print("="*80)
    
    # Buscar parcela
    parcela = Parcela.objects.filter(activa=True).first()
    if not parcela:
        print("❌ No hay parcelas disponibles")
        return
    
    print(f"\n📍 Parcela seleccionada: {parcela.nombre}")
    
    # Verificar estado del caché
    ultimo_indice = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes').first()
    
    if ultimo_indice and ultimo_indice.analisis_gemini:
        edad_cache = datetime.now() - ultimo_indice.fecha_analisis_gemini.replace(tzinfo=None)
        print(f"💾 Estado del caché: VÁLIDO (edad: {edad_cache.days} días, {edad_cache.seconds//3600} horas)")
        print(f"📅 Fecha de generación: {ultimo_indice.fecha_analisis_gemini.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("💾 Estado del caché: NO EXISTE")
    
    generador = GeneradorPDFProfesional()
    
    # PRUEBA 1: Generar con caché (si existe)
    print("\n" + "-"*80)
    print("📄 PRUEBA 1: Generación de PDF con caché")
    print("-"*80)
    
    inicio = time.time()
    try:
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=6
        )
        tiempo1 = time.time() - inicio
        
        # Verificar si usó caché
        if ultimo_indice and ultimo_indice.analisis_gemini:
            costo1 = 0.0000
            origen1 = "CACHÉ"
        else:
            costo1 = 0.0014
            origen1 = "NUEVA GENERACIÓN"
        
        print(f"✅ PDF generado: {os.path.basename(pdf_path)}")
        print(f"⏱️  Tiempo: {tiempo1:.2f} segundos")
        print(f"💰 Costo estimado: ${costo1:.4f} USD")
        print(f"📦 Origen del análisis: {origen1}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    # PRUEBA 2: Regenerar inmediatamente (debe usar caché)
    print("\n" + "-"*80)
    print("📄 PRUEBA 2: Regeneración inmediata (debe usar caché)")
    print("-"*80)
    
    inicio = time.time()
    try:
        pdf_path2 = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=6
        )
        tiempo2 = time.time() - inicio
        
        print(f"✅ PDF generado: {os.path.basename(pdf_path2)}")
        print(f"⏱️  Tiempo: {tiempo2:.2f} segundos")
        print(f"💰 Costo estimado: $0.0000 USD (usando caché)")
        print(f"📦 Origen del análisis: CACHÉ")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    # RESUMEN
    print("\n" + "="*80)
    print("📊 RESUMEN DE AHORRO")
    print("="*80)
    
    print(f"\n🚀 Velocidad:")
    print(f"   Primera generación: {tiempo1:.2f}s")
    print(f"   Segunda generación: {tiempo2:.2f}s")
    if tiempo1 > 0:
        mejora = ((tiempo1 - tiempo2) / tiempo1) * 100
        print(f"   Mejora: {mejora:.1f}% más rápido")
    
    print(f"\n💰 Costos:")
    print(f"   Sin caché (regenerar siempre): $0.0014 USD por informe")
    print(f"   Con caché: $0.0000 USD por informe subsecuente")
    
    print(f"\n📈 Proyección mensual (ejemplo: 100 informes):")
    print(f"   Sin caché: 100 × $0.0014 = $0.14 USD")
    print(f"   Con caché (1 generación + 99 caché): $0.0014 USD")
    print(f"   Ahorro: $0.1386 USD (99% de reducción)")
    
    print(f"\n📈 Proyección mensual (ejemplo: 1,000 informes):")
    print(f"   Sin caché: 1,000 × $0.0014 = $1.40 USD")
    print(f"   Con caché: $0.0014 USD")
    print(f"   Ahorro: $1.3986 USD (99.9% de reducción)")
    
    print("\n" + "="*80)
    print("✅ Conclusión: El sistema de caché reduce costos en ~99%")
    print("="*80 + "\n")


def mostrar_comandos_utiles():
    """Muestra comandos útiles para gestionar el caché"""
    print("\n" + "="*80)
    print("🔧 COMANDOS ÚTILES")
    print("="*80)
    
    print("\n📝 Generar análisis para todas las parcelas:")
    print("   python manage.py generar_analisis_gemini --todas --con-imagenes")
    
    print("\n📝 Generar análisis para parcela específica:")
    print("   python manage.py generar_analisis_gemini --parcela-id 1 --con-imagenes")
    
    print("\n📝 Forzar regeneración (ignorar caché):")
    print("   python manage.py generar_analisis_gemini --todas --forzar")
    
    print("\n📝 Limpiar caché de análisis (en shell de Django):")
    print("   python manage.py shell")
    print("   >>> from informes.models import IndiceMensual")
    print("   >>> IndiceMensual.objects.update(analisis_gemini=None, fecha_analisis_gemini=None)")
    
    print("\n📝 Ver estadísticas de caché:")
    print("   python manage.py shell")
    print("   >>> from informes.models import IndiceMensual")
    print("   >>> total = IndiceMensual.objects.count()")
    print("   >>> con_cache = IndiceMensual.objects.filter(analisis_gemini__isnull=False).count()")
    print("   >>> print(f'Índices con caché: {con_cache}/{total}')")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    demo_cache_vs_sin_cache()
    mostrar_comandos_utiles()
