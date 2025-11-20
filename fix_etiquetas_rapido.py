"""
Script rápido SQL para actualizar etiquetas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        UPDATE informes_indicemensual 
        SET fuente_datos = 'Solo Clima' 
        WHERE fuente_datos IN ('Open-Meteo', 'Simulado')
    """)
    print(f"✅ Actualizado {cursor.rowcount} registros")
