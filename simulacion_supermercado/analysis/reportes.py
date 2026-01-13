"""Generación de reportes comparativos entre escenarios."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

try:  # pragma: no cover - matplotlib es opcional
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "Se requiere matplotlib para generar reportes gráficos. "
        "Instálalo (pip install matplotlib) e inténtalo nuevamente."
    ) from exc

from simulacion_supermercado.analysis import metrics
from simulacion_supermercado.simulation.escenarios import Escenario
from simulacion_supermercado.simulation.supermercado import Supermercado


@dataclass
class ResultadoEscenario:
    nombre: str
    descripcion: str
    tiempo_cola: float
    tiempo_sistema: float
    tasa_abandono: float


def generar_reporte_comparativo(
    escenarios: Dict[str, Escenario],
    duracion: float,
    repeticiones: int = 3,
    seed: Optional[int] = None,
) -> None:
    """Ejecuta múltiples escenarios y grafica los resultados comparativos."""

    resultados: Dict[str, ResultadoEscenario] = {}
    for idx, (clave, escenario) in enumerate(escenarios.items()):
        print(f"Simulando escenario '{clave}' ({escenario.nombre})...")
        resultado = _simular_escenario(escenario, duracion, repeticiones, seed, idx)
        resultados[clave] = resultado

    _mostrar_resumen(resultados)
    _graficar_resultados(resultados)


def _simular_escenario(
    escenario: Escenario,
    duracion: float,
    repeticiones: int,
    seed: Optional[int],
    offset: int,
) -> ResultadoEscenario:
    tiempos_cola = []
    tiempos_sistema = []
    tasas_abandono = []

    for corrida in range(repeticiones):
        if seed is not None:
            random.seed(seed + offset * 100 + corrida)

        supermercado = Supermercado(
            configuracion=dict(escenario.configuracion),
            cajas_base=escenario.cajas,
        )
        tasa = float(supermercado.configuracion.get("tasa_llegada", 1.0))
        supermercado.iniciar_proceso_llegadas(tasa)
        supermercado.env.run(until=duracion)

        clientes = supermercado.clientes_generados
        tiempos_cola.append(metrics.tiempo_promedio_en_cola(clientes))
        tiempos_sistema.append(metrics.tiempo_promedio_en_sistema(clientes))
        tasas_abandono.append(metrics.tasa_abandono(supermercado.metricas))

    return ResultadoEscenario(
        nombre=escenario.nombre,
        descripcion=escenario.descripcion,
        tiempo_cola=_promedio(tiempos_cola),
        tiempo_sistema=_promedio(tiempos_sistema),
        tasa_abandono=_promedio(tasas_abandono),
    )


def _mostrar_resumen(resultados: Dict[str, ResultadoEscenario]) -> None:
    print("\n=== Resumen comparativo ===")
    for clave, resultado in resultados.items():
        print(f"\n[{clave}] {resultado.nombre}")
        print(resultado.descripcion)
        print(f"  - Tiempo promedio en cola: {resultado.tiempo_cola:.2f} min")
        print(f"  - Tiempo promedio en sistema: {resultado.tiempo_sistema:.2f} min")
        print(f"  - Tasa de abandono: {resultado.tasa_abandono:.2%}")


def _graficar_resultados(resultados: Dict[str, ResultadoEscenario]) -> None:
    etiquetas = list(resultados.keys())
    cola = [resultado.tiempo_cola for resultado in resultados.values()]
    sistema = [resultado.tiempo_sistema for resultado in resultados.values()]
    abandono = [resultado.tasa_abandono * 100 for resultado in resultados.values()]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    axes[0].bar(etiquetas, cola, color="#00aadd")
    axes[0].set_title("Tiempo promedio en cola (min)")
    axes[0].set_ylabel("Minutos")

    axes[1].bar(etiquetas, sistema, color="#f39c12")
    axes[1].set_title("Tiempo promedio en sistema (min)")

    axes[2].bar(etiquetas, abandono, color="#e74c3c")
    axes[2].set_title("Tasa de abandono (%)")

    for ax in axes:
        ax.set_xticklabels(etiquetas, rotation=15, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle("Comparativa de escenarios")
    plt.tight_layout()
    plt.show()


def _promedio(valores: Iterable[float]) -> float:
    lista = list(valores)
    return sum(lista) / len(lista) if lista else 0.0
