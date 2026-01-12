"""Definición de recursos de cajas dentro del modelo de simulación."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # Evita dependencias directas de SimPy en esta fase.
    import simpy


class TipoCaja(str, Enum):
    """Tipos de cajas soportados por el sistema."""

    TRADICIONAL = "tradicional"
    AUTOMATICA = "automatica"
    RAPIDA = "rapida"


@dataclass(slots=True)
class CajaRegistradora:
    """Modelo base para un recurso de caja en el supermercado."""

    tipo: TipoCaja
    tiempo_servicio: float  # minutos promedio por cliente
    costo_operativo: float  # unidades monetarias por hora
    capacidad: int  # número de servidores simultáneos (SimPy Resource capacity)
    recurso: Optional["simpy.Resource"] = field(default=None, repr=False)

    def asignar_recurso(self, recurso: "simpy.Resource") -> None:
        """Asocia la instancia concreta del recurso de SimPy."""
        self.recurso = recurso
