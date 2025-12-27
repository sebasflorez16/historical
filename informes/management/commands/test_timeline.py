"""
🎬 Comando para probar el Timeline Visual desde consola
Genera un reporte del timeline de una parcela sin necesidad del servidor web
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import json

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor


class Command(BaseCommand):
    help = '🎬 Prueba el Timeline Visual de una parcela desde consola'

    def add_arguments(self, parser):
        parser.add_argument(
            'parcela_id',
            type=int,
            nargs='?',
            help='ID de la parcela a analizar'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista todas las parcelas con datos disponibles'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Muestra el JSON completo del timeline'
        )

    def handle(self, *args, **options):
        # Si pide listar parcelas
        if options['listar']:
            self.listar_parcelas()
            return

        # Obtener ID de parcela
        parcela_id = options.get('parcela_id')
        if not parcela_id:
            # Si no se proporciona ID, mostrar parcelas disponibles
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.ERROR(
                "❌ Debes especificar el ID de una parcela"
            ))
            self.stdout.write("\nUso: python manage.py test_timeline <parcela_id>")
            self.stdout.write("     python manage.py test_timeline --listar\n")
            self.listar_parcelas()
            return

        try:
            # Obtener parcela
            parcela = Parcela.objects.get(id=parcela_id)
            
            # Verificar que tenga datos
            total_indices = IndiceMensual.objects.filter(parcela=parcela).count()
            
            if total_indices == 0:
                raise CommandError(
                    f"❌ La parcela '{parcela.nombre}' no tiene datos históricos"
                )
            
            # Generar timeline
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS(
                f"🎬 TIMELINE VISUAL - {parcela.nombre}"
            ))
            self.stdout.write("="*70 + "\n")
            
            # Información de la parcela
            self.stdout.write(f"📍 Parcela: {parcela.nombre}")
            self.stdout.write(f"👤 Propietario: {parcela.propietario}")
            self.stdout.write(f"🌾 Tipo de cultivo: {parcela.tipo_cultivo or 'No especificado'}")
            self.stdout.write(f"📏 Área: {parcela.area_hectareas:.2f} hectáreas")
            self.stdout.write(f"📊 Total de meses: {total_indices}\n")
            
            # Procesar timeline
            self.stdout.write(self.style.WARNING("⏳ Procesando timeline..."))
            timeline_data = TimelineProcessor.generar_timeline_completo(parcela)
            
            if timeline_data.get('error'):
                raise CommandError(f"❌ {timeline_data.get('mensaje')}")
            
            # Mostrar resumen
            self.stdout.write(self.style.SUCCESS("✅ Timeline generado exitosamente!\n"))
            
            self.stdout.write("📈 ESTADÍSTICAS GENERALES:")
            stats = timeline_data.get('estadisticas', {})
            if stats.get('ndvi_promedio'):
                self.stdout.write(f"  NDVI promedio: {stats['ndvi_promedio']:.3f}")
            if stats.get('ndmi_promedio'):
                self.stdout.write(f"  NDMI promedio: {stats['ndmi_promedio']:.3f}")
            if stats.get('savi_promedio'):
                self.stdout.write(f"  SAVI promedio: {stats['savi_promedio']:.3f}")
            
            # Mostrar frames
            self.stdout.write("\n📅 FRAMES DEL TIMELINE:")
            self.stdout.write("─" * 70)
            
            for i, frame in enumerate(timeline_data['frames'], 1):
                self.mostrar_frame(i, frame, total_indices)
            
            # Si pide JSON completo
            if options['json']:
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.WARNING("📄 JSON COMPLETO:"))
                self.stdout.write("="*70 + "\n")
                self.stdout.write(json.dumps(timeline_data, indent=2, ensure_ascii=False))
            
            # Resumen final
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("🎉 ¡Timeline procesado correctamente!"))
            self.stdout.write("\n📋 Próximos pasos:")
            self.stdout.write("  1. Inicia el servidor: python manage.py runserver")
            self.stdout.write(f"  2. Accede a: http://localhost:8000/parcelas/{parcela_id}/timeline/")
            self.stdout.write("  3. Disfruta de la visualización interactiva!\n")
            
        except Parcela.DoesNotExist:
            raise CommandError(f"❌ No existe una parcela con ID {parcela_id}")
        except Exception as e:
            raise CommandError(f"❌ Error procesando timeline: {str(e)}")

    def listar_parcelas(self):
        """Lista todas las parcelas con datos disponibles"""
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("📊 PARCELAS CON DATOS DISPONIBLES"))
        self.stdout.write("="*70 + "\n")
        
        parcelas = Parcela.objects.all().order_by('id')
        
        if not parcelas.exists():
            self.stdout.write(self.style.WARNING("⚠️  No hay parcelas registradas"))
            return
        
        tabla = []
        for parcela in parcelas:
            total_indices = IndiceMensual.objects.filter(parcela=parcela).count()
            
            if total_indices > 0:
                # Obtener rango de datos
                primer = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes').first()
                ultimo = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes').first()
                
                rango = f"{primer.periodo_texto} - {ultimo.periodo_texto}"
                estado = self.style.SUCCESS("✅")
            else:
                rango = "Sin datos"
                estado = self.style.ERROR("❌")
            
            tabla.append({
                'id': parcela.id,
                'nombre': parcela.nombre[:30],
                'propietario': parcela.propietario[:20],
                'meses': total_indices,
                'rango': rango[:30],
                'estado': estado
            })
        
        # Mostrar tabla
        self.stdout.write(f"{'ID':<5} {'Nombre':<32} {'Propietario':<22} {'Meses':<7} {'Estado'}")
        self.stdout.write("─" * 70)
        
        for item in tabla:
            self.stdout.write(
                f"{item['id']:<5} {item['nombre']:<32} {item['propietario']:<22} "
                f"{item['meses']:<7} {item['estado']}"
            )
        
        self.stdout.write("\n💡 Para ver el timeline de una parcela:")
        self.stdout.write("   python manage.py test_timeline <ID>\n")

    def mostrar_frame(self, numero, frame, total):
        """Muestra la información de un frame"""
        # Encabezado del frame
        self.stdout.write(
            self.style.SUCCESS(f"\n📅 Frame {numero}/{total}: {frame['periodo_texto']}")
        )
        
        # NDVI
        if frame.get('ndvi', {}).get('promedio') is not None:
            ndvi = frame['ndvi']['promedio']
            ndvi_class = frame.get('clasificaciones', {}).get('ndvi', {})
            
            icono = ndvi_class.get('icono', '🌿')
            etiqueta = ndvi_class.get('etiqueta', 'N/A')
            color = ndvi_class.get('color', '#000')
            
            self.stdout.write(f"  🌿 NDVI: {ndvi:.3f} {icono} {etiqueta}")
        
        # NDMI
        if frame.get('ndmi', {}).get('promedio') is not None:
            ndmi = frame['ndmi']['promedio']
            ndmi_class = frame.get('clasificaciones', {}).get('ndmi', {})
            
            icono = ndmi_class.get('icono', '💧')
            etiqueta = ndmi_class.get('etiqueta', 'N/A')
            
            self.stdout.write(f"  💧 NDMI: {ndmi:.3f} {icono} {etiqueta}")
        
        # SAVI
        if frame.get('savi', {}).get('promedio') is not None:
            savi = frame['savi']['promedio']
            savi_class = frame.get('clasificaciones', {}).get('savi', {})
            
            icono = savi_class.get('icono', '🌱')
            etiqueta = savi_class.get('etiqueta', 'N/A')
            
            self.stdout.write(f"  🌱 SAVI: {savi:.3f} {icono} {etiqueta}")
        
        # Clima
        if frame.get('temperatura'):
            self.stdout.write(f"  🌡️  Temperatura: {frame['temperatura']:.1f}°C")
        if frame.get('precipitacion'):
            self.stdout.write(f"  🌧️  Precipitación: {frame['precipitacion']:.1f}mm")
        
        # Comparación
        if frame.get('comparacion') and frame['comparacion'].get('ndvi'):
            comp = frame['comparacion']['ndvi']
            icono = comp.get('icono', '➡️')
            porcentaje = comp.get('porcentaje', 0)
            
            self.stdout.write(f"  📈 Tendencia: {icono} {porcentaje:+.1f}% vs. anterior")
        
        # Resumen simple
        if frame.get('resumen_simple'):
            self.stdout.write(f"  💬 {frame['resumen_simple']}")
        
        # Imágenes
        imagenes = frame.get('imagenes', {})
        tiene_ndvi = '✅' if imagenes.get('ndvi') else '❌'
        tiene_ndmi = '✅' if imagenes.get('ndmi') else '❌'
        tiene_savi = '✅' if imagenes.get('savi') else '❌'
        
        self.stdout.write(f"  🖼️  Imágenes: NDVI {tiene_ndvi} | NDMI {tiene_ndmi} | SAVI {tiene_savi}")
