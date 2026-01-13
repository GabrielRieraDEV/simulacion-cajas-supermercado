"""Panel de control basado en consola para ajustar parámetros del sistema."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from typing import Dict

from simulacion_supermercado.config import (
    TASA_LLEGADA_FIN_DE_MES,
    TASA_LLEGADA_NORMAL,
    TIEMPO_PROMEDIO_SERVICIO,
)
from simulacion_supermercado.simulation.caja import CajaRegistradora, TipoCaja
from simulacion_supermercado.simulation.escenarios import Escenario

DEFAULT_BLUEPRINTS = {
    TipoCaja.TRADICIONAL: {
        "tiempo_servicio": TIEMPO_PROMEDIO_SERVICIO,
        "costo_operativo": 12.0,
        "capacidad": 1,
    },
    TipoCaja.AUTOMATICA: {
        "tiempo_servicio": 1.2,
        "costo_operativo": 15.0,
        "capacidad": 1,
    },
    TipoCaja.RAPIDA: {
        "tiempo_servicio": 0.8,
        "costo_operativo": 10.0,
        "capacidad": 1,
    },
}


class ControlPanel:
    """Pequeño panel interactivo por consola para ajustar el escenario."""

    def __init__(self, escenario: Escenario) -> None:
        self.escenario = escenario
        self.config = dict(escenario.configuracion)
        self.counts = Counter(caja.tipo for caja in escenario.cajas)
        self.blueprints = self._build_blueprints(escenario)

    def lanzar(self) -> Escenario:
        print("\n=== Panel de Control del Supermercado ===")
        while True:
            self._mostrar_estado()
            opcion = input(
                "\nSelecciona una opción "
                "(1: cajas, 2: modo fin de mes, 3: cajas rápidas, q: salir): "
            ).strip().lower()

            if opcion == "1":
                self._configurar_cantidad_cajas()
            elif opcion == "2":
                self._toggle_fin_de_mes()
            elif opcion == "3":
                self._toggle_cajas_rapidas()
            elif opcion in {"q", "quit", "salir"}:
                break
            else:
                print("Opción no válida. Intenta nuevamente.")

        descripcion = (
            f"{self.escenario.descripcion} (ajustado desde el panel de control)"
        )
        cajas = self._reconstruir_cajas()
        return Escenario(
            nombre=f"{self.escenario.nombre} (panel)",
            descripcion=descripcion,
            configuracion=self.config,
            cajas=cajas,
        )

    def _mostrar_estado(self) -> None:
        print("\n---- Estado actual ----")
        print(
            f"Modo: {self.config.get('modo', 'operacion')} | "
            f"Tasa llegada: {self.config.get('tasa_llegada', TASA_LLEGADA_NORMAL):.2f}"
        )
        habilitada = "Sí" if self.config.get("habilitar_caja_rapida") else "No"
        print(f"Cajas rápidas habilitadas: {habilitada}")
        for tipo in TipoCaja:
            print(f"- {tipo.value.capitalize()}: {self.counts.get(tipo, 0)}")

    def _configurar_cantidad_cajas(self) -> None:
        print("\nConfigurar cantidad de cajas por tipo")
        for tipo in TipoCaja:
            actual = self.counts.get(tipo, 0)
            texto = f"{tipo.value.capitalize()} (actual {actual}): "
            nuevo = self._solicitar_entero(texto, minimo=0, valor_por_defecto=actual)
            self.counts[tipo] = nuevo

    def _toggle_fin_de_mes(self) -> None:
        modo_actual = self.config.get("modo")
        if modo_actual == "fin_de_mes":
            self.config["modo"] = "operacion"
            self.config["tasa_llegada"] = TASA_LLEGADA_NORMAL
            print("Modo fin de mes desactivado.")
        else:
            self.config["modo"] = "fin_de_mes"
            self.config["tasa_llegada"] = TASA_LLEGADA_FIN_DE_MES
            print("Modo fin de mes activado: se incrementará la tasa de llegada.")

    def _toggle_cajas_rapidas(self) -> None:
        estado = bool(self.config.get("habilitar_caja_rapida"))
        self.config["habilitar_caja_rapida"] = not estado
        print(
            "Cajas rápidas habilitadas."
            if not estado
            else "Cajas rápidas deshabilitadas."
        )

    def _reconstruir_cajas(self) -> list[CajaRegistradora]:
        cajas: list[CajaRegistradora] = []
        for tipo, cantidad in self.counts.items():
            blueprint = self.blueprints.get(tipo, DEFAULT_BLUEPRINTS[tipo])
            for _ in range(cantidad):
                cajas.append(
                    CajaRegistradora(
                        tipo=tipo,
                        tiempo_servicio=blueprint["tiempo_servicio"],
                        costo_operativo=blueprint["costo_operativo"],
                        capacidad=blueprint["capacidad"],
                    )
                )
        return cajas

    def _build_blueprints(self, escenario: Escenario) -> Dict[TipoCaja, Dict[str, float]]:
        blueprints: Dict[TipoCaja, Dict[str, float]] = defaultdict(dict)
        for caja in escenario.cajas:
            if caja.tipo not in blueprints:
                blueprints[caja.tipo] = {
                    "tiempo_servicio": caja.tiempo_servicio,
                    "costo_operativo": caja.costo_operativo,
                    "capacidad": caja.capacidad,
                }
        for tipo, valores in DEFAULT_BLUEPRINTS.items():
            blueprints.setdefault(tipo, valores)
        return blueprints

    @staticmethod
    def _solicitar_entero(
        mensaje: str, minimo: int = 0, valor_por_defecto: int | None = None
    ) -> int:
        while True:
            dato = input(mensaje).strip()
            if not dato and valor_por_defecto is not None:
                return valor_por_defecto
            try:
                valor = int(dato)
                if valor < minimo:
                    raise ValueError
                return valor
            except ValueError:
                print(f"Ingresa un número entero >= {minimo}.")
