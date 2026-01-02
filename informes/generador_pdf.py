"""
Generador de Informes en PDF Profesionales
Sistema completo de generación de reportes satelitales con logos AgroTech
"""
import os
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from io import BytesIO

# ReportLab imports
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, 
    Table, TableStyle, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas

# Matplotlib para gráficos (usar backend no-GUI para evitar problemas con threads)
import matplotlib
matplotlib.use('Agg')  # ✅ Backend no-GUI, seguro para threads y servidores web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns

# Django imports
from django.conf import settings

# Modelos locales
from informes.models import Parcela, IndiceMensual

# Analizadores
from informes.analizadores.ndvi_analyzer import AnalizadorNDVI
from informes.analizadores.ndmi_analyzer import AnalizadorNDMI
from informes.analizadores.savi_analyzer import AnalizadorSAVI
from informes.analizadores.tendencias_analyzer import DetectorTendencias
from informes.analizadores.recomendaciones_engine import GeneradorRecomendaciones

# Servicio de Gemini AI para análisis inteligente
from informes.services.gemini_service import gemini_service

import logging
logger = logging.getLogger(__name__)


def limpiar_html_para_reportlab(texto: str) -> str:
    """
    Limpia HTML para que sea compatible con ReportLab.
    
    ReportLab no soporta:
    - <br><br> seguidos (debe ser <br/> o usar espacers)
    - Contenido después de tags self-closing
    - Algunos caracteres especiales sin escapar
    """
    if not texto:
        return ""
    
    # Reemplazar <br><br> por <br/><br/>
    texto = re.sub(r'<br>\s*<br>', '<br/><br/>', texto)
    
    # Asegurar que todos los <br> sean self-closing
    texto = re.sub(r'<br(?!/)', '<br/', texto)
    texto = re.sub(r'<br/>\s+', '<br/>', texto)
    
    # Limpiar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    
    # Asegurar que no haya contenido después de <br/>
    texto = re.sub(r'(<br/>)\s+(\S)', r'\1 \2', texto)
    
    return texto.strip()


class GeneradorPDFProfesional:
    """
    Genera informes PDF profesionales con:
    - Logos AgroTech
    - Análisis inteligente de índices
    - Gráficos matplotlib
    - Recomendaciones accionables
    - Diseño moderno y profesional
    """
    
    def __init__(self):
        self.pagesize = A4
        self.ancho, self.alto = A4
        self.margen = 2*cm
        
        # Colores corporativos AgroTech
        self.colores = {
            'verde_principal': colors.HexColor('#2E8B57'),  # Verde AgroTech
            'verde_claro': colors.HexColor('#90EE90'),
            'naranja': colors.HexColor('#FF7A00'),
            'azul': colors.HexColor('#17a2b8'),
            'gris_oscuro': colors.HexColor('#2c3e50'),
            'gris_claro': colors.HexColor('#ecf0f1'),
        }
        
        # Estilos
        self.estilos = self._crear_estilos()
    
    def _crear_estilos(self):
        """Crea estilos personalizados para el documento"""
        estilos = getSampleStyleSheet()
        
        # Título de portada
        estilos.add(ParagraphStyle(
            name='TituloPortada',
            parent=estilos['Heading1'],
            fontSize=28,
            textColor=self.colores['verde_principal'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo de portada
        estilos.add(ParagraphStyle(
            name='SubtituloPortada',
            parent=estilos['Normal'],
            fontSize=16,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Título de sección
        estilos.add(ParagraphStyle(
            name='TituloSeccion',
            parent=estilos['Heading1'],
            fontSize=18,
            textColor=self.colores['verde_principal'],
            spaceBefore=24,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderColor=self.colores['verde_principal'],
            borderWidth=2,
            borderPadding=8
        ))
        
        # Subtítulo de sección
        estilos.add(ParagraphStyle(
            name='SubtituloSeccion',
            parent=estilos['Heading2'],
            fontSize=14,
            textColor=self.colores['azul'],
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        estilos.add(ParagraphStyle(
            name='TextoNormal',
            parent=estilos['Normal'],
            fontSize=11,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Pie de imagen
        estilos.add(ParagraphStyle(
            name='PieImagen',
            parent=estilos['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        return estilos
    
    def generar_informe_completo(self, parcela_id: int, 
                                meses_atras: int = 12,
                                output_path: str = None) -> str:
        """
        Genera informe completo en PDF
        
        Args:
            parcela_id: ID de la parcela
            meses_atras: Período de análisis (meses)
            output_path: Ruta de salida del PDF (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        # Obtener parcela
        try:
            parcela = Parcela.objects.get(id=parcela_id, activa=True)
        except Parcela.DoesNotExist:
            raise ValueError(f"Parcela {parcela_id} no encontrada")
        
        # Obtener datos históricos
        fecha_fin = date.today()
        fecha_inicio = date(fecha_fin.year, fecha_fin.month, 1)
        
        # Retroceder meses_atras
        for _ in range(meses_atras):
            if fecha_inicio.month == 1:
                fecha_inicio = date(fecha_inicio.year - 1, 12, 1)
            else:
                fecha_inicio = date(fecha_inicio.year, fecha_inicio.month - 1, 1)
        
        # Obtener índices mensuales
        indices = IndiceMensual.objects.filter(
            parcela=parcela,
            año__gte=fecha_inicio.year,
            mes__gte=fecha_inicio.month if fecha_inicio.year == fecha_fin.year else 1
        ).order_by('año', 'mes')
        
        if not indices.exists():
            raise ValueError(f"No hay datos disponibles para la parcela {parcela.nombre}")
        
        # Preparar datos para análisis
        datos_analisis = self._preparar_datos_analisis(indices)
        
        # Ejecutar análisis (pasando los índices originales para caché)
        analisis_completo = self._ejecutar_analisis(datos_analisis, parcela, indices)
        
        # Generar gráficos
        graficos = self._generar_graficos(datos_analisis)
        
        # Crear PDF
        if not output_path:
            nombre_archivo = f"informe_{parcela.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(settings.MEDIA_ROOT, 'informes', nombre_archivo)
        
        # Asegurar que existe el directorio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Construir documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=self.margen,
            leftMargin=self.margen,
            topMargin=self.margen + 1*cm,  # Espacio para header
            bottomMargin=self.margen + 0.5*cm  # Espacio para footer
        )
        
        # Contenido del documento
        story = []
        
        # Portada
        story.extend(self._crear_portada(parcela, fecha_inicio, fecha_fin))
        story.append(PageBreak())
        
        # Resumen ejecutivo
        story.extend(self._crear_resumen_ejecutivo(analisis_completo))
        story.append(Spacer(1, 0.5*cm))
        
        # 🤖 Análisis detallado de Gemini AI (si está disponible)
        if analisis_completo.get('gemini') and not analisis_completo['gemini'].get('error'):
            story.extend(self._crear_seccion_analisis_gemini(analisis_completo['gemini']))
        
        story.append(PageBreak())
        
        # 📸 Galería de Imágenes Satelitales (si hay imágenes disponibles)
        story.extend(self._crear_galeria_imagenes_satelitales(
            parcela, indices, analisis_completo.get('gemini')
        ))
        story.append(PageBreak())
        
        # Información de la parcela
        story.extend(self._crear_info_parcela(parcela))
        story.append(Spacer(1, 1*cm))
        
        # Análisis de índices
        story.extend(self._crear_seccion_ndvi(analisis_completo['ndvi'], graficos))
        story.append(PageBreak())
        
        story.extend(self._crear_seccion_ndmi(analisis_completo['ndmi'], graficos))
        story.append(PageBreak())
        
        if 'savi' in analisis_completo and analisis_completo['savi']:
            story.extend(self._crear_seccion_savi(analisis_completo['savi'], graficos))
            story.append(PageBreak())
        
        # Análisis de tendencias
        story.extend(self._crear_seccion_tendencias(analisis_completo['tendencias'], graficos))
        story.append(PageBreak())
        
        # Recomendaciones
        story.extend(self._crear_seccion_recomendaciones(analisis_completo['recomendaciones']))
        story.append(PageBreak())
        
        # Tabla de datos
        story.extend(self._crear_tabla_datos(datos_analisis))
        
        # Construir PDF con headers y footers
        doc.build(story, onFirstPage=self._crear_header_footer, 
                 onLaterPages=self._crear_header_footer)
        
        return output_path
    
    def _preparar_datos_analisis(self, indices: List[IndiceMensual]) -> List[Dict]:
        """Prepara datos en formato para análisis"""
        datos = []
        for indice in indices:
            datos.append({
                'mes': f"{indice.año}-{indice.mes:02d}",
                'periodo': indice.periodo_texto,
                'ndvi': indice.ndvi_promedio,
                'ndmi': indice.ndmi_promedio,
                'savi': indice.savi_promedio,
                'temperatura': indice.temperatura_promedio,
                'precipitacion': indice.precipitacion_total
            })
        return datos
    
    def _ejecutar_analisis(self, datos: List[Dict], parcela: Parcela, indices: List) -> Dict:
        """Ejecuta todos los análisis, incluyendo Gemini AI"""
        # Inicializar analizadores tradicionales
        analizador_ndvi = AnalizadorNDVI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_ndmi = AnalizadorNDMI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_savi = AnalizadorSAVI(tipo_cultivo=parcela.tipo_cultivo)
        detector_tendencias = DetectorTendencias()
        generador_recomendaciones = GeneradorRecomendaciones(tipo_cultivo=parcela.tipo_cultivo)
        
        # Ejecutar análisis tradicionales
        analisis_ndvi = analizador_ndvi.analizar(datos)
        analisis_ndmi = analizador_ndmi.analizar(datos)
        analisis_savi = analizador_savi.analizar(datos) if any(d.get('savi') for d in datos) else None
        
        # Tendencias
        tendencias = detector_tendencias.analizar_temporal(datos, 'ndvi')
        
        # Recomendaciones tradicionales
        recomendaciones = generador_recomendaciones.generar_recomendaciones(
            analisis_ndvi, analisis_ndmi, analisis_savi, tendencias
        )
        
        # 🤖 ANÁLISIS CON GEMINI AI (caché optimizado y control de tokens)
        analisis_gemini = None
        motivo_regeneracion = None
        if gemini_service:
            try:
                # VERIFICAR SI EXISTE ANÁLISIS EN CACHÉ
                ultimo_indice = indices.order_by('-año', '-mes').first()
                if ultimo_indice and ultimo_indice.analisis_gemini and ultimo_indice.fecha_analisis_gemini:
                    from datetime import timedelta
                    edad_cache = datetime.now() - ultimo_indice.fecha_analisis_gemini.replace(tzinfo=None)
                    # Verificar si el caché tiene menos de 30 días
                    if edad_cache < timedelta(days=30):
                        # Verificar si los datos NDVI/clima han cambiado desde el análisis
                        datos_actuales = {
                            'ndvi': ultimo_indice.ndvi_promedio,
                            'clima': getattr(ultimo_indice, 'clima', None),
                        }
                        datos_analizados = ultimo_indice.analisis_gemini.get('datos_usados', {})
                        if datos_actuales == datos_analizados:
                            logger.info(f"✅ Usando análisis de Gemini desde caché (edad: {edad_cache.days} días)")
                            analisis_gemini = ultimo_indice.analisis_gemini
                        else:
                            motivo_regeneracion = 'Datos NDVI/clima cambiaron'
                            logger.info(f"♻️ Regenerando análisis: datos cambiaron desde el último análisis")
                    else:
                        motivo_regeneracion = 'Caché expirado'
                        logger.info(f"⚠️ Caché expirado ({edad_cache.days} días), regenerando análisis")
                else:
                    motivo_regeneracion = 'No hay caché previo'
                # SI NO HAY CACHÉ VÁLIDO, GENERAR NUEVO ANÁLISIS
                if not analisis_gemini:
                    logger.info(f"🤖 Generando análisis con Gemini AI para parcela {parcela.nombre} (motivo: {motivo_regeneracion})")
                    # Preparar datos mínimos de la parcela
                    parcela_data = {
                        'nombre': parcela.nombre,
                        'area_hectareas': float(parcela.area_hectareas) if parcela.area_hectareas else 0,
                        'tipo_cultivo': parcela.tipo_cultivo or 'No especificado',
                        'propietario': str(parcela.propietario) if parcela.propietario else 'No especificado',
                    }
                    # Solo enviar imágenes si el usuario lo solicita explícitamente (por ahora, nunca por defecto)
                    imagenes_paths = None  # Cambia a lista si quieres habilitar imágenes
                    # Solo enviar los índices estrictamente necesarios
                    indices_minimos = [{
                        'mes': i.mes,
                        'año': i.año,
                        'ndvi_promedio': i.ndvi_promedio,
                        'ndvi_min': i.ndvi_min,
                        'ndvi_max': i.ndvi_max,
                    } for i in indices]
                    analisis_gemini = gemini_service.generar_analisis_informe(
                        parcela_data=parcela_data,
                        indices_mensuales=indices_minimos,
                        imagenes_paths=imagenes_paths,
                        tipo_analisis='completo'
                    )
                    # Guardar los datos usados para comparación futura
                    if analisis_gemini is not None:
                        ultimo_indice.analisis_gemini = {**analisis_gemini, 'datos_usados': datos_actuales}
                        ultimo_indice.fecha_analisis_gemini = datetime.now()
                        ultimo_indice.save(update_fields=['analisis_gemini', 'fecha_analisis_gemini'])
                        logger.info("💾 Análisis guardado en caché (con datos usados para control de duplicados)")
                    logger.info("✅ Análisis de Gemini generado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error generando análisis con Gemini: {str(e)}")
                analisis_gemini = None
        else:
            logger.warning("⚠️ Servicio de Gemini no disponible")
        
        return {
            'ndvi': analisis_ndvi,
            'ndmi': analisis_ndmi,
            'savi': analisis_savi,
            'tendencias': tendencias,
            'recomendaciones': recomendaciones,
            'gemini': analisis_gemini  # ✨ Nuevo: análisis de Gemini
        }
    
    def _generar_graficos(self, datos: List[Dict]) -> Dict[str, BytesIO]:
        """Genera todos los gráficos necesarios"""
        graficos = {}
        
        # Gráfico de evolución temporal
        graficos['evolucion_temporal'] = self._grafico_evolucion_temporal(datos)
        
        # Gráfico comparativo
        graficos['comparativo'] = self._grafico_comparativo(datos)
        
        return graficos
    
    def _grafico_evolucion_temporal(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de evolución temporal"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Configurar estilo
        sns.set_style("whitegrid")
        
        # Extraer datos
        meses = [d['periodo'] for d in datos]
        ndvi = [d.get('ndvi', 0) for d in datos]
        ndmi = [d.get('ndmi', 0) for d in datos]
        savi = [d.get('savi', 0) for d in datos]
        
        # Graficar
        ax.plot(meses, ndvi, marker='o', linewidth=2.5, color='#2E8B57', label='NDVI (Salud)', markersize=6)
        ax.plot(meses, ndmi, marker='s', linewidth=2.5, color='#17a2b8', label='NDMI (Humedad)', markersize=6)
        if any(savi):
            ax.plot(meses, savi, marker='^', linewidth=2.5, color='#FF7A00', label='SAVI (Cobertura)', markersize=6)
        
        # Configurar
        ax.set_xlabel('Período', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valor del Índice', fontsize=12, fontweight='bold')
        ax.set_title('Evolución Temporal de Índices de Vegetación', 
                     fontsize=14, fontweight='bold', color='#2c3e50')
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Rotar etiquetas
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Guardar en buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _grafico_comparativo(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de barras comparativo"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calcular promedios (filtrar None)
        ndvi_valores = [d.get('ndvi') for d in datos if d.get('ndvi') is not None]
        ndmi_valores = [d.get('ndmi') for d in datos if d.get('ndmi') is not None]
        savi_valores = [d.get('savi') for d in datos if d.get('savi') is not None]
        
        ndvi_prom = sum(ndvi_valores) / len(ndvi_valores) if ndvi_valores else 0
        ndmi_prom = sum(ndmi_valores) / len(ndmi_valores) if ndmi_valores else 0
        savi_prom = sum(savi_valores) / len(savi_valores) if savi_valores else 0
        
        indices = ['NDVI\n(Salud)', 'NDMI\n(Humedad)', 'SAVI\n(Cobertura)']
        valores = [ndvi_prom, ndmi_prom, savi_prom]
        colores_barra = ['#2E8B57', '#17a2b8', '#FF7A00']
        
        # Crear barras
        bars = ax.bar(indices, valores, color=colores_barra, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Añadir valores encima de las barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{valor:.3f}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Valor Promedio', fontsize=12, fontweight='bold')
        ax.set_title('Comparación de Índices - Promedio del Período', 
                    fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_ylim(0, max(valores) * 1.2)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _crear_portada(self, parcela: Parcela, fecha_inicio: date, fecha_fin: date) -> List:
        """Crea la portada del informe"""
        elements = []
        
        # Logo AgroTech (buscar en static)
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'img', 'agrotech-logo-text.svg')
        if not os.path.exists(logo_path):
            # Buscar alternativas
            logo_path = os.path.join(settings.BASE_DIR, 'historical', 'static', 'img', 'agrotech-logo-text.svg')
        
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=10*cm, height=3*cm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 1.5*cm))
            except:
                # Si falla, poner texto
                titulo_logo = Paragraph("🌾 AgroTech Histórico", self.estilos['TituloPortada'])
                elements.append(titulo_logo)
                elements.append(Spacer(1, 1*cm))
        else:
            # Texto alternativo
            titulo_logo = Paragraph("🌾 AgroTech Histórico", self.estilos['TituloPortada'])
            elements.append(titulo_logo)
            elements.append(Spacer(1, 1*cm))
        
        # Título del informe
        titulo = Paragraph(
            f"Informe Satelital Agrícola<br/><font size=20>{parcela.nombre}</font>",
            self.estilos['TituloPortada']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 2*cm))
        
        # Tabla de información
        info_data = [
            ['Parcela:', parcela.nombre],
            ['Propietario:', parcela.propietario],
            ['Cultivo:', parcela.tipo_cultivo or 'No especificado'],
            ['Área:', f"{parcela.area_hectareas:.2f} hectáreas"],
            ['Período Analizado:', f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"],
            ['Fecha de Generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        tabla = Table(info_data, colWidths=[5*cm, 11*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colores['verde_principal']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.colores['gris_oscuro']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.colores['gris_claro']]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(tabla)
        elements.append(Spacer(1, 3*cm))
        
        # Pie de portada
        pie = Paragraph(
            "Este informe fue generado automáticamente mediante análisis satelital "
            "con tecnología EOSDA y sistema de análisis inteligente AgroTech. "
            "Todos los datos y recomendaciones están basados en imágenes Sentinel-2 y algoritmos científicos validados.",
            self.estilos['TextoNormal']
        )
        elements.append(pie)
        
        return elements
    
    def _crear_header_footer(self, canvas_obj, doc):
        """Crea header y footer en cada página"""
        canvas_obj.saveState()
        
        # Header - Logo pequeño
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'img', 'favicon.svg')
        if os.path.exists(logo_path):
            try:
                canvas_obj.drawImage(logo_path, self.margen, self.alto - self.margen + 0.5*cm, 
                                   width=1*cm, height=1*cm, preserveAspectRatio=True)
            except:
                pass
        
        # Header - Texto
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(self.colores['gris_oscuro'])
        canvas_obj.drawString(self.margen + 1.5*cm, self.alto - self.margen + 0.7*cm, 
                            "AgroTech - Análisis Satelital Agrícola")
        
        # Footer - Número de página
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawCentredString(self.ancho / 2, self.margen / 2, 
                                     f"Página {doc.page}")
        
        # Footer - Fecha
        canvas_obj.drawRightString(self.ancho - self.margen, self.margen / 2,
                                  datetime.now().strftime('%d/%m/%Y'))
        
        canvas_obj.restoreState()
    
    # Continúo en el siguiente mensaje con las secciones del informe...
    
    def _crear_resumen_ejecutivo(self, analisis: Dict) -> List:
        """Crea resumen ejecutivo del informe, priorizando análisis de Gemini AI"""
        elements = []
        
        # Título
        titulo = Paragraph("📊 Resumen Ejecutivo", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # 🤖 SI HAY ANÁLISIS DE GEMINI, USARLO
        if analisis.get('gemini') and not analisis['gemini'].get('error'):
            gemini_data = analisis['gemini']
            
            # Añadir indicador de análisis IA
            badge_ia = Paragraph(
                '<para alignment="right"><font color="#17a2b8"><b>🤖 Análisis generado con Gemini AI</b></font></para>',
                self.estilos['TextoNormal']
            )
            elements.append(badge_ia)
            elements.append(Spacer(1, 0.3*cm))
            
            # Resumen ejecutivo de Gemini
            resumen_gemini = gemini_data.get('resumen_ejecutivo', '')
            if resumen_gemini:
                # Limpiar y formatear texto
                resumen_texto = resumen_gemini.replace('\n', '<br/>')
                resumen_texto = limpiar_html_para_reportlab(resumen_texto)
                
                resumen = Paragraph(resumen_texto, self.estilos['TextoNormal'])
                elements.append(resumen)
                elements.append(Spacer(1, 0.5*cm))
            
            # Agregar métricas básicas tradicionales como complemento
            ndvi_punt = analisis['ndvi'].get('puntuacion', 0)
            ndmi_punt = analisis['ndmi'].get('puntuacion', 0)
            promedio_general = (ndvi_punt + ndmi_punt) / 2
            
            metricas_complemento = f"""
<para alignment="left"><font size="9" color="#666666">
<b>Métricas Cuantitativas:</b><br/>
• Puntuación General: {promedio_general:.1f}/10<br/>
• NDVI: {analisis['ndvi']['estadisticas']['promedio']:.3f} ({analisis['ndvi']['estado']['etiqueta']})<br/>
• NDMI: {analisis['ndmi']['estadisticas']['promedio']:.3f} ({analisis['ndmi']['estado']['etiqueta']})<br/>
• Tendencia: {analisis['tendencias'].get('tendencia_lineal', {}).get('direccion', 'estable').title()} 
  ({analisis['tendencias'].get('tendencia_lineal', {}).get('cambio_porcentual', 0):+.1f}%)
</font></para>
"""
            complemento = Paragraph(metricas_complemento, self.estilos['TextoNormal'])
            elements.append(complemento)
            
        else:
            # FALLBACK: Usar análisis tradicional si Gemini no está disponible
            if analisis.get('gemini') and analisis['gemini'].get('error'):
                logger.warning(f"⚠️ Error en Gemini, usando análisis tradicional: {analisis['gemini'].get('error')}")
            
            # Puntuaciones tradicionales
            ndvi_punt = analisis['ndvi'].get('puntuacion', 0)
            ndmi_punt = analisis['ndmi'].get('puntuacion', 0)
            
            promedio_general = (ndvi_punt + ndmi_punt) / 2
            
            resumen_texto = f"""
<strong>Puntuación General del Cultivo: {promedio_general:.1f}/10</strong><br/><br/>

<strong>Estado de Salud Vegetal (NDVI):</strong> {analisis['ndvi']['estado']['etiqueta']} 
({analisis['ndvi']['estadisticas']['promedio']:.3f}) - Puntuación: {ndvi_punt}/10<br/>

<strong>Estado Hídrico (NDMI):</strong> {analisis['ndmi']['estado']['etiqueta']} 
({analisis['ndmi']['estadisticas']['promedio']:.3f}) - Puntuación: {ndmi_punt}/10<br/><br/>

<strong>Tendencia General:</strong> {analisis['tendencias'].get('tendencia_lineal', {}).get('direccion', 'estable').title()} 
({analisis['tendencias'].get('tendencia_lineal', {}).get('cambio_porcentual', 0):+.1f}%)<br/><br/>

<strong>Recomendaciones Prioritarias:</strong> {len([r for r in analisis['recomendaciones'] if r['prioridad'] == 'alta'])} 
recomendaciones de alta prioridad requieren atención.<br/>
"""
            
            resumen = Paragraph(resumen_texto, self.estilos['TextoNormal'])
            elements.append(resumen)
        
        return elements
    
    def _crear_info_parcela(self, parcela: Parcela) -> List:
        """Crea sección de información de la parcela"""
        elements = []
        
        titulo = Paragraph("📍 Información de la Parcela", self.estilos['TituloSeccion'])
        elements.append(titulo)
        
        # Coordenadas del centroide
        if parcela.centroide:
            lat = parcela.centroide.y
            lon = parcela.centroide.x
            coordenadas = f"{lat:.6f}, {lon:.6f}"
        else:
            coordenadas = "No disponible"
        
        info_texto = f"""
<strong>Nombre:</strong> {parcela.nombre}<br/>
<strong>Propietario:</strong> {parcela.propietario}<br/>
<strong>Tipo de Cultivo:</strong> {parcela.tipo_cultivo or 'No especificado'}<br/>
<strong>Área:</strong> {parcela.area_hectareas:.2f} hectáreas<br/>
<strong>Ubicación (Centro):</strong> {coordenadas}<br/>
<strong>Fecha de Inicio de Monitoreo:</strong> {parcela.fecha_inicio_monitoreo.strftime('%d/%m/%Y') if parcela.fecha_inicio_monitoreo else 'No especificado'}<br/>
"""
        
        info = Paragraph(info_texto, self.estilos['TextoNormal'])
        elements.append(info)
        
        return elements
    
    def _crear_seccion_ndvi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDVI"""
        elements = []
        
        titulo = Paragraph("🌱 Análisis NDVI - Salud Vegetal", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>NDVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis['puntuacion']}/10<br/>
<strong>Cobertura Estimada:</strong> {analisis['cobertura_estimada']}%<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_para_reportlab(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_para_reportlab(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['TextoNormal']))
        
        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>⚠️ Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas'][:3]:  # Máximo 3 alertas
                alerta_texto = f"{alerta['icono']} <strong>{alerta['titulo']}:</strong> {alerta['mensaje']}"
                alerta_limpia = limpiar_html_para_reportlab(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_ndmi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDMI"""
        elements = []
        
        titulo = Paragraph("💧 Análisis NDMI - Contenido de Humedad", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado Hídrico:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>NDMI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis['puntuacion']}/10<br/>
<strong>Riesgo Hídrico:</strong> {analisis['riesgo_hidrico']}<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_para_reportlab(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_para_reportlab(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['TextoNormal']))
        
        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>⚠️ Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas'][:3]:
                alerta_texto = f"{alerta['icono']} <strong>{alerta['titulo']}:</strong> {alerta['mensaje']}"
                alerta_limpia = limpiar_html_para_reportlab(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_savi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis SAVI"""
        elements = []
        
        titulo = Paragraph("🌾 Análisis SAVI - Cobertura Vegetal", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Cobertura:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>SAVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Exposición de Suelo:</strong> {analisis['exposicion_suelo']}%<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_para_reportlab(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_tendencias(self, tendencias: Dict, graficos: Dict) -> List:
        """Crea sección de análisis de tendencias"""
        elements = []
        
        titulo = Paragraph("📈 Análisis de Tendencias Temporales", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico de evolución
        if 'evolucion_temporal' in graficos:
            img = Image(graficos['evolucion_temporal'], width=16*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 1:</strong> Evolución temporal de índices de vegetación durante el período analizado.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
            elements.append(Spacer(1, 1*cm))
        
        # Resumen de tendencias
        if tendencias.get('resumen'):
            resumen_limpio = limpiar_html_para_reportlab(tendencias['resumen'])
            elements.append(Paragraph(resumen_limpio, self.estilos['TextoNormal']))
        
        # Tendencia lineal
        if 'tendencia_lineal' in tendencias:
            tl = tendencias['tendencia_lineal']
            tendencia_texto = f"""
<strong>Tendencia Lineal:</strong> {tl.get('direccion', '').title()} - 
Fuerza {tl.get('fuerza', '').title()}<br/>
<strong>Cambio Total:</strong> {tl.get('cambio_porcentual', 0):+.1f}%<br/>
<strong>Confiabilidad:</strong> {tl.get('confianza', '').title()} (R² = {tl.get('r_cuadrado', 0):.3f})<br/>
"""
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(tendencia_texto, self.estilos['TextoNormal']))
        
        # Gráfico comparativo
        if 'comparativo' in graficos:
            elements.append(Spacer(1, 1*cm))
            img = Image(graficos['comparativo'], width=14*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 2:</strong> Comparación de promedios de índices durante el período.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
        
        return elements
    
    def _crear_seccion_recomendaciones(self, recomendaciones: List[Dict]) -> List:
        """Crea sección de recomendaciones"""
        elements = []
        
        titulo = Paragraph("💡 Recomendaciones Agronómicas", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        intro = Paragraph(
            "A continuación se presentan las recomendaciones priorizadas para el manejo del cultivo, "
            "ordenadas por nivel de prioridad (Alta, Media, Baja).",
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.5*cm))
        
        # Agrupar por prioridad
        por_prioridad = {'alta': [], 'media': [], 'baja': []}
        for rec in recomendaciones:
            prioridad = rec.get('prioridad', 'baja')
            por_prioridad[prioridad].append(rec)
        
        # Renderizar por prioridad
        contador = 1
        for prioridad in ['alta', 'media', 'baja']:
            if por_prioridad[prioridad]:
                # Título de prioridad
                if prioridad == 'alta':
                    titulo_prioridad = "🔴 Prioridad Alta"
                elif prioridad == 'media':
                    titulo_prioridad = "🟡 Prioridad Media"
                else:
                    titulo_prioridad = "🟢 Prioridad Baja"
                
                elements.append(Paragraph(f"<strong>{titulo_prioridad}</strong>", self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.3*cm))
                
                for rec in por_prioridad[prioridad]:
                    # Crear tabla para cada recomendación
                    rec_data = [
                        [f"<strong>{contador}. {rec['titulo']}</strong>"],
                        [f"<strong>Para técnicos:</strong> {rec['descripcion_tecnica']}"],
                        [f"<strong>En palabras simples:</strong> {rec['descripcion_simple']}"],
                        [f"<strong>Acciones sugeridas:</strong>"]
                    ]
                    
                    # Añadir acciones
                    for accion in rec['acciones'][:5]:  # Máximo 5 acciones
                        rec_data.append([f"  • {accion}"])
                    
                    rec_data.append([f"<strong>Impacto esperado:</strong> {rec['impacto_esperado']}"])
                    rec_data.append([f"<strong>Tiempo de implementación:</strong> {rec['tiempo_implementacion']}"])
                    
                    tabla_rec = Table(rec_data, colWidths=[16*cm])
                    tabla_rec.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('TEXTCOLOR', (0, 0), (-1, -1), self.colores['gris_oscuro']),
                        ('BACKGROUND', (0, 0), (-1, 0), self.colores['gris_claro']),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    
                    elements.append(tabla_rec)
                    elements.append(Spacer(1, 0.5*cm))
                    contador += 1
        
        return elements
    
    def _crear_seccion_analisis_gemini(self, analisis_gemini: Dict) -> List:
        """
        Crea sección con análisis detallado de Gemini AI
        Incluye: Análisis de Tendencias, Recomendaciones IA y Alertas
        """
        elements = []
        
        # Título principal de la sección
        titulo = Paragraph(
            "🤖 Análisis Inteligente con Gemini AI", 
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.3*cm))
        
        # Badge informativo
        badge = Paragraph(
            '<para alignment="center"><font color="#17a2b8" size="9">'
            '<i>Los siguientes análisis han sido generados por inteligencia artificial '
            'especializada en agronomía y teledetección satelital.</i></font></para>',
            self.estilos['TextoNormal']
        )
        elements.append(badge)
        elements.append(Spacer(1, 0.7*cm))
        
        # === ANÁLISIS DE TENDENCIAS ===
        if analisis_gemini.get('analisis_tendencias'):
            subtitulo = Paragraph("📈 Análisis de Tendencias", self.estilos['SubtituloSeccion'])
            elements.append(subtitulo)
            elements.append(Spacer(1, 0.3*cm))
            
            tendencias_texto = analisis_gemini['analisis_tendencias']
            # Convertir saltos de línea a <br/>
            tendencias_texto = tendencias_texto.replace('\n\n', '<br/><br/>')
            tendencias_texto = tendencias_texto.replace('\n', '<br/>')
            tendencias_texto = limpiar_html_para_reportlab(tendencias_texto)
            
            tendencias = Paragraph(tendencias_texto, self.estilos['TextoNormal'])
            elements.append(tendencias)
            elements.append(Spacer(1, 0.7*cm))
        
        # === ANÁLISIS VISUAL DE IMÁGENES SATELITALES ===
        if analisis_gemini.get('analisis_visual'):
            analisis_visual_texto = analisis_gemini['analisis_visual'].strip()
            
            # Solo mostrar si hay análisis visual real (no el mensaje por defecto)
            if analisis_visual_texto and 'no disponible' not in analisis_visual_texto.lower():
                subtitulo = Paragraph("🛰️ Análisis Visual de Imágenes Satelitales", self.estilos['SubtituloSeccion'])
                elements.append(subtitulo)
                elements.append(Spacer(1, 0.3*cm))
                
                analisis_visual_texto = analisis_visual_texto.replace('\n\n', '<br/><br/>')
                analisis_visual_texto = analisis_visual_texto.replace('\n', '<br/>')
                analisis_visual_texto = limpiar_html_para_reportlab(analisis_visual_texto)
                
                analisis_visual = Paragraph(analisis_visual_texto, self.estilos['TextoNormal'])
                
                # Tabla con fondo verde claro para análisis visual
                tabla_visual = Table([[analisis_visual]], colWidths=[16*cm])
                tabla_visual.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fff4')),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4CAF50')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                
                elements.append(tabla_visual)
                elements.append(Spacer(1, 0.7*cm))
        
        # === RECOMENDACIONES IA ===
        if analisis_gemini.get('recomendaciones'):
            subtitulo = Paragraph("💡 Recomendaciones del Experto IA", self.estilos['SubtituloSeccion'])
            elements.append(subtitulo)
            elements.append(Spacer(1, 0.3*cm))
            
            recomendaciones_texto = analisis_gemini['recomendaciones']
            # Convertir formato de lista a HTML
            recomendaciones_texto = recomendaciones_texto.replace('\n\n', '<br/><br/>')
            recomendaciones_texto = recomendaciones_texto.replace('\n', '<br/>')
            recomendaciones_texto = limpiar_html_para_reportlab(recomendaciones_texto)
            
            # Crear caja destacada para recomendaciones
            recomendaciones = Paragraph(recomendaciones_texto, self.estilos['TextoNormal'])
            
            # Tabla para dar formato de caja
            tabla_rec = Table([[recomendaciones]], colWidths=[16*cm])
            tabla_rec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8ff')),
                ('BOX', (0, 0), (-1, -1), 2, self.colores['azul']),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            elements.append(tabla_rec)
            elements.append(Spacer(1, 0.7*cm))
        
        # === ALERTAS ===
        if analisis_gemini.get('alertas'):
            alertas_texto = analisis_gemini['alertas'].strip()
            
            # Solo mostrar si hay alertas reales (no el mensaje por defecto)
            if alertas_texto and 'No se detectaron alertas' not in alertas_texto:
                subtitulo = Paragraph("⚠️ Alertas y Situaciones Críticas", self.estilos['SubtituloSeccion'])
                elements.append(subtitulo)
                elements.append(Spacer(1, 0.3*cm))
                
                alertas_texto = alertas_texto.replace('\n\n', '<br/><br/>')
                alertas_texto = alertas_texto.replace('\n', '<br/>')
                alertas_texto = limpiar_html_para_reportlab(alertas_texto)
                
                alertas = Paragraph(alertas_texto, self.estilos['TextoNormal'])
                
                # Tabla con fondo rojo claro para alertas
                tabla_alertas = Table([[alertas]], colWidths=[16*cm])
                tabla_alertas.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff5f5')),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ff4444')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                
                elements.append(tabla_alertas)
                elements.append(Spacer(1, 0.5*cm))
            else:
                # Mensaje positivo si no hay alertas
                sin_alertas = Paragraph(
                    '<para alignment="center"><font color="green" size="10">'
                    '<b>✅ No se detectaron situaciones críticas que requieran atención inmediata.</b>'
                    '</font></para>',
                    self.estilos['TextoNormal']
                )
                elements.append(sin_alertas)
                elements.append(Spacer(1, 0.5*cm))
        
        # Nota al pie de la sección
        nota = Paragraph(
            '<para alignment="right"><font size="8" color="#666666">'
            '<i>Análisis generado por Google Gemini AI - Modelo gemini-2.5-flash</i>'
            '</font></para>',
            self.estilos['TextoNormal']
        )
        elements.append(nota)
        
        return elements
    
    def _crear_galeria_imagenes_satelitales(self, parcela: Parcela, indices: List[IndiceMensual], analisis_gemini: Dict = None) -> List:
        """
        Crea una galería de imágenes satelitales (NDVI, NDMI, SAVI) mes a mes
        con análisis visual específico por imagen generado por Gemini AI
        """
        elements = []
        
        # Título de la sección con diseño mejorado
        titulo = Paragraph(
            '📸 <font size="16"><strong>Imágenes Satelitales y Análisis Visual Detallado</strong></font>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Introducción mejorada con explicación de colores
        intro = Paragraph(
            """
            <strong>Esta sección presenta un análisis visual detallado de las imágenes satelitales capturadas mes a mes.</strong>
            <br/><br/>
            Cada imagen es analizada por inteligencia artificial para identificar patrones espaciales, zonas específicas 
            y cambios temporales. Los colores en las imágenes representan:
            <br/><br/>
            • <strong>NDVI (Vigor Vegetal):</strong> Verde oscuro = alta biomasa, amarillo/marrón = baja vegetación<br/>
            • <strong>NDMI (Contenido de Humedad):</strong> Azul/verde = alta humedad, rojo/amarillo = baja humedad<br/>
            • <strong>SAVI (Cobertura del Suelo):</strong> Verde = buena cobertura, marrón = suelo desnudo visible
            """,
            self.estilos['TextoNormal']
        )
        
        # Crear caja destacada para la introducción
        tabla_intro = Table([[intro]], colWidths=[15*cm])
        tabla_intro.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
            ('BOX', (0, 0), (-1, -1), 2, self.colores['verde_principal']),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(tabla_intro)
        elements.append(Spacer(1, 0.7*cm))
        
        # Procesar cada índice mensual
        imagenes_encontradas = 0
        meses_procesados = 0
        
        for idx in indices:
            tiene_imagenes = False
            
            # Verificar si hay imágenes para este mes
            if (idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path)) or \
               (idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path)) or \
               (idx.imagen_savi and os.path.exists(idx.imagen_savi.path)):
                tiene_imagenes = True
            
            # Si hay imágenes para este mes, procesarlas
            if tiene_imagenes:
                meses_procesados += 1
                
                # === SEPARADOR VISUAL ENTRE MESES ===
                if meses_procesados > 1:
                    from reportlab.platypus import HRFlowable
                    elements.append(Spacer(1, 0.3*cm))
                    elements.append(HRFlowable(
                        width="100%", 
                        thickness=2, 
                        color=self.colores['verde_principal'],
                        spaceAfter=0.5*cm,
                        spaceBefore=0.3*cm
                    ))
                
                # === TÍTULO DEL MES CON DISEÑO DESTACADO ===
                titulo_mes = Paragraph(
                    f'<font size="13" color="#2E8B57"><strong>📅 {idx.periodo_texto}</strong></font>',
                    self.estilos['SubtituloSeccion']
                )
                elements.append(titulo_mes)
                elements.append(Spacer(1, 0.2*cm))
                
                # === METADATOS DE LA CAPTURA EN FORMATO MEJORADO ===
                metadatos_data = [
                    ['📅 Fecha de captura:', idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'],
                    ['🛰️ Satélite:', idx.satelite_imagen or 'Sentinel-2'],
                    ['📏 Resolución espacial:', f"{idx.resolucion_imagen or 10} metros/píxel"],
                    ['☁️ Nubosidad:', f"{idx.nubosidad_imagen or 0:.1f}%"],
                    ['🌍 Coordenadas:', f"({parcela.latitud:.6f}, {parcela.longitud:.6f})" if hasattr(parcela, 'latitud') else 'N/A']
                ]
                
                tabla_metadatos = Table(metadatos_data, colWidths=[4*cm, 11*cm])
                tabla_metadatos.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), self.colores['gris_oscuro']),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                
                elements.append(tabla_metadatos)
                elements.append(Spacer(1, 0.5*cm))
                
                # === PROCESAR CADA IMAGEN DISPONIBLE ===
                
                # NDVI
                if idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path):
                    imagenes_encontradas += 1
                    elements.extend(self._agregar_imagen_con_analisis(
                        idx, 'NDVI', idx.imagen_ndvi.path, 
                        "Índice de Vegetación de Diferencia Normalizada - Mide la salud y vigor vegetal",
                        usar_gemini=True
                    ))
                
                # NDMI
                if idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path):
                    imagenes_encontradas += 1
                    elements.extend(self._agregar_imagen_con_analisis(
                        idx, 'NDMI', idx.imagen_ndmi.path,
                        "Índice de Humedad de Diferencia Normalizada - Mide el contenido de agua en la vegetación",
                        usar_gemini=True
                    ))
                
                # SAVI
                if idx.imagen_savi and os.path.exists(idx.imagen_savi.path):
                    imagenes_encontradas += 1
                    elements.extend(self._agregar_imagen_con_analisis(
                        idx, 'SAVI', idx.imagen_savi.path,
                        "Índice de Vegetación Ajustado al Suelo - Mide la cobertura vegetal minimizando el efecto del suelo",
                        usar_gemini=True
                    ))
        
        # Si no se encontraron imágenes
        if imagenes_encontradas == 0:
            sin_imagenes = Paragraph(
                '<para alignment="center"><font color="#999999" size="11">'
                '<br/><br/><br/>'
                '<strong>📭 No hay imágenes satelitales disponibles para este período</strong><br/><br/>'
                '<i>Las imágenes se descargan automáticamente desde EOSDA Field Imagery API.<br/>'
                'Pueden requerirse hasta 24-48 horas para estar disponibles después de la captura.</i>'
                '<br/><br/><br/>'
                '</font></para>',
                self.estilos['TextoNormal']
            )
            
            tabla_sin_img = Table([[sin_imagenes]], colWidths=[15*cm])
            tabla_sin_img.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107')),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            
            elements.append(tabla_sin_img)
        else:
            # === ANÁLISIS GLOBAL CONSOLIDADO ===
            elements.extend(self._crear_analisis_global_imagenes(parcela, indices, imagenes_encontradas))
            
            # Nota al final con resumen
            nota_final = Paragraph(
                f'<para alignment="right"><font size="9" color="#2E8B57">'
                f'<strong>✓ Total de imágenes analizadas: {imagenes_encontradas}</strong> | '
                f'Meses procesados: {meses_procesados}'
                f'</font></para>',
                self.estilos['TextoNormal']
            )
            elements.append(Spacer(1, 0.3*cm))
            elements.append(nota_final)
        
        return elements
    
    def _crear_analisis_global_imagenes(self, parcela: Parcela, indices: List[IndiceMensual], 
                                        total_imagenes: int) -> List:
        """
        Crea la sección de análisis global consolidado de todas las imágenes
        """
        elements = []
        
        # Separador visual fuerte
        from reportlab.platypus import HRFlowable
        elements.append(Spacer(1, 0.7*cm))
        elements.append(HRFlowable(
            width="100%", 
            thickness=3, 
            color=self.colores['verde_principal'],
            spaceAfter=0.7*cm,
            spaceBefore=0.3*cm
        ))
        
        # Título de la sección
        titulo_global = Paragraph(
            '🎯 <font size="14"><strong>Análisis Global Consolidado del Período</strong></font>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo_global)
        elements.append(Spacer(1, 0.5*cm))
        
        # Subtítulo explicativo
        subtitulo = Paragraph(
            '<font size="10"><i>Evaluación integral basada en todas las imágenes satelitales del período, '
            'con identificación de patrones espaciales y recomendaciones específicas por zona.</i></font>',
            self.estilos['TextoNormal']
        )
        elements.append(subtitulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Preparar datos para Gemini
        imagenes_datos = []
        
        for idx in indices:
            # NDVI
            if idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path) and idx.ndvi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_ndvi.path,
                    'tipo_indice': 'NDVI',
                    'valor_promedio': idx.ndvi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
            
            # NDMI
            if idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path) and idx.ndmi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_ndmi.path,
                    'tipo_indice': 'NDMI',
                    'valor_promedio': idx.ndmi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
            
            # SAVI
            if idx.imagen_savi and os.path.exists(idx.imagen_savi.path) and idx.savi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_savi.path,
                    'tipo_indice': 'SAVI',
                    'valor_promedio': idx.savi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
        
        # Generar análisis global con Gemini
        if imagenes_datos:
            try:
                parcela_info = {
                    'nombre': parcela.nombre,
                    'area': parcela.area_hectareas,
                    'coordenadas': f"({parcela.latitud:.6f}, {parcela.longitud:.6f})" if hasattr(parcela, 'latitud') else 'N/A'
                }
                
                analisis_global = gemini_service.generar_analisis_global_imagenes(
                    imagenes_datos=imagenes_datos,
                    parcela_info=parcela_info
                )
                
                # Badge de Gemini AI
                badge_ai = Paragraph(
                    '<font size="8" color="#666666"><strong>🤖 Análisis consolidado generado por Gemini AI</strong></font>',
                    self.estilos['TextoNormal']
                )
                elements.append(badge_ai)
                elements.append(Spacer(1, 0.2*cm))
                
                # Crear párrafo con el análisis
                analisis_parrafo = Paragraph(analisis_global, self.estilos['TextoNormal'])
                
                # Caja destacada con análisis global
                tabla_global = Table([[analisis_parrafo]], colWidths=[15*cm])
                tabla_global.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
                    ('BOX', (0, 0), (-1, -1), 3, self.colores['verde_principal']),
                    ('TOPPADDING', (0, 0), (-1, -1), 15),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ]))
                
                elements.append(tabla_global)
                elements.append(Spacer(1, 0.5*cm))
                
            except Exception as e:
                logger.error(f"❌ Error generando análisis global: {str(e)}")
                # Mensaje de error discreto
                error_msg = Paragraph(
                    '<font size="9" color="#999999"><i>Análisis global no disponible en este momento.</i></font>',
                    self.estilos['TextoNormal']
                )
                elements.append(error_msg)
        
        return elements
    
    def _agregar_imagen_con_analisis(self, indice: IndiceMensual, tipo_indice: str, 
                                      imagen_path: str, descripcion: str, usar_gemini: bool = True) -> List:
        """
        Agrega una imagen satelital con su análisis visual específico usando Gemini AI
        
        Args:
            indice: IndiceMensual con los datos del mes
            tipo_indice: 'NDVI', 'NDMI', 'SAVI'
            imagen_path: Ruta a la imagen
            descripcion: Descripción del índice
            usar_gemini: Si usar Gemini AI para análisis visual (default: True)
        """
        elements = []
        
        try:
            # === IMAGEN ===
            # Cargar y mostrar la imagen más grande para mejor visualización
            img = Image(imagen_path, width=14*cm, height=10*cm)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.2*cm))
            
            # === TÍTULO Y DESCRIPCIÓN ===
            titulo_imagen = Paragraph(
                f"<strong>{tipo_indice}</strong> - {descripcion}",
                self.estilos['PieImagen']
            )
            elements.append(titulo_imagen)
            elements.append(Spacer(1, 0.3*cm))
            
            # === VALORES NUMÉRICOS ===
            valor_promedio = None
            valor_minimo = None
            valor_maximo = None
            
            if tipo_indice == 'NDVI':
                valor_promedio = indice.ndvi_promedio
                valor_minimo = indice.ndvi_minimo
                valor_maximo = indice.ndvi_maximo
            elif tipo_indice == 'NDMI':
                valor_promedio = indice.ndmi_promedio
                valor_minimo = indice.ndmi_minimo
                valor_maximo = indice.ndmi_maximo
            elif tipo_indice == 'SAVI':
                valor_promedio = indice.savi_promedio
                valor_minimo = indice.savi_minimo
                valor_maximo = indice.savi_maximo
            
            if valor_promedio is not None:
                min_texto = f"{valor_minimo:.3f}" if valor_minimo is not None else "N/A"
                max_texto = f"{valor_maximo:.3f}" if valor_maximo is not None else "N/A"
                
                valores_texto = f"""
<font size="9" color="#2c3e50">
<strong>Valor promedio:</strong> {valor_promedio:.3f} | 
<strong>Mínimo:</strong> {min_texto} | 
<strong>Máximo:</strong> {max_texto}
</font>
"""
                valores = Paragraph(valores_texto, self.estilos['TextoNormal'])
                elements.append(valores)
                elements.append(Spacer(1, 0.3*cm))
            
            # === ANÁLISIS VISUAL ESPECÍFICO CON GEMINI AI ===
            if usar_gemini and valor_promedio is not None:
                # Preparar contexto para Gemini
                datos_contexto = {
                    'fecha': indice.fecha_imagen.strftime('%d/%m/%Y') if indice.fecha_imagen else 'N/A',
                    'satelite': indice.satelite_imagen or 'Sentinel-2',
                    'resolucion': indice.resolucion_imagen or 10,
                    'nubosidad': indice.nubosidad_imagen or 0,
                    'coordenadas': f"({indice.parcela.latitud:.6f}, {indice.parcela.longitud:.6f})" if hasattr(indice.parcela, 'latitud') else 'N/A'
                }
                
                # Buscar mes anterior para comparación
                mes_anterior_data = self._obtener_datos_mes_anterior(indice, tipo_indice)
                
                # Generar análisis con Gemini
                try:
                    analisis_texto = gemini_service.analizar_imagen_satelital(
                        imagen_path=imagen_path,
                        tipo_indice=tipo_indice,
                        valor_promedio=valor_promedio,
                        datos_contexto=datos_contexto,
                        mes_anterior_data=mes_anterior_data
                    )
                    
                    # Agregar badge indicando que es análisis AI
                    badge_ai = Paragraph(
                        '<font size="7" color="#666666"><strong>🤖 Análisis generado por Gemini AI</strong></font>',
                        self.estilos['TextoNormal']
                    )
                    elements.append(badge_ai)
                    elements.append(Spacer(1, 0.1*cm))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Gemini falló para {tipo_indice}, usando análisis básico: {str(e)}")
                    analisis_texto = self._generar_analisis_visual_imagen(indice, tipo_indice, valor_promedio)
            else:
                # Usar análisis basado en reglas como fallback
                analisis_texto = self._generar_analisis_visual_imagen(indice, tipo_indice, valor_promedio)
            
            if analisis_texto:
                analisis = Paragraph(analisis_texto, self.estilos['TextoNormal'])
                
                # Caja con análisis visual
                tabla_analisis = Table([[analisis]], colWidths=[15*cm])
                tabla_analisis.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8f0')),  # Verde muy claro
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),  # Borde verde
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                
                elements.append(tabla_analisis)
            
            elements.append(Spacer(1, 0.5*cm))
            
        except Exception as e:
            logger.error(f"❌ Error agregando imagen {tipo_indice} de {indice.periodo_texto}: {str(e)}")
            error_msg = Paragraph(
                f'<font color="red">Error cargando imagen {tipo_indice}</font>',
                self.estilos['TextoNormal']
            )
            elements.append(error_msg)
        
        return elements
    
    def _obtener_datos_mes_anterior(self, indice: IndiceMensual, tipo_indice: str) -> Optional[Dict]:
        """
        Obtiene datos del mes anterior para comparación temporal
        """
        try:
            if indice.mes == 1:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año - 1, mes=12
                ).first()
            else:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año, mes=indice.mes - 1
                ).first()
            
            if mes_anterior:
                valor_anterior = None
                if tipo_indice == 'NDVI':
                    valor_anterior = mes_anterior.ndvi_promedio
                elif tipo_indice == 'NDMI':
                    valor_anterior = mes_anterior.ndmi_promedio
                elif tipo_indice == 'SAVI':
                    valor_anterior = mes_anterior.savi_promedio
                
                if valor_anterior:
                    return {
                        'fecha': mes_anterior.fecha_imagen.strftime('%d/%m/%Y') if mes_anterior.fecha_imagen else 'N/A',
                        'tipo_indice': tipo_indice,
                        'valor': valor_anterior
                    }
        except Exception as e:
            logger.debug(f"No se pudo obtener datos del mes anterior: {str(e)}")
        
        return None
    
    def _generar_analisis_visual_imagen(self, indice: IndiceMensual, tipo_indice: str, 
                                        valor_promedio: float) -> str:
        """
        Genera un análisis visual específico basado en los valores del índice
        y el contexto temporal (comparación con mes anterior si está disponible)
        """
        if valor_promedio is None:
            return ""
        
        analisis_partes = []
        
        # === INTERPRETACIÓN DEL VALOR ===
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.7:
                interpretacion = "La imagen muestra <strong>vegetación muy vigorosa</strong> con tonos verdes intensos. "
                interpretacion += "Las áreas más oscuras (verdes) indican alta densidad de biomasa y excelente salud vegetal."
            elif valor_promedio >= 0.5:
                interpretacion = "La imagen muestra <strong>vegetación saludable</strong> con predominio de tonos verdes. "
                interpretacion += "Se observa buena cobertura vegetal con desarrollo normal del cultivo."
            elif valor_promedio >= 0.3:
                interpretacion = "La imagen muestra <strong>vegetación moderada</strong> con tonos amarillos-verdes. "
                interpretacion += "Posibles áreas con menor vigor vegetal o cultivo en etapa temprana."
            else:
                interpretacion = "La imagen muestra <strong>baja vegetación</strong> con tonos amarillos-marrones. "
                interpretacion += "Predominio de suelo desnudo o vegetación muy dispersa/estresada."
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.2:
                interpretacion = "La imagen refleja <strong>alto contenido de humedad</strong> en la vegetación. "
                interpretacion += "Tonos azules-verdes indican buena hidratación de las plantas."
            elif valor_promedio >= 0.0:
                interpretacion = "La imagen muestra <strong>contenido moderado de humedad</strong>. "
                interpretacion += "Vegetación con niveles normales de agua."
            elif valor_promedio >= -0.2:
                interpretacion = "La imagen indica <strong>bajo contenido de humedad</strong>. "
                interpretacion += "Tonos cálidos sugieren estrés hídrico potencial o vegetación seca."
            else:
                interpretacion = "La imagen muestra <strong>muy baja humedad</strong> con tonos rojos-marrones. "
                interpretacion += "Vegetación severamente estresada o suelo desnudo."
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.5:
                interpretacion = "La imagen muestra <strong>excelente cobertura vegetal</strong>. "
                interpretacion += "Mínima exposición de suelo desnudo visible."
            elif valor_promedio >= 0.3:
                interpretacion = "La imagen muestra <strong>buena cobertura vegetal</strong>. "
                interpretacion += "Vegetación bien establecida con algo de suelo visible."
            else:
                interpretacion = "La imagen muestra <strong>cobertura vegetal baja</strong>. "
                interpretacion += "Considerable exposición de suelo desnudo entre la vegetación."
        
        analisis_partes.append(interpretacion)
        
        # === ANÁLISIS ESPACIAL (si hay heterogeneidad) ===
        if indice.ndvi_maximo and indice.ndvi_minimo and tipo_indice == 'NDVI':
            rango = indice.ndvi_maximo - indice.ndvi_minimo
            if rango > 0.2:
                analisis_partes.append(
                    f"<br/><br/><strong>Variabilidad espacial:</strong> Se observa <strong>heterogeneidad significativa</strong> "
                    f"dentro de la parcela (rango: {rango:.3f}). Las áreas más claras pueden corresponder a zonas con "
                    f"menor vigor, posiblemente en las zonas periféricas o áreas con condiciones menos favorables."
                )
            else:
                analisis_partes.append(
                    "<br/><br/><strong>Uniformidad:</strong> La parcela muestra <strong>distribución relativamente uniforme</strong> "
                    "del índice, lo que indica condiciones homogéneas en la mayoría del área cultivada."
                )
        
        # === COMPARACIÓN TEMPORAL (buscar mes anterior) ===
        try:
            # Buscar el mes anterior
            if indice.mes == 1:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año - 1, mes=12
                ).first()
            else:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año, mes=indice.mes - 1
                ).first()
            
            if mes_anterior:
                valor_anterior = None
                if tipo_indice == 'NDVI':
                    valor_anterior = mes_anterior.ndvi_promedio
                elif tipo_indice == 'NDMI':
                    valor_anterior = mes_anterior.ndmi_promedio
                elif tipo_indice == 'SAVI':
                    valor_anterior = mes_anterior.savi_promedio
                
                if valor_anterior:
                    cambio = valor_promedio - valor_anterior
                    cambio_pct = (cambio / abs(valor_anterior)) * 100 if valor_anterior != 0 else 0
                    
                    if abs(cambio) > 0.05:  # Cambio significativo
                        if cambio > 0:
                            analisis_partes.append(
                                f"<br/><br/><strong>Cambio temporal:</strong> Comparado con {mes_anterior.periodo_texto}, "
                                f"se observa un <strong>incremento notable</strong> ({cambio:+.3f}, {cambio_pct:+.1f}%). "
                                f"Visualmente esto se traduce en mayor intensidad de color verde/azul en la imagen actual, "
                                f"indicando mejora en las condiciones de la vegetación."
                            )
                        else:
                            analisis_partes.append(
                                f"<br/><br/><strong>Cambio temporal:</strong> Comparado con {mes_anterior.periodo_texto}, "
                                f"se observa una <strong>disminución notable</strong> ({cambio:.3f}, {cambio_pct:.1f}%). "
                                f"Visualmente se aprecia un cambio hacia tonos más cálidos (amarillos/marrones), "
                                f"lo que sugiere reducción en vigor vegetal o contenido de humedad."
                            )
        except Exception as e:
            logger.debug(f"No se pudo comparar con mes anterior: {str(e)}")
        
        return "".join(analisis_partes)
    
    def _crear_tabla_datos(self, datos: List[Dict]) -> List:
        """Crea tabla con datos mensuales"""
        elements = []
        
        titulo = Paragraph("📋 Datos Mensuales Detallados", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Preparar datos de la tabla
        table_data = [['Período', 'NDVI', 'NDMI', 'SAVI', 'Temp (°C)', 'Precip (mm)']]
        
        for dato in datos:
            table_data.append([
                dato['periodo'],
                f"{dato.get('ndvi', 0):.3f}" if dato.get('ndvi') else 'N/D',
                f"{dato.get('ndmi', 0):.3f}" if dato.get('ndmi') else 'N/D',
                f"{dato.get('savi', 0):.3f}" if dato.get('savi') else 'N/D',
                f"{dato.get('temperatura', 0):.1f}" if dato.get('temperatura') else 'N/D',
                f"{dato.get('precipitacion', 0):.1f}" if dato.get('precipitacion') else 'N/D'
            ])
        
        # Crear tabla
        tabla = Table(table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.colores['gris_oscuro']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(tabla)
        
        return elements
