"""Procesos de eventos discretos para el sistema de simulación."""

from __future__ import annotations

import itertools
import random
from typing import TYPE_CHECKING, Callable, Generator, Optional

import simpy

from .caja import CajaRegistradora, TipoCaja
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
        supermercado.env.process(asignar_cliente_a_caja(supermercado, cliente))


def asignar_cliente_a_caja(
    supermercado: "Supermercado", cliente: Cliente
) -> Generator[simpy.events.Event, None, None]:
    """Gestiona la cola y asignación del cliente a la caja seleccionada."""

    caja = seleccionar_caja_para_cliente(supermercado, cliente)
    if caja is None or caja.recurso is None:
        registrar_abandono(supermercado, cliente, "sin_caja_disponible")
        return

    with caja.recurso.request() as solicitud:
        espera_max = supermercado.env.timeout(cliente.tiempo_maximo_espera)
        resultado = yield solicitud | espera_max

        if solicitud not in resultado:
            solicitud.cancel()
            registrar_abandono(supermercado, cliente, "tiempo_excedido")
            return

        cliente.asignar_caja(caja.tipo.value)
        tiempo_espera = supermercado.env.now - cliente.tiempo_llegada
        supermercado.metricas["tiempo_acumulado_espera"] += tiempo_espera
        cliente.tiempo_inicio_servicio = supermercado.env.now

        yield supermercado.env.process(servicio_cliente(supermercado, caja, cliente))


def servicio_cliente(
    supermercado: "Supermercado",
    caja: CajaRegistradora,
    cliente: Cliente,
) -> Generator[simpy.events.Event, None, None]:
    """Simula el tiempo de servicio y salida del sistema."""

    tiempo_atencion = max(0.1, caja.tiempo_servicio)
    yield supermercado.env.timeout(tiempo_atencion)

    cliente.tiempo_salida = supermercado.env.now
    supermercado.metricas["clientes_procesados"] += 1


def seleccionar_caja_para_cliente(
    supermercado: "Supermercado", cliente: Cliente
) -> Optional[CajaRegistradora]:
    """Aplica una regla simple para elegir el tipo de caja."""

    if cliente.numero_productos <= 10:
        for caja in supermercado.cajas:
            if caja.tipo == TipoCaja.RAPIDA:
                return caja

    prioridad = [TipoCaja.AUTOMATICA, TipoCaja.TRADICIONAL]
    for tipo in prioridad:
        for caja in supermercado.cajas:
            if caja.tipo == tipo:
                return caja

    for caja in supermercado.cajas:
        return caja

    return None


def registrar_abandono(
    supermercado: "Supermercado", cliente: Cliente, motivo: str
) -> None:
    """Marca al cliente como abandono y actualiza métricas."""

    cliente.abandono = True
    cliente.motivo_abandono = motivo
    cliente.tiempo_salida = supermercado.env.now
    supermercado.metricas["clientes_abandonaron"] += 1
