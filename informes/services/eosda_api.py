"""
Servicio para integración con la API de EOSDA
Obtiene datos satelitales como NDVI, NDMI, SAVI y datos climatológicos
Sistema optimizado con caché y tracking de requests
"""

import requests
import json
import logging
from datetime import datetime, date, timedelta
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import time

logger = logging.getLogger(__name__)


class EosdaAPIService:
    """
    Servicio para interactuar con la API de EOSDA y obtener datos satelitales
    Incluye Field Management API para sincronizar parcelas
    """
    
    def __init__(self):
        self.api_key = settings.EOSDA_API_KEY
        self.base_url = settings.EOSDA_BASE_URL
        self.session = requests.Session()
        # EOSDA API Connect NO usa headers para autenticación
        # El API key va como parámetro en la URL: ?api_key=xxx
        # Documentación: https://doc.eos.com/docs/field-management-api/
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Mapeo de nombres de cultivos en español a nombres válidos de EOSDA
        # ✅ VERIFICADO CONTRA LISTA OFICIAL DE EOSDA
        self.mapeo_cultivos = {
            'cacao': 'Cocoa',
            'café': 'Coffee',
            'cafe': 'Coffee',
            'maíz': 'Other',  # ❌ "Corn" no es válido en EOSDA, usar "Other"
            'maiz': 'Other',  # ❌ "Corn" no es válido en EOSDA, usar "Other"
            'arroz': 'Rice',
            'plátano': 'Plantain',
            'platano': 'Plantain',
            'banano': 'Bananas',
            'palma de aceite': 'Oil palm',
            'palma': 'Oil palm',
            'caucho': 'Rubber',
            'yuca': 'Cassava',
            'papa': 'Potatoes',
            'tomate': 'Vegetables',
            'aguacate': 'Fruit',
            'cítricos': 'Citrus',
            'citricos': 'Citrus',
            'caña de azúcar': 'Sugarcane',
            'caña': 'Sugarcane',
            'soya': 'Soybeans',
            'algodón': 'Cotton',
            'algodon': 'Cotton',
            'trigo': 'Wheat',
            'cebada': 'Oats',  # ❌ "Winter Barley" no es válido, usar "Oats"
            'avena': 'Oats',
            'sorgo': 'Other',  # ❌ "Sorghum" no es válido, usar "Other"
            'frijol': 'Beans',
            'fríjol': 'Beans',
            'girasol': 'Sunflower',
            'uva': 'Grapes',
            'uvas': 'Grapes',
            'manzana': 'Apple',
            'manzanas': 'Apple',
            'pasto': 'Pasture',
            'pastura': 'Pasture',
            'otros': 'Other',
            'otro': 'Other'
        }
        
        # Cache para la lista de tipos de cultivo válidos
        self._cultivos_validos_cache = None
    
    def validar_configuracion(self) -> bool:
        """
        Valida que la configuración de la API esté correctamente establecida
        """
        if not self.api_key or self.api_key == 'demo_token_reemplazar_con_real':
            logger.warning("Token de EOSDA no configurado correctamente")
            return False
        return True
    
    def _build_url(self, endpoint: str) -> str:
        """
        Construye la URL con el api_key como parámetro de query
        Según documentación de EOSDA: https://doc.eos.com/docs/field-management-api/
        
        Args:
            endpoint: El endpoint de la API (ej: '/field-management/fields')
        
        Returns:
            URL completa con api_key como parámetro
        """
        # Asegurar que el endpoint no tenga slash al inicio si base_url ya lo tiene
        endpoint = endpoint.lstrip('/')
        base = self.base_url.rstrip('/')
        
        # Construir URL base
        url = f"{base}/{endpoint}"
        
        # Agregar api_key como parámetro
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}api_key={self.api_key}"
    
    # ========= FIELD MANAGEMENT API =========
    
    def eliminar_campo_eosda(self, field_id: str) -> Dict:
        """
        Elimina un campo en EOSDA usando Field Management API
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        Endpoint: DELETE /field-management/fields/{field_id}
        
        Args:
            field_id: ID del campo en EOSDA
            
        Returns:
            Dict con 'exito' y 'mensaje' o 'error'
        """
        if not field_id:
            return {
                'exito': False,
                'error': 'No se proporcionó field_id'
            }
            
        try:
            url = self._build_url(f"field-management/{field_id}")
            logger.info(f"Intentando eliminar campo en EOSDA: {field_id}")
            
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 204:
                # 204 No Content = eliminación exitosa
                logger.info(f"✓ Campo eliminado exitosamente en EOSDA: {field_id}")
                return {
                    'exito': True,
                    'mensaje': f'Campo {field_id} eliminado en EOSDA'
                }
            elif response.status_code == 404:
                # El campo no existe en EOSDA (ya fue eliminado o nunca existió)
                logger.warning(f"Campo no encontrado en EOSDA: {field_id}")
                return {
                    'exito': True,
                    'mensaje': f'Campo {field_id} no existe en EOSDA (posiblemente ya eliminado)'
                }
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(f"Error eliminando campo en EOSDA {field_id}: {error_msg}")
                return {
                    'exito': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout eliminando campo en EOSDA: {field_id}")
            return {
                'exito': False,
                'error': 'Timeout al conectar con EOSDA'
            }
        except Exception as e:
            logger.error(f"Excepción eliminando campo en EOSDA {field_id}: {str(e)}")
            return {
                'exito': False,
                'error': f'Error: {str(e)}'
            }
    
    def obtener_cultivos_validos(self) -> List[str]:
        """
        Obtiene la lista de tipos de cultivo válidos desde EOSDA
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        Endpoint: GET /field-management/fields/crop-types
        """
        if self._cultivos_validos_cache:
            return self._cultivos_validos_cache
            
        try:
            url = self._build_url("field-management/fields/crop-types")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                cultivos = response.json()
                if isinstance(cultivos, list):
                    self._cultivos_validos_cache = cultivos
                    logger.info(f"Obtenidos {len(cultivos)} tipos de cultivo válidos desde EOSDA")
                    return cultivos
            else:
                logger.warning(f"Error obteniendo tipos de cultivo: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error obteniendo lista de cultivos: {str(e)}")
        
        # Fallback a lista conocida
        return [
            "Olive tree", "Pasture", "Poppy seed", "Cherry", "Summer fallow", 
            "Cassava", "Ginger", "Yams", "Kola nut", "Millet", "Plantain", 
            "Bananas", "Sesame", "Milk thistle", "Cashew", "Gum arabic", 
            "Melon", "Oil palm", "Rubber", "Turmeric", "Wheat", "Grapes", 
            "Vegetables", "Beans", "Nuts", "Almonds", "Potatoes", "Rye", 
            "Rapeseed", "Corn", "Sugar Beet", "Sunflower", "Soybeans", "Peas", 
            "Oats", "Mixed cereals", "Cotton", "Flax", "Rice", "Pulses", 
            "Coffee", "Cocoa", "Tobacco", "Tuber crops", "Citrus", "Sugarcane", 
            "Canola", "Alfalfa", "Fruit", "Apple", "Spice", "Peanuts", "Other"
        ]
    
    def normalizar_tipo_cultivo(self, tipo_cultivo: str) -> str:
        """
        Normaliza el nombre del tipo de cultivo al formato esperado por EOSDA
        
        Args:
            tipo_cultivo: Nombre del cultivo en español o inglés
            
        Returns:
            Nombre normalizado válido para EOSDA
        """
        if not tipo_cultivo:
            return "Other"
        
        # Convertir a minúsculas para búsqueda
        tipo_lower = tipo_cultivo.lower().strip()
        
        # 1. Buscar en el mapeo español -> inglés
        if tipo_lower in self.mapeo_cultivos:
            nombre_normalizado = self.mapeo_cultivos[tipo_lower]
            logger.info(f"Cultivo mapeado: '{tipo_cultivo}' -> '{nombre_normalizado}'")
            return nombre_normalizado
        
        # 2. Verificar si ya está en inglés y es válido
        cultivos_validos = self.obtener_cultivos_validos()
        
        # Búsqueda case-insensitive
        for cultivo_valido in cultivos_validos:
            if cultivo_valido.lower() == tipo_lower:
                logger.info(f"Cultivo válido encontrado: '{cultivo_valido}'")
                return cultivo_valido
        
        # 3. Si no se encuentra, usar "Other"
        logger.warning(f"Tipo de cultivo '{tipo_cultivo}' no reconocido, usando 'Other'")
        return "Other"
    
    def crear_campo_eosda(self, parcela) -> Dict:
        """
        Crea un campo en EOSDA usando Field Management API
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        """
        try:
            from django.utils import timezone
            
            # Endpoint correcto según documentación oficial
            url = self._build_url("field-management")
            
            # Preparar geometría en formato GeoJSON
            if hasattr(parcela, 'geometria') and parcela.geometria:
                # Usar geometría PostGIS nativa
                geojson_dict = json.loads(parcela.geometria.geojson)
            else:
                # Fallback a coordenadas JSON
                geojson_dict = parcela.coordenadas_dict
            
            if not geojson_dict:
                error_msg = "No hay geometría disponible para la parcela"
                parcela.marcar_error_eosda(error_msg)
                return {'exito': False, 'error': error_msg}
            
            # Payload según documentación oficial de EOSDA Field Management API
            # IMPORTANTE: La respuesta retorna "id" no "field_id"
            # IMPORTANTE: crop_type debe ser un valor válido de la lista de EOSDA
            tipo_cultivo_normalizado = self.normalizar_tipo_cultivo(parcela.tipo_cultivo)
            
            payload = {
                'type': 'Feature',
                'properties': {
                    'name': parcela.nombre,
                    'group': 'AgroTech Histórico',
                    'years_data': [{
                        'crop_type': tipo_cultivo_normalizado,
                        'year': parcela.fecha_inicio_monitoreo.year if parcela.fecha_inicio_monitoreo else datetime.now().year,
                        'sowing_date': parcela.fecha_inicio_monitoreo.isoformat() if parcela.fecha_inicio_monitoreo else None
                    }]
                },
                'geometry': geojson_dict
            }
            
            logger.info(f"Creando campo en EOSDA para parcela: {parcela.nombre}")
            logger.debug(f"Payload enviado a EOSDA: {json.dumps(payload, indent=2)}")
            
            # Crear campo en EOSDA con timeout adecuado
            response = self.session.post(url, json=payload, timeout=30)
            
            logger.info(f"Respuesta EOSDA - Status: {response.status_code}")
            logger.debug(f"Respuesta EOSDA - Body: {response.text}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                # IMPORTANTE: Según documentación, la respuesta es {"id": number, "area": number}
                field_id = data.get('id') or data.get('field_id')
                
                if field_id:
                    # Actualizar parcela con información de EOSDA
                    parcela.marcar_sincronizada_eosda(
                        field_id=str(field_id),
                        nombre_campo=payload['properties']['name']
                    )
                    
                    logger.info(f"✅ Campo creado exitosamente en EOSDA con ID: {field_id}")
                    return {
                        'exito': True,
                        'field_id': str(field_id),
                        'area': data.get('area'),
                        'mensaje': f'Campo registrado en EOSDA con ID {field_id}',
                        'datos': data
                    }
                else:
                    error_msg = f"EOSDA no retornó field_id en la respuesta: {data}"
                    parcela.marcar_error_eosda(error_msg)
                    logger.error(error_msg)
                    return {'exito': False, 'error': error_msg}
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text[:500]}"
                parcela.marcar_error_eosda(error_msg)
                logger.error(f"❌ Error creando campo en EOSDA: {error_msg}")
                return {'exito': False, 'error': error_msg, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout al conectar con EOSDA (>30s)"
            parcela.marcar_error_eosda(error_msg)
            logger.error(error_msg)
            return {'exito': False, 'error': error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "Error de conexión con EOSDA API"
            parcela.marcar_error_eosda(error_msg)
            logger.error(error_msg)
            return {'exito': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Excepción creando campo: {str(e)}"
            parcela.marcar_error_eosda(error_msg)
            logger.error(f"Error en crear_campo_eosda: {error_msg}", exc_info=True)
            return {'exito': False, 'error': error_msg}
    
    def obtener_campos_eosda(self) -> List[Dict]:
        """
        Obtiene la lista de campos desde EOSDA Field Management API
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        """
        try:
            # Endpoint correcto según documentación oficial
            url = self._build_url("field-management/fields")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                fields = response.json()
                logger.info(f"Se obtuvieron {len(fields)} campos desde EOSDA")
                return fields if isinstance(fields, list) else []
            else:
                logger.warning(f"Error obteniendo campos de EOSDA: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo campos de EOSDA: {str(e)}")
            return []
    
    def sincronizar_parcela_con_eosda(self, parcela) -> Dict:
        """
        Sincroniza una parcela con EOSDA, creándola si no existe
        """
        try:
            # Verificar si ya está sincronizada
            if parcela.eosda_sincronizada and parcela.eosda_field_id:
                logger.info(f"Parcela {parcela.nombre} ya está sincronizada con EOSDA: {parcela.eosda_field_id}")
                return {
                    'exito': True,
                    'field_id': parcela.eosda_field_id,
                    'mensaje': 'Ya sincronizada',
                    'ya_existia': True
                }
            
            # Crear campo en EOSDA
            resultado = self.crear_campo_eosda(parcela)
            
            if resultado['exito']:
                logger.info(f"Parcela {parcela.nombre} sincronizada exitosamente con EOSDA")
            else:
                logger.error(f"Error sincronizando {parcela.nombre}: {resultado['error']}")
                
            return resultado
            
        except Exception as e:
            logger.error(f"Error en sincronizar_parcela_con_eosda: {str(e)}")
            return {'exito': False, 'error': str(e)}
    
    def obtener_datos_parcela(self, parcela, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Obtiene todos los datos satelitales para una parcela en un período específico
        NUEVA VERSIÓN: Usa field_id de EOSDA en lugar de geometría
        """
        try:
            # Validar configuración
            if not self.validar_configuracion():
                return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            # 1. SINCRONIZAR CON EOSDA PRIMERO (Field Management API)
            if not parcela.eosda_sincronizada:
                logger.info(f"Sincronizando parcela {parcela.nombre} con EOSDA...")
                resultado_sync = self.sincronizar_parcela_con_eosda(parcela)
                if not resultado_sync['exito']:
                    logger.warning(f"No se pudo sincronizar {parcela.nombre}, usando datos simulados")
                    return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            # 2. USAR FIELD_ID PARA OBTENER DATOS (Statistics API)
            field_id = parcela.eosda_field_id
            if not field_id:
                logger.warning(f"Parcela {parcela.nombre} no tiene field_id, usando datos simulados")
                return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            logger.info(f"Obteniendo datos satelitales para field_id: {field_id}")
            
            # Obtener índices usando field_id
            datos_satelitales = {
                'ndvi': self._obtener_indice_temporal_por_field_id(field_id, 'NDVI', fecha_inicio, fecha_fin),
                'ndmi': self._obtener_indice_temporal_por_field_id(field_id, 'NDMI', fecha_inicio, fecha_fin),
                'savi': self._obtener_indice_temporal_por_field_id(field_id, 'SAVI', fecha_inicio, fecha_fin),
                # ❌ EOSDA Weather API deshabilitado - no tiene cobertura en Colombia
                # Usamos Open-Meteo como alternativa (ver weather_service.py)
                'datos_clima': []
            }
            
            logger.info(f"Datos obtenidos exitosamente para field_id {field_id}")
            return datos_satelitales
            
        except Exception as e:
            logger.error(f"Error al obtener datos de EOSDA para {parcela.nombre}: {str(e)}")
            # Retornar datos simulados en caso de error
            return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
    
    def _obtener_indice_temporal_por_field_id(self, field_id: str, indice: str, 
                                            fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos temporales de un índice específico usando field_id de EOSDA
        VERSIÓN OPTIMIZADA: Usa field_id en lugar de geometría
        """
        try:
            # Endpoint de estadísticas según documentación oficial
            url = f"{self.base_url}/api/gdw/api"
            
            # Convertir fechas a formato ISO
            start_date = fecha_inicio.isoformat()
            end_date = fecha_fin.isoformat()
            
            # Mapear índices a nombres de EOSDA
            index_mapping = {
                'NDVI': 'ndvi',
                'NDMI': 'ndmi', 
                'SAVI': 'savi'
            }
            
            if indice not in index_mapping:
                logger.warning(f"Índice {indice} no soportado")
                return []
            
            # Parámetros según documentación de EOSDA Statistics API con field_id
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': [index_mapping[indice]],
                    'date_start': start_date,
                    'date_end': end_date,
                    'field_id': field_id,  # USAR FIELD_ID EN LUGAR DE GEOMETRY
                    'sensors': ['S2L2A'],  # Sentinel-2
                    'reference': f'{indice}_{field_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'limit': 50,  # Número de escenas
                    'max_cloud_cover_in_aoi': 80,
                    'exclude_cover_pixels': True,  # Enmascarar nubes
                    'cloud_masking_level': 3  # Máximo enmascarado
                }
            }
            
            logger.info(f"Solicitando datos {indice} para field_id {field_id} desde {start_date} hasta {end_date}")
            
            # Crear tarea
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"Error en API EOSDA para {indice}: {response.status_code} - {response.text[:200]}")
                return []
            
            # Obtener task_id de la respuesta
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                logger.error(f"No se obtuvo task_id para {indice}")
                return []
            
            # Esperar y obtener resultados
            return self._obtener_resultados_tarea(task_id, indice)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con EOSDA para {indice}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error procesando {indice}: {str(e)}")
            return []
    
    def _obtener_datos_climaticos_por_field_id(self, field_id: str, 
                                             fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos climáticos (temperatura y precipitación) desde EOSDA Weather API
        """
        try:
            # Weather API de EOSDA
            url = f"{self.base_url}/weather/history/{field_id}"
            
            params = {
                'date_start': fecha_inicio.isoformat(),
                'date_end': fecha_fin.isoformat()
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._procesar_datos_climaticos(data)
            elif response.status_code == 404:
                logger.info(f"No hay datos climáticos disponibles para field_id: {field_id}")
                return []
            else:
                logger.warning(f"Weather API error {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.warning(f"Error obteniendo datos climáticos: {str(e)}")
            return []
    
    def _obtener_indice_temporal(self, geojson: Dict, indice: str, 
                                fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos temporales de un índice específico usando API Statistics de EOSDA
        """
        try:
            # Endpoint de estadísticas según documentación oficial
            url = f"{self.base_url}/api/gdw/api"
            
            # Convertir fechas a formato ISO
            start_date = fecha_inicio.isoformat()
            end_date = fecha_fin.isoformat()
            
            # Mapear índices a nombres de EOSDA
            index_mapping = {
                'NDVI': 'ndvi',
                'NDMI': 'ndmi', 
                'SAVI': 'savi'
            }
            
            if indice not in index_mapping:
                logger.warning(f"Índice {indice} no soportado")
                return []
            
            # Parámetros según documentación de EOSDA Statistics API
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': [index_mapping[indice]],
                    'date_start': start_date,
                    'date_end': end_date,
                    'geometry': geojson,
                    'sensors': ['S2L2A'],  # Sentinel-2
                    'reference': f'{indice}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'limit': 50,  # Número de escenas
                    'max_cloud_cover_in_aoi': 80,
                    'exclude_cover_pixels': True,  # Enmascarar nubes
                    'cloud_masking_level': 3  # Máximo enmascarado
                }
            }
            
            logger.info(f"Solicitando datos {indice} desde {start_date} hasta {end_date}")
            
            # Crear tarea
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"Error en API EOSDA para {indice}: {response.status_code} - {response.text[:200]}")
                return []
            
            # Obtener task_id de la respuesta
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                logger.error(f"No se obtuvo task_id para {indice}")
                return []
            
            # Esperar y obtener resultados
            return self._obtener_resultados_tarea(task_id, indice)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con EOSDA para {indice}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error procesando {indice}: {str(e)}")
            return []

    def _obtener_resultados_tarea(self, task_id: str, indice: str, max_intentos: int = 20) -> List[Dict]:
        """
        Obtiene los resultados de una tarea asíncrona de EOSDA Statistics
        Aumentado a 20 intentos (100 segundos) para batch requests
        """
        try:
            url = f"{self.base_url}/api/gdw/api/{task_id}"
            
            for intento in range(max_intentos):
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"❌ Error consultando tarea {task_id}: {response.status_code}")
                    if response.status_code == 429:
                        logger.warning(f"Rate limit alcanzado en intento {intento+1}/{max_intentos}")
                        time.sleep(10)  # Esperar más en rate limit
                        continue
                    return []
                
                data = response.json()
                
                # Debug: Ver el estado completo de la respuesta
                logger.debug(f"Intento {intento+1}/{max_intentos} - Estado tarea: {data.get('status', 'unknown')}")
                
                # Verificar si hay resultados
                if 'result' in data and data['result']:
                    logger.info(f"✅ Datos obtenidos para {indice}: {len(data['result'])} escenas")
                    return self._procesar_datos_estadisticas(data['result'], indice)
                
                # Verificar si la tarea aún está procesando
                status = data.get('status')
                if status in ['pending', 'processing', 'running']:
                    logger.info(f"⏳ Tarea {task_id} aún procesando... ({intento+1}/{max_intentos})")
                
                # Verificar si hay errores
                if 'errors' in data and data['errors']:
                    logger.error(f"❌ Errores en tarea {task_id}: {data['errors'][:200]}")
                    return []
                
                # Esperar antes del siguiente intento
                if intento < max_intentos - 1:
                    time.sleep(5)  # 5 segundos entre intentos
            
            logger.warning(f"⏱️ Timeout esperando resultados para {indice}, tarea {task_id}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultados de tarea {task_id}: {str(e)}")
            return []

    def _procesar_datos_estadisticas(self, resultados: List[Dict], indice: str) -> List[Dict]:
        """
        Procesa los datos de estadísticas de EOSDA en formato estándar
        """
        try:
            datos_procesados = []
            
            for resultado in resultados:
                # Extraer información relevante
                fecha_str = resultado.get('date', '')
                if not fecha_str:
                    continue
                
                # Convertir fecha
                try:
                    fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                except:
                    continue
                
                # Usar el promedio como valor principal
                valor = resultado.get('average')
                if valor is None:
                    continue
                
                # Crear punto de datos
                punto_datos = {
                    'fecha': fecha,
                    'valor': round(float(valor), 4),
                    'indice': indice,
                    'metadatos': {
                        'scene_id': resultado.get('scene_id', ''),
                        'cloud_coverage': resultado.get('cloud', 0),
                        'min': resultado.get('min'),
                        'max': resultado.get('max'),
                        'std': resultado.get('std'),
                        'median': resultado.get('median')
                    }
                }
                
                datos_procesados.append(punto_datos)
            
            # Ordenar por fecha
            datos_procesados.sort(key=lambda x: x['fecha'])
            
            logger.info(f"Procesados {len(datos_procesados)} puntos de datos para {indice}")
            return datos_procesados
            
        except Exception as e:
            logger.error(f"Error procesando estadísticas para {indice}: {str(e)}")
            return []
    
    def _obtener_resultados_tarea_lento(self, task_id: str, max_intentos: int = 15) -> List[Dict]:
        """
        Obtiene resultados de tarea con delays más largos para evitar rate limits.
        Usa 10 segundos entre intentos (6 requests/minuto vs 10/minuto del API)
        """
        try:
            url = f"{self.base_url}/api/gdw/api/{task_id}"
            
            for intento in range(max_intentos):
                # Delay ANTES de cada petición (excepto la primera)
                if intento > 0:
                    logger.debug(f"⏳ Esperando 10s antes de intento {intento+1}...")
                    time.sleep(10)  # 10 segundos entre peticiones
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    if response.status_code == 429:
                        logger.warning(f"⚠️ Rate limit en intento {intento+1}/{max_intentos}, esperando 15s...")
                        time.sleep(15)
                        continue
                    logger.error(f"❌ Error {response.status_code} consultando tarea")
                    return []
                
                data = response.json()
                status = data.get('status', 'unknown')
                
                # Log de debug cada 3 intentos
                if intento % 3 == 0:
                    logger.debug(f"   Debug intento {intento+1}: status={status}, keys={list(data.keys())}")
                
                # Verificar si hay resultados
                if 'result' in data and data['result']:
                    logger.info(f"✅ Resultados obtenidos: {len(data['result'])} escenas")
                    return data['result']
                
                # Verificar si está procesando
                if status in ['pending', 'processing', 'running', 'unknown']:
                    if status == 'unknown':
                        logger.debug(f"   Status desconocido, continuando polling ({intento+1}/{max_intentos})")
                    else:
                        logger.info(f"   Procesando... ({intento+1}/{max_intentos}, status: {status})")
                    continue
                
                # Verificar errores
                if 'errors' in data and data['errors']:
                    logger.error(f"❌ Errores en tarea: {data['errors'][:300]}")
                    return []
                
                # Si no hay result ni está procesando, seguir intentando
                logger.debug(f"   Status: {status}, sin resultados aún")
            
            logger.warning(f"⏱️ Timeout después de {max_intentos} intentos ({max_intentos * 10}s)")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultados: {str(e)}")
            return []
    
    def _obtener_datos_climaticos(self, geojson: Dict, 
                                 fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos climatológicos (temperatura, precipitación)
        """
        try:
            url = f"{self.base_url}/weather/history"
            
            payload = {
                'geometry': geojson,
                'start_date': fecha_inicio.isoformat(),
                'end_date': fecha_fin.isoformat(),
                'parameters': ['temperature', 'precipitation', 'humidity']
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._procesar_datos_climaticos(data)
            else:
                logger.warning(f"Error en datos climáticos EOSDA: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener datos climáticos: {str(e)}")
            return []
    
    def _procesar_datos_temporales(self, data: Dict, indice: str) -> List[Dict]:
        """
        Procesa los datos temporales recibidos de la API
        """
        try:
            resultados = []
            
            # Extraer series temporales de la respuesta
            time_series = data.get('time_series', [])
            
            for entry in time_series:
                fecha = datetime.fromisoformat(entry.get('date', '')).date()
                valor_promedio = entry.get('mean', None)
                valor_max = entry.get('max', None)
                valor_min = entry.get('min', None)
                nubosidad = entry.get('cloud_coverage', 0)
                
                if valor_promedio is not None:
                    resultados.append({
                        'fecha': fecha,
                        'promedio': float(valor_promedio),
                        'maximo': float(valor_max) if valor_max else None,
                        'minimo': float(valor_min) if valor_min else None,
                        'nubosidad': float(nubosidad),
                        'indice': indice
                    })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando datos temporales de {indice}: {str(e)}")
            return []
    
    def _procesar_datos_climaticos(self, data: Dict) -> List[Dict]:
        """
        Procesa los datos climatológicos recibidos de la API
        """
        try:
            resultados = []
            
            weather_data = data.get('weather_data', [])
            
            for entry in weather_data:
                fecha = datetime.fromisoformat(entry.get('date', '')).date()
                
                resultados.append({
                    'fecha': fecha,
                    'temperatura_promedio': entry.get('temperature_avg'),
                    'temperatura_maxima': entry.get('temperature_max'),
                    'temperatura_minima': entry.get('temperature_min'),
                    'precipitacion_total': entry.get('precipitation_total'),
                    'humedad_promedio': entry.get('humidity_avg')
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando datos climáticos: {str(e)}")
            return []
    
    def _generar_datos_simulados(self, parcela, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Genera datos simulados para desarrollo y pruebas
        """
        import random
        import numpy as np
        
        logger.info(f"Generando datos simulados para {parcela.nombre}")
        
        # Generar fechas mensuales en el rango
        fechas = []
        fecha_actual = fecha_inicio.replace(day=1)  # Primer día del mes
        
        while fecha_actual <= fecha_fin:
            fechas.append(fecha_actual)
            # Siguiente mes
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
        
        # Generar datos NDVI simulados (0.2 a 0.9)
        ndvi_base = 0.5 + 0.3 * np.sin(np.linspace(0, 4*np.pi, len(fechas)))
        ndvi_data = []
        for i, fecha in enumerate(fechas):
            valor = max(0.2, min(0.9, ndvi_base[i] + random.uniform(-0.1, 0.1)))
            ndvi_data.append({
                'fecha': fecha,
                'promedio': round(valor, 3),
                'maximo': round(min(0.9, valor + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(0.2, valor - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'NDVI'
            })
        
        # Generar datos NDMI simulados (-0.5 a 0.5)
        ndmi_base = 0.1 + 0.3 * np.cos(np.linspace(0, 4*np.pi, len(fechas)))
        ndmi_data = []
        for i, fecha in enumerate(fechas):
            valor = max(-0.5, min(0.5, ndmi_base[i] + random.uniform(-0.1, 0.1)))
            ndmi_data.append({
                'fecha': fecha,
                'promedio': round(valor, 3),
                'maximo': round(min(0.5, valor + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(-0.5, valor - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'NDMI'
            })
        
        # Generar datos SAVI simulados (similar a NDVI pero ligeramente menor)
        savi_data = []
        for i, fecha in enumerate(fechas):
            valor_ndvi = ndvi_data[i]['promedio']
            valor_savi = valor_ndvi * 0.85  # SAVI típicamente menor que NDVI
            savi_data.append({
                'fecha': fecha,
                'promedio': round(valor_savi, 3),
                'maximo': round(min(0.8, valor_savi + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(0.1, valor_savi - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'SAVI'
            })
        
        # Generar datos climáticos simulados
        datos_clima = []
        for fecha in fechas:
            # Simular temperaturas según época del año (Colombia)
            mes = fecha.month
            temp_base = 22 if mes in [12, 1, 2] else 25  # Más frío en diciembre-febrero
            
            datos_clima.append({
                'fecha': fecha,
                'temperatura_promedio': round(temp_base + random.uniform(-3, 3), 1),
                'temperatura_maxima': round(temp_base + random.uniform(5, 8), 1),
                'temperatura_minima': round(temp_base - random.uniform(5, 8), 1),
                'precipitacion_total': round(random.uniform(50, 200), 1),
                'humedad_promedio': round(random.uniform(65, 85), 1)
            })
        
        return {
            'ndvi': ndvi_data,
            'ndmi': ndmi_data,
            'savi': savi_data,
            'datos_clima': datos_clima,
            'simulado': True
        }
    
    def obtener_imagen_satelital(self, parcela, fecha: date, indice: str = 'NDVI') -> Optional[str]:
        """
        Obtiene una imagen satelital de la parcela para una fecha específica
        Retorna la URL de la imagen o None si no está disponible
        """
        try:
            if not self.validar_configuracion():
                return None
            
            url = f"{self.base_url}/satellite/image"
            
            payload = {
                'geometry': parcela.coordenadas_dict,
                'date': fecha.isoformat(),
                'index': indice,
                'format': 'PNG',
                'resolution': 10
            }
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('image_url')
            else:
                logger.warning(f"No se pudo obtener imagen satelital: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error al obtener imagen satelital: {str(e)}")
            return None
    
    def verificar_conectividad(self) -> Dict[str, bool]:
        """
        Verifica la conectividad con la API Statistics de EOSDA
        """
        resultado = {
            'configuracion_valida': self.validar_configuracion(),
            'conexion_exitosa': False,
            'tiempo_respuesta': None,
            'task_id': None,
            'status': None,
            'mensaje': None
        }
        
        try:
            inicio = time.time()
            # Endpoint de statistics para verificar conectividad
            url = f"{self.base_url}/api/gdw/api"
            
            # Parámetros mínimos para crear una tarea de prueba
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': ['ndvi'],
                    'date_start': '2025-01-01',
                    'date_end': '2025-01-02',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [-74.1, 4.5],
                            [-74.0, 4.5], 
                            [-74.0, 4.6],
                            [-74.1, 4.6],
                            [-74.1, 4.5]
                        ]]
                    },
                    'sensors': ['S2L2A'],
                    'reference': 'connectivity_test',
                    'limit': 1,
                    'max_cloud_cover_in_aoi': 100
                }
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            resultado['tiempo_respuesta'] = round((time.time() - inicio) * 1000, 2)
            
            if response.status_code in [200, 201, 202]:
                resultado['conexion_exitosa'] = True
                data = response.json()
                resultado['task_id'] = data.get('task_id', 'N/A')
                resultado['status'] = data.get('status', 'N/A')
                resultado['mensaje'] = 'Conectado exitosamente'
                logger.info(f"Verificación EOSDA: Status {response.status_code}, Tiempo: {resultado['tiempo_respuesta']}ms")
            else:
                resultado['conexion_exitosa'] = False
                resultado['mensaje'] = f'Error: {response.status_code} - {response.text[:100]}'
                logger.warning(f"Verificación EOSDA fallida: Status {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error verificando conectividad EOSDA: {str(e)}")
            resultado['conexion_exitosa'] = False
            resultado['mensaje'] = f'Error de conexión: {str(e)}'
        
        return resultado
    
    # ========= MÉTODOS OPTIMIZADOS CON CACHÉ Y TRACKING =========
    
    def obtener_datos_optimizado(self, parcela, fecha_inicio: date, fecha_fin: date,
                                indices: List[str], usuario,
                                max_nubosidad: int = 50) -> Dict:
        """
        Método optimizado usando Statistics API de EOSDA con geometría:
        1. Consulta caché primero (0 requests si existe)
        2. Usa Statistics API con geometría (autenticación correcta)
        3. Hace UNA petición con todos los índices
        4. Polling con delays más largos para evitar rate limits
        5. Guarda en caché para futuras consultas
        
        Args:
            parcela: Parcela con geometría GeoJSON
            fecha_inicio: Fecha de inicio del análisis
            fecha_fin: Fecha de fin del análisis
            indices: Lista de índices a obtener ['ndvi', 'ndmi', 'savi']
            usuario: Usuario que hace la petición
            max_nubosidad: Porcentaje máximo de nubes (30-50)
            
        Returns:
            Dict con los datos satelitales organizados por índice
        """
        from informes.models import CacheDatosEOSDA, EstadisticaUsoEOSDA
        import json
        
        # Validar geometría y field_id
        field_id = parcela.eosda_field_id or f"parcela_{parcela.id}"
        
        try:
            geometria = json.loads(parcela.poligono_geojson) if parcela.poligono_geojson else None
            if not geometria:
                logger.error(f"❌ Parcela {parcela.nombre} no tiene geometría GeoJSON")
                return {'error': 'Sin geometría', 'resultados': []}
        except Exception as e:
            logger.error(f"❌ Error parseando geometría: {e}")
            return {'error': f'Error geometría: {str(e)}', 'resultados': []}
        
        tiempo_inicio = time.time()
        
        # 1. CONSULTAR CACHÉ PRIMERO
        datos_cache = CacheDatosEOSDA.obtener_o_none(
            field_id=field_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            indices=indices
        )
        
        if datos_cache:
            tiempo_respuesta = time.time() - tiempo_inicio
            
            # Registrar uso desde caché (0 requests consumidos)
            EstadisticaUsoEOSDA.registrar_uso(
                usuario=usuario,
                parcela=parcela,
                tipo_operacion='statistics',
                endpoint=f'/api/gdw/api (CACHE)',
                exitoso=True,
                tiempo_respuesta=tiempo_respuesta,
                requests_consumidos=0,
                desde_cache=True,
                cache_key=CacheDatosEOSDA.generar_cache_key(
                    field_id, fecha_inicio, fecha_fin, indices
                )
            )
            
            logger.info(f"✅ Datos obtenidos desde CACHÉ para field {field_id} - 0 requests consumidos")
            return datos_cache
        
        # 2. NO HAY CACHÉ - USAR STATISTICS API CON GEOMETRÍA
        logger.info(f"🔍 No hay caché, usando Statistics API - {len(indices)} índices en 1 petición")
        
        try:
            # UNA petición con TODOS los índices usando geometría
            url = f"{self.base_url}/api/gdw/api"
            
            # Convertir índices a mayúsculas (requerido por EOSDA)
            indices_mayusculas = [idx.upper() for idx in indices]
            
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': indices_mayusculas,  # NDVI, NDMI, SAVI en mayúsculas
                    'date_start': fecha_inicio.isoformat(),
                    'date_end': fecha_fin.isoformat(),
                    'geometry': geometria,  # Usar geometría
                    'sensors': ['S2L2A'],  # Sentinel-2 Level 2A
                    'reference': f'stats_{field_id}_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'limit': 50,
                    'max_cloud_cover_in_aoi': max_nubosidad,
                    'exclude_cover_pixels': True,
                    'cloud_masking_level': 3
                }
            }
            
            logger.info(f"📡 Enviando petición Statistics API: {len(indices)} índices")
            logger.info(f"   Índices: {', '.join(indices_mayusculas)}")
            logger.info(f"   Geometría: {geometria['type']} con {len(geometria.get('coordinates', [[]])[0])} puntos")
            
            response = self.session.post(url, json=payload, timeout=60)
            tiempo_respuesta = time.time() - tiempo_inicio
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"❌ Error EOSDA: {response.status_code}")
                logger.error(f"   Respuesta: {response.text[:500]}")
                
                # Registrar fallo
                EstadisticaUsoEOSDA.registrar_uso(
                    usuario=usuario,
                    parcela=parcela,
                    tipo_operacion='statistics',
                    endpoint=url,
                    exitoso=False,
                    tiempo_respuesta=tiempo_respuesta,
                    requests_consumidos=1,
                    codigo_respuesta=response.status_code,
                    mensaje_error=response.text[:500]
                )
                
                return {'error': f'Error HTTP {response.status_code}', 'resultados': []}
            
            # Obtener task_id
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                logger.error("❌ No se obtuvo task_id de EOSDA")
                return {'error': 'No task_id', 'resultados': []}
            
            logger.info(f"✅ Tarea creada: {task_id}")
            
            # 3. ESPERAR RESULTADOS CON DELAYS MÁS LARGOS
            logger.info(f"⏳ Esperando resultados (delays de 10s para evitar rate limits)...")
            resultados = self._obtener_resultados_tarea_lento(task_id)
            
            if not resultados:
                logger.warning(f"⚠️ No se obtuvieron resultados para tarea {task_id}")
                return {'error': 'Sin resultados', 'resultados': []}
            
            # 4. DATOS CLIMÁTICOS - DESHABILITADO
            # ❌ EOSDA Weather API no tiene cobertura en Colombia
            # Se usa Open-Meteo como alternativa (ver weather_service.py en views.py)
            logger.info(f"ℹ️ Datos climáticos: usando Open-Meteo (EOSDA Weather deshabilitado)")
            datos_clima = []
            
            # 5. GUARDAR EN CACHÉ
            datos_formateados = {
                'resultados': resultados,
                'datos_clima': datos_clima,  # Siempre vacío - Open-Meteo se usa en views.py
                'field_id': field_id,
                'indices': indices,
                'fecha_consulta': datetime.now().isoformat(),
                'num_escenas': len(resultados),
                'metodo': 'statistics_api'
            }
            
            CacheDatosEOSDA.guardar_datos(
                field_id=field_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                indices=indices,
                datos=datos_formateados,
                task_id=task_id
            )
            
            # 6. REGISTRAR ESTADÍSTICAS
            tiempo_total = time.time() - tiempo_inicio
            EstadisticaUsoEOSDA.registrar_uso(
                usuario=usuario,
                parcela=parcela,
                tipo_operacion='statistics',
                endpoint=url,
                exitoso=True,
                tiempo_respuesta=tiempo_total,
                requests_consumidos=1,  # 1 request inicial + polling
                codigo_respuesta=response.status_code
            )
            
            logger.info(f"✅ Datos obtenidos - 1 petición, {len(resultados)} escenas, {len(datos_clima)} clima, {tiempo_total:.1f}s")
            return datos_formateados
            
        except requests.exceptions.Timeout:
            tiempo_respuesta = time.time() - tiempo_inicio
            EstadisticaUsoEOSDA.registrar_uso(
                usuario=usuario,
                parcela=parcela,
                tipo_operacion='statistics',
                endpoint=f'{self.base_url}/api/gdw/api',
                exitoso=False,
                tiempo_respuesta=tiempo_respuesta,
                mensaje_error='Timeout'
            )
            logger.error("❌ Timeout en petición Statistics API")
            return {'error': 'Timeout', 'resultados': []}
            
        except Exception as e:
            tiempo_respuesta = time.time() - tiempo_inicio
            EstadisticaUsoEOSDA.registrar_uso(
                usuario=usuario,
                parcela=parcela,
                tipo_operacion='statistics',
                endpoint=f'{self.base_url}/api/gdw/api',
                exitoso=False,
                tiempo_respuesta=tiempo_respuesta,
                mensaje_error=str(e)
            )
            logger.error(f"❌ Error obteniendo datos: {str(e)}", exc_info=True)
            return {'error': str(e), 'resultados': []}
    
    def descargar_imagen_satelital(self, field_id: str, indice: str, 
                                   view_id: str = None,
                                   fecha_escena: str = None,
                                   max_nubosidad: float = 50.0) -> Optional[Dict]:
        """
        Descarga imagen satelital usando Field Imagery API de EOSDA.
        
        OPTIMIZADO para reducir consumo de requests:
        - Si se proporciona view_id directamente, solo hace ~7 requests (1 POST + 6 GET polling)
        - Si no hay view_id, retorna None para evitar búsquedas costosas
        
        Args:
            field_id: ID del campo en EOSDA
            indice: Tipo de índice ('NDVI', 'NDMI', 'SAVI')
            view_id: ID de la vista satelital (RECOMENDADO - ahorra ~15 requests)
            fecha_escena: Fecha de escena específica (formato ISO) - para logging
            max_nubosidad: Máximo porcentaje de nubosidad (default 50%)
        
        Returns:
            Dict con 'imagen' (bytes), 'fecha', 'nubosidad', 'view_id' o None si falla
        """
        try:
            # Mapeo de índices
            index_mapping = {
                'NDVI': 'ndvi',
                'NDMI': 'ndmi',
                'SAVI': 'savi'
            }
            
            if indice not in index_mapping:
                logger.error(f"   ❌ Índice '{indice}' no soportado. Usar: NDVI, NDMI, SAVI")
                return None
            
            eosda_index = index_mapping[indice]
            logger.info(f"   📷 Descargando imagen {indice} para field {field_id}")
            
            # ✅ OPTIMIZACIÓN: Requerir view_id para evitar búsquedas costosas
            if not view_id:
                logger.warning(f"   ⚠️ No se proporcionó view_id")
                logger.warning(f"   💡 Recomendación: Obtener datos de Statistics API primero para obtener view_ids")
                return None
            
            fecha_imagen = fecha_escena
            nubosidad = None  # Se calculará del registro si está disponible
            
            # Paso 1: Crear request para generar imagen
            url_imagery = f"{self.base_url}/field-imagery/indicies/{field_id}"
            
            payload_imagen = {
                'params': {
                    'view_id': view_id,
                    'index': indice,  # ✅ Usar el índice en MAYÚSCULAS (NDVI, NDMI, SAVI)
                    'format': 'png'
                }
            }
            
            logger.info(f"   🎨 Generando imagen {indice} (view_id: {view_id})...")
            response = self.session.post(url_imagery, json=payload_imagen, timeout=60)
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"   ❌ Error creando request de imagen: {response.status_code}")
                logger.debug(f"   Response: {response.text[:300]}")
                return None
            
            request_id = response.json().get('request_id')
            if not request_id:
                logger.error(f"   ❌ No se obtuvo request_id para imagen")
                return None
            
            # Paso 2: Polling para descargar imagen (máximo 120 segundos, 12 intentos)
            url_download = f"{self.base_url}/field-imagery/{field_id}/{request_id}"
            max_intentos = 12  # 12 intentos x 10 segundos = 2 minutos máximo
            intervalo = 10  # 10 segundos entre intentos
            
            for intento in range(max_intentos):
                time.sleep(intervalo)
                
                logger.info(f"   ⏳ Esperando imagen... intento {intento + 1}/{max_intentos}")
                response = self.session.get(url_download, timeout=60)
                
                logger.debug(f"   Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    content_length = int(response.headers.get('Content-Length', 0))
                    
                    # ✅ Verificar si es imagen por Content-Type O por tamaño > 1KB
                    if 'image' in content_type or 'octet-stream' in content_type or content_length > 1000:
                        # Verificar que sea PNG válido
                        if response.content[:4] == b'\x89PNG' or len(response.content) > 1000:
                            logger.info(f"   ✅ Imagen {indice} descargada ({len(response.content)} bytes)")
                            return {
                                'imagen': response.content,
                                'fecha': fecha_imagen,
                                'nubosidad': nubosidad,
                                'view_id': view_id,
                                'content_type': 'image/png'
                            }
                    
                    # Si no es imagen, revisar si es JSON con estado
                    try:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        logger.debug(f"   ⏳ Estado: {status}")
                        if status in ['failed', 'error']:
                            logger.error(f"   ❌ Error en generación: {data.get('error', 'Unknown')}")
                            return None
                    except:
                        pass
                    logger.debug(f"   ⏳ Imagen aún en proceso...")
                    continue
                elif response.status_code == 404:
                    logger.debug(f"   ⏳ Imagen no lista aún...")
                    continue
                else:
                    logger.error(f"   ❌ Error descargando imagen: {response.status_code}")
                    logger.debug(f"   Response: {response.text[:200]}")
                    return None
            
            logger.warning(f"   ⏱️ Timeout esperando generación de imagen {indice}")
            return None
            
        except Exception as e:
            logger.error(f"   ❌ Error descargando imagen {indice}: {str(e)}")
            return None


# Instancia global del servicio
eosda_service = EosdaAPIService()