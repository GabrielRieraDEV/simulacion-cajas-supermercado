"""Procesos de eventos discretos para el sistema de simulación."""

from __future__ import annotations

import itertools
import random
from typing import TYPE_CHECKING, Callable, Generator, Optional

import simpy

from .cliente import Cliente

if TYPE_CHECKING:
    from .supermercado import Supermercado


def llegada_clientes(
    supermercado: "Supermercado",
    tasa_llegada: float,
    generador_productos: Optional[Callable[[], int]] = None,
) -> Generator[simpy.events.Event, None, None]:
    """Genera entidades de clientes según un proceso de Poisson."""

    if tasa_llegada <= 0:
        return

    generador_productos = generador_productos or (lambda: random.randint(5, 45))
    tiempo_max_espera = float(
        supermercado.configuracion.get("tiempo_max_espera_tolerado", 10.0)
    )
    identificadores = itertools.count(start=1)

    while True:
        interarribo = random.expovariate(tasa_llegada)
        yield supermercado.env.timeout(interarribo)

        cliente = Cliente(
            identificador=f"CLI-{next(identificadores)}",
            numero_productos=max(1, generador_productos()),
            tiempo_llegada=supermercado.env.now,
            tiempo_maximo_espera=tiempo_max_espera,
        )
        supermercado.registrar_llegada(cliente)
