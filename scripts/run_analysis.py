"""
Script para ejecutar análisis comparativo completo
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analisis.comparador import ComparadorEscenarios
from analisis.reportes import GeneradorReportes
from config import ESCENARIOS


def main():
    print("=" * 70)
    print("🛒 SUPERLATINO - ANÁLISIS COMPARATIVO DE CONFIGURACIONES")
    print("=" * 70)
    
    comparador = ComparadorEscenarios(duracion_simulacion=480.0)
    
    # Ejecutar todos los escenarios en demanda normal
    print("\n📊 Simulando escenarios en DEMANDA NORMAL...\n")
    for nombre, config in ESCENARIOS.items():
        print(f"  ▶ Ejecutando: {nombre} ({config.descripcion()})...")
        comparador.ejecutar_escenario(
            nombre=f"{nombre}_normal",
            config_cajas=config,
            politica="balanceada",
            alta_demanda=False
        )
    
    # Ejecutar todos los escenarios en alta demanda
    print("\n📊 Simulando escenarios en ALTA DEMANDA (fin de mes)...\n")
    for nombre, config in ESCENARIOS.items():
        print(f"  ▶ Ejecutando: {nombre} ({config.descripcion()})...")
        comparador.ejecutar_escenario(
            nombre=f"{nombre}_alta",
            config_cajas=config,
            politica="balanceada",
            alta_demanda=True
        )
    
    # Mostrar tabla comparativa
    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA DE RESULTADOS")
    print("=" * 70)
    tabla = comparador.obtener_tabla_comparativa()
    print(tabla.to_string(index=False))
    
    # Recomendaciones
    print("\n" + "=" * 70)
    print("📌 RECOMENDACIONES BASADAS EN ANÁLISIS")
    print("=" * 70)
    for rec in comparador.generar_recomendaciones():
        print(f"  {rec}")
    
    # Generar reportes gráficos
    print("\n" + "=" * 70)
    print("📊 GENERANDO REPORTES GRÁFICOS...")
    print("=" * 70)
    
    generador = GeneradorReportes(directorio_salida="reportes")
    generador.generar_reporte_completo(comparador, nombre_reporte="analisis_completo")
    
    print("\n✅ Análisis completado. Revise la carpeta 'reportes/' para ver los resultados.")


if __name__ == "__main__":
    main()
