import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual

# Obtener parcela 2 (lote 2)
indices = IndiceMensual.objects.filter(parcela_id=2).order_by('-año', '-mes')[:15]

print('=== DATOS CLIMÁTICOS EN BD (últimos 15 registros) ===\n')
print(f'{"Periodo":<12} {"Temp°C":<10} {"Precip(mm)":<12} {"NDVI":<8}')
print('-' * 50)

for idx in indices:
    periodo = f'{idx.año}-{idx.mes:02d}'
    temp = f'{idx.temperatura_promedio:.1f}' if idx.temperatura_promedio else 'NULL'
    precip = f'{idx.precipitacion_total:.1f}' if idx.precipitacion_total else 'NULL'
    ndvi = f'{idx.ndvi_promedio:.3f}' if idx.ndvi_promedio else 'NULL'
    
    print(f'{periodo:<12} {temp:<10} {precip:<12} {ndvi:<8}')

# Contar registros con datos climáticos
total = indices.count()
con_temp = indices.filter(temperatura_promedio__isnull=False).count()
con_precip = indices.filter(precipitacion_total__isnull=False).count()

print(f'\n📊 Total registros: {total}')
print(f'✅ Con temperatura: {con_temp} ({con_temp/total*100:.0f}%)')
print(f'✅ Con precipitación: {con_precip} ({con_precip/total*100:.0f}%)')
