#!/usr/bin/env python
"""
Script de prueba para verificar el cálculo de rangos de fechas.
Simula la lógica JavaScript del selector de rangos.
"""
from datetime import date, timedelta

def calcular_fechas(rango_meses):
    """
    Calcula fecha_inicio y fecha_fin según el rango seleccionado.
    
    Args:
        rango_meses: Número de meses hacia atrás (6, 12, 24)
    
    Returns:
        tuple: (fecha_inicio, fecha_fin)
    """
    fecha_fin = date.today()
    
    # Calcular fecha inicio restando meses
    año_inicio = fecha_fin.year
    mes_inicio = fecha_fin.month - rango_meses
    
    # Ajustar año si los meses son negativos
    while mes_inicio <= 0:
        mes_inicio += 12
        año_inicio -= 1
    
    fecha_inicio = date(año_inicio, mes_inicio, fecha_fin.day)
    
    return fecha_inicio, fecha_fin


def main():
    print("=" * 60)
    print("🧪 TEST DE RANGOS DE FECHAS - AgroTech Histórico")
    print("=" * 60)
    
    hoy = date.today()
    print(f"\n📅 Fecha actual: {hoy.strftime('%d/%m/%Y')}\n")
    
    rangos = [
        (6, "6 meses"),
        (12, "12 meses (1 año)"),
        (24, "24 meses (2 años)")
    ]
    
    for meses, descripcion in rangos:
        inicio, fin = calcular_fechas(meses)
        diferencia_dias = (fin - inicio).days
        print(f"✅ {descripcion}:")
        print(f"   Inicio: {inicio.strftime('%d/%m/%Y')}")
        print(f"   Fin:    {fin.strftime('%d/%m/%Y')}")
        print(f"   Total:  {diferencia_dias} días (~{diferencia_dias // 30} meses)")
        print()
    
    # Test de rango personalizado
    print("📝 Ejemplo de rango personalizado:")
    fecha_inicio_custom = date(2024, 1, 1)
    fecha_fin_custom = date(2024, 12, 31)
    diferencia = (fecha_fin_custom - fecha_inicio_custom).days
    print(f"   Inicio: {fecha_inicio_custom.strftime('%d/%m/%Y')}")
    print(f"   Fin:    {fecha_fin_custom.strftime('%d/%m/%Y')}")
    print(f"   Total:  {diferencia} días (~{diferencia // 30} meses)")
    print()
    
    print("=" * 60)
    print("✅ Prueba completada exitosamente")
    print("=" * 60)


if __name__ == '__main__':
    main()
