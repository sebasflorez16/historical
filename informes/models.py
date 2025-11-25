"""
Modelos para la aplicación de informes AgroTech Histórico
Sistema completo de análisis satelital agrícola con PostGIS
"""

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json

# Importar modelos de gestión de clientes
from .models_clientes import ClienteInvitacion, RegistroEconomico

# Importar modelos de configuración y caché
from .models_configuracion import (
    ConfiguracionReporte, 
    CacheDatosEOSDA, 
    EstadisticaUsoEOSDA
)

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.contrib.auth.models import User
import json


class Parcela(gis_models.Model):
    """
    Modelo para gestionar las parcelas agrícolas con geometría PostGIS nativa
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Parcela")
    propietario = models.CharField(max_length=200, verbose_name="Propietario")
    
    # Campo geoespacial nativo PostGIS - MUCHO más eficiente
    geometria = gis_models.PolygonField(
        verbose_name="Geometría de la Parcela",
        help_text="Polígono definiendo los límites de la parcela",
        srid=4326,  # WGS84 - Sistema de coordenadas estándar GPS
        null=True, blank=True  # Permitir NULL temporalmente para migración
    )
    
    # Campo de respaldo para compatibilidad con sistemas que requieren GeoJSON
    coordenadas = models.TextField(
        blank=True,
        verbose_name="GeoJSON (respaldo)",
        help_text="Representación GeoJSON para compatibilidad"
    )
    
    area_hectareas = models.FloatField(
        null=True, blank=True,
        verbose_name="Área (hectáreas)",
        help_text="Área calculada automáticamente usando PostGIS"
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_inicio_monitoreo = models.DateField(verbose_name="Inicio Monitoreo")
    fecha_fin_monitoreo = models.DateField(
        null=True, blank=True,
        verbose_name="Fin Monitoreo"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    
    # Metadatos adicionales
    tipo_cultivo = models.CharField(
        max_length=100, blank=True,
        verbose_name="Tipo de Cultivo"
    )
    notas = models.TextField(blank=True, verbose_name="Notas")
    
    # ========= INTEGRACIÓN EOSDA =========
    # Campos para sincronización con EOSDA Field Management API
    eosda_field_id = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="EOSDA Field ID",
        help_text="ID único del campo en EOSDA después de sincronización",
        unique=True  # Cada field_id de EOSDA es único
    )
    eosda_sincronizada = models.BooleanField(
        default=False,
        verbose_name="Sincronizada con EOSDA",
        help_text="Indica si la parcela fue creada exitosamente en EOSDA"
    )
    eosda_fecha_sincronizacion = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha Sincronización EOSDA",
        help_text="Cuándo se sincronizó por última vez con EOSDA"
    )
    eosda_nombre_campo = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="Nombre en EOSDA",
        help_text="Nombre del campo tal como aparece en EOSDA"
    )
    eosda_errores = models.TextField(
        null=True, blank=True,
        verbose_name="Errores EOSDA",
        help_text="Último error durante sincronización con EOSDA"
    )
    
    # Metadatos geoespaciales calculados automáticamente
    centroide = gis_models.PointField(
        null=True, blank=True,
        verbose_name="Punto Central",
        help_text="Centro geométrico calculado automáticamente",
        srid=4326
    )
    
    perimetro_metros = models.FloatField(
        null=True, blank=True,
        verbose_name="Perímetro (metros)",
        help_text="Perímetro calculado automáticamente"
    )
    
    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ['-fecha_registro']
        # Índice espacial automático para consultas geográficas ultra-rápidas
    
    def __str__(self):
        return f"{self.nombre} - {self.propietario}"
    
    @property 
    def poligono_geojson(self):
        """Retorna las coordenadas como GeoJSON string"""
        if self.geometria:
            return self.geometria.geojson
        elif self.coordenadas:
            # Compatibilidad con datos antiguos
            if isinstance(self.coordenadas, str):
                return self.coordenadas
            else:
                return json.dumps(self.coordenadas)
        return None
    
    def save(self, *args, **kwargs):
        """
        Override save para calcular automáticamente área, perímetro y centroide
        """
        if self.geometria:
            # Calcular área en hectáreas (PostGIS en metros cuadrados)
            # Usar proyección apropiada para cálculos precisos
            geom_utm = self.geometria.transform(3857, clone=True)  # Web Mercator para cálculos
            self.area_hectareas = geom_utm.area / 10000  # m² a hectáreas
            
            # Calcular perímetro en metros
            self.perimetro_metros = geom_utm.length
            
            # Calcular centroide
            self.centroide = self.geometria.centroid
            
            # Actualizar GeoJSON de respaldo para compatibilidad
            self.coordenadas = self.geometria.geojson
        
        super().save(*args, **kwargs)
    
    def marcar_sincronizada_eosda(self, field_id: str, nombre_campo: str = None):
        """
        Marca la parcela como sincronizada exitosamente con EOSDA
        """
        self.eosda_field_id = field_id
        self.eosda_sincronizada = True
        self.eosda_fecha_sincronizacion = timezone.now()
        self.eosda_nombre_campo = nombre_campo or self.nombre
        self.eosda_errores = None  # Limpiar errores previos
        self.save(update_fields=[
            'eosda_field_id', 'eosda_sincronizada', 
            'eosda_fecha_sincronizacion', 'eosda_nombre_campo', 'eosda_errores'
        ])
    
    def marcar_error_eosda(self, error_mensaje: str):
        """
        Registra un error durante la sincronización con EOSDA
        """
        self.eosda_sincronizada = False
        self.eosda_errores = error_mensaje
        self.eosda_fecha_sincronizacion = timezone.now()
        self.save(update_fields=[
            'eosda_sincronizada', 'eosda_errores', 'eosda_fecha_sincronizacion'
        ])
    
    @property
    def requiere_sincronizacion_eosda(self) -> bool:
        """
        Determina si la parcela necesita ser sincronizada con EOSDA
        """
        return not self.eosda_sincronizada or self.eosda_field_id is None
    
    @property
    def puede_obtener_datos_eosda(self) -> bool:
        """
        Determina si se pueden obtener datos satellitales de EOSDA
        """
        return self.eosda_sincronizada and self.eosda_field_id is not None
    
    @property
    def coordenadas_dict(self):
        """Convierte la geometría a diccionario Python para compatibilidad"""
        if self.geometria:
            return json.loads(self.geometria.geojson)
        elif self.coordenadas:
            try:
                return json.loads(self.coordenadas)
            except json.JSONDecodeError:
                return None
        return None
    
    @property
    def centro_parcela(self):
        """Retorna el centro como diccionario lat/lng"""
        if self.centroide:
            return {
                'lat': self.centroide.y,
                'lng': self.centroide.x
            }
        return None
    
    def parcelas_cercanas(self, radio_km=10):
        """
        Encuentra parcelas dentro de un radio específico
        Ejemplo de funcionalidad geoespacial avanzada con PostGIS
        """
        from django.contrib.gis.measure import D
        
        return Parcela.objects.filter(
            geometria__distance_lte=(self.centroide, D(km=radio_km)),
            activa=True
        ).exclude(id=self.id)
    
    def intersecta_con(self, otra_geometria):
        """
        Verifica si la parcela intersecta con otra geometría
        Útil para análisis de superposición de cultivos, zonas protegidas, etc.
        """
        return self.geometria.intersects(otra_geometria)


# =============================================================================
# MODELOS DE ÍNDICES Y ANÁLISIS
# =============================================================================

class IndiceMensual(models.Model):
    """
    Almacena los índices satelitales mensuales obtenidos desde EOSDA
    """
    parcela = models.ForeignKey(
        Parcela, on_delete=models.CASCADE,
        related_name='indices_mensuales'
    )
    
    # Período
    año = models.PositiveIntegerField(verbose_name="Año")
    mes = models.PositiveIntegerField(verbose_name="Mes")
    
    # Índices satelitales principales
    ndvi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="NDVI Promedio",
        help_text="Índice de Vegetación de Diferencia Normalizada (0 a 1)"
    )
    ndvi_maximo = models.FloatField(null=True, blank=True, verbose_name="NDVI Máximo")
    ndvi_minimo = models.FloatField(null=True, blank=True, verbose_name="NDVI Mínimo")
    
    ndmi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="NDMI Promedio",
        help_text="Índice de Humedad de Diferencia Normalizada (-1 a 1)"
    )
    ndmi_maximo = models.FloatField(null=True, blank=True, verbose_name="NDMI Máximo")
    ndmi_minimo = models.FloatField(null=True, blank=True, verbose_name="NDMI Mínimo")
    
    savi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="SAVI Promedio",
        help_text="Índice de Vegetación Ajustado al Suelo"
    )
    savi_maximo = models.FloatField(null=True, blank=True, verbose_name="SAVI Máximo")
    savi_minimo = models.FloatField(null=True, blank=True, verbose_name="SAVI Mínimo")
    
    # Datos climatológicos y condiciones
    temperatura_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="Temperatura Promedio (°C)"
    )
    temperatura_maxima = models.FloatField(null=True, blank=True, verbose_name="Temperatura Máxima")
    temperatura_minima = models.FloatField(null=True, blank=True, verbose_name="Temperatura Mínima")
    
    precipitacion_total = models.FloatField(
        null=True, blank=True,
        verbose_name="Precipitación Total (mm)"
    )
    
    nubosidad_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="Nubosidad Promedio (%)",
        help_text="Porcentaje promedio de nubosidad durante el mes"
    )
    
    # Imágenes satelitales descargadas desde Field Imagery API
    imagen_ndvi = models.ImageField(
        upload_to='imagenes_satelitales/%Y/%m/ndvi/',
        null=True, blank=True,
        verbose_name="Imagen NDVI",
        help_text="Imagen satelital del índice NDVI"
    )
    imagen_ndmi = models.ImageField(
        upload_to='imagenes_satelitales/%Y/%m/ndmi/',
        null=True, blank=True,
        verbose_name="Imagen NDMI",
        help_text="Imagen satelital del índice NDMI"
    )
    imagen_savi = models.ImageField(
        upload_to='imagenes_satelitales/%Y/%m/savi/',
        null=True, blank=True,
        verbose_name="Imagen SAVI",
        help_text="Imagen satelital del índice SAVI"
    )
    
    # Metadatos de las imágenes
    view_id_imagen = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="View ID de la Imagen",
        help_text="ID de la vista satelital usada para las imágenes"
    )
    fecha_imagen = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha de la Imagen",
        help_text="Fecha de captura de la imagen satelital"
    )
    nubosidad_imagen = models.FloatField(
        null=True, blank=True,
        verbose_name="Nubosidad de la Imagen (%)",
        help_text="Porcentaje de nubosidad de la imagen satelital descargada"
    )
    
    # Metadatos de la consulta
    fecha_consulta_api = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Consulta API"
    )
    fuente_datos = models.CharField(
        max_length=50, default="EOSDA",
        verbose_name="Fuente de Datos"
    )
    calidad_datos = models.CharField(
        max_length=20,
        choices=[
            ('excelente', 'Excelente'),
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('pobre', 'Pobre'),
        ],
        default='buena',
        verbose_name="Calidad de Datos"
    )
    
    # 🤖 CACHÉ DE ANÁLISIS GEMINI AI
    analisis_gemini = models.JSONField(
        null=True, blank=True,
        verbose_name="Análisis Gemini AI (Caché)",
        help_text="Caché del análisis generado por Gemini AI para evitar regeneraciones costosas"
    )
    fecha_analisis_gemini = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha Análisis Gemini",
        help_text="Fecha y hora del último análisis de Gemini generado"
    )
    
    # 🗺️ METADATOS ESPACIALES PARA ANÁLISIS VISUAL
    metadatos_imagen = models.JSONField(
        null=True, blank=True,
        verbose_name="Metadatos Espaciales de Imagen",
        help_text="Metadatos completos de EOSDA: coordenadas, bbox, satélite, resolución, etc."
    )
    coordenadas_imagen = models.JSONField(
        null=True, blank=True,
        verbose_name="Coordenadas de la Imagen",
        help_text="Bounding box y centroide de la imagen satelital [min_lat, min_lon, max_lat, max_lon]"
    )
    satelite_imagen = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="Satélite Fuente",
        help_text="Satélite que capturó la imagen (ej: Sentinel-2, Landsat-8)"
    )
    resolucion_imagen = models.FloatField(
        null=True, blank=True,
        verbose_name="Resolución Espacial (m)",
        help_text="Resolución espacial de la imagen en metros por píxel"
    )
    
    class Meta:
        verbose_name = "Índice Mensual"
        verbose_name_plural = "Índices Mensuales"
        ordering = ['-año', '-mes']
        unique_together = ('parcela', 'año', 'mes')
    
    def __str__(self):
        return f"{self.parcela.nombre} - {self.mes:02d}/{self.año}"
    
    @property
    def periodo_texto(self):
        """Retorna el período en formato legible"""
        meses = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return f"{meses[self.mes]} {self.año}"
    
    @property
    def fecha(self):
        """Retorna una fecha datetime para facilitar el ordenamiento y procesamiento"""
        from datetime import datetime
        return datetime(self.año, self.mes, 1)
    
    @property
    def ndvi(self):
        """Alias para ndvi_promedio, para compatibilidad con analizadores"""
        return self.ndvi_promedio or 0.0
    
    @property
    def ndmi(self):
        """Alias para ndmi_promedio, para compatibilidad con analizadores"""
        return self.ndmi_promedio or 0.0
    
    @property
    def savi(self):
        """Alias para savi_promedio, para compatibilidad con analizadores"""
        return self.savi_promedio or 0.0
    
    @property
    def salud_vegetacion(self):
        """Evalúa la salud de la vegetación basada en NDVI"""
        if not self.ndvi_promedio:
            return "Sin datos"
            
        if self.ndvi_promedio >= 0.7:
            return "Excelente"
        elif self.ndvi_promedio >= 0.5:
            return "Buena"
        elif self.ndvi_promedio >= 0.3:
            return "Regular"
        else:
            return "Pobre"


class Informe(models.Model):
    """
    Informes generados automáticamente con análisis de datos satelitales
    """
    parcela = models.ForeignKey(
        Parcela, on_delete=models.CASCADE,
        related_name='informes'
    )
    
    # Configuración del informe
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Generación")
    periodo_analisis_meses = models.PositiveIntegerField(
        verbose_name="Período Análisis (meses)",
        help_text="Número de meses analizados (6, 12, 24)"
    )
    fecha_inicio_analisis = models.DateField(verbose_name="Inicio Período")
    fecha_fin_analisis = models.DateField(verbose_name="Fin Período")
    
    # Contenido del informe
    titulo = models.CharField(max_length=300, verbose_name="Título del Informe")
    resumen_ejecutivo = models.TextField(
        verbose_name="Resumen Ejecutivo",
        help_text="Resumen generado automáticamente por IA"
    )
    analisis_tendencias = models.TextField(
        blank=True,
        verbose_name="Análisis de Tendencias",
        help_text="Análisis detallado de tendencias NDVI, NDMI, SAVI"
    )
    conclusiones_ia = models.TextField(
        blank=True,
        verbose_name="Conclusiones IA",
        help_text="Conclusiones generadas por análisis IA local"
    )
    recomendaciones = models.TextField(
        blank=True,
        verbose_name="Recomendaciones",
        help_text="Recomendaciones técnicas basadas en los datos"
    )
    
    # Archivos generados
    archivo_pdf = models.FileField(
        upload_to='informes/pdfs/%Y/%m/',
        max_length=500,
        null=True, blank=True,
        verbose_name="Archivo PDF"
    )
    mapa_ndvi_imagen = models.ImageField(
        upload_to='informes/mapas/%Y/%m/',
        max_length=500,
        null=True, blank=True,
        verbose_name="Mapa NDVI"
    )
    grafico_tendencias = models.ImageField(
        upload_to='informes/graficos/%Y/%m/',
        max_length=500,
        null=True, blank=True,
        verbose_name="Gráfico Tendencias"
    )
    
    # Estadísticas del análisis
    ndvi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="NDVI Promedio del Período"
    )
    ndmi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="NDMI Promedio del Período"
    )
    savi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="SAVI Promedio del Período"
    )
    
    # Metadatos
    version_algoritmo = models.CharField(
        max_length=20, default="1.0",
        verbose_name="Versión Algoritmo"
    )
    tiempo_procesamiento = models.DurationField(
        null=True, blank=True,
        verbose_name="Tiempo Procesamiento"
    )
    
    class Meta:
        verbose_name = "Informe"
        verbose_name_plural = "Informes"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Informe {self.parcela.nombre} - {self.fecha_generacion.strftime('%d/%m/%Y')}"
    
    @property
    def estado_salud_general(self):
        """Evalúa el estado general de salud de la parcela"""
        if not self.ndvi_promedio_periodo:
            return "Sin datos suficientes"
            
        ndvi = self.ndvi_promedio_periodo
        if ndvi >= 0.7:
            return "Excelente estado de salud"
        elif ndvi >= 0.5:
            return "Buen estado de salud"
        elif ndvi >= 0.3:
            return "Estado regular"
        else:
            return "Requiere atención"
    
    def save(self, *args, **kwargs):
        """Override save para generar título automáticamente"""
        if not self.titulo:
            self.titulo = f"Análisis Satelital - {self.parcela.nombre} ({self.periodo_analisis_meses} meses)"
        super().save(*args, **kwargs)


class ConfiguracionAPI(models.Model):
    """
    Configuración para APIs externas (EOSDA, etc.)
    """
    nombre_api = models.CharField(max_length=50, unique=True, verbose_name="Nombre API")
    url_base = models.URLField(verbose_name="URL Base")
    token_activo = models.BooleanField(default=True, verbose_name="Token Activo")
    fecha_ultima_consulta = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Última Consulta"
    )
    consultas_realizadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Consultas Realizadas"
    )
    limite_consultas_diarias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Límite Diario"
    )
    
    class Meta:
        verbose_name = "Configuración API"
        verbose_name_plural = "Configuraciones API"
    
    def __str__(self):
        return f"API {self.nombre_api}"
