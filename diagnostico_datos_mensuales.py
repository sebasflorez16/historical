"""
Script de diagnóstico para verificar qué datos satelitales se están trayendo por mes
Muestra:
- Cuántas escenas por mes
- Rangos de nubosidad
- view_ids disponibles
- Datos promedio vs datos por escena
"""

import os
import django
import json
from datetime import date, timedelta
from collections import defaultdict

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual, CacheDatosEOSDA
from django.utils import timezone


def diagnosticar_datos_parcela(parcela_id):
    """
    Diagnostica los datos almacenados para una parcela específica
    """
    try:
        parcela = Parcela.objects.get(id=parcela_id, activa=True)
        print(f"\n{'='*80}")
        print(f"📊 DIAGNÓSTICO DE DATOS SATELITALES")
        print(f"{'='*80}")
        print(f"Parcela: {parcela.nombre} ({parcela.propietario})")
        print(f"Field ID EOSDA: {parcela.eosda_field_id}")
        print(f"Sincronizada: {'✅ Sí' if parcela.eosda_sincronizada else '❌ No'}")
        
        # 1. VERIFICAR DATOS EN IndiceMensual
        print(f"\n{'─'*80}")
        print(f"1️⃣  DATOS EN BASE DE DATOS (IndiceMensual)")
        print(f"{'─'*80}")
        
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')
        print(f"\nTotal registros mensuales: {indices.count()}")
        
        for indice in indices[:6]:  # Mostrar últimos 6 meses
            print(f"\n📅 {indice.periodo_texto} ({indice.año}-{indice.mes:02d})")
            
            # NDVI
            ndvi_str = f"{indice.ndvi_promedio:.3f}" if indice.ndvi_promedio is not None else "N/A"
            ndvi_min_str = f"{indice.ndvi_minimo:.3f}" if indice.ndvi_minimo is not None else "N/A"
            ndvi_max_str = f"{indice.ndvi_maximo:.3f}" if indice.ndvi_maximo is not None else "N/A"
            print(f"   NDVI: {ndvi_str} [{ndvi_min_str} - {ndvi_max_str}]")
            
            # NDMI
            ndmi_str = f"{indice.ndmi_promedio:.3f}" if indice.ndmi_promedio is not None else "N/A"
            ndmi_min_str = f"{indice.ndmi_minimo:.3f}" if indice.ndmi_minimo is not None else "N/A"
            ndmi_max_str = f"{indice.ndmi_maximo:.3f}" if indice.ndmi_maximo is not None else "N/A"
            print(f"   NDMI: {ndmi_str} [{ndmi_min_str} - {ndmi_max_str}]")
            
            # SAVI
            savi_str = f"{indice.savi_promedio:.3f}" if indice.savi_promedio is not None else "N/A"
            savi_min_str = f"{indice.savi_minimo:.3f}" if indice.savi_minimo is not None else "N/A"
            savi_max_str = f"{indice.savi_maximo:.3f}" if indice.savi_maximo is not None else "N/A"
            print(f"   SAVI: {savi_str} [{savi_min_str} - {savi_max_str}]")
            
            # Nubosidad
            nub_str = f"{indice.nubosidad_promedio:.1f}%" if indice.nubosidad_promedio is not None else "N/A"
            print(f"   Nubosidad promedio: {nub_str}")
            
            # Verificar metadatos de imagen
            if indice.view_id_imagen:
                print(f"   ✅ view_id guardado: {indice.view_id_imagen}")
                print(f"      Fecha imagen: {indice.fecha_imagen}")
                print(f"      Nubosidad imagen: {indice.nubosidad_imagen:.1f}%" if indice.nubosidad_imagen else "      Nubosidad imagen: N/A")
            else:
                print(f"   ⚠️  NO HAY view_id guardado (no se puede descargar imagen)")
            
            # Verificar si ya tiene imágenes descargadas
            imagenes = []
            if indice.imagen_ndvi:
                imagenes.append('NDVI')
            if indice.imagen_ndmi:
                imagenes.append('NDMI')
            if indice.imagen_savi:
                imagenes.append('SAVI')
            
            if imagenes:
                print(f"   🖼️  Imágenes descargadas: {', '.join(imagenes)}")
            else:
                print(f"   📷 Sin imágenes descargadas aún")
        
        # 2. VERIFICAR DATOS EN CACHÉ DE STATISTICS API
        print(f"\n{'─'*80}")
        print(f"2️⃣  DATOS EN CACHÉ (Statistics API)")
        print(f"{'─'*80}")
        
        caches = CacheDatosEOSDA.objects.filter(
            field_id=parcela.eosda_field_id,
            valido_hasta__gte=timezone.now()
        ).order_by('-fecha_fin')
        
        print(f"\nTotal cachés válidos: {caches.count()}")
        
        for cache in caches[:3]:  # Mostrar últimos 3 cachés
            print(f"\n📦 Caché: {cache.fecha_inicio} → {cache.fecha_fin}")
            print(f"   Válido hasta: {cache.valido_hasta}")
            
            if cache.datos_json:
                try:
                    # datos_json ya es un dict, no necesita json.loads()
                    datos = cache.datos_json if isinstance(cache.datos_json, dict) else json.loads(cache.datos_json)
                    resultados = datos.get('resultados', [])
                    print(f"   Total escenas en caché: {len(resultados)}")
                    
                    # Agrupar por mes
                    escenas_por_mes = defaultdict(list)
                    for escena in resultados:
                        fecha_str = escena.get('date', '')
                        if fecha_str:
                            # Extraer año-mes
                            mes_key = fecha_str[:7]  # YYYY-MM
                            escenas_por_mes[mes_key].append(escena)
                    
                    print(f"\n   📊 Escenas por mes:")
                    for mes_key in sorted(escenas_por_mes.keys(), reverse=True)[:6]:
                        escenas = escenas_por_mes[mes_key]
                        print(f"\n      {mes_key}: {len(escenas)} escenas")
                        
                        # Ordenar por nubosidad
                        escenas_ordenadas = sorted(escenas, key=lambda x: x.get('cloud', 100))
                        
                        print(f"         Rango nubosidad: {escenas_ordenadas[0].get('cloud', 'N/A'):.1f}% - {escenas_ordenadas[-1].get('cloud', 'N/A'):.1f}%")
                        
                        # Mostrar las 3 mejores escenas
                        print(f"         🌟 Top 3 mejores escenas (menor nubosidad):")
                        for i, escena in enumerate(escenas_ordenadas[:3], 1):
                            view_id = escena.get('id', 'N/A')
                            fecha = escena.get('date', 'N/A')
                            cloud = escena.get('cloud', 'N/A')
                            indexes = escena.get('indexes', {})
                            ndvi_raw = indexes.get('NDVI', {}).get('average', None)
                            ndvi = f"{ndvi_raw:.3f}" if isinstance(ndvi_raw, (int, float)) else "N/A"
                            
                            view_id_short = view_id[:20] if view_id != 'N/A' else 'N/A'
                            cloud_str = f"{cloud:.1f}%" if isinstance(cloud, (int, float)) else str(cloud)
                            
                            print(f"            {i}. view_id: {view_id_short}...")
                            print(f"               Fecha: {fecha}, Nubosidad: {cloud_str}, NDVI: {ndvi}")
                
                except json.JSONDecodeError as e:
                    print(f"   ❌ Error parseando JSON del caché: {e}")
        
        # 3. CONCLUSIÓN Y RECOMENDACIONES
        print(f"\n{'─'*80}")
        print(f"3️⃣  CONCLUSIÓN Y RECOMENDACIONES")
        print(f"{'─'*80}\n")
        
        registros_con_view_id = indices.filter(view_id_imagen__isnull=False).count()
        registros_sin_view_id = indices.filter(view_id_imagen__isnull=True).count()
        
        if registros_sin_view_id > 0:
            print(f"⚠️  PROBLEMA DETECTADO:")
            print(f"   {registros_sin_view_id} registros mensuales NO tienen view_id guardado")
            print(f"   Esto significa que NO se puede descargar imágenes para esos meses\n")
            print(f"💡 SOLUCIÓN:")
            print(f"   1. Volver a ejecutar 'Obtener Datos Históricos'")
            print(f"   2. El sistema ahora guardará automáticamente el view_id de la mejor escena")
            print(f"   3. Luego podrá descargar imágenes usando esos view_ids")
        else:
            print(f"✅ CORRECTO: Todos los registros tienen view_id guardado")
            print(f"   Se pueden descargar imágenes para todos los meses")
        
        print(f"\n{'='*80}\n")
        
    except Parcela.DoesNotExist:
        print(f"❌ Error: No se encontró la parcela con ID {parcela_id}")
    except Exception as e:
        print(f"❌ Error en diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔍 DIAGNÓSTICO DE DATOS SATELITALES - AgroTech Histórico")
    print("="*80)
    
    # Listar todas las parcelas disponibles
    parcelas = Parcela.objects.filter(activa=True).order_by('-fecha_registro')
    
    if not parcelas.exists():
        print("❌ No hay parcelas activas en el sistema")
    else:
        print(f"\n📋 Parcelas disponibles:")
        for i, p in enumerate(parcelas, 1):
            print(f"   {i}. [{p.id}] {p.nombre} - {p.propietario} "
                  f"({'✅ Sincronizada' if p.eosda_sincronizada else '❌ No sincronizada'})")
        
        print("\n" + "="*80)
        
        # Diagnosticar la primera parcela (o puedes cambiar el ID)
        parcela_id = parcelas.first().id
        print(f"\nDiagnosticando parcela ID: {parcela_id}")
        diagnosticar_datos_parcela(parcela_id)
        
        # Para diagnosticar una parcela específica, descomenta y cambia el ID:
        # diagnosticar_datos_parcela(1)
