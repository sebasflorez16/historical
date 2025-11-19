"""
Analizador NDVI - Normalized Difference Vegetation Index
Interpreta salud vegetal basado en umbrales agronómicos científicos
"""
import statistics
from typing import Dict, List, Any, Optional


class AnalizadorNDVI:
    """
    Analiza datos de NDVI y genera interpretaciones técnicas y simples
    
    Umbrales científicos NDVI:
    - 0.0 - 0.2: Suelo desnudo, agua, construcciones
    - 0.2 - 0.4: Vegetación escasa o bajo estrés severo
    - 0.4 - 0.6: Vegetación moderada
    - 0.6 - 0.8: Vegetación vigorosa (ideal)
    - 0.8 - 1.0: Vegetación muy densa
    """
    
    # Umbrales científicos
    UMBRAL_CRITICO = 0.3
    UMBRAL_BAJO = 0.4
    UMBRAL_MODERADO = 0.6
    UMBRAL_BUENO = 0.75
    UMBRAL_EXCELENTE = 0.85
    
    def __init__(self, tipo_cultivo: str = "General"):
        """
        Inicializa el analizador con el tipo de cultivo
        
        Args:
            tipo_cultivo: Tipo de cultivo para ajustar umbrales
        """
        self.tipo_cultivo = tipo_cultivo
        self.ajustar_umbrales_por_cultivo()
    
    def ajustar_umbrales_por_cultivo(self):
        """Ajusta umbrales según el tipo de cultivo"""
        ajustes_cultivos = {
            'Café': {'moderado': 0.65, 'bueno': 0.78},
            'Cacao': {'moderado': 0.62, 'bueno': 0.75},
            'Arroz': {'moderado': 0.60, 'bueno': 0.72},
            'Caña de Azúcar': {'moderado': 0.65, 'bueno': 0.80},
            'Plátano': {'moderado': 0.70, 'bueno': 0.82},
        }
        
        if self.tipo_cultivo in ajustes_cultivos:
            ajuste = ajustes_cultivos[self.tipo_cultivo]
            self.UMBRAL_MODERADO = ajuste.get('moderado', self.UMBRAL_MODERADO)
            self.UMBRAL_BUENO = ajuste.get('bueno', self.UMBRAL_BUENO)
    
    def analizar(self, datos_ndvi: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza una serie temporal de datos NDVI
        
        Args:
            datos_ndvi: Lista de diccionarios con datos mensuales
                       [{'mes': '2024-01', 'ndvi': 0.75}, ...]
        
        Returns:
            Diccionario con análisis completo
        """
        if not datos_ndvi:
            return self._resultado_sin_datos()
        
        # Extraer valores NDVI
        valores = [d.get('ndvi', 0) for d in datos_ndvi if d.get('ndvi') is not None]
        
        if not valores:
            return self._resultado_sin_datos()
        
        # Calcular estadísticas
        promedio = statistics.mean(valores)
        mediana = statistics.median(valores)
        minimo = min(valores)
        maximo = max(valores)
        desv_std = statistics.stdev(valores) if len(valores) > 1 else 0
        
        # Analizar tendencia
        tendencia = self._calcular_tendencia(valores)
        
        # Detectar anomalías
        anomalias = self._detectar_anomalias(datos_ndvi, promedio, desv_std)
        
        # Clasificar estado
        estado = self._clasificar_estado(promedio)
        
        # Generar interpretaciones
        interpretacion_tecnica = self._generar_interpretacion_tecnica(
            promedio, desv_std, tendencia, estado, maximo, minimo
        )
        
        interpretacion_simple = self._generar_interpretacion_simple(
            promedio, tendencia, estado
        )
        
        # Generar alertas
        alertas = self._generar_alertas(promedio, minimo, tendencia, anomalias)
        
        return {
            'indice': 'NDVI',
            'nombre': 'Índice de Vegetación Normalizado',
            'estadisticas': {
                'promedio': round(promedio, 3),
                'mediana': round(mediana, 3),
                'minimo': round(minimo, 3),
                'maximo': round(maximo, 3),
                'desviacion_estandar': round(desv_std, 3),
                'variabilidad': self._clasificar_variabilidad(desv_std)
            },
            'estado': estado,
            'tendencia': tendencia,
            'interpretacion_tecnica': interpretacion_tecnica,
            'interpretacion_simple': interpretacion_simple,
            'anomalias': anomalias,
            'alertas': alertas,
            'puntuacion': self._calcular_puntuacion(promedio, tendencia),
            'cobertura_estimada': self._estimar_cobertura(promedio),
            'salud_vegetal': self._evaluar_salud(promedio)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula la tendencia temporal de los datos"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'descripcion': 'Datos insuficientes'}
        
        # Calcular tendencia lineal simple
        n = len(valores)
        suma_cambios = sum(valores[i] - valores[i-1] for i in range(1, n))
        cambio_promedio = suma_cambios / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / valores[0] * 100 if valores[0] != 0 else 0
        
        # Clasificar tendencia
        if abs(cambio_promedio) < 0.02:
            direccion = 'estable'
            descripcion = 'Valores estables'
        elif cambio_promedio > 0.05:
            direccion = 'ascendente_fuerte'
            descripcion = 'Tendencia ascendente pronunciada'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Tendencia ascendente'
        elif cambio_promedio < -0.05:
            direccion = 'descendente_fuerte'
            descripcion = 'Tendencia descendente pronunciada'
        else:
            direccion = 'descendente'
            descripcion = 'Tendencia descendente'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _detectar_anomalias(self, datos: List[Dict], promedio: float, desv_std: float) -> List[Dict]:
        """Detecta meses con valores anómalos"""
        anomalias = []
        
        for dato in datos:
            ndvi = dato.get('ndvi')
            if ndvi is None:
                continue
            
            # Anomalía: valor fuera de 2 desviaciones estándar
            if abs(ndvi - promedio) > 2 * desv_std:
                tipo = 'caida_brusca' if ndvi < promedio else 'pico_inusual'
                anomalias.append({
                    'periodo': dato.get('mes', 'Desconocido'),
                    'valor': round(ndvi, 3),
                    'tipo': tipo,
                    'desviacion': round(abs(ndvi - promedio) / desv_std, 1),
                    'descripcion': f"NDVI {'muy bajo' if tipo == 'caida_brusca' else 'muy alto'} ({ndvi:.2f})"
                })
        
        return anomalias
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica el estado general basado en el promedio"""
        if promedio < self.UMBRAL_CRITICO:
            return {
                'nivel': 'critico',
                'etiqueta': 'Crítico',
                'color': '#dc3545',
                'icono': '🚨'
            }
        elif promedio < self.UMBRAL_BAJO:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Bajo',
                'color': '#fd7e14',
                'icono': '⚠️'
            }
        elif promedio < self.UMBRAL_MODERADO:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Moderado',
                'color': '#ffc107',
                'icono': '📊'
            }
        elif promedio < self.UMBRAL_BUENO:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Bueno',
                'color': '#28a745',
                'icono': '✅'
            }
        elif promedio < self.UMBRAL_EXCELENTE:
            return {
                'nivel': 'muy_bueno',
                'etiqueta': 'Muy Bueno',
                'color': '#20c997',
                'icono': '🌟'
            }
        else:
            return {
                'nivel': 'excelente',
                'etiqueta': 'Excelente',
                'color': '#17a2b8',
                'icono': '💚'
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float, 
                                       tendencia: Dict, estado: Dict,
                                       maximo: float, minimo: float) -> str:
        """Genera interpretación para agrónomos"""
        
        # Estimar LAI y cobertura
        lai_estimado = self._estimar_lai(promedio)
        cobertura = self._estimar_cobertura(promedio)
        
        interpretacion = f"""
<strong>Análisis NDVI - {self.tipo_cultivo}</strong><br><br>

El índice NDVI promedio de <strong>{promedio:.3f}</strong> indica un estado <strong>{estado['etiqueta'].lower()}</strong> 
de la vegetación, clasificado como <em>"{self._obtener_clasificacion_tecnica(promedio)}"</em>.<br><br>

<strong>Parámetros Biofísicos:</strong><br>
• Cobertura vegetal estimada: <strong>{cobertura}%</strong><br>
• LAI (Leaf Area Index) aproximado: <strong>{lai_estimado:.1f} m²/m²</strong><br>
• Variabilidad espacial: <strong>{self._clasificar_variabilidad(desv_std)}</strong> (σ={desv_std:.3f})<br>
• Rango observado: {minimo:.3f} - {maximo:.3f}<br><br>

<strong>Tendencia Temporal:</strong><br>
{tendencia['descripcion']} con cambio de <strong>{tendencia['cambio_porcentual']:+.1f}%</strong> 
en el período analizado. {self._interpretar_tendencia_tecnica(tendencia)}<br><br>

<strong>Interpretación Agronómica:</strong><br>
{self._generar_conclusion_tecnica(promedio, tendencia, desv_std)}
"""
        
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Genera interpretación para usuarios sin conocimientos técnicos"""
        
        # Analogías simples
        analogia = self._obtener_analogia_simple(promedio)
        
        interpretacion = f"""
<strong>¿Cómo está mi cultivo?</strong><br><br>

{estado['icono']} Su cultivo está en estado <strong>{estado['etiqueta'].lower()}</strong>. {analogia}<br><br>

<strong>En palabras sencillas:</strong><br>
{self._explicar_simple(promedio, tendencia)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia)}
"""
        
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, minimo: float, 
                        tendencia: Dict, anomalias: List) -> List[Dict]:
        """Genera alertas accionables"""
        alertas = []
        
        # Alerta crítica: NDVI muy bajo
        if promedio < self.UMBRAL_CRITICO:
            alertas.append({
                'tipo': 'critico',
                'prioridad': 'alta',
                'icono': '🚨',
                'titulo': 'Salud Vegetal Crítica',
                'mensaje': f'El NDVI promedio ({promedio:.2f}) está por debajo del umbral saludable.',
                'accion': 'Requiere intervención inmediata'
            })
        
        # Alerta: Tendencia descendente fuerte
        if tendencia['direccion'] == 'descendente_fuerte':
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'alta',
                'icono': '⚠️',
                'titulo': 'Tendencia Negativa Detectada',
                'mensaje': f"El NDVI ha disminuido {abs(tendencia['cambio_porcentual']):.1f}% en el período analizado.",
                'accion': 'Analizar causas: sequía, plagas, nutrientes'
            })
        
        # Alerta: Valor mínimo muy bajo
        if minimo < self.UMBRAL_BAJO:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '📉',
                'titulo': 'Valor Mínimo Bajo Detectado',
                'mensaje': f'Se registró un valor mínimo de {minimo:.2f}, indicando posible estrés temporal.',
                'accion': 'Revisar condiciones en ese período'
            })
        
        # Alerta: Anomalías detectadas
        if len(anomalias) > 0:
            alertas.append({
                'tipo': 'info',
                'prioridad': 'media',
                'icono': '📊',
                'titulo': f'{len(anomalias)} Anomalía(s) Detectada(s)',
                'mensaje': 'Se detectaron valores fuera del patrón normal.',
                'accion': 'Revisar períodos anómalos en el informe'
            })
        
        return alertas
    
    # Métodos auxiliares
    
    def _resultado_sin_datos(self) -> Dict:
        """Retorna resultado cuando no hay datos"""
        return {
            'indice': 'NDVI',
            'nombre': 'Índice de Vegetación Normalizado',
            'error': 'No hay datos disponibles para analizar',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': '❓'},
            'interpretacion_tecnica': 'No hay datos NDVI disponibles para el período seleccionado.',
            'interpretacion_simple': 'Aún no tenemos información sobre tu cultivo.',
            'alertas': []
        }
    
    def _clasificar_variabilidad(self, desv_std: float) -> str:
        """Clasifica la variabilidad espacial"""
        if desv_std < 0.05:
            return "Muy baja (manejo homogéneo)"
        elif desv_std < 0.10:
            return "Baja (variación normal)"
        elif desv_std < 0.15:
            return "Moderada"
        else:
            return "Alta (manejo heterogéneo o estrés localizado)"
    
    def _estimar_cobertura(self, ndvi: float) -> int:
        """Estima cobertura vegetal en porcentaje"""
        if ndvi < 0.2:
            return 10
        elif ndvi < 0.4:
            return 40
        elif ndvi < 0.6:
            return 65
        elif ndvi < 0.8:
            return 85
        else:
            return 95
    
    def _estimar_lai(self, ndvi: float) -> float:
        """Estima LAI (Leaf Area Index) desde NDVI"""
        # Fórmula empírica: LAI ≈ -ln((0.69 - NDVI) / 0.59) / 0.91
        try:
            if ndvi < 0.1:
                return 0.5
            lai = -1 * (0.69 - ndvi) / 0.59
            lai = max(0.5, min(8.0, lai * 6))  # Limitar entre 0.5 y 8
            return lai
        except:
            return 2.0
    
    def _obtener_clasificacion_tecnica(self, ndvi: float) -> str:
        """Clasificación técnica del NDVI"""
        if ndvi < 0.2:
            return "suelo desnudo o agua"
        elif ndvi < 0.4:
            return "vegetación escasa o bajo estrés"
        elif ndvi < 0.6:
            return "vegetación moderada"
        elif ndvi < 0.8:
            return "vegetación vigorosa"
        else:
            return "vegetación muy densa"
    
    def _interpretar_tendencia_tecnica(self, tendencia: Dict) -> str:
        """Interpretación técnica de la tendencia"""
        direccion = tendencia['direccion']
        
        if 'ascendente' in direccion:
            return "Esto sugiere desarrollo vegetativo activo, posiblemente asociado a fenología del cultivo o respuesta a manejo agronómico."
        elif 'descendente' in direccion:
            return "Puede indicar senescencia foliar, estrés ambiental o manejo inadecuado. Requiere análisis de factores causales."
        else:
            return "Indica estabilidad temporal, común en cultivos perennes fuera de etapas críticas."
    
    def _generar_conclusion_tecnica(self, promedio: float, tendencia: Dict, desv_std: float) -> str:
        """Genera conclusión técnica"""
        if promedio >= self.UMBRAL_BUENO:
            return f"El cultivo presenta condiciones óptimas de vigor vegetativo. La {self._clasificar_variabilidad(desv_std).lower()} sugiere manejo uniforme. Mantener prácticas actuales."
        elif promedio >= self.UMBRAL_MODERADO:
            return f"Condiciones aceptables pero con margen de mejora. Evaluar nutrición, manejo hídrico y densidad de siembra para optimizar productividad."
        else:
            return f"Requiere intervención agronómica. Priorizar: 1) diagnóstico de estrés biótico/abiótico, 2) ajuste de riego/fertilización, 3) monitoreo intensivo."
    
    def _obtener_analogia_simple(self, ndvi: float) -> str:
        """Genera analogía simple para usuarios comunes"""
        if ndvi >= 0.75:
            return "Como un jardín muy bien cuidado, lleno de hojas verdes y saludables."
        elif ndvi >= 0.60:
            return "Como una planta de casa saludable, con buen color y crecimiento."
        elif ndvi >= 0.40:
            return "Como una planta que necesita más atención y cuidados."
        else:
            return "Como una planta que está sufriendo y necesita ayuda urgente."
    
    def _explicar_simple(self, promedio: float, tendencia: Dict) -> str:
        """Explicación simple del estado"""
        if promedio >= 0.75:
            texto = "¡Excelentes noticias! Su cultivo está muy saludable, con plantas vigorosas y bien desarrolladas. Las hojas tienen un color verde intenso, lo que significa que están produciendo mucha energía."
        elif promedio >= 0.60:
            texto = "Su cultivo está en buen estado. Las plantas están creciendo bien y tienen buen color verde. Hay espacio para mejorar, pero en general todo va por buen camino."
        elif promedio >= 0.40:
            texto = "Su cultivo necesita más atención. Las plantas no están tan verdes como deberían, lo que puede significar que necesitan más agua, nutrientes o tienen algún problema."
        else:
            texto = "Atención: Su cultivo está en dificultades. Las plantas están débiles y necesitan ayuda inmediata. Es importante actuar rápido para recuperarlas."
        
        return texto
    
    def _explicar_tendencia_simple(self, tendencia: Dict) -> str:
        """Explicación simple de la tendencia"""
        direccion = tendencia['direccion']
        cambio = abs(tendencia['cambio_porcentual'])
        
        if 'ascendente' in direccion:
            return f"📈 ¡Buenas noticias! Su cultivo está mejorando ({cambio:.0f}% mejor). Las plantas están creciendo más fuertes y saludables con el tiempo."
        elif 'descendente' in direccion:
            return f"📉 Cuidado: Su cultivo está empeorando ({cambio:.0f}% peor). Las plantas están perdiendo fuerza. Es momento de revisar qué está pasando."
        else:
            return f"➡️ Su cultivo se mantiene estable. No hay grandes cambios, las plantas siguen igual que antes."
    
    def _evaluar_salud(self, promedio: float) -> str:
        """Evaluación textual de salud"""
        if promedio >= 0.75:
            return "Excelente"
        elif promedio >= 0.60:
            return "Buena"
        elif promedio >= 0.40:
            return "Regular"
        else:
            return "Deficiente"
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        # Base: NDVI normalizado a 0-10
        puntuacion_base = (promedio / 1.0) * 10
        
        # Ajuste por tendencia
        if tendencia['direccion'] == 'ascendente_fuerte':
            ajuste = 1.0
        elif tendencia['direccion'] == 'ascendente':
            ajuste = 0.5
        elif tendencia['direccion'] == 'descendente':
            ajuste = -0.5
        elif tendencia['direccion'] == 'descendente_fuerte':
            ajuste = -1.0
        else:
            ajuste = 0
        
        puntuacion_final = max(0, min(10, puntuacion_base + ajuste))
        return round(puntuacion_final, 1)
