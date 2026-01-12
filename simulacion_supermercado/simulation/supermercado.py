"""Contenedor principal del sistema de simulación del supermercado."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import simpy

from .caja import CajaRegistradora


@dataclass
class Supermercado:
    """Gestiona el entorno SimPy y los recursos de cajas."""

    configuracion: Dict[str, object]
    cajas_base: Sequence[CajaRegistradora]
    env: simpy.Environment = field(init=False)
    cajas: List[CajaRegistradora] = field(init=False, default_factory=list)
    metricas: Dict[str, float] = field(init=False)

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
