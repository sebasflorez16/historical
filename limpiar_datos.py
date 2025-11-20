"""
Script para eliminar datos históricos de una parcela específica
Útil para re-generar datos con Open-Meteo
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual, CacheDatosEOSDA, Parcela

def limpiar_datos_parcela(parcela_id=None):
    """
    Borra los datos de una parcela específica o de todas
    """
    print("\n" + "="*80)
    print("🗑️  LIMPIEZA DE DATOS HISTÓRICOS")
    print("="*80)
    
    if parcela_id:
        try:
            parcela = Parcela.objects.get(id=parcela_id)
            print(f"\n📍 Parcela seleccionada: {parcela.nombre} (ID: {parcela.id})")
            
            # Contar registros de esta parcela
            total_indices = IndiceMensual.objects.filter(parcela=parcela).count()
            
            print(f"📊 Registros actuales: {total_indices}")
            
            if total_indices == 0:
                print("✅ No hay datos que eliminar")
                return False
            
            respuesta = input(f"\n⚠️  ¿Eliminar {total_indices} registros de '{parcela.nombre}'? (sí/no): ")
            
            if respuesta.lower() in ['sí', 'si', 's']:
                eliminados, _ = IndiceMensual.objects.filter(parcela=parcela).delete()
                print(f"\n✅ {eliminados} registros eliminados de '{parcela.nombre}'")
                
                # También limpiar caché de esa parcela si existe
                if parcela.field_id_eosda:
                    cache_eliminado = CacheDatosEOSDA.objects.filter(field_id=parcela.field_id_eosda).delete()
                    print(f"✅ Caché eliminado para field_id: {parcela.field_id_eosda}")
                
                print(f"\n💡 Ahora puedes obtener datos nuevos desde la interfaz")
                print(f"   Los datos incluirán climatología completa de Open-Meteo")
                return True
            else:
                print("❌ Operación cancelada")
                return False
                
        except Parcela.DoesNotExist:
            print(f"❌ ERROR: No existe parcela con ID={parcela_id}")
            return False
    else:
        # Limpiar TODAS las parcelas
        total_indices = IndiceMensual.objects.count()
        total_cache = CacheDatosEOSDA.objects.count()
        
        print(f"\n📊 Datos actuales:")
        print(f"   Índices mensuales: {total_indices}")
        print(f"   Entradas de caché: {total_cache}")
        
        respuesta = input("\n⚠️  ¿Borrar TODOS los datos de TODAS las parcelas? (sí/no): ")
        
        if respuesta.lower() in ['sí', 'si', 's']:
            print(f"\n🗑️  Borrando datos...")
            
            IndiceMensual.objects.all().delete()
            print(f"   ✅ {total_indices} índices mensuales borrados")
            
            CacheDatosEOSDA.objects.all().delete()
            print(f"   ✅ {total_cache} entradas de caché borradas")
            
            print(f"\n✅ LIMPIEZA COMPLETADA")
            return True
        else:
            print(f"\n❌ Operación cancelada")
            return False


if __name__ == "__main__":
    print("\nOpciones:")
    print("1. Limpiar solo una parcela específica")
    print("2. Limpiar TODAS las parcelas")
    
    opcion = input("\nSelecciona opción (1/2): ")
    
    if opcion == "1":
        parcela_id = input("Ingresa el ID de la parcela (ej: 2 para 'lote 2'): ")
        try:
            limpiar_datos_parcela(int(parcela_id))
        except ValueError:
            print("❌ ID inválido")
    elif opcion == "2":
        limpiar_datos_parcela(None)
    else:
        print("❌ Opción inválida")
