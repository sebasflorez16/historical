#!/usr/bin/env python3
"""
Script de verificación de estado del sistema en Railway
Ejecutar con: railway run python verificar_sistema.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from django.conf import settings
from django.db import connection
import requests

def verificar_sistema():
    """Verifica el estado completo del sistema"""
    
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE SISTEMA - AgroTech Histórico")
    print("=" * 80)
    
    errores = []
    warnings = []
    
    # 1. Verificar configuración Django
    print("\n✓ Django configurado correctamente")
    print(f"  - Versión: {django.VERSION}")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - Entorno: {'Producción' if not settings.DEBUG else 'Desarrollo'}")
    
    # 2. Verificar base de datos
    print("\n📊 Base de Datos:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"  ✅ PostgreSQL: {version.split(',')[0]}")
            
            # Verificar PostGIS
            cursor.execute("SELECT PostGIS_version();")
            postgis_version = cursor.fetchone()[0]
            print(f"  ✅ PostGIS: {postgis_version}")
            
            # Verificar tablas
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            num_tablas = cursor.fetchone()[0]
            print(f"  ✅ Tablas: {num_tablas}")
            
    except Exception as e:
        errores.append(f"Error BD: {str(e)}")
        print(f"  ❌ Error: {str(e)}")
    
    # 3. Verificar migraciones
    print("\n🔄 Migraciones:")
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', '--list', stdout=out)
        output = out.getvalue()
        
        # Contar migraciones aplicadas
        total = output.count('[X]') + output.count('[ ]')
        aplicadas = output.count('[X]')
        pendientes = output.count('[ ]')
        
        print(f"  ✅ Aplicadas: {aplicadas}/{total}")
        if pendientes > 0:
            warnings.append(f"{pendientes} migraciones pendientes")
            print(f"  ⚠️  Pendientes: {pendientes}")
        
    except Exception as e:
        errores.append(f"Error migraciones: {str(e)}")
        print(f"  ❌ Error: {str(e)}")
    
    # 4. Verificar modelos
    print("\n📦 Modelos:")
    try:
        from django.apps import apps
        
        # Contar parcelas
        Parcela = apps.get_model('informes', 'Parcela')
        num_parcelas = Parcela.objects.count()
        print(f"  ✅ Parcelas: {num_parcelas}")
        
        # Contar análisis
        Analisis = apps.get_model('informes', 'AnalisisParcela')
        num_analisis = Analisis.objects.count()
        print(f"  ✅ Análisis: {num_analisis}")
        
    except Exception as e:
        errores.append(f"Error modelos: {str(e)}")
        print(f"  ❌ Error: {str(e)}")
    
    # 5. Verificar APIs externas
    print("\n🌐 APIs Externas:")
    
    # Gemini
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key and gemini_key != 'demo_key':
        print(f"  ✅ Gemini: Configurado ({len(gemini_key)} caracteres)")
    else:
        warnings.append("Gemini API key no configurada")
        print(f"  ⚠️  Gemini: No configurado")
    
    # EOSDA
    eosda_key = getattr(settings, 'EOSDA_API_KEY', None)
    if eosda_key and 'demo' not in eosda_key.lower():
        print(f"  ✅ EOSDA: Configurado ({len(eosda_key)} caracteres)")
        
        # Probar conexión
        try:
            response = requests.get(
                f"{settings.EOSDA_BASE_URL}/field-management/fields",
                headers={'x-api-key': eosda_key},
                timeout=5
            )
            if response.status_code == 200:
                print(f"  ✅ EOSDA: Conectado ({len(response.json())} campos)")
            elif response.status_code == 403:
                warnings.append("EOSDA: API key inválida (403)")
                print(f"  ⚠️  EOSDA: API key inválida (403)")
            else:
                warnings.append(f"EOSDA: Error {response.status_code}")
                print(f"  ⚠️  EOSDA: Error {response.status_code}")
        except Exception as e:
            warnings.append(f"EOSDA: {str(e)}")
            print(f"  ⚠️  EOSDA: {str(e)[:50]}...")
    else:
        warnings.append("EOSDA API key no configurada")
        print(f"  ⚠️  EOSDA: No configurado")
    
    # 6. Verificar variables críticas
    print("\n🔒 Seguridad:")
    
    secret_key = getattr(settings, 'SECRET_KEY', None)
    if secret_key and len(secret_key) >= 50:
        print(f"  ✅ SECRET_KEY: Configurada")
    else:
        errores.append("SECRET_KEY no configurada o muy corta")
        print(f"  ❌ SECRET_KEY: Problema")
    
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    if allowed_hosts:
        print(f"  ✅ ALLOWED_HOSTS: {len(allowed_hosts)} hosts")
    else:
        warnings.append("ALLOWED_HOSTS vacío")
        print(f"  ⚠️  ALLOWED_HOSTS: Vacío")
    
    # 7. Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    
    if errores:
        print(f"\n❌ ERRORES CRÍTICOS ({len(errores)}):")
        for error in errores:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errores and not warnings:
        print("\n✅ SISTEMA FUNCIONANDO PERFECTAMENTE")
    elif not errores:
        print("\n✅ SISTEMA FUNCIONAL (con advertencias)")
    else:
        print("\n❌ SISTEMA CON ERRORES CRÍTICOS")
    
    print("\n" + "=" * 80)
    
    # Código de salida
    return 0 if not errores else 1

if __name__ == "__main__":
    exit_code = verificar_sistema()
    sys.exit(exit_code)
