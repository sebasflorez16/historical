"""
Vistas para la aplicación de informes AgroTech Histórico
Incluye dashboard, gestión de parcelas, análisis y autenticación
"""

import os
import logging
import json
import secrets
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, Dict, List, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Parcela, IndiceMensual, Informe, ConfiguracionAPI
from .models_clientes import ClienteInvitacion, RegistroEconomico
# Importaciones de servicios
from .services.eosda_api import eosda_service
from .services.weather_service import OpenMeteoWeatherService
from .services.analisis_datos import analisis_service
# Importar generador de PDF
from .generador_pdf import GeneradorPDFProfesional

# Configurar logging
logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    Panel principal del sistema - Vista general de parcelas y datos
    Solo para superusuarios
    """
    # Verificar si es superusuario
    if not request.user.is_superuser:
        messages.warning(request, 'No tiene permisos para acceder al dashboard administrativo.')
        return redirect('informes:crear_parcela')
    try:
        # Obtener estadísticas generales
        total_parcelas = Parcela.objects.filter(activa=True).count()
        total_indices = IndiceMensual.objects.count()
        total_informes = Informe.objects.count()
        
        # Estadísticas económicas (solo para superusuarios)
        estadisticas_economicas = {}
        if request.user.is_superuser:
            try:
                from .models_clientes import ClienteInvitacion, RegistroEconomico
                
                # Estadísticas de invitaciones
                total_invitaciones = ClienteInvitacion.objects.count()
                invitaciones_pendientes = ClienteInvitacion.objects.filter(
                    estado='pendiente',
                    fecha_expiracion__gte=timezone.now()
                ).count()
                invitaciones_completadas = ClienteInvitacion.objects.filter(
                    estado='utilizada'
                ).count()
                
                # Estadísticas económicas
                registros_economicos = RegistroEconomico.objects.all()
                ingresos_totales = registros_economicos.aggregate(Sum('valor_final'))['valor_final__sum'] or 0
                servicios_pendientes = registros_economicos.filter(pagado=False).count()
                servicios_pagados = registros_economicos.filter(pagado=True).count()
                
                # Total de hectáreas registradas
                total_hectareas = Parcela.objects.filter(activa=True).aggregate(
                    Sum('area_hectareas')
                )['area_hectareas__sum'] or 0
                
                estadisticas_economicas = {
                    'total_invitaciones': total_invitaciones,
                    'invitaciones_pendientes': invitaciones_pendientes,
                    'invitaciones_completadas': invitaciones_completadas,
                    'ingresos_totales': ingresos_totales,
                    'servicios_pendientes': servicios_pendientes,
                    'servicios_pagados': servicios_pagados,
                    'total_hectareas': round(total_hectareas, 2)
                }
            except Exception as e:
                logger.error(f"Error cargando estadísticas económicas: {str(e)}")
                # Si hay error, usar valores por defecto
                estadisticas_economicas = {
                    'total_invitaciones': 0,
                    'invitaciones_pendientes': 0,
                    'invitaciones_completadas': 0,
                    'ingresos_totales': 0,
                    'servicios_pendientes': 0,
                    'servicios_pagados': 0,
                    'total_hectareas': 0
                }
        
        # Parcelas recientes
        parcelas_recientes = Parcela.objects.filter(activa=True).order_by('-fecha_registro')[:5]
        
        # Últimos informes generados
        informes_recientes = Informe.objects.order_by('-fecha_generacion')[:5]
        
        # Verificar conectividad de EOSDA - Verificación real
        from .services.eosda_api import eosda_service
        try:
            conectividad_raw = eosda_service.verificar_conectividad()
            if conectividad_raw.get('conexion_exitosa', False):
                conectividad_eosda = {
                    'status': 'online',
                    'message': f'API EOSDA operativa - {conectividad_raw.get("tiempo_respuesta", "N/A")}ms'
                }
            else:
                conectividad_eosda = {
                    'status': 'offline',
                    'message': f'EOSDA: {conectividad_raw.get("mensaje", "Error de conexión")}'
                }
        except Exception as e:
            logger.error(f"Error verificando EOSDA: {str(e)}")
            conectividad_eosda = {
                'status': 'offline',
                'message': f'Error: {str(e)[:50]}'
            }
        
        # Verificar estado del email
        from .services.email_service import email_service
        estado_email = email_service.validar_configuracion_email()
        
        contexto = {
            'total_parcelas': total_parcelas,
            'total_indices': total_indices,
            'total_informes': total_informes,
            'estadisticas_economicas': estadisticas_economicas,
            'parcelas_recientes': parcelas_recientes,
            'informes_recientes': informes_recientes,
            'conectividad_eosda': conectividad_eosda,
            'estado_email': estado_email,
        }
        
        return render(request, 'informes/dashboard.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error cargando dashboard: {str(e)}")
        return render(request, 'informes/dashboard.html', {'error': str(e)})


@login_required
def lista_parcelas(request):
    """
    Lista todas las parcelas con paginación y filtros
    Solo para superusuarios
    """
    # Verificar si es superusuario
    if not request.user.is_superuser:
        messages.warning(request, 'No tiene permisos para listar parcelas.')
        return redirect('informes:crear_parcela')
        
    try:
        # Obtener todas las parcelas activas
        parcelas_queryset = Parcela.objects.filter(activa=True).order_by('-fecha_registro')
        
        # Filtro de búsqueda
        busqueda = request.GET.get('busqueda', '')
        if busqueda:
            parcelas_queryset = parcelas_queryset.filter(
                Q(nombre__icontains=busqueda) | 
                Q(propietario__icontains=busqueda) |
                Q(tipo_cultivo__icontains=busqueda)
            )
        
        # Paginación
        paginator = Paginator(parcelas_queryset, 12)  # 12 parcelas por página
        page_number = request.GET.get('page')
        parcelas = paginator.get_page(page_number)
        
        # Estadísticas para la vista
        total_parcelas = Parcela.objects.filter(activa=True).count()
        total_hectareas = Parcela.objects.filter(activa=True).aggregate(
            Sum('area_hectareas')
        )['area_hectareas__sum'] or 0
        parcelas_activas = total_parcelas
        
        # Parcelas del mes actual
        from datetime import datetime, date
        inicio_mes = date.today().replace(day=1)
        parcelas_recientes = Parcela.objects.filter(
            activa=True, 
            fecha_registro__gte=inicio_mes
        ).count()
        
        contexto = {
            'parcelas': parcelas,
            'total_parcelas': total_parcelas,
            'total_hectareas': total_hectareas,
            'parcelas_activas': parcelas_activas,
            'parcelas_recientes': parcelas_recientes,
            'busqueda': busqueda,
            'is_paginated': parcelas.has_other_pages(),
            'page_obj': parcelas,
        }
        
        return render(request, 'informes/parcelas/lista.html', contexto)
        
    except Exception as e:
        logger.error(f"Error listando parcelas: {str(e)}")
        messages.error(request, f"Error cargando parcelas: {str(e)}")
        return render(request, 'informes/parcelas/lista.html', {
            'parcelas': [],
            'total_parcelas': 0,
            'total_hectareas': 0,
            'parcelas_activas': 0,
            'parcelas_recientes': 0,
        })
        
        contexto = {
            'parcelas': parcelas,
            'busqueda': busqueda,
        }
        
        return render(request, 'informes/parcelas/lista.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en lista_parcelas: {str(e)}")
        messages.error(request, f"Error cargando parcelas: {str(e)}")
        return render(request, 'informes/parcelas/lista.html', {'error': str(e)})


def detalle_parcela(request, parcela_id):
    """
    Muestra el detalle de una parcela específica con información completa
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener registros económicos asociados
        registros_economicos = RegistroEconomico.objects.filter(
            parcela=parcela
        ).order_by('-fecha_servicio')
        
        # Obtener índices mensuales recientes (último año)
        indices_recientes = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('-año', '-mes')[:12]
        
        # Calcular estadísticas básicas
        if indices_recientes:
            ndvi_promedio = sum(i.ndvi_promedio for i in indices_recientes if i.ndvi_promedio) / len([i for i in indices_recientes if i.ndvi_promedio])
            ultimo_indice = indices_recientes[0]
        else:
            ndvi_promedio = None
            ultimo_indice = None
        
        # Obtener informes de esta parcela
        informes = Informe.objects.filter(parcela=parcela).order_by('-fecha_generacion')[:5]
        
        # Calcular centro de la parcela para el mapa con manejo de errores
        centro_lat = None
        centro_lon = None
        
        try:
            if parcela.geometria:
                centro = parcela.geometria.centroid
                centro_lat = float(centro.y)
                centro_lon = float(centro.x)
                logger.info(f"Centro calculado para {parcela.nombre}: lat={centro_lat}, lon={centro_lon}")
            elif parcela.centroide:
                centro_lat = float(parcela.centroide.y)
                centro_lon = float(parcela.centroide.x)
                logger.info(f"Usando centroide precalculado para {parcela.nombre}: lat={centro_lat}, lon={centro_lon}")
            else:
                logger.warning(f"Parcela {parcela.nombre} no tiene geometría ni centroide válidos")
        except Exception as e:
            logger.error(f"Error calculando centro para parcela {parcela.nombre}: {str(e)}")
        
        # Fecha actual para el selector de rangos
        from datetime import date
        fecha_actual = date.today()
        
        # Calcular rango de datos disponibles en BD
        rango_datos = None
        if indices_recientes:
            indices_ordenados = sorted(indices_recientes, key=lambda x: (x.año, x.mes))
            fecha_mas_antigua = date(indices_ordenados[0].año, indices_ordenados[0].mes, 1)
            fecha_mas_reciente = date(indices_ordenados[-1].año, indices_ordenados[-1].mes, 1)
            meses_disponibles = len(indices_recientes)
            rango_datos = {
                'fecha_inicio': fecha_mas_antigua,
                'fecha_fin': fecha_mas_reciente,
                'meses': meses_disponibles
            }
        
        contexto = {
            'parcela': parcela,
            'registros_economicos': registros_economicos,
            'indices_recientes': indices_recientes,
            'ndvi_promedio': ndvi_promedio,
            'ultimo_indice': ultimo_indice,
            'informes': informes,
            'centro_lat': centro_lat,
            'centro_lon': centro_lon,
            'fecha_actual': fecha_actual.isoformat(),  # Formato YYYY-MM-DD para input date
            'rango_datos': rango_datos,  # Info sobre datos disponibles
        }
        
        return render(request, 'informes/parcelas/detalle.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en detalle_parcela: {str(e)}")
        messages.error(request, f"Error cargando parcela: {str(e)}")
        return redirect('informes:lista_parcelas')


@login_required
def crear_parcela(request):
    """
    Vista para crear una nueva parcela con soporte para:
    - Dibujo interactivo en mapa
    - Entrada manual de coordenadas GPS
    Accesible para usuarios autenticados y superusuarios
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            propietario = request.POST.get('propietario')
            tipo_cultivo = request.POST.get('tipo_cultivo', '')
            fecha_inicio_monitoreo = request.POST.get('fecha_inicio_monitoreo')
            notas = request.POST.get('notas', '')
            geometria_json = request.POST.get('geometria')
            
            # Validar datos requeridos
            if not all([nombre, propietario, fecha_inicio_monitoreo, geometria_json]):
                messages.error(request, 'Por favor complete todos los campos requeridos.')
                return render(request, 'informes/parcelas/crear.html')
            
            # Importar herramientas PostGIS
            from django.contrib.gis.geos import GEOSGeometry
            import json
            from datetime import datetime
            
            # Procesar geometría
            try:
                geometria_data = json.loads(geometria_json)
                
                # Asegurar que es una Feature con geometría Polygon
                if geometria_data.get('type') == 'Feature':
                    geometry = geometria_data['geometry']
                else:
                    geometry = geometria_data
                
                # Crear geometría PostGIS
                geometria_postgis = GEOSGeometry(json.dumps(geometry))
                
                # Validar que sea un polígono válido
                if not geometria_postgis.valid:
                    messages.error(request, 'La geometría de la parcela no es válida.')
                    return render(request, 'informes/parcelas/crear.html')
                
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error procesando geometría: {str(e)}")
                messages.error(request, 'Error en los datos de geometría de la parcela.')
                return render(request, 'informes/parcelas/crear.html')
            
            # Crear la parcela con PostGIS
            parcela = Parcela.objects.create(
                nombre=nombre,
                propietario=propietario,
                geometria=geometria_postgis,  # PostGIS calcula área automáticamente
                tipo_cultivo=tipo_cultivo,
                fecha_inicio_monitoreo=datetime.strptime(fecha_inicio_monitoreo, '%Y-%m-%d').date(),
                notas=notas,
                activa=True
            )
            
            logger.info(f"Parcela '{nombre}' creada exitosamente con área de {parcela.area_hectareas:.2f} ha")
            messages.success(request, f'Parcela "{nombre}" creada exitosamente con {parcela.area_hectareas:.2f} hectáreas.')
            
            return redirect('informes:detalle_parcela', parcela_id=parcela.id)
            
        except Exception as e:
            logger.error(f"Error creando parcela: {str(e)}")
            messages.error(request, f'Error creando parcela: {str(e)}')
    
    return render(request, 'informes/parcelas/crear.html')


def registro_cliente(request):
    """
    Vista simplificada para que los clientes registren sus parcelas
    Sin acceso a funciones administrativas
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario cliente
            nombre = request.POST.get('nombre')
            propietario = request.POST.get('propietario')
            tipo_cultivo = request.POST.get('tipo_cultivo', '')
            email_contacto = request.POST.get('email_contacto', '')
            geometria_json = request.POST.get('geometria')
            fecha_inicio_monitoreo = request.POST.get('fecha_inicio_monitoreo')
            
            # Validar datos requeridos
            if not all([nombre, propietario, geometria_json]):
                messages.error(request, 'Por favor complete todos los campos requeridos.')
                return render(request, 'informes/parcelas/registro_cliente.html')
            
            # Importar herramientas PostGIS
            from django.contrib.gis.geos import GEOSGeometry
            import json
            from datetime import datetime, date
            
            # Procesar geometría
            try:
                geometria_data = json.loads(geometria_json)
                
                # Asegurar que es una Feature con geometría Polygon
                if geometria_data.get('type') == 'Feature':
                    geometry = geometria_data['geometry']
                else:
                    geometry = geometria_data
                
                # Crear geometría PostGIS
                geometria_postgis = GEOSGeometry(json.dumps(geometry))
                
                # Validar que sea un polígono válido
                if not geometria_postgis.valid:
                    messages.error(request, 'La geometría de la parcela no es válida. Por favor revise las coordenadas.')
                    return render(request, 'informes/parcelas/registro_cliente.html')
                
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error procesando geometría del cliente: {str(e)}")
                messages.error(request, 'Error en los datos de geometría. Por favor intente nuevamente.')
                return render(request, 'informes/parcelas/registro_cliente.html')
            
            # Usar fecha de inicio por defecto si no se proporciona
            if fecha_inicio_monitoreo:
                fecha_inicio = datetime.strptime(fecha_inicio_monitoreo, '%Y-%m-%d').date()
            else:
                fecha_inicio = date.today()
            
            # Crear notas especiales para clientes
            notas_cliente = f"Parcela registrada por cliente.\nEmail: {email_contacto}\nEstado: Pendiente de procesamiento\nFecha registro: {date.today()}"
            
            # Crear la parcela para cliente
            parcela = Parcela.objects.create(
                nombre=nombre,
                propietario=propietario,
                geometria=geometria_postgis,
                tipo_cultivo=tipo_cultivo,
                fecha_inicio_monitoreo=fecha_inicio,
                notas=notas_cliente,
                activa=True
            )
            
            logger.info(f"Parcela cliente '{nombre}' registrada exitosamente. Área: {parcela.area_hectareas:.2f} ha")
            
            # Respuesta de éxito para cliente
            contexto = {
                'parcela': parcela,
                'area_hectareas': parcela.area_hectareas,
                'registro_exitoso': True
            }
            
            return render(request, 'informes/parcelas/registro_cliente.html', contexto)
            
        except Exception as e:
            logger.error(f"Error en registro de cliente: {str(e)}")
            messages.error(request, 'Error procesando su solicitud. Por favor intente nuevamente.')
    
    return render(request, 'informes/parcelas/registro_cliente.html')


def mapa_parcela(request, parcela_id):
    """
    Vista del mapa interactivo de una parcela específica
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        contexto = {
            'parcela': parcela,
            'geojson_data': parcela.poligono_geojson,
            'centro_mapa': parcela.centro_parcela,
        }
        
        return render(request, 'informes/parcelas/mapa.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en mapa_parcela: {str(e)}")
        messages.error(request, f"Error cargando mapa: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


@csrf_exempt
@require_http_methods(["POST"])
def procesar_datos_parcela(request, parcela_id):
    """
    API endpoint para procesar datos satelitales de una parcela
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener parámetros
        data = json.loads(request.body) if request.body else {}
        meses_atras = data.get('meses_atras', 12)
        
        # Calcular fechas
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=meses_atras * 30)
        
        # Procesar datos
        # resultado = analisis_service.procesar_datos_mensuales(
        #     parcela, fecha_inicio, fecha_fin
        # )
        resultado = {'success': True, 'message': 'Análisis temporalmente deshabilitado'}
        
        if 'error' in resultado:
            return JsonResponse({
                'success': False,
                'error': resultado['error']
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'Datos procesados exitosamente para {parcela.nombre}',
            'meses_procesados': resultado.get('total_meses', 0),
            'simulado': resultado.get('simulado', False)
        })
        
    except Exception as e:
        logger.error(f"Error procesando datos de parcela {parcela_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def analisis_tendencias(request, parcela_id):
    """
    Vista para mostrar análisis de tendencias de una parcela
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener período de análisis
        meses_analisis = int(request.GET.get('meses', 12))
        
        # Calcular tendencias
        # tendencias = analisis_service.calcular_tendencias_parcela(
        #     parcela, meses_analisis
        # )
        tendencias = {'datos_disponibles': False, 'mensaje': 'Análisis temporalmente deshabilitado'}
        
        if 'error' in tendencias:
            messages.warning(request, tendencias['error'])
            tendencias = {'datos_disponibles': False}
        
        contexto = {
            'parcela': parcela,
            'tendencias': tendencias,
            'meses_analisis': meses_analisis,
        }
        
        return render(request, 'informes/analisis/tendencias.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en análisis de tendencias: {str(e)}")
        messages.error(request, f"Error en análisis: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


def lista_informes(request):
    """
    Lista todos los informes generados
    """
    try:
        informes_queryset = Informe.objects.all().order_by('-fecha_generacion')
        
        # Filtro por parcela
        parcela_id = request.GET.get('parcela')
        if parcela_id:
            informes_queryset = informes_queryset.filter(parcela_id=parcela_id)
        
        # Paginación
        paginator = Paginator(informes_queryset, 10)
        page_number = request.GET.get('page')
        informes = paginator.get_page(page_number)
        
        # Lista de parcelas para filtro
        parcelas = Parcela.objects.filter(activa=True).order_by('nombre')
        
        contexto = {
            'informes': informes,
            'parcelas': parcelas,
            'parcela_filtro': parcela_id,
        }
        
        return render(request, 'informes/informes/lista.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en lista_informes: {str(e)}")
        messages.error(request, f"Error cargando informes: {str(e)}")
        return render(request, 'informes/informes/lista.html', {'error': str(e)})


def detalle_informe(request, informe_id):
    """
    Muestra el detalle de un informe específico
    """
    try:
        informe = get_object_or_404(Informe, id=informe_id)
        
        contexto = {
            'informe': informe,
        }
        
        return render(request, 'informes/informes/detalle.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en detalle_informe: {str(e)}")
        messages.error(request, f"Error cargando informe: {str(e)}")
        return redirect('informes:lista_informes')


def estado_sistema(request):
    """
    Vista para monitorear el estado del sistema
    """
    try:
        # Verificar conectividad EOSDA
        # estado_eosda = eosda_service.verificar_conectividad()
        estado_eosda = {'status': 'offline', 'message': 'Servicio temporalmente deshabilitado'}
        
        # Verificar estado del email
        from .services.email_service import email_service
        estado_email = email_service.validar_configuracion_email()
        
        # Estadísticas de datos
        estadisticas = {
            'total_parcelas': Parcela.objects.filter(activa=True).count(),
            'total_indices': IndiceMensual.objects.count(),
            'total_informes': Informe.objects.count(),
            'indices_ultimo_mes': IndiceMensual.objects.filter(
                fecha_consulta_api__gte=datetime.now() - timedelta(days=30)
            ).count(),
            'informes_ultimo_mes': Informe.objects.filter(
                fecha_generacion__gte=datetime.now() - timedelta(days=30)
            ).count(),
        }
        
        # Estado general del sistema
        estado_general = 'operativo' if estado_email.get('valido', False) else 'degradado'
        
        contexto = {
            'estado_eosda': estado_eosda,
            'estado_email': estado_email,
            'estadisticas': estadisticas,
            'estado_general': estado_general,
        }
        
        return render(request, 'informes/sistema/estado.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en estado_sistema: {str(e)}")
        return render(request, 'informes/sistema/estado.html', {'error': str(e)})


@login_required
def probar_email(request):
    """
    Vista para probar la configuración de email
    Solo para superusuarios
    """
    if not request.user.is_superuser:
        messages.warning(request, 'No tiene permisos para probar la configuración de email.')
        return redirect('informes:estado_sistema')
        
    if request.method == 'POST':
        try:
            from .services.email_service import email_service
            
            email_destino = request.POST.get('email_destino', 'agrotechdigitalcolombia@gmail.com')
            resultado = email_service.probar_configuracion_email(email_destino)
            
            if resultado['exito']:
                messages.success(request, resultado['mensaje'])
                logger.info(f"Prueba de email exitosa a {email_destino}")
            else:
                messages.error(request, f"Error en prueba de email: {resultado['error']}")
                logger.error(f"Error en prueba de email: {resultado['error']}")
                
        except Exception as e:
            logger.error(f"Error en probar_email: {str(e)}")
            messages.error(request, f"Error ejecutando prueba: {str(e)}")
    
    return redirect('informes:estado_sistema')


@csrf_exempt
@require_http_methods(["GET"])
def api_datos_parcela(request, parcela_id):
    """
    API para obtener datos de una parcela en formato JSON
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener parámetros
        limite = int(request.GET.get('limite', 12))
        
        # Obtener índices recientes
        indices = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('-año', '-mes')[:limite]
        
        # Convertir a formato JSON
        datos = []
        for indice in indices:
            datos.append({
                'fecha': f"{indice.año}-{indice.mes:02d}-01",
                'periodo': indice.periodo_texto,
                'ndvi': indice.ndvi_promedio,
                'ndmi': indice.ndmi_promedio,
                'savi': indice.savi_promedio,
                'temperatura': indice.temperatura_promedio,
                'precipitacion': indice.precipitacion_total,
                'calidad_datos': indice.calidad_datos,
            })
        
        return JsonResponse({
            'success': True,
            'parcela': {
                'id': parcela.id,
                'nombre': parcela.nombre,
                'propietario': parcela.propietario,
            },
            'datos': datos,
            'total_registros': len(datos)
        })
        
    except Exception as e:
        logger.error(f"Error en api_datos_parcela: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# =============================================================================
# VISTAS DE AUTENTICACIÓN
# =============================================================================

def user_login(request):
    """
    Vista de login con redirección diferenciada:
    - Superusuarios -> Dashboard completo
    - Otros usuarios -> Registro de parcelas solamente
    """
    # Si ya está autenticado, redirigir según el tipo de usuario
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('informes:dashboard')
        else:
            return redirect('informes:crear_parcela')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    logger.info(f"Usuario '{username}' inició sesión exitosamente")
                    
                    # Redirección diferenciada
                    if user.is_superuser:
                        messages.success(request, f'¡Bienvenido {user.first_name or username}! Acceso administrativo completo.')
                        return redirect('informes:dashboard')
                    else:
                        messages.success(request, f'¡Bienvenido {user.first_name or username}! Acceso a registro de parcelas.')
                        return redirect('informes:crear_parcela')
                else:
                    messages.error(request, 'Su cuenta está desactivada.')
            else:
                logger.warning(f"Intento de login fallido para usuario: {username}")
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor ingrese usuario y contraseña.')
    
    return render(request, 'registration/login.html')


@login_required
def user_logout(request):
    """
    Vista de logout
    """
    username = request.user.username
    logout(request)
    messages.info(request, f'Sesión cerrada correctamente. ¡Hasta pronto!')
    logger.info(f"Usuario '{username}' cerró sesión")
    return redirect('informes:login')


def is_superuser(user):
    """
    Helper function para verificar si el usuario es superusuario
    """
    return user.is_superuser


@user_passes_test(is_superuser, login_url='informes:crear_parcela')
@login_required
def admin_dashboard(request):
    """
    Dashboard completo solo para superusuarios
    Redirige a usuarios normales al registro de parcelas
    """
    return dashboard(request)


# Actualizar la vista dashboard existente para verificar permisos
@login_required
def dashboard_admin(request):
    """
    Dashboard principal del sistema
    Solo accesible para superusuarios
    """
    # Verificar si es superusuario
    if not request.user.is_superuser:
        messages.warning(request, 'No tiene permisos para acceder al dashboard administrativo.')
        return redirect('informes:crear_parcela')
    
    # Redirigir al dashboard principal
    return dashboard(request)


# =============================================================================
# VISTAS DE GESTIÓN DE INVITACIONES
# =============================================================================

@login_required
@user_passes_test(is_superuser, login_url='informes:crear_parcela')
def gestionar_invitaciones(request):
    """
    Vista para gestionar invitaciones de clientes
    Solo para superusuarios
    """
    try:
        # Obtener invitaciones con filtros
        estado_filtro = request.GET.get('estado', 'todas')
        busqueda = request.GET.get('busqueda', '')
        
        invitaciones_queryset = ClienteInvitacion.objects.all()
        
        if estado_filtro != 'todas':
            invitaciones_queryset = invitaciones_queryset.filter(estado=estado_filtro)
        
        if busqueda:
            invitaciones_queryset = invitaciones_queryset.filter(
                Q(nombre_cliente__icontains=busqueda) |
                Q(email_cliente__icontains=busqueda) |
                Q(telefono_cliente__icontains=busqueda)
            )
        
        # Paginación
        paginator = Paginator(invitaciones_queryset, 10)
        page_number = request.GET.get('page')
        invitaciones = paginator.get_page(page_number)
        
        # Estadísticas
        estadisticas = {
            'total_invitaciones': ClienteInvitacion.objects.count(),
            'pendientes': ClienteInvitacion.objects.filter(estado='pendiente').count(),
            'utilizadas': ClienteInvitacion.objects.filter(estado='utilizada').count(),
            'expiradas': ClienteInvitacion.objects.filter(estado='expirada').count(),
            'ingresos_totales': RegistroEconomico.objects.aggregate(
                total=Sum('valor_final')
            )['total'] or 0,
            'ingresos_pendientes': RegistroEconomico.objects.filter(
                pagado=False
            ).aggregate(total=Sum('valor_final'))['total'] or 0,
        }
        
        contexto = {
            'invitaciones': invitaciones,
            'estadisticas': estadisticas,
            'estado_filtro': estado_filtro,
            'busqueda': busqueda,
        }
        
        return render(request, 'informes/invitaciones/gestionar.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en gestionar_invitaciones: {str(e)}")
        messages.error(request, f"Error cargando invitaciones: {str(e)}")
        return redirect('informes:dashboard')


@login_required
@login_required
@user_passes_test(is_superuser, login_url='informes:crear_parcela')
def crear_invitacion(request):
    """
    Vista para crear nueva invitación de cliente
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_cliente = request.POST.get('nombre_cliente')
            email_cliente = request.POST.get('email_cliente', '')
            descripcion_servicio = request.POST.get('descripcion_servicio', 'Análisis satelital agrícola')
            precio_servicio = request.POST.get('precio_servicio', '0.00')
            dias_vigencia = int(request.POST.get('dias_vigencia', '15'))
            
            # Validaciones
            if not nombre_cliente:
                messages.error(request, 'El nombre del cliente es requerido.')
                return render(request, 'informes/invitaciones/crear.html')
            
            if not email_cliente:
                messages.error(request, 'El email del cliente es requerido.')
                return render(request, 'informes/invitaciones/crear.html')
            
            # Generar token único
            import secrets
            token = secrets.token_urlsafe(24)
            
            # Calcular fecha de expiración
            from datetime import timedelta
            fecha_expiracion = timezone.now() + timedelta(days=dias_vigencia)
            
            # Crear invitación
            invitacion = ClienteInvitacion.objects.create(
                token=token,
                nombre_cliente=nombre_cliente,
                email_cliente=email_cliente,
                telefono_cliente='',  # No se solicita en el formulario actual
                costo_servicio=Decimal(precio_servicio),
                descripcion_servicio=descripcion_servicio,
                fecha_expiracion=fecha_expiracion,
                creado_por=request.user
            )
            
            logger.info(f"Invitación creada para {nombre_cliente} por {request.user.username}")
            messages.success(request, f'Invitación creada exitosamente para {nombre_cliente}')
            
            return redirect('informes:detalle_invitacion', invitacion_id=invitacion.id)
            
        except Exception as e:
            logger.error(f"Error creando invitación: {str(e)}")
            messages.error(request, f'Error creando invitación: {str(e)}')
    
    return render(request, 'informes/invitaciones/crear.html')


@login_required
@user_passes_test(is_superuser, login_url='informes:crear_parcela')
def detalle_invitacion(request, invitacion_id):
    """
    Vista de detalle de una invitación específica
    """
    try:
        invitacion = get_object_or_404(ClienteInvitacion, id=invitacion_id)
        
        # Manejar envío de email
        if request.method == 'POST' and 'enviar_email' in request.POST:
            from .services.email_service import email_service
            
            url_completa = request.build_absolute_uri(invitacion.url_invitacion)
            resultado = email_service.enviar_invitacion(invitacion, url_completa)
            
            if resultado['exito']:
                messages.success(request, resultado['mensaje'])
                logger.info(f"Email enviado exitosamente para invitación {invitacion.id}")
            else:
                # Usar error level para mostrar modal crítico
                messages.error(request, f"{resultado['error']}")
                logger.error(f"Error enviando email para invitación {invitacion.id}: {resultado['error']}")
        
        # Obtener registros económicos asociados
        registros_economicos = RegistroEconomico.objects.filter(
            invitacion=invitacion
        ).order_by('-fecha_servicio')
        
        # Generar mensaje de WhatsApp
        from .services.email_service import email_service
        url_completa = request.build_absolute_uri(invitacion.url_invitacion)
        mensaje_whatsapp = email_service.generar_mensaje_whatsapp(invitacion, url_completa)
        
        contexto = {
            'invitacion': invitacion,
            'registros_economicos': registros_economicos,
            'url_completa': url_completa,
            'mensaje_whatsapp': mensaje_whatsapp,
        }
        
        return render(request, 'informes/invitaciones/detalle.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en detalle_invitacion: {str(e)}")
        messages.error(request, f"Error cargando invitación: {str(e)}")
        return redirect('informes:gestionar_invitaciones')


def registro_invitacion(request, token):
    """
    Vista pública para registro usando token de invitación
    """
    try:
        # Buscar invitación por token
        invitacion = get_object_or_404(ClienteInvitacion, token=token)
        
        # Verificar estado de la invitación
        if invitacion.estado != 'pendiente':
            messages.error(request, 'Esta invitación ya ha sido utilizada o ha expirado.')
            return render(request, 'informes/invitaciones/error.html', {
                'error': 'Invitación no válida',
                'invitacion': invitacion
            })
        
        # Verificar expiración
        if invitacion.esta_expirada:
            invitacion.estado = 'expirada'
            invitacion.save()
            messages.error(request, 'Esta invitación ha expirado.')
            return render(request, 'informes/invitaciones/error.html', {
                'error': 'Invitación expirada',
                'invitacion': invitacion
            })
        
        # Procesar registro de parcela
        if request.method == 'POST':
            try:
                # Obtener datos del formulario
                nombre = request.POST.get('nombre')
                tipo_cultivo = request.POST.get('tipo_cultivo', '')
                geometria_json = request.POST.get('geometria')
                notas = request.POST.get('notas', '')
                
                # Validar datos requeridos
                if not all([nombre, geometria_json]):
                    messages.error(request, 'Por favor complete todos los campos requeridos.')
                    return render(request, 'informes/invitaciones/registro.html', {
                        'invitacion': invitacion
                    })
                
                # Procesar geometría con PostGIS
                from django.contrib.gis.geos import GEOSGeometry
                import json
                from datetime import date
                
                geometria_data = json.loads(geometria_json)
                
                if geometria_data.get('type') == 'Feature':
                    geometry = geometria_data['geometry']
                else:
                    geometry = geometria_data
                
                geometria_postgis = GEOSGeometry(json.dumps(geometry))
                
                if not geometria_postgis.valid:
                    messages.error(request, 'La geometría de la parcela no es válida.')
                    return render(request, 'informes/invitaciones/registro.html', {
                        'invitacion': invitacion
                    })
                
                # Crear parcela
                parcela = Parcela.objects.create(
                    nombre=nombre,
                    propietario=invitacion.nombre_cliente,
                    geometria=geometria_postgis,
                    tipo_cultivo=tipo_cultivo,
                    fecha_inicio_monitoreo=date.today(),
                    notas=f"Registrada por invitación.\nCliente: {invitacion.nombre_cliente}\nEmail: {invitacion.email_cliente}\n{notas}",
                    activa=True
                )
                
                # Marcar invitación como utilizada
                invitacion.marcar_como_utilizada(parcela)
                
                # Crear registro económico
                if invitacion.costo_servicio > 0:
                    RegistroEconomico.objects.create(
                        invitacion=invitacion,
                        parcela=parcela,
                        tipo_servicio='analisis_basico',
                        descripcion=f'Análisis satelital para parcela {parcela.nombre}',
                        valor_servicio=invitacion.costo_servicio,
                        valor_final=invitacion.costo_servicio
                    )
                
                logger.info(f"Parcela registrada por invitación: {invitacion.token} - {parcela.nombre}")
                
                return render(request, 'informes/invitaciones/exito.html', {
                    'invitacion': invitacion,
                    'parcela': parcela
                })
                
            except Exception as e:
                logger.error(f"Error procesando registro por invitación: {str(e)}")
                messages.error(request, 'Error procesando su solicitud. Por favor intente nuevamente.')
        
        # Mostrar formulario de registro
        return render(request, 'informes/invitaciones/registro.html', {
            'invitacion': invitacion
        })
        
    except Exception as e:
        logger.error(f"Error en registro_invitacion: {str(e)}")
        messages.error(request, 'Error procesando invitación.')
        return render(request, 'informes/invitaciones/error.html', {
            'error': 'Error del sistema'
        })


@login_required
def verificar_eosda(request):
    """
    Vista para verificar la conectividad con la API de EOSDA
    """
    try:
        logger.info("Iniciando verificación de conexión con EOSDA")
        
        # Verificar configuración básica
        resultado_conexion = eosda_service.verificar_conectividad()
        
        # Información de configuración
        configuracion = {
            'api_key_configurado': bool(eosda_service.api_key and eosda_service.api_key != ''),
            'api_key_valido': len(eosda_service.api_key) > 10 if eosda_service.api_key else False,
            'url_base': eosda_service.base_url,
            'api_key_preview': f"{eosda_service.api_key[:10]}..." if eosda_service.api_key else "No configurado"
        }
        
        # Intentar una consulta real si hay una parcela disponible
        datos_prueba = None
        parcela_prueba = None
        try:
            parcela_prueba = Parcela.objects.filter(activa=True).first()
            if parcela_prueba and resultado_conexion['conexion_exitosa']:
                logger.info(f"Probando obtener datos para parcela: {parcela_prueba.nombre}")
                from datetime import date, timedelta
                
                fecha_fin = date.today()
                fecha_inicio = fecha_fin - timedelta(days=90)  # Últimos 3 meses
                
                # Intentar obtener datos reales
                datos_prueba = eosda_service.obtener_datos_parcela(
                    parcela_prueba, 
                    fecha_inicio, 
                    fecha_fin
                )
                
                if datos_prueba:
                    ndvi_count = len(datos_prueba.get('ndvi', []))
                    ndmi_count = len(datos_prueba.get('ndmi', []))
                    savi_count = len(datos_prueba.get('savi', []))
                    logger.info(f"Datos obtenidos - NDVI: {ndvi_count}, NDMI: {ndmi_count}, SAVI: {savi_count}")
                else:
                    logger.warning("No se obtuvieron datos de prueba")
                    
        except Exception as e:
            logger.error(f"Error obteniendo datos de prueba: {str(e)}")
            datos_prueba = None
        
        contexto = {
            'resultado_conexion': resultado_conexion,
            'configuracion': configuracion,
            'datos_prueba': datos_prueba,
            'parcela_prueba': parcela_prueba,
            'timestamp': timezone.now()
        }
        
        return render(request, 'informes/sistema/verificar_eosda.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en verificar_eosda: {str(e)}")
        messages.error(request, f"Error verificando EOSDA: {str(e)}")
        return redirect('informes:estado_sistema')


@login_required
def obtener_datos_historicos(request, parcela_id):
    """
    Vista para obtener datos históricos de una parcela específica desde EOSDA.
    Soporta rangos predeterminados (6m, 12m, 24m) y personalizado.
    Requiere obligatoriamente parámetros de fecha.
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener parámetros de fecha desde URL (enviados por el selector de rangos)
        from datetime import date, timedelta
        fecha_inicio_param = request.GET.get('fecha_inicio')
        fecha_fin_param = request.GET.get('fecha_fin')
        
        # Validar que se proporcionaron ambas fechas
        if not fecha_inicio_param or not fecha_fin_param:
            logger.warning("⚠️ Intento de obtener datos sin seleccionar rango de fechas")
            messages.error(request, '⚠️ Debes seleccionar un período de análisis antes de obtener datos satelitales.')
            return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
        # Parsear y validar formato de fechas
        try:
            fecha_inicio = date.fromisoformat(fecha_inicio_param)
            fecha_fin = date.fromisoformat(fecha_fin_param)
            logger.info(f"📅 Usando rango seleccionado: {fecha_inicio} a {fecha_fin}")
        except ValueError:
            logger.error(f"❌ Formato de fecha inválido: {fecha_inicio_param} - {fecha_fin_param}")
            messages.error(request, '❌ Formato de fecha inválido. Usa el selector de período de análisis.')
            return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
        # Validar que fecha_inicio es anterior a fecha_fin
        if fecha_inicio >= fecha_fin:
            logger.error(f"❌ Rango inválido: inicio ({fecha_inicio}) debe ser anterior a fin ({fecha_fin})")
            messages.error(request, '❌ La fecha de inicio debe ser anterior a la fecha de fin.')
            return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
        logger.info(f"Obteniendo datos históricos para {parcela.nombre} desde {fecha_inicio} hasta {fecha_fin}")
        
        # Verificar que la parcela esté sincronizada con EOSDA
        if not parcela.eosda_sincronizada or not parcela.eosda_field_id:
            logger.warning(f"Parcela {parcela.nombre} no sincronizada, sincronizando primero...")
            resultado_sync = eosda_service.sincronizar_parcela_con_eosda(parcela)
            if not resultado_sync['exito']:
                messages.error(request, f'Error: La parcela debe estar sincronizada con EOSDA primero. {resultado_sync.get("error", "")}')
                return redirect('informes:detalle_parcela', parcela_id=parcela.id)
            # Recargar parcela después de sincronizar
            parcela.refresh_from_db()
        
        # Obtener datos desde EOSDA usando método optimizado (1 request en lugar de 3)
        datos_satelitales = eosda_service.obtener_datos_optimizado(
            parcela=parcela,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            indices=['NDVI', 'NDMI', 'SAVI'],  # ✅ MAYÚSCULAS según documentación EOSDA
            usuario=request.user,
            max_nubosidad=50
        )
        
        # Debug: Log para ver estructura de datos
        logger.info(f"Estructura de datos recibida: {list(datos_satelitales.keys())}")
        for clave, valor in datos_satelitales.items():
            if isinstance(valor, list):
                logger.info(f"  {clave}: {len(valor)} elementos")
                if valor:
                    logger.info(f"    Ejemplo: {valor[0]}")
        
        # Procesar y guardar los datos en la base de datos
        indices_creados = 0
        datos_procesados = 0
        
        # Agrupar datos por año-mes desde la estructura real de EOSDA
        from collections import defaultdict
        datos_por_mes = defaultdict(lambda: {
            'ndvi_valores': [], 'ndvi_max': [], 'ndvi_min': [],
            'ndmi_valores': [], 'ndmi_max': [], 'ndmi_min': [],
            'savi_valores': [], 'savi_max': [], 'savi_min': [],
            'nubosidad': [],
            'escenas': []  # Guardar todas las escenas para encontrar la mejor
        })
        
        # Procesar cada escena satelital
        for escena in datos_satelitales.get('resultados', []):
            try:
                fecha_str = escena.get('date')
                if not fecha_str:
                    continue
                
                fecha = datetime.fromisoformat(fecha_str).date()
                clave_mes = (fecha.year, fecha.month)
                
                # Extraer índices de cada escena
                indexes = escena.get('indexes', {})
                nubosidad = escena.get('cloud', 0)
                view_id = escena.get('view_id')  # ✅ view_id de la escena (campo correcto según API)
                
                # NDVI
                if 'NDVI' in indexes:
                    datos_por_mes[clave_mes]['ndvi_valores'].append(indexes['NDVI'].get('average', 0))
                    datos_por_mes[clave_mes]['ndvi_max'].append(indexes['NDVI'].get('max', 0))
                    datos_por_mes[clave_mes]['ndvi_min'].append(indexes['NDVI'].get('min', 0))
                
                # NDMI
                if 'NDMI' in indexes:
                    datos_por_mes[clave_mes]['ndmi_valores'].append(indexes['NDMI'].get('average', 0))
                    datos_por_mes[clave_mes]['ndmi_max'].append(indexes['NDMI'].get('max', 0))
                    datos_por_mes[clave_mes]['ndmi_min'].append(indexes['NDMI'].get('min', 0))
                
                # SAVI
                if 'SAVI' in indexes:
                    datos_por_mes[clave_mes]['savi_valores'].append(indexes['SAVI'].get('average', 0))
                    datos_por_mes[clave_mes]['savi_max'].append(indexes['SAVI'].get('max', 0))
                    datos_por_mes[clave_mes]['savi_min'].append(indexes['SAVI'].get('min', 0))
                
                datos_por_mes[clave_mes]['nubosidad'].append(nubosidad)
                
                # ✅ Guardar info completa de la escena para encontrar la mejor
                datos_por_mes[clave_mes]['escenas'].append({
                    'view_id': view_id,
                    'fecha': fecha,
                    'nubosidad': nubosidad
                })
                
            except Exception as e:
                logger.error(f"Error procesando escena: {str(e)}")
                continue
        
        # Guardar datos agrupados por mes
        for (year, month), datos in datos_por_mes.items():
            try:
                # Calcular promedios
                ndvi_prom = sum(datos['ndvi_valores']) / len(datos['ndvi_valores']) if datos['ndvi_valores'] else None
                ndvi_max = max(datos['ndvi_max']) if datos['ndvi_max'] else None
                ndvi_min = min(datos['ndvi_min']) if datos['ndvi_min'] else None
                
                ndmi_prom = sum(datos['ndmi_valores']) / len(datos['ndmi_valores']) if datos['ndmi_valores'] else None
                ndmi_max = max(datos['ndmi_max']) if datos['ndmi_max'] else None
                ndmi_min = min(datos['ndmi_min']) if datos['ndmi_min'] else None
                
                savi_prom = sum(datos['savi_valores']) / len(datos['savi_valores']) if datos['savi_valores'] else None
                savi_max = max(datos['savi_max']) if datos['savi_max'] else None
                savi_min = min(datos['savi_min']) if datos['savi_min'] else None
                
                nub_prom = sum(datos['nubosidad']) / len(datos['nubosidad']) if datos['nubosidad'] else 0
                
                # ✅ Encontrar la escena con MENOR nubosidad del mes para imágenes
                mejor_escena = None
                if datos['escenas']:
                    mejor_escena = min(datos['escenas'], key=lambda x: x['nubosidad'])
                    logger.info(f"   🎯 Mejor escena para {month:02d}/{year}: "
                               f"view_id={mejor_escena['view_id']}, "
                               f"fecha={mejor_escena['fecha']}, "
                               f"nubosidad={mejor_escena['nubosidad']:.1f}%")
                
                # Crear o actualizar registro mensual
                defaults = {
                    'ndvi_promedio': ndvi_prom,
                    'ndvi_maximo': ndvi_max,
                    'ndvi_minimo': ndvi_min,
                    'ndmi_promedio': ndmi_prom,
                    'ndmi_maximo': ndmi_max,
                    'ndmi_minimo': ndmi_min,
                    'savi_promedio': savi_prom,
                    'savi_maximo': savi_max,
                    'savi_minimo': savi_min,
                    'nubosidad_promedio': nub_prom,
                    'fuente_datos': 'EOSDA',
                    'calidad_datos': 'buena' if nub_prom < 30 else ('regular' if nub_prom < 50 else 'pobre')
                }
                
                # ✅ Agregar metadatos de la mejor escena para descarga de imágenes
                if mejor_escena:
                    defaults['view_id_imagen'] = mejor_escena['view_id']
                    defaults['fecha_imagen'] = mejor_escena['fecha']
                    defaults['nubosidad_imagen'] = mejor_escena['nubosidad']
                
                indice, created = IndiceMensual.objects.update_or_create(
                    parcela=parcela,
                    año=year,
                    mes=month,
                    defaults=defaults
                )
                
                if created:
                    indices_creados += 1
                datos_procesados += 1
                
                # Log con formato correcto
                ndvi_str = f"{ndvi_prom:.3f}" if ndvi_prom else "N/A"
                ndmi_str = f"{ndmi_prom:.3f}" if ndmi_prom else "N/A"
                savi_str = f"{savi_prom:.3f}" if savi_prom else "N/A"
                logger.info(f"✅ Guardado {month:02d}/{year}: NDVI={ndvi_str}, "
                           f"NDMI={ndmi_str}, SAVI={savi_str}, "
                           f"Nubosidad={nub_prom:.1f}%")
                
            except Exception as e:
                logger.error(f"Error guardando datos de {month}/{year}: {str(e)}")
        
        # 🌦️ OBTENER DATOS CLIMÁTICOS CON OPEN-METEO
        # EOSDA Weather API deshabilitado (sin cobertura en Colombia)
        # Usamos Open-Meteo como alternativa gratuita con cobertura global
        logger.info("🌦️ Obteniendo datos climáticos con Open-Meteo...")
        meses_clima_actualizados = 0
        try:
            # Calcular centroide de la parcela para las coordenadas
            centroide = parcela.geometria.centroid
            latitud = centroide.y
            longitud = centroide.x
            
            # Obtener datos diarios de Open-Meteo
            datos_diarios = OpenMeteoWeatherService.obtener_datos_historicos(
                latitud=latitud,
                longitud=longitud,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            if datos_diarios:
                # Agrupar por mes
                datos_clima_por_mes = OpenMeteoWeatherService.agrupar_por_mes(datos_diarios)
                
                # Actualizar O CREAR registros mensuales con datos climáticos
                for (year, month), datos in datos_clima_por_mes.items():
                    try:
                        # Verificar si ya existe el registro (creado por datos satelitales)
                        registro_existente = IndiceMensual.objects.filter(
                            parcela=parcela,
                            año=year,
                            mes=month
                        ).first()
                        
                        if registro_existente:
                            # ACTUALIZAR solo datos climáticos, mantener fuente_datos = 'EOSDA'
                            registro_existente.temperatura_promedio = datos.get('temperatura_promedio')
                            registro_existente.temperatura_maxima = datos.get('temperatura_maxima')
                            registro_existente.temperatura_minima = datos.get('temperatura_minima')
                            registro_existente.precipitacion_total = datos.get('precipitacion_total')
                            registro_existente.save(update_fields=[
                                'temperatura_promedio', 'temperatura_maxima', 
                                'temperatura_minima', 'precipitacion_total'
                            ])
                            accion = "actualizado"
                        else:
                            # CREAR nuevo registro solo con datos climáticos (sin índices satelitales)
                            IndiceMensual.objects.create(
                                parcela=parcela,
                                año=year,
                                mes=month,
                                temperatura_promedio=datos.get('temperatura_promedio'),
                                temperatura_maxima=datos.get('temperatura_maxima'),
                                temperatura_minima=datos.get('temperatura_minima'),
                                precipitacion_total=datos.get('precipitacion_total'),
                                fuente_datos='Solo Clima',  # Datos climáticos reales sin imágenes satelitales
                                calidad_datos='buena'
                            )
                            accion = "creado"
                        
                        meses_clima_actualizados += 1
                        temp = datos.get('temperatura_promedio')
                        precip = datos.get('precipitacion_total')
                        temp_str = f"{temp:.1f}" if temp else "N/A"
                        precip_str = f"{precip:.1f}" if precip else "N/A"
                        logger.info(f"   🌡️ Clima {accion} {month:02d}/{year}: "
                                   f"Temp={temp_str}°C, Precip={precip_str}mm")
                    except Exception as e:
                        logger.error(f"Error actualizando datos climáticos de {month}/{year}: {str(e)}")
                
                logger.info(f"✅ Open-Meteo: {meses_clima_actualizados} meses con datos climáticos")
            else:
                logger.warning("⚠️ Open-Meteo no retornó datos climáticos")
                
        except Exception as e:
            logger.error(f"Error obteniendo datos climáticos de Open-Meteo: {str(e)}")
        
        logger.info(f"Datos históricos procesados para {parcela.nombre}: {indices_creados} nuevos índices, {datos_procesados} meses satelitales, {meses_clima_actualizados} meses climáticos")
        
        # Calcular meses esperados vs obtenidos
        meses_esperados = ((fecha_fin.year - fecha_inicio.year) * 12 + fecha_fin.month - fecha_inicio.month) + 1
        meses_faltantes = meses_esperados - datos_procesados
        meses_solo_clima = meses_clima_actualizados - datos_procesados  # Meses con clima pero sin satélite
        
        # Mensaje informativo según disponibilidad de datos
        if datos_satelitales.get('simulado'):
            messages.info(request, 
                f'Se obtuvieron datos para {parcela.nombre}. '
                f'Procesados: {datos_procesados} registros, Nuevos: {indices_creados}. '
                'Nota: Algunos datos pueden ser simulados si EOSDA no tiene cobertura completa.'
            )
        else:
            # Construir mensaje detallado y claro
            mensaje_partes = []
            
            # Datos satelitales completos
            if datos_procesados > 0:
                msg_satelital = f'✅ {datos_procesados} mes(es) con datos satelitales completos (NDVI, NDMI, SAVI + clima)'
                if indices_creados > 0:
                    msg_satelital += f' - {indices_creados} nuevo(s)'
                mensaje_partes.append(msg_satelital)
            
            # Meses solo con clima (sin imágenes satelitales)
            if meses_solo_clima > 0:
                mensaje_partes.append(
                    f'🌦️ {meses_solo_clima} mes(es) solo con datos climáticos reales (temperatura, precipitación). '
                    f'Sin imágenes satelitales disponibles (nubosidad alta o satélite no pasó por la zona).'
                )
            
            # Meses completamente sin datos
            if meses_faltantes > 0 and meses_solo_clima < meses_faltantes:
                meses_sin_nada = meses_faltantes - meses_solo_clima
                if meses_sin_nada > 0:
                    mensaje_partes.append(f'⚠️ {meses_sin_nada} mes(es) sin ningún dato disponible.')
            
            mensaje_base = ' | '.join(mensaje_partes) if mensaje_partes else '✅ Datos actualizados.'
            messages.success(request, mensaje_base)
        
        return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {str(e)}")
        messages.error(request, f"Error obteniendo datos históricos: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


@login_required 
def ver_datos_guardados(request, parcela_id):
    """
    Vista para mostrar todos los datos históricos guardados en la base de datos
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener todos los índices mensuales de la parcela
        indices = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('-año', '-mes')
        
        # Estadísticas
        total_registros = indices.count()
        registros_eosda = indices.filter(fuente_datos='EOSDA').count()
        registros_simulados = indices.filter(fuente_datos='Simulado').count()
        
        # Preparar datos para visualización
        datos_graficos = {
            'fechas': [],
            'ndvi': [],
            'ndmi': [],
            'savi': [],
            'temperatura': [],
            'precipitacion': []
        }
        
        for indice in indices:
            fecha_label = f"{indice.año}-{indice.mes:02d}"
            datos_graficos['fechas'].append(fecha_label)
            datos_graficos['ndvi'].append(indice.ndvi_promedio)
            datos_graficos['ndmi'].append(indice.ndmi_promedio)
            datos_graficos['savi'].append(indice.savi_promedio)
            datos_graficos['temperatura'].append(indice.temperatura_promedio)
            datos_graficos['precipitacion'].append(indice.precipitacion_total)
        
        contexto = {
            'parcela': parcela,
            'indices': indices[:20],  # Mostrar últimos 20 registros
            'total_registros': total_registros,
            'registros_eosda': registros_eosda,
            'registros_simulados': registros_simulados,
            'datos_graficos': json.dumps(datos_graficos),
            'tiene_datos': total_registros > 0
        }
        
        return render(request, 'informes/parcelas/datos_guardados.html', contexto)
        
    except Exception as e:
        logger.error(f"Error mostrando datos guardados: {str(e)}")
        messages.error(request, f"Error cargando datos: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


@login_required
def sincronizar_con_eosda(request, parcela_id):
    """
    Vista para sincronizar una parcela específica con EOSDA Field Management API
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        logger.info(f"Iniciando sincronización de {parcela.nombre} con EOSDA")
        
        # Sincronizar con EOSDA
        resultado = eosda_service.sincronizar_parcela_con_eosda(parcela)
        
        if resultado['exito']:
            if resultado.get('ya_existia'):
                messages.info(request, 
                    f'La parcela {parcela.nombre} ya estaba sincronizada con EOSDA '
                    f'(Field ID: {resultado["field_id"]})'
                )
            else:
                messages.success(request, 
                    f'Parcela {parcela.nombre} sincronizada exitosamente con EOSDA '
                    f'(Field ID: {resultado["field_id"]})'
                )
        else:
            messages.error(request, 
                f'Error sincronizando {parcela.nombre} con EOSDA: {resultado["error"]}'
            )
        
        return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
    except Exception as e:
        logger.error(f"Error sincronizando parcela con EOSDA: {str(e)}")
        messages.error(request, f"Error en sincronización: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


@login_required 
def estado_sincronizacion_eosda(request):
    """
    Vista para mostrar el estado de sincronización de todas las parcelas con EOSDA
    """
    try:
        parcelas = Parcela.objects.filter(activa=True).order_by('-fecha_registro')
        
        # Estadísticas generales
        total_parcelas = parcelas.count()
        sincronizadas = parcelas.filter(eosda_sincronizada=True).count()
        con_errores = parcelas.exclude(eosda_errores__isnull=True).exclude(eosda_errores='').count()
        
        # Agrupar por estado
        parcelas_data = []
        for parcela in parcelas:
            parcelas_data.append({
                'parcela': parcela,
                'estado': 'sincronizada' if parcela.eosda_sincronizada else 'pendiente',
                'field_id': parcela.eosda_field_id,
                'fecha_sync': parcela.eosda_fecha_sincronizacion,
                'errores': parcela.eosda_errores,
                'requiere_sync': parcela.requiere_sincronizacion_eosda,
                'puede_obtener_datos': parcela.puede_obtener_datos_eosda
            })
        
        contexto = {
            'parcelas_data': parcelas_data,
            'total_parcelas': total_parcelas,
            'sincronizadas': sincronizadas,
            'pendientes': total_parcelas - sincronizadas,
            'con_errores': con_errores,
            'porcentaje_sync': round((sincronizadas / total_parcelas * 100) if total_parcelas > 0 else 0, 1)
        }
        
        return render(request, 'informes/sistema/sincronizacion_eosda.html', contexto)
        
    except Exception as e:
        logger.error(f"Error mostrando estado sincronización: {str(e)}")
        messages.error(request, f"Error cargando estado: {str(e)}")
        return redirect('informes:estado_sistema')


@login_required
def galeria_imagenes(request, parcela_id):
    """
    Vista para mostrar galería de imágenes satelitales de una parcela
    Muestra todas las imágenes NDVI, NDMI, SAVI descargadas organizadas por mes
    """
    try:
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Obtener todos los registros con imágenes
        from django.db.models import Q
        registros_con_imagenes = IndiceMensual.objects.filter(
            parcela=parcela
        ).filter(
            Q(imagen_ndvi__isnull=False) | 
            Q(imagen_ndmi__isnull=False) | 
            Q(imagen_savi__isnull=False)
        ).order_by('-año', '-mes')
        
        # Estadísticas
        total_imagenes = 0
        imagenes_por_tipo = {'NDVI': 0, 'NDMI': 0, 'SAVI': 0}
        
        for registro in registros_con_imagenes:
            if registro.imagen_ndvi:
                total_imagenes += 1
                imagenes_por_tipo['NDVI'] += 1
            if registro.imagen_ndmi:
                total_imagenes += 1
                imagenes_por_tipo['NDMI'] += 1
            if registro.imagen_savi:
                total_imagenes += 1
                imagenes_por_tipo['SAVI'] += 1
        
        contexto = {
            'parcela': parcela,
            'registros_con_imagenes': registros_con_imagenes,
            'total_imagenes': total_imagenes,
            'imagenes_por_tipo': imagenes_por_tipo,
        }
        
        return render(request, 'informes/parcelas/galeria_imagenes.html', contexto)
        
    except Exception as e:
        logger.error(f"Error en galería de imágenes: {str(e)}")
        messages.error(request, f"Error cargando galería: {str(e)}")
        return redirect('informes:detalle_parcela', parcela_id=parcela_id)


def descargar_imagen_indice(request, registro_id):
    """
    Vista AJAX para descargar imagen satelital desde Field Imagery API de EOSDA.
    
    Verifica si la imagen ya existe localmente, si no la descarga desde EOSDA.
    Retorna URL de la imagen o mensaje de error.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.eosda_api import EosdaAPIService
        from django.core.files.base import ContentFile
        import os
        
        # Obtener registro mensual
        registro = get_object_or_404(IndiceMensual, id=registro_id)
        
        # Obtener tipo de índice solicitado
        indice = request.POST.get('indice', '').upper()
        if indice not in ['NDVI', 'NDMI', 'SAVI']:
            return JsonResponse({
                'success': False, 
                'error': f'Índice no válido: {indice}. Usar NDVI, NDMI o SAVI'
            }, status=400)
        
        # Verificar si la imagen ya existe localmente
        campo_imagen = f'imagen_{indice.lower()}'
        imagen_existente = getattr(registro, campo_imagen, None)
        
        if imagen_existente and imagen_existente.name:
            # Imagen ya descargada, retornar URL
            logger.info(f"✅ Imagen {indice} ya existe para registro {registro_id}")
            return JsonResponse({
                'success': True,
                'existe': True,
                'url': imagen_existente.url,
                'fecha': registro.fecha_imagen.isoformat() if registro.fecha_imagen else None,
                'nubosidad': registro.nubosidad_imagen
            })
        
        # Verificar que la parcela tenga field_id de EOSDA
        if not registro.parcela.eosda_field_id:
            return JsonResponse({
                'success': False,
                'error': 'La parcela no está sincronizada con EOSDA'
            }, status=400)
        
        # ✅ OPTIMIZACIÓN: Usar view_id ya guardado en el modelo (0 requests adicionales!)
        if not registro.view_id_imagen:
            return JsonResponse({
                'success': False,
                'error': (
                    f'⚠️ Sin view_id para {registro.año}-{registro.mes:02d}.\n\n'
                    f'📋 Flujo correcto:\n'
                    f'1️⃣ Obtener Datos Históricos (Statistics API)\n'
                    f'2️⃣ Descargar imágenes específicas\n\n'
                    f'💡 Esto ahorra ~15-20 requests por imagen.\n\n'
                    f'Haz clic en "Actualizar Datos" en la parte superior.'
                ),
                'requiere_statistics': True
            }, status=400)
        
        logger.info(f"📷 Descargando imagen {indice} para registro {registro_id} usando view_id guardado: {registro.view_id_imagen}")
        eosda_service = EosdaAPIService()
        
        # ✅ Usar view_id y fecha ya guardados en el modelo
        resultado = eosda_service.descargar_imagen_satelital(
            field_id=registro.parcela.eosda_field_id,
            indice=indice,
            view_id=registro.view_id_imagen,  # ✅ Usar view_id guardado
            fecha_escena=registro.fecha_imagen.isoformat() if registro.fecha_imagen else None,
            max_nubosidad=50.0
        )
        
        if not resultado:
            return JsonResponse({
                'success': False,
                'error': f'No se pudo descargar imagen {indice}. Verifique que hay escenas disponibles con baja nubosidad.'
            }, status=500)
        
        # Guardar imagen en el modelo
        nombre_archivo = f"{registro.parcela.nombre}_{registro.año}_{registro.mes:02d}_{indice}.png"
        nombre_archivo = nombre_archivo.replace(' ', '_').replace('/', '_')
        
        content_file = ContentFile(resultado['imagen'])
        
        # Guardar en el campo correspondiente
        if indice == 'NDVI':
            registro.imagen_ndvi.save(nombre_archivo, content_file, save=False)
        elif indice == 'NDMI':
            registro.imagen_ndmi.save(nombre_archivo, content_file, save=False)
        elif indice == 'SAVI':
            registro.imagen_savi.save(nombre_archivo, content_file, save=False)
        
        # Actualizar metadatos
        registro.view_id_imagen = resultado.get('view_id')
        registro.fecha_imagen = resultado.get('fecha')
        registro.nubosidad_imagen = resultado.get('nubosidad')
        registro.save()
        
        logger.info(f"✅ Imagen {indice} guardada para registro {registro_id}")
        
        # Obtener URL de la imagen guardada
        imagen_guardada = getattr(registro, campo_imagen)
        
        return JsonResponse({
            'success': True,
            'existe': False,
            'url': imagen_guardada.url if imagen_guardada else None,
            'fecha': resultado.get('fecha'),
            'nubosidad': resultado.get('nubosidad'),
            'view_id': resultado.get('view_id')
        })
        
    except IndiceMensual.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Registro no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Error descargando imagen para registro {registro_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


@login_required
def generar_informe_pdf(request, parcela_id):
    """
    Vista para generar informe PDF profesional de una parcela
    Accesible desde el botón "Generar Informe" en detalle de parcela
    """
    try:
        # Verificar que la parcela existe
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # Verificar permisos (propietario o superusuario)
        if not request.user.is_superuser and parcela.propietario != request.user.username:
            messages.error(request, 'No tiene permisos para generar informes de esta parcela.')
            return redirect('informes:detalle_parcela', parcela_id=parcela_id)
        
        # Obtener parámetros opcionales
        meses_atras = int(request.GET.get('meses', 12))
        
        # Validar que hay datos disponibles
        indices_count = IndiceMensual.objects.filter(parcela=parcela).count()
        if indices_count == 0:
            messages.warning(request, 
                           'No hay datos satelitales disponibles para esta parcela. '
                           'Por favor sincronice datos primero.')
            return redirect('informes:detalle_parcela', parcela_id=parcela_id)
        
        # Generar PDF
        try:
            generador = GeneradorPDFProfesional()
            ruta_pdf = generador.generar_informe_completo(
                parcela_id=parcela_id,
                meses_atras=meses_atras
            )
            
            # Verificar que el archivo se generó
            if not os.path.exists(ruta_pdf):
                raise FileNotFoundError(f"El PDF no se generó correctamente en {ruta_pdf}")
            
            # Crear registro de informe en BD
            from datetime import timedelta
            titulo_informe = f"Informe - {parcela.nombre}"[:290]  # Limitar a 290 caracteres
            informe = Informe.objects.create(
                parcela=parcela,
                periodo_analisis_meses=meses_atras,
                fecha_inicio_analisis=(datetime.now() - timedelta(days=meses_atras*30)).date(),
                fecha_fin_analisis=datetime.now().date(),
                titulo=titulo_informe,
                resumen_ejecutivo=f"Informe generado con {indices_count} meses de datos satelitales.",
                archivo_pdf=ruta_pdf
            )
            
            # Enviar archivo para descarga
            from django.http import FileResponse
            response = FileResponse(
                open(ruta_pdf, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="informe_{parcela.nombre.replace(" ", "_")}.pdf"'
            
            # Log de éxito
            logger.info(f"Informe PDF generado exitosamente para parcela {parcela.nombre} (ID: {parcela_id})")
            messages.success(request, 
                           f'¡Informe generado exitosamente! '
                                                     f'Analizados {indices_count} registros mensuales.')
            
            return response
            
        except Exception as e_generacion:
            logger.error(f"Error generando PDF para parcela {parcela_id}: {str(e_generacion)}")
            logger.exception(e_generacion)
            messages.error(request, 
                          f'Error generando el informe PDF: {str(e_generacion)}. '
                          'Por favor contacte al administrador.')
            return redirect('informes:detalle_parcela', parcela_id=parcela_id)
        
    except Exception as e:
        logger.error(f"Error en generar_informe_pdf para parcela {parcela_id}: {str(e)}")
        logger.exception(e)
        messages.error(request, f'Error: {str(e)}')
        return redirect('informes:lista_parcelas')
