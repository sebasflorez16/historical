"""
Script de prueba para validar el análisis espacial y visual con Gemini AI
Verifica que las referencias espaciales y metadatos de EOSDA se incluyan correctamente
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.gemini_service import gemini_service


def test_analisis_espacial_gemini():
    """
    Probar el análisis espacial de Gemini con datos reales
    """
    print("=" * 80)
    print("🧪 TEST: ANÁLISIS ESPACIAL Y VISUAL CON GEMINI AI")
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
    
    # Obtener índices mensuales
    indices = parcela.indices_mensuales.order_by('año', 'mes')[:6]
    
    if not indices:
        print("❌ No se encontraron índices mensuales")
        return
    
    print(f"\n📊 Índices mensuales disponibles: {indices.count()}")
    
    # Verificar si hay imágenes
    imagenes_count = sum([
        1 for idx in indices if idx.imagen_ndvi or idx.imagen_ndmi or idx.imagen_savi
    ])
    
    print(f"📸 Imágenes satelitales disponibles: {imagenes_count}")
    
    # Preparar datos para Gemini
    print("\n🔧 PREPARANDO DATOS PARA GEMINI...")
    print("-" * 80)
    
    # Datos de la parcela con información espacial
    parcela_data = {
        'nombre': parcela.nombre,
        'area_hectareas': float(parcela.area_hectareas) if parcela.area_hectareas else 0,
        'tipo_cultivo': parcela.tipo_cultivo or 'No especificado',
        'propietario': str(parcela.propietario) if parcela.propietario else 'No especificado',
        'coordenadas': {}
    }
    
    # Agregar información espacial
    if parcela.centroide:
        parcela_data['coordenadas']['centroide'] = {
            'lat': parcela.centroide.y,
            'lng': parcela.centroide.x
        }
        print(f"   ✅ Centroide: {parcela.centroide.y:.4f}°N, {parcela.centroide.x:.4f}°W")
    
    if parcela.geometria:
        extent = parcela.geometria.extent
        parcela_data['coordenadas']['bbox'] = {
            'min_lon': extent[0],
            'min_lat': extent[1],
            'max_lon': extent[2],
            'max_lat': extent[3]
        }
        print(f"   ✅ Bounding Box: {extent[1]:.4f}°N-{extent[3]:.4f}°N, {extent[0]:.4f}°W-{extent[2]:.4f}°W")
    
    # Preparar datos mensuales con metadatos espaciales
    indices_mensuales = []
    imagenes_paths = []
    
    for idx in indices:
        mes_data = {
            'periodo': idx.periodo_texto,
            'ndvi_promedio': idx.ndvi_promedio,
            'ndmi_promedio': idx.ndmi_promedio,
            'savi_promedio': idx.savi_promedio,
            'nubosidad_promedio': idx.nubosidad_promedio,
            'nubosidad_imagen': idx.nubosidad_imagen,
            'temperatura_promedio': idx.temperatura_promedio,
            'precipitacion_total': idx.precipitacion_total,
            'calidad_datos': idx.calidad_datos or 'BUENA',
            'tiene_imagen_ndvi': bool(idx.imagen_ndvi),
            'tiene_imagen_ndmi': bool(idx.imagen_ndmi),
            'tiene_imagen_savi': bool(idx.imagen_savi)
        }
        
        # Agregar metadatos espaciales si existen
        if idx.fecha_imagen:
            mes_data['fecha_imagen'] = idx.fecha_imagen.isoformat()
        
        if idx.satelite_imagen:
            mes_data['satelite_imagen'] = idx.satelite_imagen
        
        if idx.resolucion_imagen:
            mes_data['resolucion_imagen'] = idx.resolucion_imagen
        
        if idx.coordenadas_imagen:
            mes_data['coordenadas_imagen'] = idx.coordenadas_imagen
        
        if idx.metadatos_imagen:
            mes_data['metadatos_imagen'] = idx.metadatos_imagen
        
        indices_mensuales.append(mes_data)
        
        # Recopilar imágenes
        if idx.imagen_ndvi and idx.imagen_ndvi.path and os.path.exists(idx.imagen_ndvi.path):
            imagenes_paths.append(idx.imagen_ndvi.path)
            print(f"   ✅ Imagen NDVI: {os.path.basename(idx.imagen_ndvi.path)}")
        
        if idx.imagen_ndmi and idx.imagen_ndmi.path and os.path.exists(idx.imagen_ndmi.path):
            imagenes_paths.append(idx.imagen_ndmi.path)
            print(f"   ✅ Imagen NDMI: {os.path.basename(idx.imagen_ndmi.path)}")
    
    print(f"\n📦 Total de imágenes recopiladas: {len(imagenes_paths)}")
    
    # Generar análisis con Gemini
    print("\n🤖 GENERANDO ANÁLISIS CON GEMINI AI...")
    print("-" * 80)
    
    try:
        analisis = gemini_service.generar_analisis_informe(
            parcela_data=parcela_data,
            indices_mensuales=indices_mensuales,
            imagenes_paths=imagenes_paths if imagenes_paths else None,
            tipo_analisis='completo'
        )
        
        print("✅ Análisis generado exitosamente")
        print("\n" + "=" * 80)
        print("📝 RESULTADO DEL ANÁLISIS")
        print("=" * 80)
        
        # Resumen ejecutivo
        if analisis.get('resumen_ejecutivo'):
            print("\n### RESUMEN EJECUTIVO:")
            print("-" * 80)
            print(analisis['resumen_ejecutivo'])
        
        # Análisis de tendencias
        if analisis.get('analisis_tendencias'):
            print("\n### ANÁLISIS DE TENDENCIAS:")
            print("-" * 80)
            print(analisis['analisis_tendencias'])
        
        # Análisis visual (NUEVO)
        if analisis.get('analisis_visual'):
            print("\n### 🛰️ ANÁLISIS VISUAL DE IMÁGENES:")
            print("-" * 80)
            print(analisis['analisis_visual'])
            
            # Verificar si hay referencias espaciales
            analisis_visual_lower = analisis['analisis_visual'].lower()
            referencias_espaciales = [
                'zona norte', 'zona sur', 'zona este', 'zona oeste',
                'norte de la parcela', 'sur de la parcela',
                'heterogeneidad', 'uniformidad', 'variación espacial'
            ]
            
            refs_encontradas = [ref for ref in referencias_espaciales if ref in analisis_visual_lower]
            
            if refs_encontradas:
                print("\n✅ REFERENCIAS ESPACIALES DETECTADAS:")
                for ref in refs_encontradas:
                    print(f"   - {ref}")
            else:
                print("\n⚠️ No se detectaron referencias espaciales explícitas")
        
        # Recomendaciones
        if analisis.get('recomendaciones'):
            print("\n### RECOMENDACIONES:")
            print("-" * 80)
            print(analisis['recomendaciones'])
        
        # Alertas
        if analisis.get('alertas'):
            print("\n### ALERTAS:")
            print("-" * 80)
            print(analisis['alertas'])
        
        # Validaciones
        print("\n" + "=" * 80)
        print("🔍 VALIDACIONES")
        print("=" * 80)
        
        validaciones = {
            '✅ Resumen ejecutivo presente': bool(analisis.get('resumen_ejecutivo')),
            '✅ Análisis de tendencias presente': bool(analisis.get('analisis_tendencias')),
            '✅ Análisis visual presente': bool(analisis.get('analisis_visual')),
            '✅ Recomendaciones presentes': bool(analisis.get('recomendaciones')),
            '✅ Incluye imágenes en análisis': len(imagenes_paths) > 0,
            '✅ Incluye datos espaciales': bool(parcela_data.get('coordenadas')),
        }
        
        for validacion, resultado in validaciones.items():
            estado = "✅" if resultado else "❌"
            print(f"{estado} {validacion}")
        
        # Guardar en caché
        if not analisis.get('error'):
            # Obtener el último índice sin slice
            ultimo_indice = IndiceMensual.objects.filter(
                parcela=parcela
            ).order_by('-año', '-mes').first()
            
            if ultimo_indice:
                ultimo_indice.analisis_gemini = analisis
                ultimo_indice.fecha_analisis_gemini = datetime.now()
                ultimo_indice.save(update_fields=['analisis_gemini', 'fecha_analisis_gemini'])
                print("\n💾 Análisis guardado en caché en la base de datos")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_analisis_espacial_gemini()
