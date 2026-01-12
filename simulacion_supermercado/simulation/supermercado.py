"""Contenedor principal del sistema de simulación del supermercado."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Callable

import simpy

from .caja import CajaRegistradora
from .cliente import Cliente
from . import procesos


@dataclass
class Supermercado:
    """Gestiona el entorno SimPy y los recursos de cajas."""

    configuracion: Dict[str, object]
    cajas_base: Sequence[CajaRegistradora]
    env: simpy.Environment = field(init=False)
    cajas: List[CajaRegistradora] = field(init=False, default_factory=list)
    metricas: Dict[str, float] = field(init=False)
    clientes_generados: List[Cliente] = field(init=False, default_factory=list)
    proceso_llegadas: Optional[simpy.events.Process] = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.env = simpy.Environment()
        self.metricas = {
            "clientes_procesados": 0,
            "clientes_abandonaron": 0,
            "tiempo_acumulado_espera": 0.0,
        }
        self._registrar_cajas()

    def _registrar_cajas(self) -> None:
        """Crea recursos de SimPy para cada caja disponible."""
        self.cajas = []
        for caja in self.cajas_base:
            recurso = simpy.Resource(self.env, capacity=caja.capacidad)
            caja.asignar_recurso(recurso)
            self.cajas.append(caja)

    def reiniciar_metricas(self) -> None:
        """Restablece métricas acumuladas para nuevas corridas."""
        for clave in self.metricas:
            self.metricas[clave] = 0 if "tiempo" not in clave else 0.0
        self.clientes_generados.clear()

    def registrar_llegada(self, cliente: Cliente) -> None:
        """Almacena la entidad creada para análisis posteriores."""
        self.clientes_generados.append(cliente)

    def iniciar_proceso_llegadas(
        self,
        tasa_llegada: float,
        generador_productos: Optional[Callable[[], int]] = None,
    ) -> None:
        """Programa el proceso de llegada de clientes."""
        self.proceso_llegadas = self.env.process(
            procesos.llegada_clientes(self, tasa_llegada, generador_productos)
        )
