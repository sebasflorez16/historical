#!/usr/bin/env python
"""
Script de prueba para verificar el cálculo de meses esperados vs obtenidos.
Simula lo que pasará cuando obtengas datos de 12 meses.
"""
from datetime import date

def calcular_meses_info(fecha_inicio, fecha_fin, datos_procesados):
    """
    Calcula información sobre meses esperados vs obtenidos.
    """
    # Calcular meses esperados
    meses_esperados = ((fecha_fin.year - fecha_inicio.year) * 12 + 
                       fecha_fin.month - fecha_inicio.month) + 1
    meses_faltantes = meses_esperados - datos_procesados
    
    return {
        'esperados': meses_esperados,
        'obtenidos': datos_procesados,
        'faltantes': meses_faltantes
    }

def generar_mensaje(info, tiene_datos_clima=False):
    """
    Genera el mensaje que verá el usuario.
    """
    mensaje = f'✅ Datos históricos actualizados: 7 nuevos registros, {info["obtenidos"]} meses procesados.'
    
    if info['faltantes'] > 0:
        mensaje += f' ℹ️ Nota: {info["faltantes"]} mes(es) sin datos satelitales disponibles (nubosidad alta, sensor no pasó por la zona, o datos no procesados por EOSDA).'
    
    if not tiene_datos_clima:
        mensaje += ' ⚠️ Datos climáticos (temperatura, precipitación) no disponibles para esta parcela en EOSDA.'
    
    return mensaje


def main():
    print("=" * 80)
    print("🧪 TEST CÁLCULO DE MESES FALTANTES - AgroTech Histórico")
    print("=" * 80)
    
    # Simular caso real: 12 meses solicitados, 10 obtenidos
    hoy = date.today()
    fecha_inicio = date(2024, 11, 20)
    fecha_fin = date(2025, 11, 20)
    datos_procesados = 10  # Como en tu caso real
    
    print(f"\n📅 Rango solicitado:")
    print(f"   Inicio: {fecha_inicio.strftime('%d/%m/%Y')}")
    print(f"   Fin:    {fecha_fin.strftime('%d/%m/%Y')}")
    print(f"   Meses esperados: 13 meses")
    print(f"   Meses obtenidos: {datos_procesados} meses")
    
    info = calcular_meses_info(fecha_inicio, fecha_fin, datos_procesados)
    
    print(f"\n📊 Análisis:")
    print(f"   ✅ Esperados: {info['esperados']} meses")
    print(f"   ✅ Obtenidos: {info['obtenidos']} meses")
    print(f"   ❌ Faltantes: {info['faltantes']} meses")
    
    print(f"\n💬 Mensaje que verás en la interfaz:")
    print("─" * 80)
    mensaje = generar_mensaje(info, tiene_datos_clima=False)
    print(mensaje)
    print("─" * 80)
    
    # Caso ideal: todos los meses disponibles
    print(f"\n\n🎯 Caso ideal (todos los meses disponibles):")
    info_ideal = calcular_meses_info(fecha_inicio, fecha_fin, 13)
    mensaje_ideal = generar_mensaje(info_ideal, tiene_datos_clima=True)
    print("─" * 80)
    print(mensaje_ideal)
    print("─" * 80)
    
    print("\n" + "=" * 80)
    print("✅ Test completado - El sistema informará claramente sobre datos faltantes")
    print("=" * 80)


if __name__ == '__main__':
    main()
