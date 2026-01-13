"""Punto de entrada para la simulación del sistema de cajas."""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from typing import Dict, Iterable

from simulacion_supermercado.analysis import metrics
from simulacion_supermercado.simulation.escenarios import (
    Escenario,
    todos_los_escenarios,
)
from simulacion_supermercado.simulation.supermercado import Supermercado


def main() -> None:
    args = _parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    escenarios = todos_los_escenarios()
    if args.escenario not in escenarios:
        _mostrar_escenarios_disponibles(escenarios)
        raise SystemExit(1)

    escenario = escenarios[args.escenario]
    supermercado = Supermercado(
        configuracion=dict(escenario.configuracion),
        cajas_base=escenario.cajas,
    )

    tasa_llegada = float(supermercado.configuracion.get("tasa_llegada", 1.0))
    supermercado.iniciar_proceso_llegadas(tasa_llegada)
    supermercado.env.run(until=args.duracion)

    _mostrar_resultados(supermercado, escenario, args.duracion)

    if args.visualizar:
        _mostrar_visualizacion(supermercado, escenario)


def _mostrar_resultados(
    supermercado: Supermercado, escenario: Escenario, duracion: float
) -> None:
    clientes = supermercado.clientes_generados
    print(f"\n=== Resultados escenario: {escenario.nombre} ===")
    print(escenario.descripcion)
    print(f"Duración simulada: {duracion} min")
    print(f"Clientes generados: {len(clientes)}")
    print(f"Clientes procesados: {supermercado.metricas['clientes_procesados']}")
    print(f"Clientes que abandonaron: {supermercado.metricas['clientes_abandonaron']}")

    print("\n--- Métricas de desempeño ---")
    print(
        f"Tiempo promedio en cola: "
        f"{metrics.tiempo_promedio_en_cola(clientes):.2f} min"
    )
    print(
        f"Tiempo promedio en sistema: "
        f"{metrics.tiempo_promedio_en_sistema(clientes):.2f} min"
    )
    print(f"Tasa de abandono: {metrics.tasa_abandono(supermercado.metricas):.2%}")

    metricas_cajas = _construir_metricas_cajas(escenario.cajas, clientes, duracion)
    utilizaciones = metrics.utilizacion_cajas(metricas_cajas)
    if utilizaciones:
        print("\n--- Utilización de cajas ---")
        for identificador, valor in utilizaciones.items():
            print(f"{identificador}: {valor:.2%}")


def _construir_metricas_cajas(
    cajas: Iterable, clientes, duracion: float
) -> Dict[str, Dict[str, float]]:
    capacidad_por_tipo = defaultdict(int)
    for caja in cajas:
        capacidad_por_tipo[caja.tipo.value] += caja.capacidad

    ocupacion_por_tipo = defaultdict(float)
    for cliente in clientes:
        if (
            cliente.tipo_caja_asignada is None
            or cliente.tiempo_inicio_servicio is None
            or cliente.tiempo_salida is None
        ):
            continue
        servicio = max(0.0, cliente.tiempo_salida - cliente.tiempo_inicio_servicio)
        ocupacion_por_tipo[cliente.tipo_caja_asignada] += servicio

    metricas = {}
    for tipo, capacidad in capacidad_por_tipo.items():
        metricas[tipo] = {
            "tiempo_ocupado": ocupacion_por_tipo.get(tipo, 0.0),
            "tiempo_total": duracion * capacidad,
        }
    return metricas


def _mostrar_escenarios_disponibles(escenarios: Dict[str, Escenario]) -> None:
    print("Escenario no válido. Opciones disponibles:")
    for clave, escenario in escenarios.items():
        print(f"- {clave}: {escenario.descripcion}")


def _mostrar_visualizacion(supermercado: Supermercado, escenario: Escenario) -> None:
    try:
        from simulacion_supermercado.ui.pygame_view import PygameVisualizer
    except RuntimeError as exc:
        print(f"No fue posible iniciar la visualización: {exc}")
        return

    visualizer = PygameVisualizer(escenario=escenario, clientes=supermercado.clientes_generados)
    visualizer.run()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulador del sistema de cajas del supermercado"
    )
    parser.add_argument(
        "--escenario",
        choices=todos_los_escenarios().keys(),
        default="tradicional",
        help="Escenario operativo a ejecutar",
    )
    parser.add_argument(
        "--duracion",
        type=float,
        default=240.0,
        help="Duración de la simulación en minutos",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Semilla para los generadores aleatorios",
    )
    parser.add_argument(
        "--visualizar",
        action="store_true",
        help="Muestra una visualización básica en Pygame al finalizar la simulación",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
