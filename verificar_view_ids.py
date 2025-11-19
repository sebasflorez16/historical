"""
Script para verificar si los view_ids están siendo guardados correctamente
después de la corrección en views.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual, Parcela
from datetime import date

def verificar_view_ids():
    """
    Verifica si hay view_ids guardados en los registros mensuales
    """
    print("\n" + "="*80)
    print("🔍 VERIFICACIÓN DE VIEW_IDS EN BASE DE DATOS")
    print("="*80)
    
    # Obtener todos los registros mensuales
    indices = IndiceMensual.objects.all().order_by('-año', '-mes')
    
    total_registros = indices.count()
    con_view_id = indices.filter(view_id_imagen__isnull=False).count()
    sin_view_id = total_registros - con_view_id
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total registros mensuales: {total_registros}")
    print(f"   ✅ Con view_id guardado: {con_view_id}")
    print(f"   ❌ Sin view_id: {sin_view_id}")
    
    if con_view_id == 0:
        print(f"\n⚠️  PROBLEMA: No hay registros con view_id guardado")
        print(f"   Esto significa que la corrección aún no se ha aplicado.")
        print(f"   Necesitas:")
        print(f"   1. Borrar los datos antiguos (que no tienen view_id)")
        print(f"   2. Volver a obtener datos históricos con el código corregido")
    else:
        print(f"\n✅ ÉXITO: Hay {con_view_id} registros con view_id guardado")
        
        # Mostrar algunos ejemplos
        print(f"\n📋 Ejemplos de registros CON view_id:")
        registros_con_view = indices.filter(view_id_imagen__isnull=False)[:5]
        for registro in registros_con_view:
            print(f"   {registro.año}-{registro.mes:02d} | {registro.parcela.nombre}")
            print(f"      view_id: {registro.view_id_imagen}")
            print(f"      fecha: {registro.fecha_imagen}")
            print(f"      nubosidad: {registro.nubosidad_imagen}%")
            print()
    
    if sin_view_id > 0:
        print(f"\n⚠️  Hay {sin_view_id} registros SIN view_id")
        print(f"   Estos son datos antiguos que necesitan ser re-obtenidos.")
        
        # Mostrar algunos ejemplos
        print(f"\n📋 Ejemplos de registros SIN view_id:")
        registros_sin_view = indices.filter(view_id_imagen__isnull=True)[:5]
        for registro in registros_sin_view:
            ndvi_str = f"{registro.ndvi_promedio:.3f}" if registro.ndvi_promedio else 'N/A'
            print(f"   {registro.año}-{registro.mes:02d} | {registro.parcela.nombre}")
            print(f"      NDVI: {ndvi_str}")
            print(f"      Fecha consulta: {registro.fecha_consulta_api}")
            print()
    
    print("\n" + "="*80)
    
    return {
        'total': total_registros,
        'con_view_id': con_view_id,
        'sin_view_id': sin_view_id
    }


if __name__ == "__main__":
    stats = verificar_view_ids()
    
    if stats['sin_view_id'] > 0:
        print("\n💡 RECOMENDACIÓN:")
        print("   Para limpiar los datos antiguos y volver a obtener con view_ids:")
        print("   1. Ir a la interfaz web")
        print("   2. Borrar los datos históricos de una parcela")
        print("   3. Volver a obtener datos históricos")
        print("   O ejecutar:")
        print("   >>> from informes.models import IndiceMensual")
        print("   >>> IndiceMensual.objects.all().delete()")
        print("   >>> # Luego volver a obtener datos desde la interfaz\n")
