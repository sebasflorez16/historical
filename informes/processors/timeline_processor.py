"""
📊 Procesador de Timeline para AgroTech Histórico
Genera metadata enriquecida para visualización temporal de datos satelitales
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..models import IndiceMensual, Parcela
from ..analizadores.ndvi_analyzer import AnalizadorNDVI
from ..analizadores.ndmi_analyzer import AnalizadorNDMI
from ..analizadores.savi_analyzer import AnalizadorSAVI

logger = logging.getLogger(__name__)


class TimelineProcessor:
    """
    Procesador para generar datos enriquecidos del timeline visual
    """
    
    @staticmethod
    def generar_metadata_frame(indice_mensual: IndiceMensual, mes_anterior: Optional[IndiceMensual] = None) -> Dict[str, Any]:
        """
        Genera metadata completa para un frame del timeline
        
        Args:
            indice_mensual: Registro de IndiceMensual
            mes_anterior: Registro del mes anterior (para comparaciones)
            
        Returns:
            Dict con toda la información necesaria para renderizar el frame
        """
        try:
            # Datos básicos
            frame_data = {
                'id': indice_mensual.id,
                'año': indice_mensual.año,
                'mes': indice_mensual.mes,
                'periodo_texto': indice_mensual.periodo_texto,  # "Enero 2024"
                
                # Índices
                'ndvi': {
                    'promedio': float(indice_mensual.ndvi_promedio) if indice_mensual.ndvi_promedio else None,
                    'maximo': float(indice_mensual.ndvi_maximo) if indice_mensual.ndvi_maximo else None,
                    'minimo': float(indice_mensual.ndvi_minimo) if indice_mensual.ndvi_minimo else None,
                },
                'ndmi': {
                    'promedio': float(indice_mensual.ndmi_promedio) if indice_mensual.ndmi_promedio else None,
                    'maximo': float(indice_mensual.ndmi_maximo) if indice_mensual.ndmi_maximo else None,
                    'minimo': float(indice_mensual.ndmi_minimo) if indice_mensual.ndmi_minimo else None,
                },
                'savi': {
                    'promedio': float(indice_mensual.savi_promedio) if indice_mensual.savi_promedio else None,
                    'maximo': float(indice_mensual.savi_maximo) if indice_mensual.savi_maximo else None,
                    'minimo': float(indice_mensual.savi_minimo) if indice_mensual.savi_minimo else None,
                },
                
                # Clima
                'temperatura': float(indice_mensual.temperatura_promedio) if indice_mensual.temperatura_promedio else None,
                'precipitacion': float(indice_mensual.precipitacion_total) if indice_mensual.precipitacion_total else None,
                
                # URLs de imágenes
                'imagenes': {
                    'ndvi': indice_mensual.imagen_ndvi.url if indice_mensual.imagen_ndvi and indice_mensual.imagen_ndvi.name else None,
                    'ndmi': indice_mensual.imagen_ndmi.url if indice_mensual.imagen_ndmi and indice_mensual.imagen_ndmi.name else None,
                    'savi': indice_mensual.imagen_savi.url if indice_mensual.imagen_savi and indice_mensual.imagen_savi.name else None,
                },
                
                # Metadata de imagen
                'imagen_metadata': {
                    'view_id': indice_mensual.view_id_imagen,
                    'fecha_captura': indice_mensual.fecha_imagen.isoformat() if indice_mensual.fecha_imagen else None,
                    'nubosidad': float(indice_mensual.nubosidad_imagen) if indice_mensual.nubosidad_imagen else None,
                },
                
                # Calidad general
                'calidad_datos': indice_mensual.calidad_datos,
                'salud_vegetacion': indice_mensual.salud_vegetacion,  # Property del modelo
            }
            
            # Clasificación automática por índice usando analizadores
            frame_data['clasificaciones'] = TimelineProcessor._generar_clasificaciones(indice_mensual)
            
            # Comparación con mes anterior
            if mes_anterior:
                frame_data['comparacion'] = TimelineProcessor._comparar_con_mes_anterior(
                    indice_mensual, 
                    mes_anterior
                )
            else:
                frame_data['comparacion'] = None
                
            # Resumen ejecutivo para agricultores (lenguaje simple)
            frame_data['resumen_simple'] = TimelineProcessor._generar_resumen_simple(
                indice_mensual, 
                frame_data['clasificaciones']
            )
            
            return frame_data
            
        except Exception as e:
            logger.error(f"Error generando metadata para frame {indice_mensual.id}: {str(e)}")
            logger.exception(e)
            return {
                'error': True,
                'mensaje': 'Error procesando datos del mes',
                'id': indice_mensual.id if indice_mensual else None
            }
    
    @staticmethod
    def _generar_clasificaciones(indice: IndiceMensual) -> Dict[str, Dict[str, Any]]:
        """
        Genera clasificaciones automáticas usando los analizadores existentes
        """
        clasificaciones = {}
        
        # NDVI
        if indice.ndvi_promedio is not None:
            if indice.ndvi_promedio >= 0.85:
                clasificaciones['ndvi'] = {
                    'nivel': 'excelente',
                    'etiqueta': 'Vegetación Excelente',
                    'color': '#20c997',
                    'icono': '🌟',
                    'descripcion': 'Vegetación muy densa y saludable'
                }
            elif indice.ndvi_promedio >= 0.75:
                clasificaciones['ndvi'] = {
                    'nivel': 'muy_bueno',
                    'etiqueta': 'Muy Buena Salud',
                    'color': '#28a745',
                    'icono': '✅',
                    'descripcion': 'Vegetación vigorosa y productiva'
                }
            elif indice.ndvi_promedio >= 0.6:
                clasificaciones['ndvi'] = {
                    'nivel': 'bueno',
                    'etiqueta': 'Buena Salud',
                    'color': '#17a2b8',
                    'icono': '👍',
                    'descripcion': 'Vegetación saludable con buen desarrollo'
                }
            elif indice.ndvi_promedio >= 0.4:
                clasificaciones['ndvi'] = {
                    'nivel': 'moderado',
                    'etiqueta': 'Salud Moderada',
                    'color': '#ffc107',
                    'icono': '⚠️',
                    'descripcion': 'Vegetación en desarrollo o estrés leve'
                }
            else:
                clasificaciones['ndvi'] = {
                    'nivel': 'bajo',
                    'etiqueta': 'Estrés Detectado',
                    'color': '#dc3545',
                    'icono': '🔴',
                    'descripcion': 'Vegetación escasa o estrés severo'
                }
        
        # NDMI
        if indice.ndmi_promedio is not None:
            if indice.ndmi_promedio >= 0.35:
                clasificaciones['ndmi'] = {
                    'nivel': 'optimo',
                    'etiqueta': 'Humedad Óptima',
                    'color': '#007bff',
                    'icono': '💧',
                    'descripcion': 'Contenido de humedad excelente'
                }
            elif indice.ndmi_promedio >= 0.2:
                clasificaciones['ndmi'] = {
                    'nivel': 'bueno',
                    'etiqueta': 'Humedad Adecuada',
                    'color': '#17a2b8',
                    'icono': '💧',
                    'descripcion': 'Humedad dentro del rango normal'
                }
            elif indice.ndmi_promedio >= 0.1:
                clasificaciones['ndmi'] = {
                    'nivel': 'moderado',
                    'etiqueta': 'Humedad Moderada',
                    'color': '#ffc107',
                    'icono': '⚠️',
                    'descripcion': 'Posible estrés hídrico moderado'
                }
            else:
                clasificaciones['ndmi'] = {
                    'nivel': 'bajo',
                    'etiqueta': 'Estrés Hídrico',
                    'color': '#dc3545',
                    'icono': '🔥',
                    'descripcion': 'Déficit de agua detectado'
                }
        
        # SAVI
        if indice.savi_promedio is not None:
            if indice.savi_promedio >= 0.75:
                clasificaciones['savi'] = {
                    'nivel': 'excelente',
                    'etiqueta': 'Cobertura Excelente',
                    'color': '#20c997',
                    'icono': '🌾',
                    'descripcion': 'Cobertura vegetal muy densa'
                }
            elif indice.savi_promedio >= 0.65:
                clasificaciones['savi'] = {
                    'nivel': 'bueno',
                    'etiqueta': 'Buena Cobertura',
                    'color': '#28a745',
                    'icono': '🌱',
                    'descripcion': 'Buena densidad de vegetación'
                }
            elif indice.savi_promedio >= 0.5:
                clasificaciones['savi'] = {
                    'nivel': 'moderado',
                    'etiqueta': 'Cobertura Moderada',
                    'color': '#ffc107',
                    'icono': '🌿',
                    'descripcion': 'Cobertura en desarrollo'
                }
            else:
                clasificaciones['savi'] = {
                    'nivel': 'bajo',
                    'etiqueta': 'Cobertura Baja',
                    'color': '#dc3545',
                    'icono': '⚠️',
                    'descripcion': 'Cobertura vegetal escasa'
                }
        
        return clasificaciones
    
    @staticmethod
    def _comparar_con_mes_anterior(actual: IndiceMensual, anterior: IndiceMensual) -> Dict[str, Any]:
        """
        Compara los valores actuales con el mes anterior
        """
        comparacion = {}
        
        # NDVI
        if actual.ndvi_promedio and anterior.ndvi_promedio:
            diff_ndvi = actual.ndvi_promedio - anterior.ndvi_promedio
            porcentaje = (diff_ndvi / anterior.ndvi_promedio) * 100 if anterior.ndvi_promedio != 0 else 0
            
            comparacion['ndvi'] = {
                'diferencia': float(diff_ndvi),
                'porcentaje': float(porcentaje),
                'tendencia': 'mejora' if diff_ndvi > 0.02 else 'deterioro' if diff_ndvi < -0.02 else 'estable',
                'icono': '📈' if diff_ndvi > 0.02 else '📉' if diff_ndvi < -0.02 else '➡️'
            }
        
        # NDMI
        if actual.ndmi_promedio and anterior.ndmi_promedio:
            diff_ndmi = actual.ndmi_promedio - anterior.ndmi_promedio
            porcentaje = (diff_ndmi / anterior.ndmi_promedio) * 100 if anterior.ndmi_promedio != 0 else 0
            
            comparacion['ndmi'] = {
                'diferencia': float(diff_ndmi),
                'porcentaje': float(porcentaje),
                'tendencia': 'mejora' if diff_ndmi > 0.02 else 'deterioro' if diff_ndmi < -0.02 else 'estable',
                'icono': '📈' if diff_ndmi > 0.02 else '📉' if diff_ndmi < -0.02 else '➡️'
            }
        
        # SAVI
        if actual.savi_promedio and anterior.savi_promedio:
            diff_savi = actual.savi_promedio - anterior.savi_promedio
            porcentaje = (diff_savi / anterior.savi_promedio) * 100 if anterior.savi_promedio != 0 else 0
            
            comparacion['savi'] = {
                'diferencia': float(diff_savi),
                'porcentaje': float(porcentaje),
                'tendencia': 'mejora' if diff_savi > 0.02 else 'deterioro' if diff_savi < -0.02 else 'estable',
                'icono': '📈' if diff_savi > 0.02 else '📉' if diff_savi < -0.02 else '➡️'
            }
        
        return comparacion
    
    @staticmethod
    def _generar_resumen_simple(indice: IndiceMensual, clasificaciones: Dict[str, Dict]) -> str:
        """
        Genera un resumen en lenguaje simple para agricultores
        """
        resumen_partes = []
        
        # Estado principal basado en NDVI
        if 'ndvi' in clasificaciones:
            ndvi_class = clasificaciones['ndvi']
            resumen_partes.append(f"{ndvi_class['icono']} {ndvi_class['etiqueta']}")
        
        # Estado de humedad
        if 'ndmi' in clasificaciones:
            ndmi_class = clasificaciones['ndmi']
            resumen_partes.append(f"{ndmi_class['icono']} {ndmi_class['etiqueta']}")
        
        # Información climática
        if indice.temperatura_promedio:
            resumen_partes.append(f"🌡️ {indice.temperatura_promedio:.1f}°C")
        
        if indice.precipitacion_total:
            resumen_partes.append(f"🌧️ {indice.precipitacion_total:.1f}mm")
        
        return " • ".join(resumen_partes) if resumen_partes else "Datos en análisis"
    
    @staticmethod
    def generar_timeline_completo(parcela: Parcela, fecha_inicio: Optional[datetime] = None, 
                                  fecha_fin: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Genera el timeline completo de una parcela con todos los frames
        
        Args:
            parcela: Parcela a analizar
            fecha_inicio: Fecha de inicio del período (opcional)
            fecha_fin: Fecha de fin del período (opcional)
            
        Returns:
            Dict con información del timeline y lista de frames
        """
        try:
            # Query base
            query = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
            
            # Filtros opcionales por fecha
            if fecha_inicio:
                query = query.filter(
                    año__gte=fecha_inicio.year
                ).exclude(
                    año=fecha_inicio.year, 
                    mes__lt=fecha_inicio.month
                )
            
            if fecha_fin:
                query = query.filter(
                    año__lte=fecha_fin.year
                ).exclude(
                    año=fecha_fin.year, 
                    mes__gt=fecha_fin.month
                )
            
            indices = list(query)
            
            if not indices:
                return {
                    'parcela': {
                        'id': parcela.id,
                        'nombre': parcela.nombre,
                        'tipo_cultivo': parcela.tipo_cultivo,
                    },
                    'total_frames': 0,
                    'frames': [],
                    'mensaje': 'No hay datos históricos disponibles para esta parcela'
                }
            
            # Generar frames con metadata enriquecida
            frames = []
            for i, indice in enumerate(indices):
                mes_anterior = indices[i - 1] if i > 0 else None
                frame = TimelineProcessor.generar_metadata_frame(indice, mes_anterior)
                frames.append(frame)
            
            # Estadísticas generales del timeline
            return {
                'parcela': {
                    'id': parcela.id,
                    'nombre': parcela.nombre,
                    'tipo_cultivo': parcela.tipo_cultivo,
                    'area_hectareas': float(parcela.area_hectareas),
                    'propietario': parcela.propietario,
                },
                'total_frames': len(frames),
                'fecha_inicio': f"{indices[0].año}-{indices[0].mes:02d}",
                'fecha_fin': f"{indices[-1].año}-{indices[-1].mes:02d}",
                'frames': frames,
                'estadisticas': {
                    'ndvi_promedio': sum(f['ndvi']['promedio'] for f in frames if f.get('ndvi', {}).get('promedio')) / len([f for f in frames if f.get('ndvi', {}).get('promedio')]) if any(f.get('ndvi', {}).get('promedio') for f in frames) else None,
                    'ndmi_promedio': sum(f['ndmi']['promedio'] for f in frames if f.get('ndmi', {}).get('promedio')) / len([f for f in frames if f.get('ndmi', {}).get('promedio')]) if any(f.get('ndmi', {}).get('promedio') for f in frames) else None,
                    'savi_promedio': sum(f['savi']['promedio'] for f in frames if f.get('savi', {}).get('promedio')) / len([f for f in frames if f.get('savi', {}).get('promedio')]) if any(f.get('savi', {}).get('promedio') for f in frames) else None,
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando timeline para parcela {parcela.id}: {str(e)}")
            logger.exception(e)
            return {
                'error': True,
                'mensaje': f'Error generando timeline: {str(e)}',
                'parcela': {'id': parcela.id, 'nombre': parcela.nombre}
            }
