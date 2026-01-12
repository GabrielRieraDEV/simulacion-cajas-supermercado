"""Entidad Cliente utilizada dentro de la simulación discreta."""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Cliente:
    """Representa a un cliente que atraviesa el sistema de cajas."""

    identificador: str
    numero_productos: int
    tiempo_llegada: float
    tiempo_maximo_espera: float
    tipo_caja_asignada: Optional[str] = None
    tiempo_inicio_servicio: Optional[float] = None
    tiempo_salida: Optional[float] = None
    abandono: bool = False
    motivo_abandono: Optional[str] = None

    def asignar_caja(self, tipo_caja: str) -> None:
        """Actualiza el tipo de caja asignada al cliente."""
        self.tipo_caja_asignada = tipo_caja
