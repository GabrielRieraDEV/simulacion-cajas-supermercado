"""Cálculo de métricas de desempeño para el sistema de cajas."""

from __future__ import annotations

from typing import Iterable, Mapping

from simulacion_supermercado.simulation.cliente import Cliente


def tiempo_promedio_en_cola(clientes: Iterable[Cliente]) -> float:
    """Promedio del tiempo de espera antes de iniciar servicio."""

    tiempos = [
        (cliente.tiempo_inicio_servicio - cliente.tiempo_llegada)
        for cliente in clientes
        if cliente.tiempo_inicio_servicio is not None
    ]
    return sum(tiempos) / len(tiempos) if tiempos else 0.0


def tiempo_promedio_en_sistema(clientes: Iterable[Cliente]) -> float:
    """Tiempo promedio desde llegada hasta salida."""

    tiempos = [
        (cliente.tiempo_salida - cliente.tiempo_llegada)
        for cliente in clientes
        if cliente.tiempo_salida is not None
    ]
    return sum(tiempos) / len(tiempos) if tiempos else 0.0


def tasa_abandono(metricas: Mapping[str, float]) -> float:
    """Relación entre abandonos y clientes totales registrados."""

    abandonos = metricas.get("clientes_abandonaron", 0)
    procesados = metricas.get("clientes_procesados", 0)
    total = abandonos + procesados
    return abandonos / total if total else 0.0


def utilizacion_cajas(metricas_por_caja: Mapping[str, float]) -> Mapping[str, float]:
    """Calcula la utilización por caja usando tiempo ocupado / tiempo total."""

    utilizaciones = {}
    for caja_id, valores in metricas_por_caja.items():
        tiempo_ocupado = valores.get("tiempo_ocupado", 0.0)
        tiempo_total = valores.get("tiempo_total", 0.0)
        utilizaciones[caja_id] = (
            tiempo_ocupado / tiempo_total if tiempo_total > 0 else 0.0
        )
    return utilizaciones
