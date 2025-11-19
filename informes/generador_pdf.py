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
        
        # Ejecutar análisis
        analisis_completo = self._ejecutar_analisis(datos_analisis, parcela)
        
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
    
    def _ejecutar_analisis(self, datos: List[Dict], parcela: Parcela) -> Dict:
        """Ejecuta todos los análisis"""
        # Inicializar analizadores
        analizador_ndvi = AnalizadorNDVI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_ndmi = AnalizadorNDMI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_savi = AnalizadorSAVI(tipo_cultivo=parcela.tipo_cultivo)
        detector_tendencias = DetectorTendencias()
        generador_recomendaciones = GeneradorRecomendaciones(tipo_cultivo=parcela.tipo_cultivo)
        
        # Ejecutar análisis
        analisis_ndvi = analizador_ndvi.analizar(datos)
        analisis_ndmi = analizador_ndmi.analizar(datos)
        analisis_savi = analizador_savi.analizar(datos) if any(d.get('savi') for d in datos) else None
        
        # Tendencias
        tendencias = detector_tendencias.analizar_temporal(datos, 'ndvi')
        
        # Recomendaciones
        recomendaciones = generador_recomendaciones.generar_recomendaciones(
            analisis_ndvi, analisis_ndmi, analisis_savi, tendencias
        )
        
        return {
            'ndvi': analisis_ndvi,
            'ndmi': analisis_ndmi,
            'savi': analisis_savi,
            'tendencias': tendencias,
            'recomendaciones': recomendaciones
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
        
        # Calcular promedios
        ndvi_prom = sum(d.get('ndvi', 0) for d in datos) / len(datos)
        ndmi_prom = sum(d.get('ndmi', 0) for d in datos) / len(datos)
        savi_prom = sum(d.get('savi', 0) for d in datos if d.get('savi')) / max(1, len([d for d in datos if d.get('savi')]))
        
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
        """Crea resumen ejecutivo del informe"""
        elements = []
        
        # Título
        titulo = Paragraph("📊 Resumen Ejecutivo", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Puntuaciones
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
