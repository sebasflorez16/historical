"""
Script de prueba mejorado para generación de informes PDF
Configura Django correctamente antes de ejecutar
"""
import os
import sys
import django

# Configurar Django ANTES de importar modelos
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Ahora sí importar modelos
from informes.models import Parcela, IndiceMensual, Informe
from informes.generador_pdf import GeneradorPDFProfesional
from datetime import datetime, date, timedelta


def main():
    """
    Prueba completa de generación de informe PDF
    """
    print("=" * 80)
    print("🧪 TEST DE GENERACIÓN DE INFORMES PDF")
    print("=" * 80)
    
    # 1. Verificar parcelas disponibles
    print("\n📊 1. Verificando parcelas disponibles...")
    parcelas = Parcela.objects.filter(activa=True)
    print(f"   ✅ Parcelas activas: {parcelas.count()}")
    
    if parcelas.count() == 0:
        print("   ❌ ERROR: No hay parcelas activas")
        return False
    
    # Seleccionar primera parcela
    parcela = parcelas.first()
    print(f"   📍 Parcela: {parcela.nombre} (ID: {parcela.id})")
    print(f"      - Área: {parcela.area_hectareas:.2f} ha")
    print(f"      - Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
    
    # 2. Verificar datos
    print("\n📈 2. Verificando datos satelitales...")
    indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')
    print(f"   ✅ Registros: {indices.count()}")
    
    if indices.count() == 0:
        print("   ❌ ERROR: No hay datos satelitales")
        print("   💡 Ejecute primero: python manage.py shell -c \"from informes.views import obtener_datos_historicos; ...\"")
        return False
    
    # Mostrar muestra
    print("\n   📅 Últimos 3 registros:")
    for idx in indices[:3]:
        ndvi = idx.ndvi_promedio or 0
        ndmi = idx.ndmi_promedio or 0
        savi = idx.savi_promedio or 0
        print(f"      - {idx.periodo_texto}: NDVI={ndvi:.3f}, NDMI={ndmi:.3f}, SAVI={savi:.3f}")
    
    # 3. Generar informe
    print("\n📄 3. Generando informe PDF...")
    try:
        generador = GeneradorPDFProfesional()
        
        ruta_pdf = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12
        )
        
        print(f"   ✅ PDF generado!")
        print(f"   📁 Ruta: {ruta_pdf}")
        
        # Verificar archivo
        if os.path.exists(ruta_pdf):
            size_mb = os.path.getsize(ruta_pdf) / (1024 * 1024)
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
        else:
            print(f"   ❌ ERROR: Archivo no encontrado")
            return False
        
        # 4. Registrar en BD
        print("\n💾 4. Creando registro en BD...")
        try:
            titulo_informe = f"Informe - {parcela.nombre}"[:290]
            informe = Informe.objects.create(
                parcela=parcela,
                periodo_analisis_meses=12,
                fecha_inicio_analisis=(datetime.now() - timedelta(days=365)).date(),
                fecha_fin_analisis=datetime.now().date(),
                titulo=titulo_informe,
                resumen_ejecutivo=f"Informe generado con {indices.count()} registros.",
                archivo_pdf=ruta_pdf
            )
            print(f"   ✅ Registro ID: {informe.id}")
            
        except Exception as e:
            print(f"   ⚠️  Error en BD: {str(e)}")
            print(f"   💡 El PDF se generó pero no se registró")
        
        # Resumen
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📊 Resumen:")
        print(f"   - Parcela: {parcela.nombre}")
        print(f"   - Datos: {indices.count()} meses")
        print(f"   - PDF: {os.path.basename(ruta_pdf)}")
        print(f"\n💡 Ver informe:")
        print(f"   open \"{ruta_pdf}\"")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Cancelado")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
