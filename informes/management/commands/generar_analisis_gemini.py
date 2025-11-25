"""
Management Command para generar análisis masivos con Gemini AI
Permite regenerar análisis para todas las parcelas o parcelas específicas
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from informes.models import Parcela, IndiceMensual
from informes.services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Genera análisis masivos con Gemini AI para parcelas seleccionadas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--parcela-id',
            type=int,
            help='ID de una parcela específica (opcional)'
        )
        parser.add_argument(
            '--todas',
            action='store_true',
            help='Procesar todas las parcelas activas'
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar regeneración incluso si existe caché válido'
        )
        parser.add_argument(
            '--meses',
            type=int,
            default=6,
            help='Número de meses a analizar (default: 6)'
        )
        parser.add_argument(
            '--con-imagenes',
            action='store_true',
            help='Incluir análisis visual de imágenes satelitales'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🤖 GENERADOR MASIVO DE ANÁLISIS GEMINI AI'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Verificar que Gemini esté disponible
        if not gemini_service:
            raise CommandError('❌ Servicio de Gemini AI no disponible')
        
        # Obtener parcelas
        if options['parcela_id']:
            parcelas = Parcela.objects.filter(id=options['parcela_id'], activa=True)
            if not parcelas.exists():
                raise CommandError(f'❌ Parcela {options["parcela_id"]} no encontrada')
        elif options['todas']:
            parcelas = Parcela.objects.filter(activa=True)
        else:
            raise CommandError('❌ Debe especificar --parcela-id o --todas')
        
        total_parcelas = parcelas.count()
        self.stdout.write(f'📊 Parcelas a procesar: {total_parcelas}\n')
        
        # Configuración
        meses_analizar = options['meses']
        forzar = options['forzar']
        con_imagenes = options['con_imagenes']
        
        # Estadísticas
        procesadas = 0
        con_cache = 0
        generadas = 0
        errores = 0
        
        # Procesar cada parcela
        for parcela in parcelas:
            self.stdout.write(f'\n📍 Procesando: {parcela.nombre}')
            self.stdout.write(f'   ID: {parcela.id} | Área: {parcela.area_hectareas:.2f} ha')
            
            try:
                # Obtener índices mensuales
                indices = IndiceMensual.objects.filter(
                    parcela=parcela
                ).order_by('-año', '-mes')[:meses_analizar]
                
                if not indices.exists():
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No hay datos para {parcela.nombre}'))
                    continue
                
                # Verificar caché
                ultimo_indice = indices.first()
                usar_cache = False
                
                if not forzar and ultimo_indice.analisis_gemini and ultimo_indice.fecha_analisis_gemini:
                    edad_cache = timezone.now() - ultimo_indice.fecha_analisis_gemini
                    if edad_cache < timedelta(days=30):
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Caché válido ({edad_cache.days} días)'))
                        usar_cache = True
                        con_cache += 1
                
                if not usar_cache:
                    # Preparar datos
                    parcela_data = {
                        'nombre': parcela.nombre,
                        'area_hectareas': float(parcela.area_hectareas) if parcela.area_hectareas else 0,
                        'tipo_cultivo': parcela.tipo_cultivo or 'No especificado',
                        'propietario': str(parcela.propietario) if parcela.propietario else 'No especificado'
                    }
                    
                    indices_data = []
                    imagenes_paths = []
                    
                    for idx in indices:
                        indices_data.append({
                            'periodo': f"{idx.año}-{idx.mes:02d}",
                            'ndvi_promedio': float(idx.ndvi_promedio) if idx.ndvi_promedio else None,
                            'ndmi_promedio': float(idx.ndmi_promedio) if idx.ndmi_promedio else None,
                            'savi_promedio': float(idx.savi_promedio) if idx.savi_promedio else None,
                            'nubosidad_promedio': float(idx.nubosidad_promedio) if idx.nubosidad_promedio else None,
                            'temperatura_promedio': float(idx.temperatura_promedio) if idx.temperatura_promedio else None,
                            'precipitacion_total': float(idx.precipitacion_total) if idx.precipitacion_total else None,
                            'calidad_datos': idx.calidad_datos or 'BUENA'
                        })
                        
                        # Recopilar imágenes si está habilitado
                        if con_imagenes:
                            if idx.imagen_ndvi and hasattr(idx.imagen_ndvi, 'path'):
                                try:
                                    if idx.imagen_ndvi.path:
                                        imagenes_paths.append(idx.imagen_ndvi.path)
                                except:
                                    pass
                    
                    # Generar análisis
                    self.stdout.write('   🤖 Generando análisis con Gemini AI...')
                    
                    analisis = gemini_service.generar_analisis_informe(
                        parcela_data=parcela_data,
                        indices_mensuales=indices_data,
                        imagenes_paths=imagenes_paths if imagenes_paths else None,
                        tipo_analisis='completo'
                    )
                    
                    if analisis and not analisis.get('error'):
                        # Guardar en caché
                        ultimo_indice.analisis_gemini = analisis
                        ultimo_indice.fecha_analisis_gemini = timezone.now()
                        ultimo_indice.save(update_fields=['analisis_gemini', 'fecha_analisis_gemini'])
                        
                        self.stdout.write(self.style.SUCCESS('   ✅ Análisis generado y guardado en caché'))
                        generadas += 1
                    else:
                        self.stdout.write(self.style.ERROR(f'   ❌ Error: {analisis.get("error", "Desconocido")}'))
                        errores += 1
                
                procesadas += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error procesando {parcela.nombre}: {str(e)}'))
                errores += 1
        
        # Resumen final
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE PROCESAMIENTO'))
        self.stdout.write('='*80)
        self.stdout.write(f'✅ Parcelas procesadas: {procesadas}/{total_parcelas}')
        self.stdout.write(f'💾 Desde caché: {con_cache}')
        self.stdout.write(f'🆕 Generadas nuevas: {generadas}')
        self.stdout.write(f'❌ Errores: {errores}')
        
        if generadas > 0:
            costo_estimado = generadas * 0.00135
            self.stdout.write(f'\n💰 Costo estimado: ${costo_estimado:.4f} USD')
        
        self.stdout.write('\n' + '='*80 + '\n')
