"""
Detector de Tendencias Temporales
Analiza patrones, estacionalidad y anomalías en series temporales
"""
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math


class DetectorTendencias:
    """
    Detecta patrones temporales en datos satelitales:
    - Tendencias (ascendente/descendente/estable)
    - Estacionalidad
    - Anomalías
    - Ciclos del cultivo
    - Comparaciones interanuales
    """
    
    def __init__(self):
        pass
    
    def analizar_temporal(self, datos_mensuales: List[Dict[str, Any]], 
                         indice: str = 'ndvi') -> Dict[str, Any]:
        """
        Analiza tendencias temporales de un índice
        
        Args:
            datos_mensuales: Lista de datos con formato
                            [{'mes': '2024-01', 'ndvi': 0.75, ...}, ...]
            indice: Nombre del índice a analizar (ndvi, ndmi, savi)
        
        Returns:
            Diccionario con análisis completo de tendencias
        """
        if not datos_mensuales or len(datos_mensuales) < 3:
            return self._resultado_insuficiente()
        
        # Extraer valores y fechas
        valores = []
        fechas = []
        for dato in datos_mensuales:
            valor = dato.get(indice)
            if valor is not None:
                valores.append(valor)
                mes_str = dato.get('mes', '')
                try:
                    fecha = datetime.strptime(mes_str, '%Y-%m')
                    fechas.append(fecha)
                except:
                    fechas.append(None)
        
        if len(valores) < 3:
            return self._resultado_insuficiente()
        
        # Análisis de tendencia lineal
        tendencia_lineal = self._calcular_tendencia_lineal(valores)
        
        # Detectar estacionalidad
        estacionalidad = self._detectar_estacionalidad(valores, fechas)
        
        # Detectar anomalías
        anomalias = self._detectar_anomalias_avanzadas(valores, fechas, datos_mensuales)
        
        # Identificar ciclos del cultivo
        ciclos = self._identificar_ciclos(valores, fechas)
        
        # Análisis de variabilidad
        variabilidad = self._analizar_variabilidad(valores)
        
        # Comparaciones (si hay más de un año)
        comparaciones = self._comparar_periodos(valores, fechas)
        
        # Proyección simple
        proyeccion = self._proyectar_proximo_periodo(valores, tendencia_lineal)
        
        return {
            'tendencia_lineal': tendencia_lineal,
            'estacionalidad': estacionalidad,
            'anomalias': anomalias,
            'ciclos': ciclos,
            'variabilidad': variabilidad,
            'comparaciones': comparaciones,
            'proyeccion': proyeccion,
            'resumen': self._generar_resumen(tendencia_lineal, estacionalidad, anomalias)
        }
    
    def _calcular_tendencia_lineal(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia lineal por mínimos cuadrados"""
        n = len(valores)
        x = list(range(n))
        
        # Mínimos cuadrados
        x_mean = sum(x) / n
        y_mean = sum(valores) / n
        
        numerator = sum((x[i] - x_mean) * (valores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            pendiente = 0
        else:
            pendiente = numerator / denominator
        
        intercepto = y_mean - pendiente * x_mean
        
        # Calcular R² (bondad de ajuste)
        y_pred = [pendiente * xi + intercepto for xi in x]
        ss_res = sum((valores[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((valores[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Cambio total
        cambio_total = valores[-1] - valores[0]
        cambio_porcentual = (cambio_total / valores[0] * 100) if valores[0] != 0 else 0
        
        # Clasificar tendencia
        if abs(pendiente) < 0.005:
            direccion = 'estable'
            fuerza = 'ninguna'
        elif pendiente > 0.02:
            direccion = 'ascendente'
            fuerza = 'fuerte'
        elif pendiente > 0:
            direccion = 'ascendente'
            fuerza = 'moderada'
        elif pendiente < -0.02:
            direccion = 'descendente'
            fuerza = 'fuerte'
        else:
            direccion = 'descendente'
            fuerza = 'moderada'
        
        return {
            'direccion': direccion,
            'fuerza': fuerza,
            'pendiente': round(pendiente, 4),
            'intercepto': round(intercepto, 4),
            'r_cuadrado': round(r_squared, 3),
            'cambio_total': round(cambio_total, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'confianza': 'alta' if r_squared > 0.7 else 'media' if r_squared > 0.4 else 'baja'
        }
    
    def _detectar_estacionalidad(self, valores: List[float], 
                                fechas: List[Optional[datetime]]) -> Dict[str, Any]:
        """Detecta patrones estacionales"""
        if len(valores) < 12:
            return {'detectada': False, 'motivo': 'Datos insuficientes (< 12 meses)'}
        
        # Agrupar por mes del año
        meses_datos = {}
        for i, fecha in enumerate(fechas):
            if fecha:
                mes = fecha.month
                if mes not in meses_datos:
                    meses_datos[mes] = []
                meses_datos[mes].append(valores[i])
        
        # Calcular promedios por mes
        if len(meses_datos) < 6:
            return {'detectada': False, 'motivo': 'Datos insuficientes por mes'}
        
        promedios_mensuales = {mes: statistics.mean(vals) for mes, vals in meses_datos.items()}
        
        # Detectar picos y valles
        meses_ordenados = sorted(promedios_mensuales.keys())
        valores_ordenados = [promedios_mensuales[m] for m in meses_ordenados]
        
        if len(valores_ordenados) < 6:
            return {'detectada': False}
        
        max_val = max(valores_ordenados)
        min_val = min(valores_ordenados)
        rango = max_val - min_val
        
        # Considerar estacional si hay variación > 20%
        variacion_porcentual = (rango / min_val * 100) if min_val != 0 else 0
        
        meses_nombres = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        mes_pico = meses_ordenados[valores_ordenados.index(max_val)]
        mes_valle = meses_ordenados[valores_ordenados.index(min_val)]
        
        return {
            'detectada': variacion_porcentual > 15,
            'variacion_porcentual': round(variacion_porcentual, 1),
            'mes_pico': meses_nombres[mes_pico],
            'mes_valle': meses_nombres[mes_valle],
            'valor_pico': round(max_val, 3),
            'valor_valle': round(min_val, 3),
            'patron': self._describir_patron_estacional(mes_pico, mes_valle)
        }
    
    def _detectar_anomalias_avanzadas(self, valores: List[float], 
                                     fechas: List[Optional[datetime]],
                                     datos_completos: List[Dict]) -> List[Dict]:
        """Detecta anomalías usando múltiples criterios"""
        if len(valores) < 5:
            return []
        
        anomalias = []
        promedio = statistics.mean(valores)
        desv_std = statistics.stdev(valores)
        
        for i, valor in enumerate(valores):
            # Criterio 1: Desviación estándar (Z-score)
            z_score = (valor - promedio) / desv_std if desv_std > 0 else 0
            
            # Criterio 2: Cambio brusco respecto al anterior
            cambio_brusco = False
            if i > 0:
                cambio = abs(valor - valores[i-1])
                cambio_relativo = cambio / valores[i-1] if valores[i-1] != 0 else 0
                if cambio_relativo > 0.25:  # Cambio > 25%
                    cambio_brusco = True
            
            # Detectar anomalía
            if abs(z_score) > 2 or cambio_brusco:
                tipo = 'caida_brusca' if valor < promedio else 'pico_inusual'
                severidad = 'severa' if abs(z_score) > 3 else 'moderada'
                
                fecha_str = fechas[i].strftime('%B %Y') if i < len(fechas) and fechas[i] else 'Desconocido'
                
                anomalias.append({
                    'indice': i,
                    'fecha': fecha_str,
                    'valor': round(valor, 3),
                    'tipo': tipo,
                    'severidad': severidad,
                    'z_score': round(z_score, 2),
                    'descripcion': f"Valor {'muy bajo' if tipo == 'caida_brusca' else 'muy alto'} en {fecha_str}"
                })
        
        return anomalias
    
    def _identificar_ciclos(self, valores: List[float], 
                          fechas: List[Optional[datetime]]) -> Dict[str, Any]:
        """Identifica ciclos del cultivo"""
        if len(valores) < 6:
            return {'identificados': False}
        
        # Buscar picos (fases de máximo desarrollo)
        picos = []
        for i in range(1, len(valores) - 1):
            if valores[i] > valores[i-1] and valores[i] > valores[i+1]:
                if valores[i] > statistics.mean(valores):
                    fecha_str = fechas[i].strftime('%B %Y') if i < len(fechas) and fechas[i] else f"Mes {i+1}"
                    picos.append({
                        'indice': i,
                        'fecha': fecha_str,
                        'valor': round(valores[i], 3)
                    })
        
        # Buscar valles (fases de menor desarrollo)
        valles = []
        for i in range(1, len(valores) - 1):
            if valores[i] < valores[i-1] and valores[i] < valores[i+1]:
                if valores[i] < statistics.mean(valores):
                    fecha_str = fechas[i].strftime('%B %Y') if i < len(fechas) and fechas[i] else f"Mes {i+1}"
                    valles.append({
                        'indice': i,
                        'fecha': fecha_str,
                        'valor': round(valores[i], 3)
                    })
        
        return {
            'identificados': len(picos) > 0 or len(valles) > 0,
            'picos': picos[:3],  # Máximo 3 picos
            'valles': valles[:3],  # Máximo 3 valles
            'numero_ciclos': len(picos),
            'descripcion': f"Detectados {len(picos)} pico(s) y {len(valles)} valle(s) en el período"
        }
    
    def _analizar_variabilidad(self, valores: List[float]) -> Dict[str, Any]:
        """Analiza variabilidad de los datos"""
        promedio = statistics.mean(valores)
        desv_std = statistics.stdev(valores) if len(valores) > 1 else 0
        coef_variacion = (desv_std / promedio * 100) if promedio != 0 else 0
        
        if coef_variacion < 10:
            clasificacion = 'Muy baja - Datos muy estables'
        elif coef_variacion < 20:
            clasificacion = 'Baja - Datos estables'
        elif coef_variacion < 30:
            clasificacion = 'Moderada - Variación normal'
        else:
            clasificacion = 'Alta - Datos muy variables'
        
        return {
            'desviacion_estandar': round(desv_std, 3),
            'coeficiente_variacion': round(coef_variacion, 1),
            'clasificacion': clasificacion,
            'rango': round(max(valores) - min(valores), 3)
        }
    
    def _comparar_periodos(self, valores: List[float], 
                          fechas: List[Optional[datetime]]) -> Dict[str, Any]:
        """Compara períodos anuales si hay datos suficientes"""
        if len(valores) < 12:
            return {'disponible': False, 'motivo': 'Datos insuficientes'}
        
        # Agrupar por año
        años_datos = {}
        for i, fecha in enumerate(fechas):
            if fecha:
                año = fecha.year
                if año not in años_datos:
                    años_datos[año] = []
                años_datos[año].append(valores[i])
        
        if len(años_datos) < 2:
            return {'disponible': False, 'motivo': 'Solo un año de datos'}
        
        # Calcular promedios por año
        promedios_anuales = {año: statistics.mean(vals) for año, vals in años_datos.items()}
        años_ordenados = sorted(promedios_anuales.keys())
        
        # Comparar último año vs anterior
        if len(años_ordenados) >= 2:
            año_actual = años_ordenados[-1]
            año_anterior = años_ordenados[-2]
            
            promedio_actual = promedios_anuales[año_actual]
            promedio_anterior = promedios_anuales[año_anterior]
            
            diferencia = promedio_actual - promedio_anterior
            porcentaje_cambio = (diferencia / promedio_anterior * 100) if promedio_anterior != 0 else 0
            
            if porcentaje_cambio > 5:
                conclusion = f"mejor que {año_anterior}"
            elif porcentaje_cambio < -5:
                conclusion = f"peor que {año_anterior}"
            else:
                conclusion = f"similar a {año_anterior}"
            
            return {
                'disponible': True,
                'año_actual': año_actual,
                'año_anterior': año_anterior,
                'promedio_actual': round(promedio_actual, 3),
                'promedio_anterior': round(promedio_anterior, 3),
                'diferencia': round(diferencia, 3),
                'porcentaje_cambio': round(porcentaje_cambio, 1),
                'conclusion': conclusion
            }
        
        return {'disponible': False}
    
    def _proyectar_proximo_periodo(self, valores: List[float], 
                                  tendencia: Dict) -> Dict[str, Any]:
        """Proyecta valor del próximo período basado en tendencia"""
        ultimo_valor = valores[-1]
        pendiente = tendencia['pendiente']
        
        # Proyección simple: último valor + pendiente
        valor_proyectado = ultimo_valor + pendiente
        
        # Calcular intervalo de confianza simple
        desv_std = statistics.stdev(valores)
        margen_error = 1.96 * desv_std / math.sqrt(len(valores))  # 95% confianza
        
        return {
            'valor_actual': round(ultimo_valor, 3),
            'valor_proyectado': round(valor_proyectado, 3),
            'limite_inferior': round(valor_proyectado - margen_error, 3),
            'limite_superior': round(valor_proyectado + margen_error, 3),
            'confianza': tendencia['confianza'],
            'descripcion': self._describir_proyeccion(ultimo_valor, valor_proyectado, tendencia)
        }
    
    def _generar_resumen(self, tendencia: Dict, estacionalidad: Dict, 
                        anomalias: List) -> str:
        """Genera resumen ejecutivo del análisis temporal"""
        resumen = f"<strong>Resumen de Tendencias:</strong><br>"
        
        # Tendencia
        if tendencia['direccion'] == 'estable':
            resumen += f"• Los valores se mantienen estables (cambio: {tendencia['cambio_porcentual']:+.1f}%).<br>"
        elif 'ascendente' in tendencia['direccion']:
            resumen += f"• Tendencia {tendencia['direccion']} {tendencia['fuerza']} ({tendencia['cambio_porcentual']:+.1f}%).<br>"
        else:
            resumen += f"• Tendencia {tendencia['direccion']} {tendencia['fuerza']} ({tendencia['cambio_porcentual']:+.1f}%).<br>"
        
        # Estacionalidad
        if estacionalidad.get('detectada'):
            resumen += f"• Patrón estacional detectado: pico en {estacionalidad['mes_pico']}, valle en {estacionalidad['mes_valle']}.<br>"
        
        # Anomalías
        if len(anomalias) > 0:
            resumen += f"• {len(anomalias)} anomalía(s) detectada(s) que requieren atención.<br>"
        
        return resumen
    
    # Métodos auxiliares
    
    def _resultado_insuficiente(self) -> Dict:
        """Retorna resultado cuando no hay datos suficientes"""
        return {
            'error': 'Datos insuficientes para análisis de tendencias',
            'minimo_requerido': '3 meses de datos',
            'tendencia_lineal': {},
            'estacionalidad': {'detectada': False},
            'anomalias': [],
            'ciclos': {'identificados': False},
            'comparaciones': {'disponible': False}
        }
    
    def _describir_patron_estacional(self, mes_pico: int, mes_valle: int) -> str:
        """Describe el patrón estacional"""
        if mes_pico in [3, 4, 5]:
            return "Primavera como temporada de mayor desarrollo"
        elif mes_pico in [6, 7, 8]:
            return "Verano como temporada de mayor desarrollo"
        elif mes_pico in [9, 10, 11]:
            return "Otoño como temporada de mayor desarrollo"
        else:
            return "Invierno como temporada de mayor desarrollo"
    
    def _describir_proyeccion(self, actual: float, proyectado: float, 
                            tendencia: Dict) -> str:
        """Describe la proyección"""
        if tendencia['direccion'] == 'ascendente':
            return f"Se espera que el valor continúe aumentando de {actual:.2f} a {proyectado:.2f}"
        elif tendencia['direccion'] == 'descendente':
            return f"Se espera que el valor continúe disminuyendo de {actual:.2f} a {proyectado:.2f}"
        else:
            return f"Se espera que el valor se mantenga estable alrededor de {proyectado:.2f}"
