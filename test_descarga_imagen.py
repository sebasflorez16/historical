"""
Script para probar la descarga de imagen directamente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual
from informes.services.eosda_api import eosda_service

def test_descarga_imagen():
    """
    Prueba la descarga de imagen para un registro específico
    """
    print("\n" + "="*80)
    print("🧪 TEST DE DESCARGA DE IMAGEN SATELITAL")
    print("="*80)
    
    # Obtener el primer registro con view_id
    registro = IndiceMensual.objects.filter(view_id_imagen__isnull=False).first()
    
    if not registro:
        print("❌ No hay registros con view_id")
        return
    
    print(f"\n📋 Registro seleccionado:")
    print(f"   Parcela: {registro.parcela.nombre}")
    print(f"   Período: {registro.año}-{registro.mes:02d}")
    print(f"   Field ID: {registro.parcela.eosda_field_id}")
    print(f"   View ID: {registro.view_id_imagen}")
    print(f"   Fecha imagen: {registro.fecha_imagen}")
    print(f"   Nubosidad: {registro.nubosidad_imagen}%")
    
    # Probar descarga de NDVI
    print(f"\n📷 Intentando descargar imagen NDVI...")
    
    resultado = eosda_service.descargar_imagen_satelital(
        field_id=registro.parcela.eosda_field_id,
        indice='NDVI',
        view_id=registro.view_id_imagen,
        fecha_escena=registro.fecha_imagen.isoformat() if registro.fecha_imagen else None,
        max_nubosidad=50.0
    )
    
    if resultado:
        print(f"\n✅ ÉXITO - Imagen descargada")
        print(f"   Tamaño: {len(resultado['imagen'])} bytes")
        print(f"   Tipo: {resultado.get('content_type', 'N/A')}")
        print(f"   View ID: {resultado.get('view_id')}")
        print(f"   Fecha: {resultado.get('fecha')}")
        print(f"   Nubosidad: {resultado.get('nubosidad')}")
        
        # Guardar imagen de prueba
        with open('test_imagen_ndvi.png', 'wb') as f:
            f.write(resultado['imagen'])
        print(f"\n💾 Imagen guardada como: test_imagen_ndvi.png")
    else:
        print(f"\n❌ ERROR - No se pudo descargar la imagen")
        print(f"   Revisa los logs para más detalles")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_descarga_imagen()
