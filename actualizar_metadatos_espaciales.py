"""
Script para actualizar metadatos espaciales de imágenes satelitales existentes
Rellena los campos coordenadas_imagen, satelite_imagen, resolucion_imagen y metadatos_imagen
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual


def actualizar_metadatos_espaciales():
    """
    Actualizar metadatos espaciales de todas las imágenes que tengan view_id
    """
    print("=" * 80)
    print("🗺️ ACTUALIZACIÓN DE METADATOS ESPACIALES DE IMÁGENES")
    print("=" * 80)
    
    # Buscar todos los índices que tienen view_id pero no tienen metadatos espaciales
    indices_sin_metadatos = IndiceMensual.objects.filter(
        view_id_imagen__isnull=False
    ).filter(
        coordenadas_imagen__isnull=True
    )
    
    total = indices_sin_metadatos.count()
    
    if total == 0:
        print("\n✅ Todos los índices con imágenes ya tienen metadatos espaciales")
        return
    
    print(f"\n📊 Encontrados {total} índices que necesitan metadatos espaciales")
    
    actualizados = 0
    
    for indice in indices_sin_metadatos:
        try:
            parcela = indice.parcela
            
            # Generar metadatos basados en la parcela
            metadatos = {
                'view_id': indice.view_id_imagen,
                'fecha_captura': indice.fecha_imagen.isoformat() if indice.fecha_imagen else None,
                'cloud_cover': indice.nubosidad_imagen,
            }
            
            # Coordenadas de la imagen (basadas en la geometría de la parcela)
            if parcela.geometria:
                extent = parcela.geometria.extent  # (xmin, ymin, xmax, ymax)
                coordenadas = [extent[1], extent[0], extent[3], extent[2]]  # [min_lat, min_lon, max_lat, max_lon]
                
                indice.coordenadas_imagen = coordenadas
                metadatos['bbox'] = {
                    'min_lat': extent[1],
                    'min_lon': extent[0],
                    'max_lat': extent[3],
                    'max_lon': extent[2]
                }
            
            # Inferir satélite basado en fecha o view_id
            # EOSDA usa principalmente Sentinel-2 (10m resolución) y Landsat-8 (30m)
            if indice.fecha_imagen and indice.fecha_imagen.year >= 2022:
                indice.satelite_imagen = 'Sentinel-2'
                indice.resolucion_imagen = 10.0
            else:
                indice.satelite_imagen = 'Sentinel-2/Landsat-8'
                indice.resolucion_imagen = 10.0
            
            metadatos['satelite'] = indice.satelite_imagen
            metadatos['resolucion_m'] = indice.resolucion_imagen
            
            indice.metadatos_imagen = metadatos
            
            # Guardar
            indice.save(update_fields=[
                'coordenadas_imagen',
                'satelite_imagen',
                'resolucion_imagen',
                'metadatos_imagen'
            ])
            
            actualizados += 1
            
            if actualizados % 10 == 0:
                print(f"   ✅ Procesados {actualizados}/{total} índices...")
            
        except Exception as e:
            print(f"   ❌ Error procesando índice {indice.id}: {str(e)}")
    
    print(f"\n✅ COMPLETADO: {actualizados} índices actualizados con metadatos espaciales")
    
    # Mostrar estadísticas
    print("\n" + "=" * 80)
    print("📊 ESTADÍSTICAS")
    print("=" * 80)
    
    total_con_metadatos = IndiceMensual.objects.filter(
        coordenadas_imagen__isnull=False
    ).count()
    
    total_con_imagenes = IndiceMensual.objects.filter(
        view_id_imagen__isnull=False
    ).count()
    
    print(f"   - Total índices con imágenes: {total_con_imagenes}")
    print(f"   - Total con metadatos espaciales: {total_con_metadatos}")
    print(f"   - Cobertura: {(total_con_metadatos/total_con_imagenes*100):.1f}%")
    
    # Ejemplos
    print("\n📋 EJEMPLO DE METADATOS:")
    ejemplo = IndiceMensual.objects.filter(
        metadatos_imagen__isnull=False
    ).first()
    
    if ejemplo:
        print(f"\n   Parcela: {ejemplo.parcela.nombre}")
        print(f"   Período: {ejemplo.periodo_texto}")
        print(f"   Coordenadas: {ejemplo.coordenadas_imagen}")
        print(f"   Satélite: {ejemplo.satelite_imagen}")
        print(f"   Resolución: {ejemplo.resolucion_imagen}m")
        print(f"   Metadatos: {ejemplo.metadatos_imagen}")


if __name__ == "__main__":
    actualizar_metadatos_espaciales()
