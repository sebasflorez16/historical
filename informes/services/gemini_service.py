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
        
        # Usar modelo Gemini 2.0 Flash (mejor para FREE TIER)
        # Límites FREE: 1,500 solicitudes/día, 15 solicitudes/minuto
        # Input: 1M tokens, Output: 8K tokens
        # Nota: gemini-2.5-flash solo tiene 20 req/día en free tier
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
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
        """
        Construir prompt enriquecido para análisis agrícola profesional con Gemini.
        Incluye serie temporal completa, contexto agronómico, clima y recomendaciones.
        """
        # Información básica de la parcela
        nombre = parcela_data.get('nombre', 'Parcela sin nombre')
        area = parcela_data.get('area_hectareas', 0)
        cultivo = parcela_data.get('tipo_cultivo', 'No especificado')
        propietario = parcela_data.get('propietario', 'No especificado')
        ubicacion = parcela_data.get('ubicacion', 'No especificada')
        
        # Determinar si hay cultivo activo o terreno sin sembrar
        tiene_cultivo = cultivo and cultivo.lower() not in ['no especificado', 'sin cultivo', 'ninguno', '']
        contexto_cultivo = f"cultivo de {cultivo}" if tiene_cultivo else "terreno sin cultivo activo (análisis para planificación)"
        
        # Construir tabla enriquecida con serie temporal completa
        tabla = self._construir_tabla_temporal_enriquecida(indices_mensuales)
        
        # Obtener estadísticas clave de la serie temporal
        estadisticas = self._calcular_estadisticas_serie_temporal(indices_mensuales)
        
        # Construir el prompt profesional según el tipo de análisis
        if tiene_cultivo:
            prompt = f"""**ACTÚA COMO UN AGRÓNOMO EXPERTO EN AGRICULTURA DE PRECISIÓN**

Analiza la siguiente parcela agrícola y proporciona un análisis técnico profesional:

**INFORMACIÓN DE LA PARCELA:**
- Nombre: {nombre}
- Cultivo: {cultivo}
- Área: {area:.2f} hectáreas
- Ubicación: {ubicacion}
- Propietario: {propietario}

**SERIE TEMPORAL DE DATOS SATELITALES Y CLIMÁTICOS (ÚLTIMOS MESES):**

{tabla}

**ESTADÍSTICAS GENERALES:**
{estadisticas}

**TU MISIÓN COMO AGRÓNOMO:**

1. **ANÁLISIS DE TENDENCIAS**: Analiza la evolución temporal de los índices de vegetación (NDVI, NDMI, SAVI) y clima. ¿Qué patrones observas? ¿Hay crecimiento, estancamiento o deterioro de la cobertura vegetal?

2. **DETECCIÓN DE ALERTAS**: Identifica cualquier signo de:
   - Estrés hídrico (NDMI bajo, precipitación insuficiente)
   - Estrés por calor o sequía (temperaturas extremas, NDVI descendente)
   - Posibles plagas o enfermedades (caídas abruptas de NDVI sin causa climática)
   - Anomalías en la calidad de los datos o nubosidad excesiva
   - Variabilidad espacial excesiva (NDVI max vs min muy diferentes)

3. **RECOMENDACIONES PRÁCTICAS**: Proporciona acciones concretas que el agricultor debe tomar:
   - Riego: ¿necesita más o menos agua? ¿cuándo?
   - Fertilización: ¿hay síntomas de déficit nutricional?
   - Manejo de plagas: ¿se recomienda inspección en campo?
   - Optimización de prácticas: ¿qué puede mejorar?

4. **PROYECCIÓN Y PLANIFICACIÓN**: Basándote en las tendencias, ¿qué esperas en los próximos meses? ¿Qué debe anticipar el agricultor?

**FORMATO DE RESPUESTA:**
Estructura tu análisis en 4 secciones claramente diferenciadas:

### RESUMEN EJECUTIVO
[Resumen de 2-3 frases del estado actual de la parcela y hallazgos principales]

### ANÁLISIS DE TENDENCIAS
[Análisis detallado de la evolución temporal, patrones estacionales y comportamiento de índices]

### ALERTAS Y DIAGNÓSTICO
[Lista de alertas, riesgos identificados y diagnóstico de posibles problemas]

### RECOMENDACIONES
[Acciones concretas y priorizadas que el agricultor debe implementar]

**IMPORTANTE:** Sé técnico pero comprensible. No repitas los datos numéricos, sino interprétalos. Enfócate en insights accionables."""
        else:
            # Prompt para terreno sin cultivo (análisis para planificación)
            prompt = f"""**ACTÚA COMO UN AGRÓNOMO EXPERTO EN PLANIFICACIÓN AGRÍCOLA**

Analiza la siguiente parcela SIN CULTIVO ACTIVO y proporciona recomendaciones para su aprovechamiento:

**INFORMACIÓN DE LA PARCELA:**
- Nombre: {nombre}
- Estado: Terreno sin cultivo activo (preparación o planificación)
- Área: {area:.2f} hectáreas
- Ubicación: {ubicacion}
- Propietario: {propietario}

**SERIE TEMPORAL DE DATOS SATELITALES Y CLIMÁTICOS (ÚLTIMOS MESES):**

{tabla}

**ESTADÍSTICAS GENERALES:**
{estadisticas}

**TU MISIÓN COMO AGRÓNOMO:**

1. **ANÁLISIS DE CONDICIONES BASE**: Evalúa la evolución de la cobertura vegetal natural (malezas, vegetación espontánea) y condiciones climáticas. ¿Qué indica sobre el potencial del suelo?

2. **EVALUACIÓN DE APTITUD**: Basándote en los datos de NDVI, NDMI, clima y temporada, ¿qué cultivos serían más apropiados para esta parcela?

3. **RECOMENDACIONES DE PREPARACIÓN**: ¿Qué acciones debe tomar el propietario antes de sembrar? (limpieza, riego, fertilización, análisis de suelo, etc.)

4. **VENTANA ÓPTIMA DE SIEMBRA**: Según las condiciones climáticas observadas, ¿cuál sería el mejor momento para iniciar un cultivo?

**FORMATO DE RESPUESTA:**
Estructura tu análisis en 4 secciones:

### RESUMEN EJECUTIVO
[Resumen del potencial de la parcela y recomendación principal]

### ANÁLISIS DE CONDICIONES BASE
[Evaluación de cobertura vegetal, clima y aptitud del terreno]

### ALERTAS Y CONSIDERACIONES
[Advertencias, limitaciones o riesgos a tener en cuenta antes de sembrar]

### RECOMENDACIONES
[Acciones concretas para preparación del terreno, cultivos sugeridos y calendario]

**IMPORTANTE:** Sé técnico pero comprensible. Enfócate en insights accionables para ayudar al propietario a tomar decisiones."""
        
        return prompt
    
    def _construir_tabla_temporal_enriquecida(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """
        Construir tabla enriquecida con serie temporal completa de índices y clima.
        Incluye NDVI, NDMI, SAVI, temperatura, precipitación, nubosidad y calidad.
        """
        if not indices_mensuales:
            return "No hay datos mensuales disponibles para análisis."
        
        # Encabezado de la tabla
        tabla = "| Período | NDVI | NDMI | SAVI | Temp (°C) | Precip (mm) | Nubosidad | Calidad |\n"
        tabla += "|---------|------|------|------|-----------|-------------|-----------|----------|\n"
        
        for dato in indices_mensuales:
            # Período (mes/año)
            periodo = dato.get('periodo', 'N/A')
            
            # Índices de vegetación (promedio, min, max)
            ndvi_prom = dato.get('ndvi_promedio')
            ndvi_min = dato.get('ndvi_minimo') or dato.get('ndvi_min')  # Compatibilidad
            ndvi_max = dato.get('ndvi_maximo') or dato.get('ndvi_max')
            
            if ndvi_prom is not None:
                ndvi_str = f"{ndvi_prom:.3f}"
                if ndvi_min is not None and ndvi_max is not None:
                    ndvi_str += f" ({ndvi_min:.3f}-{ndvi_max:.3f})"
            else:
                ndvi_str = 'N/A'
            
            # NDMI (índice de humedad)
            ndmi_prom = dato.get('ndmi_promedio')
            ndmi_min = dato.get('ndmi_minimo') or dato.get('ndmi_min')
            ndmi_max = dato.get('ndmi_maximo') or dato.get('ndmi_max')
            
            if ndmi_prom is not None:
                ndmi_str = f"{ndmi_prom:.3f}"
                if ndmi_min is not None and ndmi_max is not None:
                    ndmi_str += f" ({ndmi_min:.3f}-{ndmi_max:.3f})"
            else:
                ndmi_str = 'N/A'
            
            # SAVI (índice ajustado de vegetación)
            savi_prom = dato.get('savi_promedio')
            savi_min = dato.get('savi_minimo') or dato.get('savi_min')
            savi_max = dato.get('savi_maximo') or dato.get('savi_max')
            
            if savi_prom is not None:
                savi_str = f"{savi_prom:.3f}"
                if savi_min is not None and savi_max is not None:
                    savi_str += f" ({savi_min:.3f}-{savi_max:.3f})"
            else:
                savi_str = 'N/A'
            
            # Clima
            temp = dato.get('temperatura_promedio')
            temp_str = f"{temp:.1f}" if temp is not None else 'N/A'
            
            precip = dato.get('precipitacion_total')
            precip_str = f"{precip:.1f}" if precip is not None else 'N/A'
            
            nubosidad = dato.get('nubosidad_promedio')
            nubosidad_str = f"{nubosidad:.0f}%" if nubosidad is not None else 'N/A'
            
            calidad = dato.get('calidad_datos', 'N/A')
            
            # Fila de la tabla
            tabla += f"| {periodo} | {ndvi_str} | {ndmi_str} | {savi_str} | {temp_str} | {precip_str} | {nubosidad_str} | {calidad} |\n"
        
        # Nota explicativa
        tabla += "\n*Nota: Valores entre paréntesis indican (mínimo-máximo) del índice en el período.*"
        
        return tabla
    
    def _calcular_estadisticas_serie_temporal(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """
        Calcular estadísticas descriptivas de la serie temporal para dar contexto a Gemini.
        Incluye tendencias, promedios, variabilidad y alertas numéricas.
        """
        if not indices_mensuales:
            return "No hay datos suficientes para calcular estadísticas."
        
        # Extraer valores válidos
        ndvi_values = [d.get('ndvi_promedio') for d in indices_mensuales if d.get('ndvi_promedio') is not None]
        ndmi_values = [d.get('ndmi_promedio') for d in indices_mensuales if d.get('ndmi_promedio') is not None]
        temp_values = [d.get('temperatura_promedio') for d in indices_mensuales if d.get('temperatura_promedio') is not None]
        precip_values = [d.get('precipitacion_total') for d in indices_mensuales if d.get('precipitacion_total') is not None]
        
        stats = []
        
        # NDVI
        if ndvi_values:
            ndvi_mean = sum(ndvi_values) / len(ndvi_values)
            ndvi_min = min(ndvi_values)
            ndvi_max = max(ndvi_values)
            ndvi_trend = "creciente" if len(ndvi_values) >= 2 and ndvi_values[-1] > ndvi_values[0] else "decreciente" if len(ndvi_values) >= 2 and ndvi_values[-1] < ndvi_values[0] else "estable"
            stats.append(f"- **NDVI**: Promedio {ndvi_mean:.3f} | Rango {ndvi_min:.3f}-{ndvi_max:.3f} | Tendencia: {ndvi_trend}")
        
        # NDMI
        if ndmi_values:
            ndmi_mean = sum(ndmi_values) / len(ndmi_values)
            ndmi_min = min(ndmi_values)
            ndmi_max = max(ndmi_values)
            stats.append(f"- **NDMI**: Promedio {ndmi_mean:.3f} | Rango {ndmi_min:.3f}-{ndmi_max:.3f}")
        
        # Temperatura
        if temp_values:
            temp_mean = sum(temp_values) / len(temp_values)
            temp_min = min(temp_values)
            temp_max = max(temp_values)
            stats.append(f"- **Temperatura**: Promedio {temp_mean:.1f}°C | Rango {temp_min:.1f}-{temp_max:.1f}°C")
        
        # Precipitación
        if precip_values:
            precip_total = sum(precip_values)
            precip_mean = precip_total / len(precip_values)
            stats.append(f"- **Precipitación**: Total {precip_total:.1f}mm | Promedio mensual {precip_mean:.1f}mm")
        
        # Número de meses con datos
        stats.append(f"- **Período analizado**: {len(indices_mensuales)} meses de datos")
        
        return "\n".join(stats) if stats else "Datos insuficientes para estadísticas."
    
    def _construir_tabla_datos(self, indices_mensuales: List[Dict[str, Any]]) -> str:
        """Construir tabla de datos mensuales en formato texto"""
        if not indices_mensuales:
            return "No hay datos mensuales disponibles."
        
        tabla = "| Mes | NDVI | NDMI | SAVI | Nubosidad | Temp (°C) | Precip (mm) | Calidad |\n"
        tabla += "|-----|------|------|------|-----------|-----------|-------------|----------|\n"
        
        for dato in indices_mensuales:
            mes = dato.get('periodo', 'N/A')
            
            # Manejar valores None de forma segura
            ndvi_val = dato.get('ndvi_promedio')
            ndvi = f"{ndvi_val:.3f}" if ndvi_val is not None else 'N/A'
            
            ndmi_val = dato.get('ndmi_promedio')
            ndmi = f"{ndmi_val:.3f}" if ndmi_val is not None else 'N/A'
            
            savi_val = dato.get('savi_promedio')
            savi = f"{savi_val:.3f}" if savi_val is not None else 'N/A'
            
            nubosidad_val = dato.get('nubosidad_promedio')
            nubosidad = f"{nubosidad_val:.1f}%" if nubosidad_val is not None else 'N/A'
            
            temp_val = dato.get('temperatura_promedio')
            temp = f"{temp_val:.1f}" if temp_val is not None else 'N/A'
            
            precip_val = dato.get('precipitacion_total')
            precip = f"{precip_val:.1f}" if precip_val is not None else 'N/A'
            
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
                
                # Manejar nubosidad None
                nubosidad_str = f"{nubosidad:.1f}%" if nubosidad is not None else 'N/A'
                desc.append(f"- **{mes}**: Imágenes disponibles: {', '.join(imagenes)} (Nubosidad: {nubosidad_str})")
        
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
