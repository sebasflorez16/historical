"""
Script para borrar los datos antiguos y volver a obtenerlos con view_ids
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual, CacheDatosEOSDA

def limpiar_datos():
    """
    Borra los datos antiguos sin view_id y el caché
    """
    print("\n" + "="*80)
    print("🗑️  LIMPIEZA DE DATOS ANTIGUOS")
    print("="*80)
    
    # Contar registros antes
    total_indices = IndiceMensual.objects.count()
    total_cache = CacheDatosEOSDA.objects.count()
    
    print(f"\n📊 Datos actuales:")
    print(f"   Índices mensuales: {total_indices}")
    print(f"   Entradas de caché: {total_cache}")
    
    # Confirmar
    respuesta = input("\n⚠️  ¿Borrar todos los datos? (sí/no): ")
    
    if respuesta.lower() == 'sí' or respuesta.lower() == 'si':
        print(f"\n🗑️  Borrando datos...")
        
        # Borrar índices mensuales
        IndiceMensual.objects.all().delete()
        print(f"   ✅ {total_indices} índices mensuales borrados")
        
        # Borrar caché
        CacheDatosEOSDA.objects.all().delete()
        print(f"   ✅ {total_cache} entradas de caché borradas")
        
        print(f"\n✅ LIMPIEZA COMPLETADA")
        print(f"\n💡 Ahora puedes:")
        print(f"   1. Ir a http://localhost:8000/informes/parcelas/")
        print(f"   2. Seleccionar una parcela")
        print(f"   3. Hacer clic en 'Obtener Datos Históricos'")
        print(f"   4. Los nuevos datos incluirán view_ids para descarga de imágenes\n")
        
        return True
    else:
        print(f"\n❌ Operación cancelada")
        return False


if __name__ == "__main__":
    limpiar_datos()
