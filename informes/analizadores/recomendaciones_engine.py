"""
Motor de Generación de Recomendaciones Agronómicas
Genera consejos accionables basados en análisis de índices
"""
from typing import Dict, List, Any
from datetime import datetime


class GeneradorRecomendaciones:
    """
    Genera recomendaciones agronómicas priorizadas basadas en:
    - Estados de índices (NDVI, NDMI, SAVI)
    - Tendencias temporales
    - Alertas detectadas
    - Tipo de cultivo
    - Época del año
    """
    
    def __init__(self, tipo_cultivo: str = "General", epoca_año: str = None):
        self.tipo_cultivo = tipo_cultivo
        self.epoca_año = epoca_año or self._determinar_epoca()
    
    def generar_recomendaciones(self, analisis_ndvi: Dict, analisis_ndmi: Dict,
                               analisis_savi: Dict = None, 
                               tendencias: Dict = None) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones basadas en todos los análisis
        
        Returns:
            Lista de recomendaciones ordenadas por prioridad
        """
        recomendaciones = []
        
        # Recomendaciones basadas en NDVI (salud vegetal)
        recomendaciones.extend(self._recomendar_por_ndvi(analisis_ndvi))
        
        # Recomendaciones basadas en NDMI (humedad)
        recomendaciones.extend(self._recomendar_por_ndmi(analisis_ndmi))
        
        # Recomendaciones basadas en SAVI (cobertura)
        if analisis_savi:
            recomendaciones.extend(self._recomendar_por_savi(analisis_savi))
        
        # Recomendaciones basadas en tendencias
        if tendencias:
            recomendaciones.extend(self._recomendar_por_tendencias(tendencias))
        
        # Recomendaciones estacionales
        recomendaciones.extend(self._recomendar_por_epoca())
        
        # Ordenar por prioridad
        recomendaciones_ordenadas = self._priorizar_recomendaciones(recomendaciones)
        
        # Eliminar duplicados
        recomendaciones_unicas = self._eliminar_duplicados(recomendaciones_ordenadas)
        
        # Limitar a top 10
        return recomendaciones_unicas[:10]
    
    def _recomendar_por_ndvi(self, analisis: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en NDVI"""
        recomendaciones = []
        
        if not analisis or 'estadisticas' not in analisis:
            return recomendaciones
        
        promedio = analisis['estadisticas'].get('promedio', 0)
        estado = analisis.get('estado', {}).get('nivel', '')
        tendencia = analisis.get('tendencia', {}).get('direccion', '')
        
        # CRÍTICO: NDVI muy bajo
        if promedio < 0.3:
            recomendaciones.append({
                'prioridad': 'alta',
                'categoria': 'salud_vegetal',
                'titulo': 'Intervención Inmediata Requerida',
                'descripcion_tecnica': 'NDVI crítico (<0.30) indica estrés severo o cultivo en estado deficiente. '
                                      'Realizar diagnóstico inmediato de factores bióticos y abióticos.',
                'descripcion_simple': 'Sus plantas están en muy mal estado y necesitan atención urgente.',
                'acciones': [
                    'Inspección física inmediata del cultivo',
                    'Análisis de suelo (NPK, pH, materia orgánica)',
                    'Verificar sistema de riego y drenaje',
                    'Descartar plagas y enfermedades',
                    'Considerar consultoría agronómica profesional'
                ],
                'impacto_esperado': 'Crítico - Requiere acción en 24-48 horas',
                'costo_estimado': 'Alto',
                'tiempo_implementacion': 'Inmediato'
            })
        
        # BAJO: NDVI bajo
        elif promedio < 0.4:
            recomendaciones.append({
                'prioridad': 'alta',
                'categoria': 'salud_vegetal',
                'titulo': 'Mejorar Vigor Vegetativo',
                'descripcion_tecnica': f'NDVI de {promedio:.2f} sugiere desarrollo vegetativo subóptimo. '
                                      'Evaluar nutrición, especialmente nitrógeno, y condiciones hídricas.',
                'descripcion_simple': 'Sus plantas están débiles y necesitan más nutrientes y agua.',
                'acciones': [
                    f'Aplicar fertilización nitrogenada (Urea 46% o equivalente)',
                    'Aumentar frecuencia de riego',
                    'Aplicar abono foliar para respuesta rápida',
                    'Monitorear evolución cada 15 días'
                ],
                'impacto_esperado': 'Alto - Mejora en 3-4 semanas',
                'costo_estimado': 'Medio',
                'tiempo_implementacion': '1-2 semanas'
            })
        
        # MODERADO: NDVI moderado con tendencia descendente
        elif promedio < 0.6 and 'descendente' in tendencia:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'mantenimiento',
                'titulo': 'Prevenir Deterioro de Salud Vegetal',
                'descripcion_tecnica': f'NDVI de {promedio:.2f} con tendencia descendente requiere ajustes preventivos '
                                      'en manejo para evitar declive progresivo.',
                'descripcion_simple': 'Sus plantas están perdiendo fuerza, mejor actuar ahora antes que empeore.',
                'acciones': [
                    'Revisar plan de fertilización actual',
                    'Asegurar riego adecuado',
                    'Aplicar correctivos según análisis de suelo',
                    'Monitoreo quincenal de evolución'
                ],
                'impacto_esperado': 'Medio - Estabilización en 2-3 semanas',
                'costo_estimado': 'Medio',
                'tiempo_implementacion': '1-2 semanas'
            })
        
        # BUENO: Mantener
        elif promedio >= 0.6 and promedio < 0.8:
            recomendaciones.append({
                'prioridad': 'baja',
                'categoria': 'mantenimiento',
                'titulo': 'Mantener Prácticas Actuales',
                'descripcion_tecnica': f'NDVI de {promedio:.2f} indica condiciones adecuadas. '
                                      'Mantener régimen actual de manejo.',
                'descripcion_simple': '¡Buen trabajo! Sus plantas están saludables, siga así.',
                'acciones': [
                    'Continuar con plan de fertilización actual',
                    'Mantener frecuencia de riego',
                    'Monitoreo mensual de rutina',
                    'Aplicar fertilización de mantenimiento según cronograma'
                ],
                'impacto_esperado': 'Mantenimiento del estado actual',
                'costo_estimado': 'Bajo',
                'tiempo_implementacion': 'Continuo'
            })
        
        # EXCELENTE: Optimizar
        elif promedio >= 0.8:
            recomendaciones.append({
                'prioridad': 'baja',
                'categoria': 'optimizacion',
                'titulo': 'Optimizar para Máxima Productividad',
                'descripcion_tecnica': f'NDVI excelente ({promedio:.2f}). Enfocar en optimización de productividad '
                                      'y calidad de cosecha.',
                'descripcion_simple': '¡Excelente! Sus plantas están en óptimas condiciones.',
                'acciones': [
                    'Preparar para cosecha en momento óptimo',
                    'Aplicar fertilización de llenado de grano/fruto',
                    'Monitoreo de plagas y enfermedades',
                    'Documentar prácticas exitosas para replicar'
                ],
                'impacto_esperado': 'Maximización de rendimiento',
                'costo_estimado': 'Bajo-Medio',
                'tiempo_implementacion': 'Según fenología del cultivo'
            })
        
        return recomendaciones
    
    def _recomendar_por_ndmi(self, analisis: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en NDMI"""
        recomendaciones = []
        
        if not analisis or 'estadisticas' not in analisis:
            return recomendaciones
        
        promedio = analisis['estadisticas'].get('promedio', 0)
        tendencia = analisis.get('tendencia', {}).get('direccion', '')
        
        # ESTRÉS HÍDRICO SEVERO
        if promedio < -0.2:
            recomendaciones.append({
                'prioridad': 'alta',
                'categoria': 'riego',
                'titulo': 'Estrés Hídrico Severo - Acción Urgente',
                'descripcion_tecnica': f'NDMI de {promedio:.2f} indica déficit hídrico crítico. '
                                      'Riego de emergencia requerido para evitar pérdidas.',
                'descripcion_simple': 'Sus plantas tienen mucha sed. Necesitan agua urgente.',
                'acciones': [
                    'Riego inmediato (aumentar 30-40% del volumen actual)',
                    'Riego diario hasta recuperación',
                    'Verificar funcionamiento del sistema de riego',
                    'Aplicar mulch o cobertura para retener humedad',
                    'Monitoreo diario de recuperación'
                ],
                'impacto_esperado': 'Crítico - Recuperación en 3-7 días',
                'costo_estimado': 'Alto',
                'tiempo_implementacion': 'Inmediato'
            })
        
        # ESTRÉS HÍDRICO MODERADO
        elif promedio < 0.1:
            recomendaciones.append({
                'prioridad': 'alta',
                'categoria': 'riego',
                'titulo': 'Aumentar Frecuencia/Volumen de Riego',
                'descripcion_tecnica': f'NDMI de {promedio:.2f} sugiere contenido hídrico subóptimo. '
                                      'Ajustar régimen de riego para prevenir estrés.',
                'descripcion_simple': 'Sus plantas necesitan más agua. Es momento de regar más seguido.',
                'acciones': [
                    'Aumentar frecuencia de riego (20-30% más)',
                    'Regar en horas frescas (madrugada/tarde)',
                    'Verificar uniformidad del riego',
                    'Considerar sistema de riego tecnificado',
                    'Instalar sensores de humedad de suelo (opcional)'
                ],
                'impacto_esperado': 'Alto - Mejora en 1-2 semanas',
                'costo_estimado': 'Medio',
                'tiempo_implementacion': '1-3 días'
            })
        
        # TENDENCIA DESCENDENTE (pérdida de humedad)
        elif 'descendente' in tendencia:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'riego',
                'titulo': 'Preparar Plan de Riego para Temporada Seca',
                'descripcion_tecnica': 'Tendencia descendente en NDMI indica consumo hídrico activo o inicio de período seco. '
                                      'Preparar estrategia de riego preventiva.',
                'descripcion_simple': 'El agua está bajando. Prepare un plan para la temporada seca que viene.',
                'acciones': [
                    'Revisar y mantener sistema de riego',
                    'Programar riegos más frecuentes',
                    'Aplicar mulch orgánico para conservar humedad',
                    'Monitorear pronóstico climático',
                    'Considerar cosecha de agua si es posible'
                ],
                'impacto_esperado': 'Prevención de estrés futuro',
                'costo_estimado': 'Bajo-Medio',
                'tiempo_implementacion': '1-2 semanas'
            })
        
        # SATURACIÓN (demasiada humedad)
        elif promedio > 0.5:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'drenaje',
                'titulo': 'Alta Humedad - Verificar Drenaje',
                'descripcion_tecnica': f'NDMI muy alto ({promedio:.2f}) puede indicar exceso hídrico o saturación. '
                                      'Verificar drenaje para evitar anoxia radicular.',
                'descripcion_simple': 'Hay mucha agua. Revise que el agua no se esté acumulando.',
                'acciones': [
                    'Reducir frecuencia de riego',
                    'Verificar sistema de drenaje',
                    'Evitar riego durante períodos lluviosos',
                    'Construir/mejorar canales de drenaje si necesario',
                    'Monitorear salud radicular'
                ],
                'impacto_esperado': 'Prevención de problemas radiculares',
                'costo_estimado': 'Variable',
                'tiempo_implementacion': '1-4 semanas'
            })
        
        return recomendaciones
    
    def _recomendar_por_savi(self, analisis: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en SAVI"""
        recomendaciones = []
        
        if not analisis or 'estadisticas' not in analisis:
            return recomendaciones
        
        promedio = analisis['estadisticas'].get('promedio', 0)
        
        # BAJA COBERTURA
        if promedio < 0.3:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'manejo_cultivo',
                'titulo': 'Baja Cobertura Vegetal - Evaluar Densidad',
                'descripcion_tecnica': f'SAVI de {promedio:.2f} indica baja cobertura vegetal y alto suelo expuesto. '
                                      'Evaluar si corresponde a etapa fenológica o densidad de siembra inadecuada.',
                'descripcion_simple': 'Hay mucho espacio vacío entre las plantas. Tal vez están muy separadas.',
                'acciones': [
                    'Evaluar densidad de siembra vs recomendada',
                    'Si es cultivo joven, esperar desarrollo natural',
                    'Considerar resiembra en espacios vacíos',
                    'Aplicar mulch en suelo expuesto',
                    'Controlar malezas competidoras'
                ],
                'impacto_esperado': 'Mejora gradual en 4-8 semanas',
                'costo_estimado': 'Variable',
                'tiempo_implementacion': '1-2 semanas'
            })
        
        return recomendaciones
    
    def _recomendar_por_tendencias(self, tendencias: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en análisis de tendencias"""
        recomendaciones = []
        
        # Anomalías detectadas
        anomalias = tendencias.get('anomalias', [])
        if len(anomalias) > 0:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'monitoreo',
                'titulo': f'{len(anomalias)} Anomalía(s) Detectada(s) - Investigar Causas',
                'descripcion_tecnica': 'Se detectaron valores fuera del patrón normal. '
                                      'Investigar factores causales en esos períodos.',
                'descripcion_simple': 'Hubo momentos donde los valores fueron muy diferentes a lo normal.',
                'acciones': [
                    'Revisar registros de manejo en esos períodos',
                    'Correlacionar con eventos climáticos',
                    'Identificar patrones repetibles',
                    'Ajustar prácticas si se identifican problemas'
                ],
                'impacto_esperado': 'Mejor comprensión del sistema',
                'costo_estimado': 'Ninguno (análisis)',
                'tiempo_implementacion': '1-2 días'
            })
        
        return recomendaciones
    
    def _recomendar_por_epoca(self) -> List[Dict]:
        """Genera recomendaciones según época del año"""
        recomendaciones = []
        
        mes_actual = datetime.now().month
        
        # Recomendaciones para temporada seca (Diciembre-Marzo en Colombia)
        if mes_actual in [12, 1, 2, 3]:
            recomendaciones.append({
                'prioridad': 'media',
                'categoria': 'estacional',
                'titulo': 'Temporada Seca - Reforzar Plan Hídrico',
                'descripcion_tecnica': 'Época seca requiere atención especial al manejo hídrico y prevención de estrés.',
                'descripcion_simple': 'Es temporada seca. Asegúrese de que sus plantas tengan suficiente agua.',
                'acciones': [
                    'Aumentar frecuencia de riego',
                    'Monitorear humedad del suelo',
                    'Aplicar mulch para retener humedad',
                    'Revisar pronósticos climáticos',
                    'Preparar plan de contingencia'
                ],
                'impacto_esperado': 'Prevención de estrés hídrico',
                'costo_estimado': 'Bajo-Medio',
                'tiempo_implementacion': 'Continuo durante época'
            })
        
        # Recomendaciones para temporada lluviosa (Abril-Noviembre)
        elif mes_actual in [4, 5, 6, 7, 8, 9, 10, 11]:
            recomendaciones.append({
                'prioridad': 'baja',
                'categoria': 'estacional',
                'titulo': 'Temporada de Lluvias - Monitoreo de Enfermedades',
                'descripcion_tecnica': 'Alta humedad ambiental favorece desarrollo de patógenos. '
                                      'Monitoreo preventivo de enfermedades foliares.',
                'descripcion_simple': 'Llueve mucho. Revise que las plantas no tengan hongos o enfermedades.',
                'acciones': [
                    'Inspección semanal de síntomas de enfermedades',
                    'Asegurar buen drenaje del cultivo',
                    'Aplicar fungicidas preventivos si necesario',
                    'Evitar riego durante lluvias intensas',
                    'Mantener ventilación en cultivos densos'
                ],
                'impacto_esperado': 'Prevención de enfermedades',
                'costo_estimado': 'Bajo',
                'tiempo_implementacion': 'Continuo durante época'
            })
        
        return recomendaciones
    
    def _priorizar_recomendaciones(self, recomendaciones: List[Dict]) -> List[Dict]:
        """Ordena recomendaciones por prioridad"""
        orden_prioridad = {'alta': 1, 'media': 2, 'baja': 3}
        return sorted(recomendaciones, 
                     key=lambda x: (orden_prioridad.get(x['prioridad'], 99), x['titulo']))
    
    def _eliminar_duplicados(self, recomendaciones: List[Dict]) -> List[Dict]:
        """Elimina recomendaciones duplicadas"""
        vistas = set()
        unicas = []
        
        for rec in recomendaciones:
            titulo = rec['titulo']
            if titulo not in vistas:
                vistas.add(titulo)
                unicas.append(rec)
        
        return unicas
    
    def _determinar_epoca(self) -> str:
        """Determina época del año"""
        mes = datetime.now().month
        if mes in [12, 1, 2, 3]:
            return 'seca'
        else:
            return 'lluviosa'
