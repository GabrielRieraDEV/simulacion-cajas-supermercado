"""
🛒 SuperLatino - Sistema de Simulación de Cajas Registradoras
Punto de entrada principal del proyecto
"""
import sys
import argparse


def mostrar_menu():
    """Muestra menú interactivo"""
    print("\n" + "=" * 60)
    print("🛒 SUPERLATINO - SIMULACIÓN DE CAJAS REGISTRADORAS")
    print("=" * 60)
    print("\nSeleccione una opción:\n")
    print("  1. 🎮 Visualización Pygame (animación en tiempo real)")
    print("  2. 📊 Dashboard Dash (panel web interactivo)")
    print("  3. 📈 Análisis comparativo (ejecutar todos los escenarios)")
    print("  4. 🖥️  Simulación rápida (solo consola)")
    print("  5. ❌ Salir")
    print()
    
    while True:
        try:
            opcion = input("Ingrese opción (1-5): ").strip()
            if opcion in ['1', '2', '3', '4', '5']:
                return opcion
            print("❌ Opción no válida. Intente de nuevo.")
        except KeyboardInterrupt:
            return '5'


def ejecutar_pygame():
    """Ejecuta visualización con Pygame"""
    print("\n🎮 Iniciando visualización Pygame...")
    print("   Controles: ESPACIO=Pausar, ↑↓=Velocidad, R=Reiniciar, ESC=Salir\n")
    
    from visualizacion.pygame_sim import VisualizadorPygame
    from config import ESCENARIOS
    
    viz = VisualizadorPygame(
        config_cajas=ESCENARIOS["hibrido_con_rapidas"],
        politica="balanceada",
        alta_demanda=False
    )
    stats = viz.ejecutar()
    
    if stats:
        print("\n📊 Resultados finales:")
        for k, v in stats.resumen().items():
            print(f"   {k}: {v}")


def ejecutar_dashboard():
    """Ejecuta dashboard web con Dash"""
    print("\n📊 Iniciando Dashboard web...")
    
    from dashboard.app import ejecutar_dashboard
    ejecutar_dashboard(debug=False)


def ejecutar_analisis():
    """Ejecuta análisis comparativo completo"""
    print("\n📈 Ejecutando análisis comparativo de escenarios...")
    
    from analisis.comparador import ComparadorEscenarios
    from analisis.reportes import GeneradorReportes
    
    comparador = ComparadorEscenarios(duracion_simulacion=480.0)
    
    # Ejecutar en demanda normal
    print("\n--- Demanda Normal ---")
    comparador.ejecutar_todos_escenarios(alta_demanda=False, politica="balanceada")
    
    # Mostrar resultados
    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA DE RESULTADOS")
    print("=" * 70)
    tabla = comparador.obtener_tabla_comparativa()
    print(tabla.to_string(index=False))
    
    # Recomendaciones
    print("\n" + "=" * 70)
    print("RECOMENDACIONES")
    print("=" * 70)
    for rec in comparador.generar_recomendaciones():
        print(f"  {rec}")
    
    # Generar reportes
    print("\n📊 Generando gráficas y reportes...")
    generador = GeneradorReportes(directorio_salida="reportes")
    generador.generar_reporte_completo(comparador)


def ejecutar_simulacion_rapida():
    """Ejecuta simulación rápida en consola"""
    from config import ESCENARIOS, ConfiguracionSimulacion
    from simulacion.supermercado import Supermercado
    
    print("\n🖥️ Simulación rápida en consola")
    print("-" * 40)
    
    # Seleccionar escenario
    print("\nEscenarios disponibles:")
    escenarios_lista = list(ESCENARIOS.keys())
    for i, nombre in enumerate(escenarios_lista, 1):
        config = ESCENARIOS[nombre]
        print(f"  {i}. {nombre} ({config.descripcion()})")
    
    try:
        sel = int(input("\nSeleccione escenario (1-4): ")) - 1
        escenario_nombre = escenarios_lista[sel]
    except (ValueError, IndexError):
        escenario_nombre = "hibrido_con_rapidas"
        print(f"Usando escenario por defecto: {escenario_nombre}")
    
    config_cajas = ESCENARIOS[escenario_nombre]
    
    # Demanda
    demanda = input("¿Alta demanda? (s/n): ").strip().lower() == 's'
    
    print(f"\n⏳ Ejecutando simulación: {escenario_nombre}")
    print(f"   Demanda: {'Alta' if demanda else 'Normal'}")
    print(f"   Duración: 8 horas simuladas")
    print("-" * 40)
    
    config_sim = ConfiguracionSimulacion()
    supermercado = Supermercado(
        config_sim=config_sim,
        config_cajas=config_cajas,
        politica="balanceada",
        alta_demanda=demanda
    )
    
    stats = supermercado.ejecutar()
    
    # Mostrar resultados
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DE LA SIMULACIÓN")
    print("=" * 50)
    
    for key, value in stats.resumen().items():
        print(f"  {key}: {value}")
    
    # Costo-beneficio
    cb = stats.calcular_costo_beneficio(config_cajas, 8.0)
    print("\n💰 Análisis Costo-Beneficio:")
    print(f"  Costo operacional: ${cb['costo_operacional_total']:.2f} (8 horas)")
    print(f"  Throughput: {cb['throughput_hora']:.1f} clientes/hora")
    print(f"  Costo por cliente: ${cb['costo_por_cliente']:.2f}")
    print(f"  Pérdida por abandonos: ${cb['perdida_por_abandonos']:.2f}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="SuperLatino - Simulación de Cajas Registradoras"
    )
    parser.add_argument(
        '--modo', '-m',
        choices=['pygame', 'dash', 'analisis', 'consola', 'menu'],
        default='menu',
        help='Modo de ejecución'
    )
    
    args = parser.parse_args()
    
    if args.modo == 'pygame':
        ejecutar_pygame()
    elif args.modo == 'dash':
        ejecutar_dashboard()
    elif args.modo == 'analisis':
        ejecutar_analisis()
    elif args.modo == 'consola':
        ejecutar_simulacion_rapida()
    else:
        # Menú interactivo
        while True:
            opcion = mostrar_menu()
            
            if opcion == '1':
                ejecutar_pygame()
            elif opcion == '2':
                ejecutar_dashboard()
            elif opcion == '3':
                ejecutar_analisis()
            elif opcion == '4':
                ejecutar_simulacion_rapida()
            elif opcion == '5':
                print("\n👋 ¡Hasta luego!")
                break


if __name__ == "__main__":
    main()
