#!/usr/bin/env python3
"""
Script para exponer el último análisis Gemini en caché de cada parcela
No consume tokens ni hace requests externos.
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual

print("\n=== CACHÉ DE ANÁLISIS GEMINI POR PARCELA ===\n")

for parcela in Parcela.objects.all():
    ultimo_indice = IndiceMensual.objects.filter(parcela=parcela, analisis_gemini__isnull=False, fecha_analisis_gemini__isnull=False).order_by('-año', '-mes').first()
    if ultimo_indice:
        edad = (datetime.now() - ultimo_indice.fecha_analisis_gemini.replace(tzinfo=None)).days
        print(f"Parcela: {parcela.nombre} (ID: {parcela.id})")
        print(f"  Fecha caché: {ultimo_indice.fecha_analisis_gemini.strftime('%Y-%m-%d %H:%M:%S')}  |  Edad: {edad} días")
        resumen = str(ultimo_indice.analisis_gemini)[:300].replace('\n',' ')
        print(f"  Resumen caché: {resumen} ...\n")
    else:
        print(f"Parcela: {parcela.nombre} (ID: {parcela.id})")
        print("  ⚠️  No hay análisis Gemini en caché\n")
