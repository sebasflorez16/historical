"""
Servicio de integración con Google Gemini AI para análisis de informes agrícolas
Genera análisis inteligentes de datos satelitales, climáticos e imágenes
"""

import os
import logging
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Servicio para interactuar con Google Gemini AI
    Especializado en análisis agrícola y satelital
    """
    
    def __init__(self):
        """Inicializar el servicio con la API Key desde settings"""
        # Primero intentar desde settings, luego desde env
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY no configurada en .env o settings.py")
            raise ValueError("GEMINI_API_KEY no está configurada")
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Usar modelo Gemini 2.5 Flash (más económico y rápido)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        logger.info("✅ GeminiService inicializado correctamente")
    
    def generar_analisis_informe(
        self, 
        parcela_data: Dict[str, Any],
        indices_mensuales: List[Dict[str, Any]],
        imagenes_paths: Optional[List[str]] = None,
        tipo_analisis: str = 'completo'
    ) -> Dict[str, str]:
        """
        Genera un análisis completo para un informe agrícola
        
        Args:
            parcela_data: Diccionario con info de la parcela (nombre, área, cultivo, etc.)
            indices_mensuales: Lista de diccionarios con datos mensuales (NDVI, clima, etc.)
            imagenes_paths: Lista de rutas a imágenes satelitales (opcional)
            tipo_analisis: 'completo', 'resumen', 'tendencias', 'recomendaciones'
        
        Returns:
            Dict con: resumen_ejecutivo, analisis_tendencias, recomendaciones, alertas
        """
        try:
            logger.info(f"🤖 Generando análisis con Gemini para parcela {parcela_data.get('nombre')}")
            
            # Construir el prompt
            prompt = self._construir_prompt(parcela_data, indices_mensuales, tipo_analisis)
            
            # Preparar contenido (texto + imágenes si existen)
            contenido = [prompt]
            
            if imagenes_paths:
                contenido.extend(self._cargar_imagenes(imagenes_paths))
            
            # Generar respuesta
            response = self.model.generate_content(contenido)
            
            # Procesar respuesta
            texto_completo = response.text
            
            # Parsear secciones
            resultado = self._parsear_respuesta(texto_completo, tipo_analisis)
            
            logger.info(f"✅ Análisis generado exitosamente ({len(texto_completo)} caracteres)")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error generando análisis con Gemini: {str(e)}")
            return {
                'error': str(e),
                'resumen_ejecutivo': 'Error al generar análisis automático.',
                'analisis_tendencias': '',
                'recomendaciones': '',
                'alertas': ''
            }
    
    def _construir_prompt(
        self, 
        parcela_data: Dict[str, Any],
        indices_mensuales: List[Dict[str, Any]],
        tipo_analisis: str
    ) -> str:
        """Construir el prompt especializado para análisis agrícola con análisis espacial y visual"""
        
        # Información de la parcela
        nombre = parcela_data.get('nombre', 'Parcela sin nombre')
        area = parcela_data.get('area_hectareas', 0)
        cultivo = parcela_data.get('tipo_cultivo', 'No especificado')
        propietario = parcela_data.get('propietario', 'No especificado')
        coordenadas_parcela = parcela_data.get('coordenadas', {})
        
        # Construir tabla de datos mensuales
        tabla_datos = self._construir_tabla_datos(indices_mensuales)
        
        # Construir descripción de imágenes con metadatos espaciales
        desc_imagenes = self._construir_descripcion_imagenes_espacial(indices_mensuales)
        
        # Análisis comparativo visual entre meses
        analisis_comparativo = self._construir_analisis_comparativo_visual(indices_mensuales)
        
        # Información espacial de la parcela
        info_espacial = ""
        if coordenadas_parcela:
            centroide = coordenadas_parcela.get('centroide', {})
            bbox = coordenadas_parcela.get('bbox', {})
            if centroide:
                info_espacial = f"""
**UBICACIÓN ESPACIAL DE LA PARCELA:**
- Centroide: Latitud {centroide.get('lat', 'N/A'):.4f}, Longitud {centroide.get('lng', 'N/A'):.4f}
- Bounding Box: {bbox.get('min_lat', 'N/A'):.4f}°N - {bbox.get('max_lat', 'N/A'):.4f}°N, {bbox.get('min_lon', 'N/A'):.4f}°W - {bbox.get('max_lon', 'N/A'):.4f}°W
- Para referencias espaciales, usa: "zona norte" (cerca de {bbox.get('max_lat', 'N/A'):.4f}°N), "zona sur" (cerca de {bbox.get('min_lat', 'N/A'):.4f}°N), "zona este" (cerca de {bbox.get('max_lon', 'N/A'):.4f}°W), "zona oeste" (cerca de {bbox.get('min_lon', 'N/A'):.4f}°W)
"""
        
        # Prompt base mejorado con análisis espacial y visual
        prompt = f"""Eres un ingeniero agrónomo experto en teledetección y análisis satelital agrícola con 20 años de experiencia. 
Analiza la siguiente información de la parcela "{nombre}" ubicada en Colombia, dedicada a {cultivo}, con un área de {area:.2f} hectáreas, propiedad de {propietario}.

{info_espacial}

**DATOS NUMÉRICOS MENSUALES:**

{tabla_datos}

**IMÁGENES SATELITALES DISPONIBLES (Con Metadatos Espaciales):**
{desc_imagenes}

**ANÁLISIS COMPARATIVO VISUAL ENTRE MESES:**
{analisis_comparativo}

**TU TAREA - ANÁLISIS ESPACIALMENTE CONSCIENTE:**

1. **ANÁLISIS NUMÉRICO:** Analiza comparativamente mes a mes los índices de vegetación (NDVI, NDMI, SAVI).

2. **ANÁLISIS VISUAL Y ESPACIAL:** Si hay imágenes disponibles, identifica:
   - Cambios de color entre meses (ej: "zona sur más verde en Marzo vs Febrero")
   - Patrones espaciales de vegetación (ej: "mayor vigor en zona norte", "estrés visible en zona este")
   - Variaciones dentro de la parcela (ej: "heterogeneidad norte-sur", "uniformidad este-oeste")
   - Diferencias visuales en las imágenes NDVI/NDMI/SAVI entre meses consecutivos

3. **CONTEXTO GEOGRÁFICO:** Usa las coordenadas para hacer referencias espaciales precisas:
   - "zona norte" (latitudes mayores)
   - "zona sur" (latitudes menores)
   - "zona este" (longitudes mayores/menos negativas)
   - "zona oeste" (longitudes menores/más negativas)

4. **METADATOS DE CALIDAD:** Considera:
   - Nubosidad de cada imagen (>40% = calidad reducida)
   - Fechas de captura satelital (gaps temporales)
   - Resolución espacial (detalle disponible)
   - Satélite fuente (Sentinel-2 = 10m, Landsat = 30m)

5. **TENDENCIAS Y ANOMALÍAS:** Detecta:
   - Cambios significativos en salud vegetal (temporal y espacial)
   - Patrones climáticos que expliquen las variaciones observadas
   - Períodos críticos (estrés hídrico, exceso de humedad, bajas temperaturas)

6. **RECOMENDACIONES ESPACIALMENTE ESPECÍFICAS:** Proporciona acciones concretas:
   - Zonas específicas que requieren atención (ej: "inspeccionar zona sur por baja NDVI")
   - Acciones diferenciadas por área de la parcela si hay heterogeneidad
   - Monitoreo focalizado en zonas de cambio

**FORMATO DE RESPUESTA:**
Estructura tu respuesta EXACTAMENTE con estas secciones (usa estos títulos literales):

### RESUMEN EJECUTIVO
[Escribe un resumen claro y conciso de 200-300 palabras sobre el estado general de la parcela, incluyendo referencias espaciales y visuales si hay imágenes disponibles]

### ANÁLISIS DE TENDENCIAS
[Analiza mes a mes las tendencias numéricas y visuales. Identifica patrones espaciales y temporales. Menciona zonas específicas si hay heterogeneidad visible]

### ANÁLISIS VISUAL DE IMÁGENES
[Si hay imágenes: describe cambios de color, patrones espaciales, y variaciones visuales entre meses. Usa referencias como "zona norte/sur/este/oeste". Si no hay imágenes: escribe "Análisis visual no disponible - sin imágenes satelitales"]

### RECOMENDACIONES
[Lista 4-6 recomendaciones prácticas y específicas. Incluye acciones espacialmente focalizadas si hay heterogeneidad. Prioriza por urgencia]

### ALERTAS
[Identifica situaciones críticas, incluyendo alertas espaciales (ej: "zona sur requiere inspección urgente"). Si no hay alertas: "No se detectaron alertas críticas"]

**IMPORTANTE:**
- Usa lenguaje profesional pero comprensible para un agricultor.
- Sé específico con meses, valores, y zonas espaciales.
- Si hay imágenes, describe lo que ves visualmente.
- Si los datos son limitados o de baja calidad, indícalo claramente.
- Enfócate en información accionable, no solo descriptiva.
- Las referencias espaciales hacen el análisis más útil y específico.
"""
        
        return prompt
    
    def _construir_tabla_datos(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """Construir tabla de datos mensuales en formato texto"""
        if not indices_mensuales:
            return "No hay datos mensuales disponibles."
        
        tabla = "| Mes | NDVI | NDMI | SAVI | Nubosidad | Temp (°C) | Precip (mm) | Calidad |\n"
        tabla += "|-----|------|------|------|-----------|-----------|-------------|----------|\n"
        
        for dato in indices_mensuales:
            mes = dato.get('periodo', 'N/A')
            ndvi = f"{dato.get('ndvi_promedio', 0):.3f}" if dato.get('ndvi_promedio') else 'N/A'
            ndmi = f"{dato.get('ndmi_promedio', 0):.3f}" if dato.get('ndmi_promedio') else 'N/A'
            savi = f"{dato.get('savi_promedio', 0):.3f}" if dato.get('savi_promedio') else 'N/A'
            nubosidad = f"{dato.get('nubosidad_promedio', 0):.1f}%" if dato.get('nubosidad_promedio') else 'N/A'
            temp = f"{dato.get('temperatura_promedio', 0):.1f}" if dato.get('temperatura_promedio') else 'N/A'
            precip = f"{dato.get('precipitacion_total', 0):.1f}" if dato.get('precipitacion_total') else 'N/A'
            calidad = dato.get('calidad_datos', 'N/A')
            
            tabla += f"| {mes} | {ndvi} | {ndmi} | {savi} | {nubosidad} | {temp} | {precip} | {calidad} |\n"
        
        return tabla
    
    def _construir_descripcion_imagenes(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """Construir descripción de las imágenes disponibles (versión simple, legacy)"""
        desc = []
        for dato in indices_mensuales:
            mes = dato.get('periodo', 'N/A')
            tiene_ndvi = dato.get('tiene_imagen_ndvi', False)
            tiene_ndmi = dato.get('tiene_imagen_ndmi', False)
            tiene_savi = dato.get('tiene_imagen_savi', False)
            nubosidad = dato.get('nubosidad_imagen', 0)
            
            if tiene_ndvi or tiene_ndmi or tiene_savi:
                imagenes = []
                if tiene_ndvi:
                    imagenes.append('NDVI')
                if tiene_ndmi:
                    imagenes.append('NDMI')
                if tiene_savi:
                    imagenes.append('SAVI')
                
                desc.append(f"- **{mes}**: Imágenes disponibles: {', '.join(imagenes)} (Nubosidad: {nubosidad:.1f}%)")
        
        if not desc:
            return "No hay imágenes satelitales adjuntas en este análisis."
        
        return "\n".join(desc)
    
    def _construir_descripcion_imagenes_espacial(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """Construir descripción detallada de imágenes con metadatos espaciales completos"""
        desc = []
        for dato in indices_mensuales:
            mes = dato.get('periodo', 'N/A')
            tiene_ndvi = dato.get('tiene_imagen_ndvi', False)
            tiene_ndmi = dato.get('tiene_imagen_ndmi', False)
            tiene_savi = dato.get('tiene_imagen_savi', False)
            
            if tiene_ndvi or tiene_ndmi or tiene_savi:
                imagenes = []
                if tiene_ndvi:
                    imagenes.append('NDVI')
                if tiene_ndmi:
                    imagenes.append('NDMI')
                if tiene_savi:
                    imagenes.append('SAVI')
                
                # Metadatos de la imagen
                nubosidad = dato.get('nubosidad_imagen', 0)
                fecha_captura = dato.get('fecha_imagen', 'N/A')
                satelite = dato.get('satelite_imagen', 'N/A')
                resolucion = dato.get('resolucion_imagen', 'N/A')
                coordenadas = dato.get('coordenadas_imagen', {})
                metadatos = dato.get('metadatos_imagen', {})
                
                # Construir descripción completa
                desc_mes = f"- **{mes}**: Imágenes {', '.join(imagenes)}\n"
                desc_mes += f"  - Fecha captura: {fecha_captura}\n"
                desc_mes += f"  - Satélite: {satelite} | Resolución: {resolucion}m/píxel\n"
                desc_mes += f"  - Nubosidad: {nubosidad:.1f}%\n"
                
                if coordenadas:
                    if isinstance(coordenadas, list) and len(coordenadas) == 4:
                        min_lat, min_lon, max_lat, max_lon = coordenadas
                        desc_mes += f"  - Área cubierta: {min_lat:.4f}°N-{max_lat:.4f}°N, {min_lon:.4f}°W-{max_lon:.4f}°W\n"
                    elif isinstance(coordenadas, dict):
                        desc_mes += f"  - Coordenadas: {coordenadas}\n"
                
                if metadatos:
                    view_id = metadatos.get('view_id', 'N/A')
                    cloud_cover = metadatos.get('cloud_cover', nubosidad)
                    desc_mes += f"  - View ID: {view_id} | Cloud Cover: {cloud_cover:.1f}%\n"
                
                desc.append(desc_mes)
        
        if not desc:
            return "No hay imágenes satelitales adjuntas en este análisis. El análisis se basará únicamente en datos numéricos."
        
        return "\n".join(desc)
    
    def _construir_analisis_comparativo_visual(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """Construir análisis comparativo visual mes a mes basado en cambios de índices"""
        if len(indices_mensuales) < 2:
            return "No hay suficientes meses para análisis comparativo visual."
        
        analisis = []
        for i in range(1, len(indices_mensuales)):
            mes_actual = indices_mensuales[i]
            mes_anterior = indices_mensuales[i-1]
            
            periodo_actual = mes_actual.get('periodo', 'N/A')
            periodo_anterior = mes_anterior.get('periodo', 'N/A')
            
            # Calcular cambios en índices
            ndvi_actual = mes_actual.get('ndvi_promedio', 0)
            ndvi_anterior = mes_anterior.get('ndvi_promedio', 0)
            cambio_ndvi = ndvi_actual - ndvi_anterior if (ndvi_actual and ndvi_anterior) else 0
            
            ndmi_actual = mes_actual.get('ndmi_promedio', 0)
            ndmi_anterior = mes_anterior.get('ndmi_promedio', 0)
            cambio_ndmi = ndmi_actual - ndmi_anterior if (ndmi_actual and ndmi_anterior) else 0
            
            # Solo reportar cambios significativos
            if abs(cambio_ndvi) > 0.05 or abs(cambio_ndmi) > 0.05:
                tendencia_ndvi = "aumentó" if cambio_ndvi > 0 else "disminuyó"
                tendencia_ndmi = "aumentó" if cambio_ndmi > 0 else "disminuyó"
                
                desc_cambio = f"**{periodo_anterior} → {periodo_actual}:**\n"
                
                if abs(cambio_ndvi) > 0.05:
                    desc_cambio += f"  - NDVI {tendencia_ndvi} {abs(cambio_ndvi):.3f} ({ndvi_anterior:.3f} → {ndvi_actual:.3f})"
                    if cambio_ndvi > 0.1:
                        desc_cambio += " ⬆️ INCREMENTO NOTABLE"
                    elif cambio_ndvi < -0.1:
                        desc_cambio += " ⬇️ DECREMENTO NOTABLE"
                    desc_cambio += "\n"
                
                if abs(cambio_ndmi) > 0.05:
                    desc_cambio += f"  - NDMI {tendencia_ndmi} {abs(cambio_ndmi):.3f} ({ndmi_anterior:.3f} → {ndmi_actual:.3f})"
                    if cambio_ndmi > 0.1:
                        desc_cambio += " ⬆️ MÁS HUMEDAD"
                    elif cambio_ndmi < -0.1:
                        desc_cambio += " ⬇️ MENOS HUMEDAD"
                    desc_cambio += "\n"
                
                # Agregar interpretación visual
                if cambio_ndvi > 0.1:
                    desc_cambio += "  → Visual: Probable aumento en vegetación/verdor visible en imágenes\n"
                elif cambio_ndvi < -0.1:
                    desc_cambio += "  → Visual: Probable disminución en vegetación/verdor visible en imágenes\n"
                
                analisis.append(desc_cambio)
        
        if not analisis:
            return "No se detectaron cambios visuales significativos entre meses consecutivos (variaciones <5%)."
        
        return "\n".join(analisis)
    
    def _parsear_respuesta(self, texto: str, tipo_analisis: str) -> Dict[str, str]:
        """Parsear la respuesta de Gemini en secciones estructuradas, incluyendo análisis visual"""
        resultado = {
            'resumen_ejecutivo': '',
            'analisis_tendencias': '',
            'analisis_visual': '',
            'recomendaciones': '',
            'alertas': '',
            'texto_completo': texto
        }
        
        try:
            # Buscar secciones por marcadores
            secciones = {
                'resumen_ejecutivo': ['### RESUMEN EJECUTIVO', '### ANÁLISIS DE TENDENCIAS'],
                'analisis_tendencias': ['### ANÁLISIS DE TENDENCIAS', '### ANÁLISIS VISUAL'],
                'analisis_visual': ['### ANÁLISIS VISUAL DE IMÁGENES', '### RECOMENDACIONES'],
                'recomendaciones': ['### RECOMENDACIONES', '### ALERTAS'],
                'alertas': ['### ALERTAS', None]
            }
            
            for clave, (inicio, fin) in secciones.items():
                idx_inicio = texto.find(inicio)
                if idx_inicio == -1:
                    continue
                
                # Saltar el título
                idx_inicio += len(inicio)
                
                # Buscar el fin
                if fin:
                    idx_fin = texto.find(fin, idx_inicio)
                    if idx_fin == -1:
                        idx_fin = len(texto)
                else:
                    idx_fin = len(texto)
                
                # Extraer y limpiar
                contenido = texto[idx_inicio:idx_fin].strip()
                resultado[clave] = contenido
            
            # Si no se encontraron marcadores, usar todo como resumen
            if not any([resultado['resumen_ejecutivo'], resultado['analisis_tendencias']]):
                resultado['resumen_ejecutivo'] = texto
            
        except Exception as e:
            logger.error(f"❌ Error parseando respuesta: {str(e)}")
            resultado['resumen_ejecutivo'] = texto
        
        return resultado
    
    def probar_conexion(self) -> Dict[str, Any]:
        """Probar la conexión con Gemini API"""
        try:
            logger.info("🧪 Probando conexión con Gemini API...")
            
            # Hacer una consulta simple
            response = self.model.generate_content("Di 'Conexión exitosa' si puedes leer esto.")
            
            logger.info(f"✅ Respuesta de Gemini: {response.text}")
            
            return {
                'exito': True,
                'mensaje': 'Conexión exitosa con Gemini API',
                'respuesta': response.text
            }
            
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {str(e)}")
            return {
                'exito': False,
                'error': str(e)
            }
    
    def analizar_imagen_satelital(
        self,
        imagen_path: str,
        tipo_indice: str,
        valor_promedio: float,
        datos_contexto: Dict[str, Any],
        mes_anterior_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera análisis visual específico de una imagen satelital usando Gemini Vision
        
        Args:
            imagen_path: Ruta a la imagen
            tipo_indice: 'NDVI', 'NDMI' o 'SAVI'
            valor_promedio: Valor promedio del índice
            datos_contexto: Dict con fecha, satélite, coordenadas, etc.
            mes_anterior_data: Datos del mes anterior para comparación temporal
        
        Returns:
            Análisis visual detallado en HTML
        """
        try:
            # Cargar imagen
            imagen = self._cargar_imagen_individual(imagen_path)
            
            # Construir prompt específico para análisis visual
            prompt = f"""
Eres un experto en análisis de imágenes satelitales agrícolas. Analiza esta imagen {tipo_indice} y proporciona un análisis visual DETALLADO Y ESPECÍFICO.

**CONTEXTO:**
- Índice: {tipo_indice} ({self._get_descripcion_indice(tipo_indice)})
- Valor promedio: {valor_promedio:.3f}
- Fecha de captura: {datos_contexto.get('fecha', 'N/A')}
- Satélite: {datos_contexto.get('satelite', 'N/A')}
- Coordenadas: {datos_contexto.get('coordenadas', 'N/A')}
- Resolución: {datos_contexto.get('resolucion', 10)}m/píxel
- Nubosidad: {datos_contexto.get('nubosidad', 0):.1f}%
"""
            
            # Agregar contexto de mes anterior si existe
            if mes_anterior_data:
                prompt += f"""
- Mes anterior ({mes_anterior_data.get('fecha', 'N/A')}): {mes_anterior_data.get('tipo_indice', tipo_indice)} = {mes_anterior_data.get('valor', 0):.3f}
- Cambio respecto al mes anterior: {valor_promedio - mes_anterior_data.get('valor', valor_promedio):.3f}
"""
            
            prompt += f"""

**INSTRUCCIONES DE ANÁLISIS:**

1. **INTERPRETACIÓN VISUAL DIRECTA** (2-3 líneas):
   - Describe lo que VES en la imagen: colores predominantes, patrones, distribución
   - Interpreta estos colores según la escala {tipo_indice} (valores bajos/altos, qué significan)

2. **ANÁLISIS ESPACIAL DETALLADO** (3-4 líneas):
   - Identifica ZONAS ESPECÍFICAS: "zona norte/sur/este/oeste", "esquina superior derecha", "centro de la parcela"
   - Describe PATRONES: áreas homogéneas vs heterogéneas, gradientes, manchas
   - Explica QUÉ INDICAN estos patrones: zonas de mejor/peor condición, posibles causas

3. **VARIABILIDAD INTRAPARCELA** (2-3 líneas):
   - Rangos de valores visibles (del color más claro al más oscuro)
   - Qué zonas se destacan positiva o negativamente
   - Posibles explicaciones agronómicas (riego, topografía, suelo)

"""
            
            # Si hay comparación temporal, agregar instrucciones específicas
            if mes_anterior_data:
                prompt += """
4. **COMPARACIÓN TEMPORAL** (3-4 líneas):
   - Describe cómo ha CAMBIADO visualmente la imagen respecto al mes anterior
   - Qué áreas han mejorado o empeorado
   - Interpretación agronómica del cambio (crecimiento del cultivo, estrés, cosecha, etc.)

"""
            
            prompt += f"""
**FORMATO DE RESPUESTA:**
Escribe en párrafos cortos y concisos, usando lenguaje técnico pero accesible.
Usa <strong> para términos clave y <br/> para separar secciones.
Sé ESPECÍFICO con las ubicaciones espaciales ("zona sur muestra...", "en la esquina noreste se observa...").
Máximo 300 palabras.

Valor de referencia del índice: {valor_promedio:.3f}
"""
            
            # Generar análisis
            response = self.model.generate_content([prompt, imagen])
            
            analisis = response.text
            
            # Limpiar y formatear
            analisis = self._limpiar_texto_para_pdf(analisis)
            
            logger.info(f"✅ Análisis visual generado para {tipo_indice} ({len(analisis)} caracteres)")
            
            return analisis
            
        except Exception as e:
            logger.error(f"❌ Error analizando imagen {tipo_indice}: {str(e)}")
            # Retornar análisis básico como fallback
            return self._generar_analisis_basico_fallback(tipo_indice, valor_promedio)
    
    def _cargar_imagen_individual(self, imagen_path: str):
        """Carga una imagen individual para enviar a Gemini"""
        try:
            from PIL import Image as PILImage
            
            img = PILImage.open(imagen_path)
            
            # Redimensionar si es muy grande (optimización de costos)
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, PILImage.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.error(f"❌ Error cargando imagen {imagen_path}: {str(e)}")
            raise
    
    def _get_descripcion_indice(self, tipo_indice: str) -> str:
        """Retorna descripción del índice para el prompt"""
        descripciones = {
            'NDVI': 'Normalized Difference Vegetation Index - mide salud y vigor vegetal',
            'NDMI': 'Normalized Difference Moisture Index - mide contenido de humedad en vegetación',
            'SAVI': 'Soil Adjusted Vegetation Index - mide cobertura vegetal ajustando efecto del suelo'
        }
        return descripciones.get(tipo_indice, 'índice de vegetación')
    
    def _generar_analisis_basico_fallback(self, tipo_indice: str, valor_promedio: float) -> str:
        """Genera análisis básico si Gemini falla"""
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.7:
                return "La imagen muestra <strong>vegetación muy vigorosa</strong> con alta densidad de biomasa."
            elif valor_promedio >= 0.5:
                return "La imagen muestra <strong>vegetación saludable</strong> con desarrollo normal."
            elif valor_promedio >= 0.3:
                return "La imagen muestra <strong>vegetación moderada</strong> en desarrollo."
            else:
                return "La imagen muestra <strong>baja vegetación</strong> o suelo predominantemente desnudo."
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.2:
                return "La imagen refleja <strong>alto contenido de humedad</strong> en la vegetación."
            elif valor_promedio >= 0.0:
                return "La imagen muestra <strong>contenido moderado de humedad</strong>."
            else:
                return "La imagen indica <strong>bajo contenido de humedad</strong> o estrés hídrico."
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.5:
                return "La imagen muestra <strong>excelente cobertura vegetal</strong>."
            elif valor_promedio >= 0.3:
                return "La imagen muestra <strong>buena cobertura vegetal</strong>."
            else:
                return "La imagen muestra <strong>cobertura vegetal baja</strong> con suelo visible."
        
        return "Análisis no disponible."
    
    def _limpiar_texto_para_pdf(self, texto: str) -> str:
        """Limpia y formatea el texto de Gemini para PDF"""
        # Remover markdown que ReportLab no soporta
        # Primero, manejar **texto** correctamente
        import re
        
        # Contar asteriscos y asegurar que estén balanceados
        texto = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', texto)
        texto = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', texto)
        
        # Limpiar cualquier asterisco suelto restante
        texto = texto.replace('**', '').replace('*', '')
        
        # Asegurar que los tags HTML estén correctamente cerrados
        # Contar y balancear <strong> y </strong>
        strong_open = texto.count('<strong>')
        strong_close = texto.count('</strong>')
        if strong_open > strong_close:
            texto += '</strong>' * (strong_open - strong_close)
        elif strong_close > strong_open:
            # Remover </strong> sobrantes
            for _ in range(strong_close - strong_open):
                texto = texto.replace('</strong>', '', 1)
        
        # Contar y balancear <em> y </em>
        em_open = texto.count('<em>')
        em_close = texto.count('</em>')
        if em_open > em_close:
            texto += '</em>' * (em_open - em_close)
        elif em_close > em_open:
            for _ in range(em_close - em_open):
                texto = texto.replace('</em>', '', 1)
        
        # Reemplazar saltos de línea por <br/>
        texto = texto.replace('\n\n\n', '<br/><br/>')
        texto = texto.replace('\n\n', '<br/><br/>')
        texto = texto.replace('\n', '<br/>')
        
        # Limpiar múltiples <br/> seguidos (máximo 2)
        texto = re.sub(r'(<br/>){3,}', '<br/><br/>', texto)
        
        return texto.strip()

    def generar_analisis_global_imagenes(
        self,
        imagenes_datos: List[Dict[str, Any]],
        parcela_info: Dict[str, Any]
    ) -> str:
        """
        Genera un análisis global consolidado de todas las imágenes del período
        
        Args:
            imagenes_datos: Lista de dicts con info de cada imagen:
                - imagen_path: ruta a la imagen
                - tipo_indice: NDVI/NDMI/SAVI
                - valor_promedio: valor del índice
                - mes: nombre del mes
                - fecha: fecha de captura
            parcela_info: Dict con info de la parcela (nombre, área, coordenadas)
        
        Returns:
            Análisis global en HTML con recomendaciones por zona
        """
        try:
            logger.info(f"🤖 Generando análisis global de {len(imagenes_datos)} imágenes")
            
            # Cargar todas las imágenes
            imagenes = []
            resumen_datos = []
            
            for img_data in imagenes_datos[:12]:  # Máximo 12 imágenes para no exceder límites
                try:
                    img = self._cargar_imagen_individual(img_data['imagen_path'])
                    imagenes.append(img)
                    resumen_datos.append(
                        f"• {img_data['mes']}: {img_data['tipo_indice']} = {img_data['valor_promedio']:.3f}"
                    )
                except Exception as e:
                    logger.warning(f"No se pudo cargar imagen {img_data['imagen_path']}: {e}")
            
            if not imagenes:
                return self._generar_analisis_global_fallback()
            
            # Construir prompt para análisis global
            prompt = f"""
Eres un agrónomo experto analizando imágenes satelitales de una parcela agrícola. 
Has revisado {len(imagenes)} imágenes del período completo y ahora debes generar un 
**ANÁLISIS GLOBAL CONSOLIDADO** con conclusiones y recomendaciones específicas.

**INFORMACIÓN DE LA PARCELA:**
- Nombre: {parcela_info.get('nombre', 'N/A')}
- Área: {parcela_info.get('area', 0):.2f} hectáreas
- Coordenadas: {parcela_info.get('coordenadas', 'N/A')}

**IMÁGENES ANALIZADAS:**
{chr(10).join(resumen_datos)}

**INSTRUCCIONES PARA EL ANÁLISIS GLOBAL:**

1. **EVALUACIÓN GENERAL DEL VIGOR** (3-4 líneas):
   - ¿Cómo está el estado general de la parcela en todo el período?
   - ¿Los valores son buenos, moderados o preocupantes?
   - ¿Hay una tendencia clara (mejora/deterioro)?

2. **PATRONES ESPACIALES CONSISTENTES** (4-5 líneas):
   - ¿Qué ZONAS específicas (norte/sur/este/oeste) muestran mejor/peor desempeño CONSISTENTEMENTE?
   - ¿Hay áreas problemáticas recurrentes?
   - Ejemplo: "La zona norte muestra sistemáticamente menor vigor en todas las imágenes"

3. **EVOLUCIÓN TEMPORAL** (3-4 líneas):
   - ¿Cómo ha evolucionado la parcela a lo largo del período?
   - ¿Hubo cambios significativos entre meses?
   - ¿La tendencia es positiva o preocupante?

4. **RECOMENDACIONES PRIORITARIAS POR ZONA** (5-6 líneas):
   - Da 2-3 recomendaciones ACCIONABLES y ESPECÍFICAS por zona
   - Menciona ZONAS CONCRETAS: "En la zona sur se recomienda..."
   - Prioriza las acciones más importantes
   - Sé específico con acciones (riego, nutrición, monitoreo, etc.)

**FORMATO DE RESPUESTA:**
Usa <strong> para encabezados y términos clave.
Usa <br/> para separar secciones.
Sé DIRECTO y ACCIONABLE.
Menciona ZONAS ESPECÍFICAS en cada punto.
Máximo 400 palabras.

**TONO:** Profesional pero accesible, como un consultor agrícola hablando con el productor.
"""
            
            # Preparar contenido: prompt + todas las imágenes
            contenido = [prompt] + imagenes
            
            # Generar análisis global
            response = self.model.generate_content(contenido)
            
            analisis = response.text
            
            # Limpiar y formatear
            analisis = self._limpiar_texto_para_pdf(analisis)
            
            logger.info(f"✅ Análisis global generado ({len(analisis)} caracteres)")
            
            return analisis
            
        except Exception as e:
            logger.error(f"❌ Error generando análisis global: {str(e)}")
            return self._generar_analisis_global_fallback()
    
    def _generar_analisis_global_fallback(self) -> str:
        """Genera análisis global básico si Gemini falla"""
        return """
<strong>EVALUACIÓN GENERAL:</strong><br/>
Los índices satelitales muestran condiciones variables a lo largo del período analizado. 
Se recomienda revisar cada sección para identificar áreas específicas de mejora.<br/><br/>

<strong>RECOMENDACIONES:</strong><br/>
• Monitorear zonas con valores consistentemente bajos<br/>
• Ajustar riego según variabilidad espacial observada<br/>
• Realizar análisis de suelo en áreas problemáticas<br/>
• Mantener seguimiento regular con imágenes satelitales
"""


# Instancia global del servicio
try:
    gemini_service = GeminiService()
    logger.info("✅ GeminiService instanciado globalmente")
except Exception as e:
    logger.error(f"❌ Error instanciando GeminiService: {str(e)}")
    gemini_service = None
