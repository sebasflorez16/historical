"""
Servicio para obtener datos climáticos históricos usando Open-Meteo API.
Alternativa gratuita a EOSDA Weather API con cobertura global.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OpenMeteoWeatherService:
    """
    Servicio para obtener datos climáticos desde Open-Meteo Historical Weather API.
    
    API gratuita sin límites estrictos:
    - Hasta 10,000 requests/día
    - Cobertura global incluyendo Colombia
    - Datos históricos desde 1940
    - Variables: temperatura, precipitación, humedad, viento, etc.
    """
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @staticmethod
    def obtener_datos_historicos(
        latitud: float,
        longitud: float,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict]:
        """
        Obtiene datos climáticos históricos para una ubicación y rango de fechas.
        
        Args:
            latitud: Latitud del punto (ej: 5.736933)
            longitud: Longitud del punto (ej: -71.520019)
            fecha_inicio: Fecha inicial (datetime)
            fecha_fin: Fecha final (datetime)
            
        Returns:
            Lista de diccionarios con datos diarios:
            [
                {
                    'fecha': '2025-01-15',
                    'temperatura_promedio': 25.3,
                    'temperatura_maxima': 30.1,
                    'temperatura_minima': 20.5,
                    'precipitacion_total': 12.5
                },
                ...
            ]
        """
        try:
            # Formatear fechas para la API (YYYY-MM-DD)
            start_date = fecha_inicio.strftime('%Y-%m-%d')
            end_date = fecha_fin.strftime('%Y-%m-%d')
            
            # Parámetros de la petición
            params = {
                'latitude': latitud,
                'longitude': longitud,
                'start_date': start_date,
                'end_date': end_date,
                'daily': [
                    'temperature_2m_max',      # Temperatura máxima diaria (°C)
                    'temperature_2m_min',      # Temperatura mínima diaria (°C)
                    'temperature_2m_mean',     # Temperatura promedio diaria (°C)
                    'precipitation_sum',       # Precipitación total diaria (mm)
                ],
                'timezone': 'America/Bogota'
            }
            
            logger.info(f"🌦️ Obteniendo datos climáticos Open-Meteo: {start_date} a {end_date}")
            logger.info(f"   Coordenadas: lat={latitud:.6f}, lon={longitud:.6f}")
            
            # Realizar petición
            response = requests.get(
                OpenMeteoWeatherService.BASE_URL,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Error Open-Meteo API: Status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
            
            data = response.json()
            
            # Verificar que tenemos datos
            if 'daily' not in data:
                logger.warning("Open-Meteo no retornó datos diarios")
                return []
            
            daily = data['daily']
            fechas = daily.get('time', [])
            temps_max = daily.get('temperature_2m_max', [])
            temps_min = daily.get('temperature_2m_min', [])
            temps_mean = daily.get('temperature_2m_mean', [])
            precipitacion = daily.get('precipitation_sum', [])
            
            # Construir lista de datos
            datos_climaticos = []
            for i, fecha in enumerate(fechas):
                datos_climaticos.append({
                    'fecha': fecha,
                    'temperatura_promedio': temps_mean[i] if i < len(temps_mean) else None,
                    'temperatura_maxima': temps_max[i] if i < len(temps_max) else None,
                    'temperatura_minima': temps_min[i] if i < len(temps_min) else None,
                    'precipitacion_total': precipitacion[i] if i < len(precipitacion) else None,
                })
            
            logger.info(f"✅ Open-Meteo: {len(datos_climaticos)} días obtenidos")
            return datos_climaticos
            
        except requests.RequestException as e:
            logger.error(f"Error de red en Open-Meteo API: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error procesando datos Open-Meteo: {str(e)}")
            return []
    
    @staticmethod
    def agrupar_por_mes(datos_diarios: List[Dict]) -> Dict[Tuple[int, int], Dict]:
        """
        Agrupa datos diarios por mes y calcula promedios/totales mensuales.
        
        Args:
            datos_diarios: Lista de datos diarios de obtener_datos_historicos()
            
        Returns:
            Diccionario con clave (año, mes) y valores agregados:
            {
                (2025, 1): {
                    'temperatura_promedio': 25.3,
                    'temperatura_maxima': 30.1,
                    'temperatura_minima': 20.5,
                    'precipitacion_total': 125.5
                },
                ...
            }
        """
        from collections import defaultdict
        
        datos_por_mes = defaultdict(lambda: {
            'temp_promedio': [],
            'temp_max': [],
            'temp_min': [],
            'precipitacion': []
        })
        
        for dato in datos_diarios:
            try:
                # Parsear fecha (formato: YYYY-MM-DD)
                fecha = datetime.strptime(dato['fecha'], '%Y-%m-%d')
                clave_mes = (fecha.year, fecha.month)
                
                # Agregar valores si existen
                if dato.get('temperatura_promedio') is not None:
                    datos_por_mes[clave_mes]['temp_promedio'].append(dato['temperatura_promedio'])
                if dato.get('temperatura_maxima') is not None:
                    datos_por_mes[clave_mes]['temp_max'].append(dato['temperatura_maxima'])
                if dato.get('temperatura_minima') is not None:
                    datos_por_mes[clave_mes]['temp_min'].append(dato['temperatura_minima'])
                if dato.get('precipitacion_total') is not None:
                    datos_por_mes[clave_mes]['precipitacion'].append(dato['precipitacion_total'])
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parseando dato climático: {str(e)}")
                continue
        
        # Calcular promedios y totales por mes
        resultado = {}
        for (year, month), valores in datos_por_mes.items():
            resultado[(year, month)] = {
                'temperatura_promedio': sum(valores['temp_promedio']) / len(valores['temp_promedio']) if valores['temp_promedio'] else None,
                'temperatura_maxima': max(valores['temp_max']) if valores['temp_max'] else None,
                'temperatura_minima': min(valores['temp_min']) if valores['temp_min'] else None,
                'precipitacion_total': sum(valores['precipitacion']) if valores['precipitacion'] else None,
            }
        
        return resultado
