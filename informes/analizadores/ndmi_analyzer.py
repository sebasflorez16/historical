"""
Analizador NDMI - Normalized Difference Moisture Index
Interpreta contenido de humedad en vegetación
"""
import statistics
from typing import Dict, List, Any


class AnalizadorNDMI:
    """
    Analiza datos de NDMI para evaluar estado hídrico de la vegetación
    
    Umbrales NDMI:
    - < -0.4: Estrés hídrico severo
    - -0.4 a -0.1: Estrés hídrico moderado
    - -0.1 a 0.2: Humedad normal-baja
    - 0.2 a 0.4: Humedad óptima
    - > 0.4: Humedad muy alta / saturación
    """
    
    UMBRAL_ESTRES_SEVERO = -0.2
    UMBRAL_ESTRES_MODERADO = 0.1
    UMBRAL_NORMAL = 0.2
    UMBRAL_OPTIMO = 0.35
    UMBRAL_SATURACION = 0.5
    
    def __init__(self, tipo_cultivo: str = "General"):
        self.tipo_cultivo = tipo_cultivo
    
    def analizar(self, datos_ndmi: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza serie temporal de NDMI"""
        if not datos_ndmi:
            return self._resultado_sin_datos()
        
        valores = [d.get('ndmi', 0) for d in datos_ndmi if d.get('ndmi') is not None]
        
        if not valores:
            return self._resultado_sin_datos()
        
        # Estadísticas
        promedio = statistics.mean(valores)
        mediana = statistics.median(valores)
        minimo = min(valores)
        maximo = max(valores)
        desv_std = statistics.stdev(valores) if len(valores) > 1 else 0
        
        # Análisis
        tendencia = self._calcular_tendencia(valores)
        estado = self._clasificar_estado(promedio)
        alertas = self._generar_alertas(promedio, minimo, tendencia, valores)
        
        # Interpretaciones
        interpretacion_tecnica = self._generar_interpretacion_tecnica(
            promedio, desv_std, tendencia, estado, minimo, maximo
        )
        
        interpretacion_simple = self._generar_interpretacion_simple(
            promedio, tendencia, estado
        )
        
        return {
            'indice': 'NDMI',
            'nombre': 'Índice de Humedad Normalizado',
            'estadisticas': {
                'promedio': round(promedio, 3),
                'mediana': round(mediana, 3),
                'minimo': round(minimo, 3),
                'maximo': round(maximo, 3),
                'desviacion_estandar': round(desv_std, 3)
            },
            'estado': estado,
            'tendencia': tendencia,
            'interpretacion_tecnica': interpretacion_tecnica,
            'interpretacion_simple': interpretacion_simple,
            'alertas': alertas,
            'puntuacion': self._calcular_puntuacion(promedio, tendencia),
            'riesgo_hidrico': self._evaluar_riesgo_hidrico(promedio, minimo)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia temporal"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'descripcion': 'Datos insuficientes'}
        
        n = len(valores)
        cambio_promedio = sum(valores[i] - valores[i-1] for i in range(1, n)) / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / abs(valores[0]) * 100 if valores[0] != 0 else 0
        
        if abs(cambio_promedio) < 0.02:
            direccion = 'estable'
            descripcion = 'Humedad estable'
        elif cambio_promedio > 0.05:
            direccion = 'ascendente_fuerte'
            descripcion = 'Aumento significativo de humedad'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Humedad en aumento'
        elif cambio_promedio < -0.05:
            direccion = 'descendente_fuerte'
            descripcion = 'Pérdida significativa de humedad'
        else:
            direccion = 'descendente'
            descripcion = 'Humedad en descenso'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica estado hídrico"""
        if promedio < self.UMBRAL_ESTRES_SEVERO:
            return {
                'nivel': 'critico',
                'etiqueta': 'Estrés Hídrico Severo',
                'color': '#dc3545',
                'icono': '🚨'
            }
        elif promedio < self.UMBRAL_ESTRES_MODERADO:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Estrés Hídrico',
                'color': '#fd7e14',
                'icono': '⚠️'
            }
        elif promedio < self.UMBRAL_NORMAL:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Humedad Normal-Baja',
                'color': '#ffc107',
                'icono': '💧'
            }
        elif promedio < self.UMBRAL_OPTIMO:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Humedad Óptima',
                'color': '#28a745',
                'icono': '✅'
            }
        elif promedio < self.UMBRAL_SATURACION:
            return {
                'nivel': 'muy_bueno',
                'etiqueta': 'Humedad Alta',
                'color': '#17a2b8',
                'icono': '💦'
            }
        else:
            return {
                'nivel': 'saturacion',
                'etiqueta': 'Saturación',
                'color': '#6c757d',
                'icono': '🌊'
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float,
                                       tendencia: Dict, estado: Dict,
                                       minimo: float, maximo: float) -> str:
        """Interpretación técnica"""
        interpretacion = f"""
<strong>Análisis NDMI - Contenido de Humedad</strong><br><br>

El NDMI promedio de <strong>{promedio:.3f}</strong> indica un estado <strong>{estado['etiqueta'].lower()}</strong> 
del contenido de agua en la vegetación.<br><br>

<strong>Parámetros Hídricos:</strong><br>
• Estado hídrico: <strong>{self._interpretar_estado_hidrico(promedio)}</strong><br>
• Rango observado: {minimo:.3f} - {maximo:.3f}<br>
• Variabilidad: σ={desv_std:.3f}<br><br>

<strong>Tendencia Temporal:</strong><br>
{tendencia['descripcion']} ({tendencia['cambio_porcentual']:+.1f}%). 
{self._interpretar_tendencia_tecnica(tendencia, promedio)}<br><br>

<strong>Recomendación Hídrica:</strong><br>
{self._generar_recomendacion_tecnica(promedio, tendencia)}
"""
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Interpretación simple"""
        interpretacion = f"""
<strong>¿Tienen agua suficiente mis plantas?</strong><br><br>

{estado['icono']} El contenido de agua en sus plantas es <strong>{estado['etiqueta'].lower()}</strong>. 
{self._explicar_simple(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia, promedio)}
"""
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, minimo: float, 
                        tendencia: Dict, valores: List[float]) -> List[Dict]:
        """Genera alertas hídricas"""
        alertas = []
        
        # Estrés hídrico
        if promedio < self.UMBRAL_ESTRES_MODERADO:
            alertas.append({
                'tipo': 'critico' if promedio < self.UMBRAL_ESTRES_SEVERO else 'advertencia',
                'prioridad': 'alta',
                'icono': '💧',
                'titulo': 'Estrés Hídrico Detectado',
                'mensaje': f'NDMI promedio ({promedio:.2f}) indica déficit hídrico.',
                'accion': 'Aumentar frecuencia/volumen de riego'
            })
        
        # Tendencia descendente
        if tendencia['direccion'] in ['descendente', 'descendente_fuerte']:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'alta',
                'icono': '📉',
                'titulo': 'Pérdida de Humedad',
                'mensaje': f"El contenido de humedad ha bajado {abs(tendencia['cambio_porcentual']):.1f}%.",
                'accion': 'Monitorear y ajustar plan de riego'
            })
        
        # Saturación
        if promedio > self.UMBRAL_SATURACION:
            alertas.append({
                'tipo': 'info',
                'prioridad': 'media',
                'icono': '🌊',
                'titulo': 'Alta Humedad / Saturación',
                'mensaje': f'NDMI muy alto ({promedio:.2f}). Posible exceso hídrico o período lluvioso.',
                'accion': 'Verificar drenaje, evitar riego excesivo'
            })
        
        return alertas
    
    # Métodos auxiliares
    
    def _resultado_sin_datos(self) -> Dict:
        """Resultado cuando no hay datos"""
        return {
            'indice': 'NDMI',
            'nombre': 'Índice de Humedad Normalizado',
            'error': 'No hay datos disponibles',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': '❓'},
            'interpretacion_tecnica': 'No hay datos NDMI disponibles.',
            'interpretacion_simple': 'Aún no tenemos información sobre humedad.',
            'alertas': []
        }
    
    def _interpretar_estado_hidrico(self, ndmi: float) -> str:
        """Interpretación del estado hídrico"""
        if ndmi < self.UMBRAL_ESTRES_SEVERO:
            return "Déficit hídrico severo"
        elif ndmi < self.UMBRAL_ESTRES_MODERADO:
            return "Estrés hídrico moderado"
        elif ndmi < self.UMBRAL_NORMAL:
            return "Contenido hídrico normal-bajo"
        elif ndmi < self.UMBRAL_OPTIMO:
            return "Contenido hídrico óptimo"
        else:
            return "Contenido hídrico alto/saturación"
    
    def _interpretar_tendencia_tecnica(self, tendencia: Dict, promedio: float) -> str:
        """Interpretación técnica de tendencia"""
        if 'descendente' in tendencia['direccion']:
            return "Indica consumo hídrico activo o déficit progresivo. Evaluar evapotranspiración y ajustar riego."
        elif 'ascendente' in tendencia['direccion']:
            return "Asociado a precipitación o incremento en frecuencia de riego. Verificar balance hídrico."
        else:
            return "Estabilidad en contenido hídrico, acorde con manejo actual."
    
    def _generar_recomendacion_tecnica(self, promedio: float, tendencia: Dict) -> str:
        """Recomendación técnica de manejo"""
        if promedio < self.UMBRAL_ESTRES_MODERADO:
            return "Aumentar lámina de riego en 20-30%. Considerar riego más frecuente o sistema tecnificado."
        elif promedio < self.UMBRAL_NORMAL and 'descendente' in tendencia['direccion']:
            return "Monitorear evolución. Preparar plan de contingencia para temporada seca."
        elif promedio > self.UMBRAL_SATURACION:
            return "Reducir frecuencia de riego. Verificar sistema de drenaje para evitar anegamiento."
        else:
            return "Mantener régimen hídrico actual. Estado óptimo para el cultivo."
    
    def _explicar_simple(self, promedio: float) -> str:
        """Explicación simple"""
        if promedio < self.UMBRAL_ESTRES_MODERADO:
            return "Sus plantas tienen poca agua, como si usted tuviera mucha sed. Necesitan más riego pronto."
        elif promedio < self.UMBRAL_NORMAL:
            return "El agua es suficiente pero podría ser mejor. Como cuando toma agua pero podría tomar más."
        elif promedio < self.UMBRAL_OPTIMO:
            return "¡Perfecto! Sus plantas tienen el agua que necesitan, están bien hidratadas."
        else:
            return "Hay mucha agua, tal vez demasiada. Como tomar mucho líquido, no siempre es necesario."
    
    def _explicar_tendencia_simple(self, tendencia: Dict, promedio: float) -> str:
        """Explicación simple de tendencia"""
        if 'descendente' in tendencia['direccion']:
            return f"📉 El agua está bajando ({abs(tendencia['cambio_porcentual']):.0f}% menos). Sus plantas están usando el agua o no están recibiendo suficiente. Momento de regar más."
        elif 'ascendente' in tendencia['direccion']:
            return f"📈 El agua está subiendo ({tendencia['cambio_porcentual']:.0f}% más). Buena señal, las plantas están recibiendo agua de lluvia o riego."
        else:
            return "➡️ El nivel de agua se mantiene estable. Todo normal."
    
    def _evaluar_riesgo_hidrico(self, promedio: float, minimo: float) -> str:
        """Evalúa riesgo hídrico"""
        if minimo < self.UMBRAL_ESTRES_SEVERO:
            return "Alto"
        elif promedio < self.UMBRAL_ESTRES_MODERADO:
            return "Medio-Alto"
        elif promedio < self.UMBRAL_NORMAL:
            return "Medio"
        else:
            return "Bajo"
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        # Normalizar NDMI (-1 a 1) a escala 0-10
        # Óptimo es 0.3, penalizar extremos
        if promedio < 0:
            puntuacion_base = max(0, (promedio + 1) * 5)  # -1=0, 0=5
        else:
            if promedio <= 0.4:
                puntuacion_base = 5 + (promedio / 0.4) * 5  # 0=5, 0.4=10
            else:
                puntuacion_base = 10 - (promedio - 0.4) * 5  # >0.4 baja de 10
        
        # Ajuste por tendencia
        if 'descendente' in tendencia['direccion'] and promedio < 0.2:
            puntuacion_base -= 1
        
        return round(max(0, min(10, puntuacion_base)), 1)
