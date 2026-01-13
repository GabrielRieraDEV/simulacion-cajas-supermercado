"""Escenarios operativos predefinidos para el supermercado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping

from .caja import CajaRegistradora, TipoCaja
from ..config import (
    DEFAULT_CONFIG,
    TASA_LLEGADA_FIN_DE_MES,
    TASA_LLEGADA_NORMAL,
    TIEMPO_PROMEDIO_SERVICIO,
)


@dataclass(frozen=True, slots=True)
class Escenario:
    nombre: str
    descripcion: str
    configuracion: Mapping[str, object]
    cajas: List[CajaRegistradora]


def escenario_tradicional() -> Escenario:
    """100% de cajas tradicionales operativas."""

    config = _base_config(
        modo="operacion",
        tasa_llegada=TASA_LLEGADA_NORMAL,
    )
    cajas = _crear_cajas(
        [
            (TipoCaja.TRADICIONAL, 6, TIEMPO_PROMEDIO_SERVICIO, 12.0, 1),
        ]
    )
    return Escenario(
        nombre="Tradicional",
        descripcion="100% de cajas atendidas por personal",
        configuracion=config,
        cajas=cajas,
    )


def escenario_hibrido() -> Escenario:
    """Escenario 50% tradicional y 50% automático."""

    config = _base_config(
        modo="hibrido",
        tasa_llegada=TASA_LLEGADA_NORMAL,
    )
    cajas = _crear_cajas(
        [
            (TipoCaja.TRADICIONAL, 4, TIEMPO_PROMEDIO_SERVICIO, 12.0, 1),
            (TipoCaja.AUTOMATICA, 4, 1.2, 15.0, 1),
        ]
    )
    return Escenario(
        nombre="Híbrido",
        descripcion="Distribución 50/50 entre cajas tradicionales y automáticas",
        configuracion=config,
        cajas=cajas,
    )


def escenario_cajas_rapidas() -> Escenario:
    """Escenario con habilitación de cajas rápidas."""

    config = _base_config(
        modo="cajas_rapidas",
        habilitar_caja_rapida=True,
        tasa_llegada=TASA_LLEGADA_NORMAL,
    )
    cajas = _crear_cajas(
        [
            (TipoCaja.TRADICIONAL, 4, TIEMPO_PROMEDIO_SERVICIO, 12.0, 1),
            (TipoCaja.AUTOMATICA, 2, 1.2, 15.0, 1),
            (TipoCaja.RAPIDA, 2, 0.8, 10.0, 1),
        ]
    )
    return Escenario(
        nombre="Cajas rápidas",
        descripcion="Incluye líneas rápidas para compras de <=10 productos",
        configuracion=config,
        cajas=cajas,
    )


def escenario_fin_de_mes() -> Escenario:
    """Escenario de alta demanda al cierre de mes."""

    config = _base_config(
        modo="fin_de_mes",
        tasa_llegada=TASA_LLEGADA_FIN_DE_MES,
    )
    cajas = _crear_cajas(
        [
            (TipoCaja.TRADICIONAL, 6, TIEMPO_PROMEDIO_SERVICIO, 12.0, 1),
            (TipoCaja.AUTOMATICA, 4, 1.2, 15.0, 1),
            (TipoCaja.RAPIDA, 2, 0.8, 10.0, 1),
        ]
    )
    return Escenario(
        nombre="Fin de mes",
        descripcion="Configuración reforzada para picos salariales",
        configuracion=config,
        cajas=cajas,
    )


def todos_los_escenarios() -> Dict[str, Escenario]:
    """Devuelve un diccionario indexado por identificador de escenario."""

    return {
        "tradicional": escenario_tradicional(),
        "hibrido": escenario_hibrido(),
        "cajas_rapidas": escenario_cajas_rapidas(),
        "fin_de_mes": escenario_fin_de_mes(),
    }


def _base_config(**overrides: object) -> Dict[str, object]:
    config = dict(DEFAULT_CONFIG)
    config.update(overrides)
    return config


def _crear_cajas(definiciones: List[tuple]) -> List[CajaRegistradora]:
    cajas: List[CajaRegistradora] = []
    for tipo, cantidad, tiempo_servicio, costo, capacidad in definiciones:
        for _ in range(cantidad):
            cajas.append(
                CajaRegistradora(
                    tipo=tipo,
                    tiempo_servicio=tiempo_servicio,
                    costo_operativo=costo,
                    capacidad=capacidad,
                )
            )
    return cajas
